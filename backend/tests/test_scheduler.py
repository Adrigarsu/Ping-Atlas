from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_target(host: str, enabled: bool) -> MagicMock:
    t = MagicMock()
    t.host = host
    t.enabled = enabled
    return t


@pytest.mark.asyncio
async def test_probe_all_enabled_calls_execute_for_enabled_only() -> None:
    enabled = _make_target("8.8.8.8", True)
    disabled = _make_target("1.1.1.1", False)

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [enabled]  # query already filtered by enabled=True

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    mock_session_factory = MagicMock(return_value=mock_session)

    with patch("app.scheduler.AsyncSessionLocal", mock_session_factory):
        with patch("app.scheduler._execute_probe", new_callable=AsyncMock) as mock_exec:
            from app.scheduler import _probe_all_enabled

            await _probe_all_enabled()

            mock_exec.assert_called_once_with("8.8.8.8")
            # disabled target must not be probed
            for call in mock_exec.call_args_list:
                assert call.args[0] != disabled.host


@pytest.mark.asyncio
async def test_probe_all_enabled_continues_after_failure() -> None:
    t1 = _make_target("8.8.8.8", True)
    t2 = _make_target("1.1.1.1", True)

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [t1, t2]

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    mock_session_factory = MagicMock(return_value=mock_session)

    async def fail_first(host: str) -> None:
        if host == "8.8.8.8":
            raise ValueError("cannot resolve")

    with patch("app.scheduler.AsyncSessionLocal", mock_session_factory):
        with patch("app.scheduler._execute_probe", side_effect=fail_first):
            from app import scheduler

            # should not raise — errors are caught per-target
            await scheduler._probe_all_enabled()


def test_start_adds_job_and_stop_shuts_down() -> None:
    mock_scheduler = MagicMock()
    mock_scheduler.running = True

    with patch("app.scheduler._scheduler", mock_scheduler):
        with patch.dict("os.environ", {"PROBE_INTERVAL_SECONDS": "60"}):
            from app import scheduler

            scheduler.start()
            mock_scheduler.add_job.assert_called_once()
            mock_scheduler.start.assert_called_once()

            scheduler.stop()
            mock_scheduler.shutdown.assert_called_once_with(wait=False)