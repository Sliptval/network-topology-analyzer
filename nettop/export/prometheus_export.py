"""Prometheus text-exposition output.

Emits gauges suitable for scraping or piping to the Pushgateway. Labels are
escaped per the exposition format so hostnames with awkward characters do not
produce invalid metrics.
"""

from __future__ import annotations

from ..models import ScanResult, Status


def render(result: ScanResult) -> str:
    net_label = _escape(result.network)
    lines: list[str] = []

    lines.append("# HELP nettop_devices_total Total devices seen in the last scan.")
    lines.append("# TYPE nettop_devices_total gauge")
    lines.append(f'nettop_devices_total{{network="{net_label}"}} {len(result.devices)}')

    lines.append("# HELP nettop_devices_online Devices currently online.")
    lines.append("# TYPE nettop_devices_online gauge")
    lines.append(
        f'nettop_devices_online{{network="{net_label}"}} {result.online_count}'
    )

    lines.append("# HELP nettop_device_up Per-device up state (1 = online).")
    lines.append("# TYPE nettop_device_up gauge")
    for device in result.devices:
        up = 1 if device.status is Status.ONLINE else 0
        host = _escape(device.hostname or "")
        lines.append(
            f'nettop_device_up{{network="{net_label}",ip="{device.ip}",'
            f'hostname="{host}"}} {up}'
        )

    lines.append("# HELP nettop_device_open_ports Number of open ports per device.")
    lines.append("# TYPE nettop_device_open_ports gauge")
    for device in result.devices:
        lines.append(
            f'nettop_device_open_ports{{network="{net_label}",ip="{device.ip}"}} '
            f"{len(device.ports)}"
        )

    if any(d.latency_ms is not None for d in result.devices):
        lines.append("# HELP nettop_device_latency_ms Round-trip latency per device.")
        lines.append("# TYPE nettop_device_latency_ms gauge")
        for device in result.devices:
            if device.latency_ms is not None:
                lines.append(
                    f'nettop_device_latency_ms{{network="{net_label}",'
                    f'ip="{device.ip}"}} {device.latency_ms}'
                )

    if result.connections:
        lines.append("# HELP nettop_bandwidth_mbps Observed bandwidth per link.")
        lines.append("# TYPE nettop_bandwidth_mbps gauge")
        for conn in result.connections:
            lines.append(
                f'nettop_bandwidth_mbps{{source="{conn.source_ip}",'
                f'dest="{conn.dest_ip}",protocol="{conn.protocol.value}"}} '
                f"{conn.bandwidth_mbps}"
            )

    return "\n".join(lines) + "\n"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
