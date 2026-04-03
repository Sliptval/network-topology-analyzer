"""Network helpers: address expansion, the ARP table and MAC vendor lookup.

Everything here is standard library only. It works the same whether or not
nmap/arp-scan are installed, which keeps the tool usable out of the box.
"""

from __future__ import annotations

import ipaddress
import re
import shutil
import socket
import subprocess
import sys
from typing import Iterable

# A deliberately small OUI table covering the vendors seen most often on home
# and office LANs. The full IEEE registry is huge; when arp-scan or nmap are
# available they provide richer data, and this keeps zero-dependency mode
# useful without shipping a multi-megabyte database.
OUI_VENDORS: dict[str, str] = {
    "00:00:0C": "Cisco",
    "00:1A:11": "Google",
    "00:1B:63": "Apple",
    "00:03:93": "Apple",
    "00:0C:29": "VMware",
    "00:05:69": "VMware",
    "00:50:56": "VMware",
    "00:15:5D": "Microsoft (Hyper-V)",
    "08:00:27": "Oracle VirtualBox",
    "52:54:00": "QEMU/KVM",
    "B8:27:EB": "Raspberry Pi",
    "DC:A6:32": "Raspberry Pi",
    "E4:5F:01": "Raspberry Pi",
    "00:1D:0F": "TP-Link",
    "50:C7:BF": "TP-Link",
    "F4:F2:6D": "TP-Link",
    "00:18:E7": "Cameo (IoT)",
    "00:24:E4": "Withings",
    "00:17:88": "Philips Hue",
    "EC:FA:BC": "Espressif (ESP)",
    "24:0A:C4": "Espressif (ESP)",
    "3C:2E:FF": "Sonos",
    "B8:E9:37": "Sonos",
    "00:11:32": "Synology",
    "00:1E:06": "WibRain",
    "AC:DE:48": "Private",
}


class NetworkError(Exception):
    """Raised for user-facing network configuration problems."""


def parse_targets(spec: str) -> list[str]:
    """Expand a target spec into a list of host addresses.

    Accepts CIDR ("192.168.1.0/24"), a single IP, a hyphen range
    ("192.168.1.10-192.168.1.20") or a comma-separated mix of the above.
    """
    hosts: list[str] = []
    for part in (p.strip() for p in spec.split(",") if p.strip()):
        if "/" in part:
            hosts.extend(_expand_cidr(part))
        elif "-" in part and part.count("-") == 1 and _looks_like_range(part):
            hosts.extend(_expand_range(part))
        else:
            hosts.append(_validate_ip(part))
    # De-duplicate while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for host in hosts:
        if host not in seen:
            seen.add(host)
            ordered.append(host)
    return ordered


def _looks_like_range(part: str) -> bool:
    left, right = part.split("-", 1)
    return "." in left and "." in right


def _expand_cidr(part: str) -> list[str]:
    try:
        network = ipaddress.ip_network(part, strict=False)
    except ValueError as exc:
        raise NetworkError(f"Invalid network '{part}': {exc}") from exc
    if network.num_addresses > 65536:
        raise NetworkError(
            f"Network '{part}' has {network.num_addresses} addresses; "
            "refusing to scan more than a /16 at once."
        )
    if network.num_addresses <= 2:
        return [str(network.network_address)]
    return [str(host) for host in network.hosts()]


def _expand_range(part: str) -> list[str]:
    left, right = part.split("-", 1)
    try:
        start = ipaddress.ip_address(left.strip())
        end = ipaddress.ip_address(right.strip())
    except ValueError as exc:
        raise NetworkError(f"Invalid range '{part}': {exc}") from exc
    if int(end) < int(start):
        raise NetworkError(f"Range '{part}' ends before it starts.")
    if int(end) - int(start) > 65536:
        raise NetworkError(f"Range '{part}' is too large to scan at once.")
    return [str(ipaddress.ip_address(i)) for i in range(int(start), int(end) + 1)]


