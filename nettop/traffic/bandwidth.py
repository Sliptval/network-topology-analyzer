"""Bandwidth bookkeeping for captured traffic."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BandwidthAccumulator:
    total_bytes: int = 0
    packets: int = 0

    def add(self, length: int) -> None:
        self.total_bytes += max(0, length)
        self.packets += 1

    def mbps(self, duration_seconds: float) -> float:
        if duration_seconds <= 0:
            return 0.0
        bits = self.total_bytes * 8
        return bits / duration_seconds / 1_000_000
