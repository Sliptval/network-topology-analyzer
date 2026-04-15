"""Markdown network documentation.

Produces a document you can drop straight into a wiki or a repo: an overview, a
device table, per-device detail sections, observed connections and any alerts.
"""

from __future__ import annotations

from ..models import ScanResult


def render(result: ScanResult) -> str:
    parts: list[str] = []
    parts.append(f"# Network Documentation — `{result.network}`\n")
    parts.append(
        f"_Generated {result.scan_timestamp} · "
        f"{len(result.devices)} device(s), {result.online_count} online._\n"
    )

    parts.append("## Overview\n")
    parts.append(_overview_table(result))

    parts.append("\n## Devices\n")
    parts.append(_device_table(result))

    parts.append("\n## Device details\n")
    for device in result.devices:
        parts.append(_device_section(device))

    if result.connections:
        parts.append("\n## Connections\n")
        parts.append(_connection_table(result))

    if result.alerts:
        parts.append("\n## Alerts\n")
        for alert in result.alerts:
            parts.append(f"- **{alert.severity.value.upper()}** — {alert.message}")

    return "\n".join(parts).rstrip() + "\n"


def _overview_table(result: ScanResult) -> str:
    type_counts: dict[str, int] = {}
    for device in result.devices:
        type_counts[device.device_type.value] = (
            type_counts.get(device.device_type.value, 0) + 1
        )
    rows = ["| Metric | Value |", "| --- | --- |"]
    rows.append(f"| Network | `{result.network}` |")
    rows.append(f"| Devices online | {result.online_count} |")
    rows.append(f"| Total devices | {len(result.devices)} |")
    for name, count in sorted(type_counts.items()):
        rows.append(f"| {name.capitalize()} devices | {count} |")
    return "\n".join(rows)


def _device_table(result: ScanResult) -> str:
    rows = [
        "| IP | Hostname | Type | OS | Open ports |",
        "| --- | --- | --- | --- | --- |",
    ]
    for device in result.devices:
        ports = ", ".join(str(p) for p in device.ports) or "—"
        rows.append(
            f"| `{device.ip}` | {device.hostname or '—'} | "
            f"{device.device_type.value} | {device.os or '—'} | {ports} |"
        )
    return "\n".join(rows)


def _device_section(device) -> str:  # noqa: ANN001 - Device
    heading = device.hostname or device.ip
    lines = [f"### {heading} (`{device.ip}`)\n"]
    lines.append(f"- **Status:** {device.status.value}")
    if device.mac:
        lines.append(f"- **MAC:** `{device.mac}`")
    if device.vendor:
        lines.append(f"- **Vendor:** {device.vendor}")
    if device.os:
        lines.append(f"- **OS:** {device.os}")
    lines.append(f"- **Type:** {device.device_type.value}")
    if device.services:
        lines.append(f"- **Services:** {', '.join(device.services)}")
    if device.ports:
        lines.append(
            "- **Open ports:** " + ", ".join(f"`{p}`" for p in device.ports)
        )
    if device.latency_ms is not None:
        lines.append(f"- **Latency:** {device.latency_ms:.1f} ms")
    lines.append("")
    return "\n".join(lines)


def _connection_table(result: ScanResult) -> str:
    rows = [
        "| Source | Destination | Protocol | Bandwidth (Mbps) |",
        "| --- | --- | --- | --- |",
    ]
    for conn in result.connections:
        rows.append(
            f"| `{conn.source_ip}` | `{conn.dest_ip}` | "
            f"{conn.protocol.value.upper()} | {conn.bandwidth_mbps:.1f} |"
        )
    return "\n".join(rows)
