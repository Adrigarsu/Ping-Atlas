from unittest.mock import MagicMock, patch

from app.probe.icmp_probe import ping


def _make_reply() -> MagicMock:
    return MagicMock()


@patch("app.probe.icmp_probe.sr1")
def test_ping_returns_rtt_list(mock_sr1: MagicMock) -> None:
    mock_sr1.return_value = _make_reply()
    result = ping("8.8.8.8", count=3)
    assert len(result) == 3
    assert all(isinstance(r, float) for r in result)
    assert mock_sr1.call_count == 3


@patch("app.probe.icmp_probe.sr1")
def test_ping_timeout_returns_none(mock_sr1: MagicMock) -> None:
    mock_sr1.return_value = None
    result = ping("8.8.8.8", count=3)
    assert result == [None, None, None]


@patch("app.probe.icmp_probe.sr1")
def test_ping_partial_timeout(mock_sr1: MagicMock) -> None:
    mock_sr1.side_effect = [_make_reply(), None, _make_reply()]
    result = ping("8.8.8.8", count=3)
    assert result[0] is not None
    assert result[1] is None
    assert result[2] is not None