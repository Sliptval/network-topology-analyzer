"""CSV output - one row per device, for spreadsheets and quick grep/awk."""

from __future__ import annotations

import csv
import io

from ..models import ScanResult


def render(result: ScanResult) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "ip",
            "mac",
            "hostname",
            "os",
            "vendor",
            "device_type",
            "status",
            "ports",
            "services",
            "latency_ms",
            "last_seen",
        ]
    )
    for device in result.devices:
        writer.writerow(
            [
                device.ip,
                device.mac or "",
                device.hostname or "",
                device.os or "",
                device.vendor or "",
                device.device_type.value,
                device.status.value,
                " ".join(str(p) for p in device.ports),
                " ".join(device.services),
                "" if device.latency_ms is None else device.latency_ms,
                device.last_seen,
            ]
        )
    return buffer.getvalue()
