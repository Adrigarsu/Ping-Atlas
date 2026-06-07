import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.anomaly import check_and_alert


def _make_session(rtt_history: list[float]) -> AsyncMock:
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = rtt_history

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    session = AsyncMock()
    session.execute.return_value = mock_result
    return session


@pytest.mark.asyncio
async def test_alert_created_when_delta_exceeds_threshold() -> None:
    target_id = uuid.uuid4()
    probe_id = uuid.uuid4()
    # rolling avg = 50 ms, current = 150 ms → delta = 100 ms > default 50 ms threshold
    session = _make_session([50.0, 50.0, 50.0])

    with patch.dict("os.environ", {"LATENCY_ALERT_DELTA_MS": "50"}):
        with patch("app.anomaly._send_webhook", new_callable=AsyncMock):
            alert = await check_and_alert(session, target_id, probe_id, current_rtt=150.0)

    assert alert is not None
    assert alert.target_id == target_id
    assert alert.probe_id == probe_id
    assert alert.rtt_ms == 150.0
    assert abs(alert.rolling_avg_ms - 50.0) < 0.01
    assert abs(alert.delta_ms - 100.0) < 0.01
    session.add.assert_called_once_with(alert)


@pytest.mark.asyncio
async def test_no_alert_when_delta_within_threshold() -> None:
    target_id = uuid.uuid4()
    probe_id = uuid.uuid4()
    # rolling avg = 60 ms, current = 70 ms → delta = 10 ms ≤ 50 ms threshold
    session = _make_session([60.0, 60.0, 60.0])

    with patch.dict("os.environ", {"LATENCY_ALERT_DELTA_MS": "50"}):
        alert = await check_and_alert(session, target_id, probe_id, current_rtt=70.0)

    assert alert is None
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_no_alert_when_no_probe_history() -> None:
    target_id = uuid.uuid4()
    probe_id = uuid.uuid4()
    session = _make_session([])  # no history

    alert = await check_and_alert(session, target_id, probe_id, current_rtt=500.0)

    assert alert is None
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_sent_on_alert() -> None:
    target_id = uuid.uuid4()
    probe_id = uuid.uuid4()
    session = _make_session([40.0])

    with patch.dict("os.environ", {"LATENCY_ALERT_DELTA_MS": "50", "ALERT_WEBHOOK_URL": "http://hook.example/alert"}):
        with patch("app.anomaly._send_webhook", new_callable=AsyncMock) as mock_webhook:
            alert = await check_and_alert(session, target_id, probe_id, current_rtt=200.0)

    assert alert is not None
    mock_webhook.assert_called_once_with(alert)


@pytest.mark.asyncio
async def test_webhook_skipped_when_url_not_set() -> None:
    import asyncio
    import urllib.request
    from app.anomaly import _send_webhook
    from app.db.models import Alert
    from datetime import UTC, datetime

    alert = Alert(
        id=uuid.uuid4(),
        target_id=uuid.uuid4(),
        probe_id=uuid.uuid4(),
        triggered_at=datetime.now(UTC),
        rtt_ms=200.0,
        rolling_avg_ms=50.0,
        delta_ms=150.0,
    )

    with patch.dict("os.environ", {}, clear=True):
        with patch.object(urllib.request, "urlopen") as mock_urlopen:
            await _send_webhook(alert)
            mock_urlopen.assert_not_called()