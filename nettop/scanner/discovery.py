"""Host discovery.

Two complementary probes decide whether a host is up:

* an ICMP echo via the system ``ping`` (works unprivileged on every platform
  and also gives us a TTL for a rough OS guess), and
* a TCP connect to a handful of very common ports, which catches hosts that
  drop ICMP but still serve something.

Both run in a thread pool so a /24 sweep finishes in seconds.
"""

from __future__ import annotations

import re
import selectors
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from ..utils import net
from ..utils.logging import get_logger

log = get_logger(__name__)

# Ports probed during discovery only to decide "is anything alive here?".
_LIVENESS_PORTS = (80, 443, 22, 445, 3389, 8080)

_TTL_RE = re.compile(r"ttl[=:]\s*(\d+)", re.IGNORECASE)


@dataclass
class LiveHost:
    ip: str
    reachable_via: str  # "icmp" or "tcp"
    ttl: int | None = None
    latency_ms: float | None = None


def _ping(ip: str, timeout_ms: int) -> LiveHost | None:
    cmd = net.default_ping_command(ip, timeout_ms)
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=max(2, timeout_ms / 1000 + 1),
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    # Some platforms return 0 even for "unreachable"; require a TTL as proof.
    ttl_match = _TTL_RE.search(completed.stdout)
    if not ttl_match:
        return None
    ttl = int(ttl_match.group(1))
    latency = _parse_ping_latency(completed.stdout)
    return LiveHost(ip=ip, reachable_via="icmp", ttl=ttl, latency_ms=latency)


def _parse_ping_latency(output: str) -> float | None:
    match = re.search(r"time[=<]\s*([\d.]+)\s*ms", output, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _tcp_ping(ip: str, timeout: float) -> LiveHost | None:
    """Probe several common ports at once and return on the first that answers.

    Uses non-blocking connects multiplexed through a selector so all ports
    share a single ``timeout`` window instead of summing per port. That keeps
    the discovery sweep fast even when most hosts are down.
    """
    selector = selectors.DefaultSelector()
    sockets: list[socket.socket] = []
    try:
        for port in _LIVENESS_PORTS:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setblocking(False)
            err = sock.connect_ex((ip, port))
            # 0 => connected immediately; EINPROGRESS/EWOULDBLOCK => pending.
            if err == 0:
                return LiveHost(ip=ip, reachable_via="tcp")
            selector.register(sock, selectors.EVENT_WRITE)
            sockets.append(sock)

        deadline = time.monotonic() + timeout
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            for key, _ in selector.select(remaining):
                sock = key.fileobj  # type: ignore[assignment]
                if sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR) == 0:
                    return LiveHost(ip=ip, reachable_via="tcp")
                selector.unregister(sock)
        return None
    finally:
        selector.close()
        for sock in sockets:
            sock.close()


def discover(
    targets: list[str],
    *,
    timeout_ms: int = 1000,
    workers: int = 128,
    tcp_fallback: bool = True,
) -> list[LiveHost]:
    """Return the subset of ``targets`` that appear to be online."""
    tcp_timeout = timeout_ms / 1000

    def probe(ip: str) -> LiveHost | None:
        host = _ping(ip, timeout_ms)
        if host is not None:
            return host
        if tcp_fallback:
            return _tcp_ping(ip, tcp_timeout)
        return None

    live: list[LiveHost] = []
    worker_count = max(1, min(workers, len(targets) or 1))
    log.info("Discovering hosts across %d addresses (%d workers)", len(targets), worker_count)
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = {pool.submit(probe, ip): ip for ip in targets}
        for future in as_completed(futures):
            host = future.result()
            if host is not None:
                live.append(host)
    live.sort(key=lambda h: tuple(int(o) for o in h.ip.split(".")))
    log.info("Found %d live host(s)", len(live))
    return live
