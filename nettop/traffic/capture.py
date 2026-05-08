"""Packet capture via tcpdump.

Live capture needs both a capture tool and elevated privileges, neither of which
is guaranteed. The design here is honest about that: :func:`capture_available`
reports whether capture can work, and :class:`TrafficCapture` raises a clear
error rather than pretending. Output is aggregated into per-link
:class:`~nettop.models.Connection` records.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from collections import defaultdict

from ..models import Connection, Protocol
from ..utils.logging import get_logger
from ..utils.privileges import elevation_hint, is_elevated
from .bandwidth import BandwidthAccumulator

log = get_logger(__name__)

# tcpdump verbose line, e.g.:
# 12:00:00.1 IP 192.168.1.5.5432 > 192.168.1.10.51000: Flags [P.], length 240
_LINE_RE = re.compile(
    r"IP6?\s+"
    r"(?P<src>[\d.]+)(?:\.\d+)?\s+>\s+"
    r"(?P<dst>[\d.]+)(?:\.\d+)?:.*?length\s+(?P<length>\d+)",
)


def capture_available() -> tuple[bool, str]:
    """Return (available, reason). Reason is empty when available."""
    if shutil.which("tcpdump") is None and shutil.which("tshark") is None:
        return False, "neither tcpdump nor tshark is installed"
    if not is_elevated():
        return False, f"packet capture needs elevated privileges. {elevation_hint()}"
    return True, ""


class TrafficCapture:
    """Capture packets for a fixed duration and summarise per-link bandwidth."""

    def __init__(self, interface: str | None = None) -> None:
        self.interface = interface

    def capture(self, duration_seconds: float) -> list[Connection]:
        available, reason = capture_available()
        if not available:
            raise RuntimeError(reason)

        tcpdump = shutil.which("tcpdump")
        if not tcpdump:
            raise RuntimeError("tcpdump is required for traffic capture")

        cmd = [tcpdump, "-n", "-l", "-q"]
        if self.interface:
            cmd += ["-i", self.interface]
        log.info("Capturing traffic for %.0fs", duration_seconds)

        acc: dict[tuple[str, str], BandwidthAccumulator] = defaultdict(
            BandwidthAccumulator
        )
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError(f"could not start tcpdump: {exc}") from exc

        try:
            import time

            deadline = time.monotonic() + duration_seconds
            assert proc.stdout is not None
            for line in proc.stdout:
                match = _LINE_RE.search(line)
                if match:
                    key = (match.group("src"), match.group("dst"))
                    acc[key].add(int(match.group("length")))
                if time.monotonic() >= deadline:
                    break
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:  # pragma: no cover
                proc.kill()

        connections: list[Connection] = []
        for (src, dst), bw in acc.items():
            connections.append(
                Connection(
                    source_ip=src,
                    dest_ip=dst,
                    protocol=Protocol.TCP,
                    bandwidth_mbps=round(bw.mbps(duration_seconds), 3),
                    packets=bw.packets,
                    bytes=bw.total_bytes,
                )
            )
        connections.sort(key=lambda c: c.bandwidth_mbps, reverse=True)
        return connections
