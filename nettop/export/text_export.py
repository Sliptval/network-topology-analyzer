"""Human-friendly terminal output.

A boxed, aligned table of devices followed by a short summary. No ANSI colours,
so it stays readable when piped to a file or a pager.
"""

from __future__ import annotations

from collections import Counter

from ..models import ScanResult, Status

_COLUMNS = ("IP", "HOSTNAME", "OS", "TYPE", "ST", "PORTS")


def render(result: ScanResult) -> str:
    lines: list[str] = []
    lines.append(_header(result))
    lines.append("")
    if result.devices:
        lines.append(_device_table(result))
    else:
        lines.append("  No live devices found on this network.")
    lines.append("")
    lines.extend(_summary(result))
    if result.connections:
        lines.append("")
        lines.extend(_traffic(result))
    if result.alerts:
        lines.append("")
        lines.extend(_alerts(result))
    return "\n".join(lines).rstrip() + "\n"


def _header(result: ScanResult) -> str:
    title = f"Network scan: {result.network}"
    meta = f"{result.scan_timestamp}  |  {len(result.devices)} device(s)  |  {result.online_count} online"
    width = max(len(title), len(meta)) + 2
    top = "┌" + "─" * width + "┐"
    bottom = "└" + "─" * width + "┘"
    body = "\n".join(
        "│ " + text.ljust(width - 1) + "│" for text in (title, meta)
    )
    return f"{top}\n{body}\n{bottom}"


def _device_table(result: ScanResult) -> str:
    rows = []
    for device in result.devices:
        ports = ", ".join(str(p) for p in device.ports[:6])
        if len(device.ports) > 6:
            ports += f" (+{len(device.ports) - 6})"
        status = "✓" if device.status is Status.ONLINE else "✗"
        rows.append(
            (
                device.ip,
                device.hostname or "-",
                (device.os or "-")[:20],
                device.device_type.value,
                status,
                ports or "-",
            )
        )

    widths = [len(col) for col in _COLUMNS]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    def fmt_row(cells: tuple, sep: str = " │ ") -> str:
        return "  " + sep.join(str(c).ljust(widths[i]) for i, c in enumerate(cells))

    divider = "  " + "─┼─".join("─" * w for w in widths)
    out = [fmt_row(_COLUMNS), divider]
    out.extend(fmt_row(row) for row in rows)
    return "\n".join(out)


def _summary(result: ScanResult) -> list[str]:
    type_counts = Counter(d.device_type.value for d in result.devices)
    service_counts: Counter[str] = Counter()
    for device in result.devices:
        service_counts.update(device.services)

    lines = ["Summary"]
    lines.append("  Devices by type:")
    for name, count in sorted(type_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"    {name:<10} {count}")
    if service_counts:
        lines.append("  Top services:")
        for name, count in service_counts.most_common(8):
            lines.append(f"    {name:<24} {count}")
    return lines


def _traffic(result: ScanResult) -> list[str]:
    lines = ["Traffic"]
    for conn in sorted(
        result.connections, key=lambda c: c.bandwidth_mbps, reverse=True
    )[:12]:
        latency = f"{conn.latency_ms:.1f}ms" if conn.latency_ms is not None else "-"
        lines.append(
            f"  {conn.source_ip:>15} -> {conn.dest_ip:<15} "
            f"{conn.protocol.value.upper():<4} {conn.bandwidth_mbps:>7.1f} Mbps  {latency}"
        )
    return lines


def _alerts(result: ScanResult) -> list[str]:
    lines = ["Alerts"]
    for alert in result.alerts:
        lines.append(f"  [{alert.severity.value.upper()}] {alert.message}")
    return lines
