"""The monitor loop.

Runs a scan every ``interval`` seconds, stores it, diffs it against the last
one and prints any alerts. Designed to run in the foreground under systemd (see
``scripts/setup-daemon.sh``); a single Ctrl-C shuts it down cleanly.
"""

from __future__ import annotations

import threading
import time

from ..config import Config
from ..models import ScanResult
from ..scanner import ScanEngine, ScanOptions
from ..storage import Database
from ..utils.logging import get_logger
from .alerting import AlertEngine

log = get_logger(__name__)


class Monitor:
    def __init__(
        self,
        network: str,
        *,
        interval_seconds: float,
        database: Database,
        config: Config | None = None,
    ) -> None:
        self.network = network
        self.interval_seconds = interval_seconds
        self.database = database
        self.config = config or Config()
        alerts_cfg = self.config.alerts
        self.alert_engine = AlertEngine(
            offline=alerts_cfg.get("offline", True),
            new_device=alerts_cfg.get("new_device", True),
            high_bandwidth_mbps=alerts_cfg.get("high_bandwidth_mbps", 500),
            slow_latency_ms=alerts_cfg.get("slow_latency_ms", 200),
        )
        self._stop = threading.Event()
        self.active_alerts: list = []

    def stop(self) -> None:
        self._stop.set()

    def run_once(self, previous: ScanResult | None) -> ScanResult:
        engine = ScanEngine(ScanOptions(network=self.network))
        result = engine.run()
        alerts = self.alert_engine.evaluate(previous, result)
        result.alerts = alerts
        self.active_alerts = alerts
        self.database.save_scan(result)
        for alert in alerts:
            log.warning("[ALERT] %s", alert.message)
        return result

    def run_forever(self) -> None:
        log.info(
            "Monitoring %s every %.0fs (Ctrl-C to stop)",
            self.network,
            self.interval_seconds,
        )
        previous = self.database.latest_scan(self.network)
        while not self._stop.is_set():
            started = time.monotonic()
            try:
                previous = self.run_once(previous)
            except Exception as exc:  # keep the daemon alive across transient errors
                log.error("Scan cycle failed: %s", exc)
            elapsed = time.monotonic() - started
            wait = max(0.0, self.interval_seconds - elapsed)
            if self._stop.wait(wait):
                break
        log.info("Monitor stopped")
