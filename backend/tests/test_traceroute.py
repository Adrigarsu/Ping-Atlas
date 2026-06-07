from unittest.mock import MagicMock, patch

from app.probe.traceroute import Hop, traceroute


def _make_reply(src: str, dst: str) -> MagicMock:
    reply = MagicMock()
    reply.__getitem__ = lambda self, key: MagicMock(src=src)
    reply.dst = dst
    return reply


@patch("app.probe.traceroute.sr1")
def test_traceroute_returns_hop_list(mock_sr1: MagicMock) -> None:
    target = "8.8.8.8"
    mock_sr1.side_effect = [
        _make_reply("10.0.0.1", target),
        _make_reply("10.0.0.2", target),
        _make_reply(target, target),
    ]
    result = traceroute(target, max_hops=30)
    assert len(result) == 3
    assert all(isinstance(h, Hop) for h in result)
    assert result[0].ttl == 1
    assert result[0].ip == "10.0.0.1"
    assert result[0].rtt_ms is not None


@patch("app.probe.traceroute.sr1")
def test_traceroute_stops_at_destination(mock_sr1: MagicMock) -> None:
    target = "8.8.8.8"
    mock_sr1.side_effect = [
        _make_reply("10.0.0.1", target),
        _make_reply(target, target),
        _make_reply(target, target),  # should never be called
    ]
    result = traceroute(target, max_hops=30)
    assert len(result) == 2
    assert mock_sr1.call_count == 2


@patch("app.probe.traceroute.sr1")
def test_traceroute_unresponsive_hop(mock_sr1: MagicMock) -> None:
    target = "8.8.8.8"
    mock_sr1.side_effect = [
        None,
        _make_reply(target, target),
    ]
    result = traceroute(target, max_hops=30)
    assert result[0] == Hop(ttl=1, ip=None, rtt_ms=None)
    assert result[1].ip == target