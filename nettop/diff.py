"""Compare two scans and describe what changed.

Used by ``nettop diff`` and, in the daemon, to raise new-device / offline
alerts. The result is a plain dataclass so it can be rendered as text or JSON.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import Device, ScanResult


@dataclass
class PortChange:
    ip: str
    opened: list[int] = field(default_factory=list)
    closed: list[int] = field(default_factory=list)


@dataclass
class ScanDiff:
    new_devices: list[Device] = field(default_factory=list)
    removed_devices: list[Device] = field(default_factory=list)
    port_changes: list[PortChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.new_devices or self.removed_devices or self.port_changes)

    def to_dict(self) -> dict:
        return {
            "new_devices": [d.ip for d in self.new_devices],
            "removed_devices": [d.ip for d in self.removed_devices],
            "port_changes": [
                {"ip": pc.ip, "opened": pc.opened, "closed": pc.closed}
                for pc in self.port_changes
            ],
        }


def diff_scans(before: ScanResult, after: ScanResult) -> ScanDiff:
    before_by_ip = {d.ip: d for d in before.devices}
    after_by_ip = {d.ip: d for d in after.devices}

    result = ScanDiff()
    for ip, device in after_by_ip.items():
        if ip not in before_by_ip:
            result.new_devices.append(device)
    for ip, device in before_by_ip.items():
        if ip not in after_by_ip:
            result.removed_devices.append(device)

    for ip in sorted(set(before_by_ip) & set(after_by_ip)):
        old_ports = set(before_by_ip[ip].ports)
        new_ports = set(after_by_ip[ip].ports)
        opened = sorted(new_ports - old_ports)
        closed = sorted(old_ports - new_ports)
        if opened or closed:
            result.port_changes.append(PortChange(ip=ip, opened=opened, closed=closed))

    result.new_devices.sort(key=lambda d: _ip_key(d.ip))
    result.removed_devices.sort(key=lambda d: _ip_key(d.ip))
    return result


def render_diff(diff: ScanDiff) -> str:
    if not diff.has_changes:
        return "No changes between the two scans.\n"

    lines: list[str] = ["Topology changes", ""]
    if diff.new_devices:
        lines.append(f"New devices ({len(diff.new_devices)}):")
        for device in diff.new_devices:
            label = device.hostname or "unknown"
            lines.append(f"  + {device.ip}  {label}")
        lines.append("")
    if diff.removed_devices:
        lines.append(f"Removed devices ({len(diff.removed_devices)}):")
        for device in diff.removed_devices:
            label = device.hostname or "unknown"
            lines.append(f"  - {device.ip}  {label}")
        lines.append("")
    if diff.port_changes:
        lines.append("Port changes:")
        for change in diff.port_changes:
            if change.opened:
                lines.append(
                    f"  {change.ip}  opened: "
                    + ", ".join(str(p) for p in change.opened)
                )
            if change.closed:
                lines.append(
                    f"  {change.ip}  closed: "
                    + ", ".join(str(p) for p in change.closed)
                )
    return "\n".join(lines).rstrip() + "\n"


def _ip_key(ip: str) -> tuple[int, ...]:
    try:
        return tuple(int(o) for o in ip.split("."))
    except ValueError:
        return (0,)
