"""Optional nmap backend.

When nmap is installed it does OS fingerprinting and service/version detection
far better than a bare socket scan. This module shells out to it and parses the
XML output. It is entirely optional - if nmap is missing the engine silently
falls back to the built-in scanner.
"""

from __future__ import annotations

import shutil
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from ..utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class NmapHost:
    ip: str
    mac: str | None = None
    vendor: str | None = None
    hostname: str | None = None
    os: str | None = None
    ports: list[int] = field(default_factory=list)
    services: dict[int, str] = field(default_factory=dict)


def is_available() -> bool:
    return shutil.which("nmap") is not None


def scan(network: str, *, deep: bool = False, os_detect: bool = False) -> list[NmapHost]:
    """Run nmap against ``network`` and return parsed hosts.

    ``deep`` enables service/version detection (-sV); ``os_detect`` enables OS
    fingerprinting (-O, which needs root). Raises RuntimeError on failure so the
    caller can fall back gracefully.
    """
    nmap = shutil.which("nmap")
    if not nmap:
        raise RuntimeError("nmap is not installed")

    cmd = [nmap, "-oX", "-", "-T4"]
    if deep:
        cmd.append("-sV")
    else:
        cmd.append("-sT")
    if os_detect:
        cmd.append("-O")
    cmd.append(network)

    log.info("Running nmap: %s", " ".join(cmd))
    try:
        completed = subprocess.run(
            cmd, capture_output=True, text=True, timeout=1800, check=False
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"nmap failed to run: {exc}") from exc

    if completed.returncode != 0 and not completed.stdout.strip():
        raise RuntimeError(completed.stderr.strip() or "nmap returned no output")

    return _parse_xml(completed.stdout)


def _parse_xml(xml_text: str) -> list[NmapHost]:
    hosts: list[NmapHost] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise RuntimeError(f"could not parse nmap output: {exc}") from exc

    for host_el in root.findall("host"):
        status = host_el.find("status")
        if status is not None and status.get("state") != "up":
            continue

        ip = None
        mac = None
        vendor = None
        for addr in host_el.findall("address"):
            addr_type = addr.get("addrtype")
            if addr_type in ("ipv4", "ipv6"):
                ip = addr.get("addr")
            elif addr_type == "mac":
                mac = addr.get("addr")
                vendor = addr.get("vendor")
        if not ip:
            continue

        host = NmapHost(ip=ip, mac=mac, vendor=vendor)

        hostnames = host_el.find("hostnames")
        if hostnames is not None:
            name_el = hostnames.find("hostname")
            if name_el is not None:
                host.hostname = name_el.get("name")

        os_el = host_el.find("os")
        if os_el is not None:
            match = os_el.find("osmatch")
            if match is not None:
                host.os = match.get("name")

        ports_el = host_el.find("ports")
        if ports_el is not None:
            for port_el in ports_el.findall("port"):
                state = port_el.find("state")
                if state is None or state.get("state") != "open":
                    continue
                try:
                    portid = int(port_el.get("portid", "0"))
                except ValueError:
                    continue
                host.ports.append(portid)
                svc = port_el.find("service")
                if svc is not None:
                    name = svc.get("name") or ""
                    product = svc.get("product") or ""
                    label = f"{product} {name}".strip() or name
                    if label:
                        host.services[portid] = label
        host.ports.sort()
        hosts.append(host)
    return hosts
