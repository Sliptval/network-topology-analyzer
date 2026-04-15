"""ASCII topology graph.

Renders the network as a tree rooted at the gateway (or a synthetic root when
no gateway is obvious), with each device shown as a branch and its key services
listed beneath it.
"""

from __future__ import annotations

import ipaddress

from ..models import Device, ScanResult


def render(result: ScanResult) -> str:
    devices = list(result.devices)
    if not devices:
        return f"{result.network}\n  (no devices found)\n"

    gateway = _guess_gateway(devices, result.network)
    lines: list[str] = [f"{result.network}"]
    root_label = f"[gateway] {gateway.ip}" if gateway else result.network
    lines.append(f"└─ {root_label}")

    branch_devices = [d for d in devices if d is not gateway]
    for index, device in enumerate(branch_devices):
        last = index == len(branch_devices) - 1
        lines.extend(_render_device(device, last))
    return "\n".join(lines) + "\n"


def _render_device(device: Device, last: bool) -> list[str]:
    connector = "   └─" if last else "   ├─"
    child_prefix = "      " if last else "   │  "
    label = device.hostname or device.ip
    type_tag = device.device_type.value
    header = f"{connector} {label} ({device.ip}) [{type_tag}]"
    lines = [header]
    details: list[str] = []
    if device.os:
        details.append(f"os: {device.os}")
    if device.services:
        details.append("services: " + ", ".join(device.services[:5]))
    elif device.ports:
        details.append("ports: " + ", ".join(str(p) for p in device.ports[:6]))
    for i, detail in enumerate(details):
        leaf = "└─" if i == len(details) - 1 else "├─"
        lines.append(f"{child_prefix}{leaf} {detail}")
    return lines


def _guess_gateway(devices: list[Device], network: str) -> Device | None:
    """Pick the most likely gateway: the .1 host, else the network router."""
    try:
        net = ipaddress.ip_network(network, strict=False)
        gateway_ip = str(net.network_address + 1)
    except ValueError:
        gateway_ip = None

    for device in devices:
        if gateway_ip and device.ip == gateway_ip:
            return device
    for device in devices:
        if device.device_type.value == "network":
            return device
    return None
