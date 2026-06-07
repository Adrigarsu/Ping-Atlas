import os
import time
from dataclasses import dataclass

from scapy.layers.inet import ICMP, IP
from scapy.sendrecv import sr1

MAX_HOPS = int(os.environ.get("MAX_HOPS", 30))


@dataclass
class Hop:
    ttl: int
    ip: str | None
    rtt_ms: float | None


def traceroute(host: str, max_hops: int = MAX_HOPS, timeout: float = 2.0) -> list[Hop]:
    """Probe each TTL from 1 to max_hops and return per-hop results."""
    hops: list[Hop] = []

    for ttl in range(1, max_hops + 1):
        packet = IP(dst=host, ttl=ttl) / ICMP()
        t0 = time.perf_counter()
        reply = sr1(packet, timeout=timeout, verbose=False)
        rtt_ms = round((time.perf_counter() - t0) * 1000, 3) if reply else None

        if reply is None:
            hops.append(Hop(ttl=ttl, ip=None, rtt_ms=None))
            continue

        hop_ip: str = reply[IP].src
        hops.append(Hop(ttl=ttl, ip=hop_ip, rtt_ms=rtt_ms))

        if hop_ip == reply.dst:
            break

    return hops