def _validate_ip(value: str) -> str:
    try:
        return str(ipaddress.ip_address(value))
    except ValueError as exc:
        raise NetworkError(f"Invalid IP address '{value}': {exc}") from exc


def normalize_mac(mac: str) -> str:
    """Return a MAC in upper-case colon-separated form, or '' if unparsable."""
    digits = re.sub(r"[^0-9a-fA-F]", "", mac)
    if len(digits) != 12:
        return ""
    return ":".join(digits[i : i + 2] for i in range(0, 12, 2)).upper()


def vendor_for_mac(mac: str | None) -> str | None:
    """Best-effort vendor name from a MAC address prefix (OUI)."""
    if not mac:
        return None
    normalized = normalize_mac(mac)
    if not normalized:
        return None
    prefix = normalized[:8]
    return OUI_VENDORS.get(prefix)


def read_arp_table() -> dict[str, str]:
    """Read the OS ARP cache and return a mapping of IP -> MAC.

    Uses ``arp -a`` which exists on Windows, macOS and Linux. Entries with an
    incomplete or invalid MAC are skipped.
    """
    arp = shutil.which("arp")
    if not arp:
        return {}
    try:
        completed = subprocess.run(
            [arp, "-a"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return {}

    table: dict[str, str] = {}
    ip_re = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})")
    mac_re = re.compile(r"([0-9a-fA-F]{2}(?:[:-][0-9a-fA-F]{2}){5})")
    for line in completed.stdout.splitlines():
        ip_match = ip_re.search(line)
        mac_match = mac_re.search(line)
        if not ip_match or not mac_match:
            continue
        mac = normalize_mac(mac_match.group(1))
        if mac and mac != "FF:FF:FF:FF:FF:FF" and not mac.startswith("00:00:00"):
            table[ip_match.group(1)] = mac
    return table


def resolve_hostname(ip: str, timeout: float = 2.0) -> str | None:
    """Reverse-resolve an IP to a hostname, returning None on failure.

    The OS reverse-DNS call ignores ``socket.setdefaulttimeout`` on some
    platforms (notably Windows), where a lookup for a non-resolvable host can
    block for several seconds. We run it in a daemon thread and give up after
    ``timeout`` so a scan never stalls on DNS.
    """
    result: dict[str, str | None] = {}

    def _lookup() -> None:
        try:
            result["name"] = socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror, OSError):
            result["name"] = None

    import threading

    thread = threading.Thread(target=_lookup, daemon=True)
    thread.start()
    thread.join(timeout)
    return result.get("name")


def local_networks() -> list[str]:
    """Guess the local /24 network(s) from this host's own addresses."""
    networks: set[str] = set()
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip.startswith("127."):
                continue
            iface = ipaddress.ip_interface(f"{ip}/24")
            networks.add(str(iface.network))
    except (socket.gaierror, ValueError, OSError):
        pass
    return sorted(networks)


def which_tools(names: Iterable[str]) -> dict[str, bool]:
    """Report which external CLI tools are available on PATH."""
    return {name: shutil.which(name) is not None for name in names}


def os_guess_from_ttl(ttl: int | None) -> str | None:
    """Very rough OS family guess from an ICMP TTL.

    TTLs are set to a small number of well-known initial values and decremented
    per hop, so the ceiling they sit under is a decent hint.
    """
    if ttl is None:
        return None
    if ttl <= 64:
        return "Linux/Unix"
    if ttl <= 128:
        return "Windows"
    return "Network device"


def default_ping_command(ip: str, timeout_ms: int = 1000) -> list[str]:
    """Build a single-probe ping command for the current platform."""
    if sys.platform == "win32":
        return ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    # -c count, -W timeout in seconds (Linux) / -t on macOS is TTL, so use -W-less
    seconds = max(1, round(timeout_ms / 1000))
    if sys.platform == "darwin":
        return ["ping", "-c", "1", "-t", str(seconds), ip]
    return ["ping", "-c", "1", "-W", str(seconds), ip]
