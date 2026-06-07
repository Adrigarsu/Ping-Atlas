import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.limiter import limiter
from app.main import app

VALID_KEY = "test-secret-key"


@pytest.fixture(autouse=True)
def reset_limiter() -> None:
    limiter._storage.reset()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_probe_without_api_key_returns_401(client: TestClient) -> None:
    resp = client.post("/probe", json={"target": "8.8.8.8"})
    assert resp.status_code == 401


def test_probe_with_invalid_api_key_returns_401(client: TestClient) -> None:
    resp = client.post("/probe", json={"target": "8.8.8.8"}, headers={"X-Api-Key": "wrong-key"})
    assert resp.status_code == 401


def test_probe_with_valid_api_key_succeeds(client: TestClient) -> None:
    with patch.dict("os.environ", {"API_KEYS": VALID_KEY}):
        with patch("app.api.probes._execute_probe", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = uuid.uuid4()
            resp = client.post("/probe", json={"target": "8.8.8.8"}, headers={"X-Api-Key": VALID_KEY})
    assert resp.status_code == 202


def test_probe_accepts_any_key_in_comma_list(client: TestClient) -> None:
    second_key = "another-key"
    with patch.dict("os.environ", {"API_KEYS": f"{VALID_KEY},{second_key}"}):
        with patch("app.api.probes._execute_probe", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = uuid.uuid4()
            resp = client.post("/probe", json={"target": "8.8.8.8"}, headers={"X-Api-Key": second_key})
    assert resp.status_code == 202


def test_read_endpoints_require_no_auth(client: TestClient) -> None:
    assert client.get("/health").status_code == 200
    # DB-dependent endpoints: verify they are not blocked by auth (not 401)
    assert client.get("/results").status_code != 401
    assert client.get("/targets").status_code != 401
    assert client.get("/alerts").status_code != 401