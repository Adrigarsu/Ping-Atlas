import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.limiter import limiter
from app.main import app

VALID_KEY = "test-key"
AUTH_HEADERS = {"X-Api-Key": VALID_KEY}


@pytest.fixture(autouse=True)
def reset_limiter() -> None:
    limiter._storage.reset()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_probe_allowed_within_limit(client: TestClient) -> None:
    with patch.dict("os.environ", {"API_KEYS": VALID_KEY}):
        with patch("app.api.probes._execute_probe", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = uuid.uuid4()
            resp = client.post("/probe", json={"target": "8.8.8.8"}, headers=AUTH_HEADERS)
    assert resp.status_code == 202


def test_probe_rate_limited_after_10_requests(client: TestClient) -> None:
    with patch.dict("os.environ", {"API_KEYS": VALID_KEY}):
        with patch("app.api.probes._execute_probe", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = uuid.uuid4()

            for i in range(10):
                resp = client.post("/probe", json={"target": "8.8.8.8"}, headers=AUTH_HEADERS)
                assert resp.status_code == 202, f"Request {i + 1} should be allowed"

            resp = client.post("/probe", json={"target": "8.8.8.8"}, headers=AUTH_HEADERS)

    assert resp.status_code == 429
    assert "Retry-After" in resp.headers


def test_other_endpoints_not_rate_limited(client: TestClient) -> None:
    for _ in range(15):
        resp = client.get("/health")
        assert resp.status_code == 200