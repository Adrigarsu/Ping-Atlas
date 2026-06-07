import time

from scapy.layers.inet import ICMP, IP
from scapy.sendrecv import sr1


def ping(host: str, count: int = 4, timeout: float = 2.0) -> list[float | None]:
    """Send ICMP echo requests and return RTT in ms per packet (None on timeout)."""
    results: list[float | None] = []

    for seq in range(count):
        packet = IP(dst=host) / ICMP(seq=seq)
        t0 = time.perf_counter()
        reply = sr1(packet, timeout=timeout, verbose=False)
        elapsed = (time.perf_counter() - t0) * 1000

        if reply is None:
            results.append(None)
        else:
            results.append(round(elapsed, 3))

    return results