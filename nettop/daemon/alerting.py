"""Alert generation.

Compares each fresh scan against the previous one and against configured
thresholds to produce :class:`~nettop.models.Alert` records. Pure functions of
(previous, current, thresholds) so the logic is easy to unit test.
"""

from __future__ import annotations

from ..diff import diff_scans
from ..models import Alert, ScanResult, Severity


class AlertEngine:
    def __init__(
        self,
        *,
        offline: bool = True,
        new_device: bool = True,
        high_bandwidth_mbps: float = 500,
        slow_latency_ms: float = 200,
    ) -> None:
        self.offline = offline
        self.new_device = new_device
        self.high_bandwidth_mbps = high_bandwidth_mbps
        self.slow_latency_ms = slow_latency_ms

    def evaluate(
        self, previous: ScanResult | None, current: ScanResult
    ) -> list[Alert]:
        alerts: list[Alert] = []

        if previous is not None:
            change = diff_scans(previous, current)
            if self.new_device:
                for device in change.new_devices:
                    label = device.hostname or device.ip
                    alerts.append(
                        Alert(
                            device_ip=device.ip,
                            alert_type="new_device",
                            message=f"New device joined the network: {label} ({device.ip})",
                            severity=Severity.INFO,
                        )
                    )
            if self.offline:
                for device in change.removed_devices:
                    label = device.hostname or device.ip
                    alerts.append(
                        Alert(
                            device_ip=device.ip,
                            alert_type="offline",
                            message=f"Device went offline: {label} ({device.ip})",
                            severity=Severity.WARNING,
                        )
                    )

        for device in current.devices:
            if (
                device.latency_ms is not None
                and device.latency_ms >= self.slow_latency_ms
            ):
                alerts.append(
                    Alert(
                        device_ip=device.ip,
                        alert_type="slow_latency",
                        message=(
                            f"High latency to {device.ip}: "
                            f"{device.latency_ms:.0f} ms"
                        ),
                        severity=Severity.WARNING,
                    )
                )

        for conn in current.connections:
            if conn.bandwidth_mbps >= self.high_bandwidth_mbps:
                alerts.append(
                    Alert(
                        device_ip=conn.source_ip,
                        alert_type="high_bandwidth",
                        message=(
                            f"High bandwidth {conn.source_ip} -> {conn.dest_ip}: "
                            f"{conn.bandwidth_mbps:.0f} Mbps"
                        ),
                        severity=Severity.WARNING,
                    )
                )

        return alerts
