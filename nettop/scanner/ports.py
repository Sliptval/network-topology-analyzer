"""TCP port scanning and lightweight service/banner detection.

A plain connect() scan needs no privileges and works everywhere, which is what
makes the tool useful without root. When ``--deep`` is requested we also try a
short banner grab to sharpen service identification.
"""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..services import service_name
from ..utils.logging import get_logger

log = get_logger(__name__)

# A curated default set: the ports that actually tell you something about a
# host without scanning all 65535.
DEFAULT_PORTS: tuple[int, ...] = (
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 161, 389, 443, 445,
    514, 515, 587, 631, 993, 995, 1433, 1521, 1883, 2049, 2375, 3000, 3306,
    3389, 5000, 5060, 5432, 5900, 6379, 8006, 8080, 8086, 8443, 9090, 9100,
    9200, 11211, 27017, 32400, 51820,
)

# A wider list used with --deep.
EXTENDED_PORTS: tuple[int, ...] = tuple(
    sorted(set(DEFAULT_PORTS) | {
        20, 67, 68, 69, 123, 137, 138, 162, 179, 465, 500, 636, 1080, 1723,
        2376, 3690, 4444, 5601, 5672, 6443, 7070, 8000, 8081, 8883, 9000,
        9093, 9418, 10000, 25565, 50000,
    })
)


def _grab_banner(sock: socket.socket) -> str | None:
    """Read a short banner if the service volunteers one quickly."""
    try:
        sock.settimeout(0.8)
        data = sock.recv(128)
    except (OSError, socket.timeout):
        return None
    if not data:
        return None
    text = data.decode("latin-1", errors="replace").strip()
    # Collapse to a single tidy line.
    return " ".join(text.split())[:80] or None


def scan_ports(
    ip: str,
    ports: tuple[int, ...] = DEFAULT_PORTS,
    *,
    timeout: float = 0.6,
    workers: int = 64,
    grab_banners: bool = False,
) -> tuple[list[int], dict[int, str]]:
    """Scan ``ports`` on ``ip``.

    Returns the sorted list of open ports and a map of port -> banner for any
    banners captured.
    """
    open_ports: list[int] = []
    banners: dict[int, str] = {}

    def probe(port: int) -> tuple[int, bool, str | None]:
        try:
            sock = socket.create_connection((ip, port), timeout=timeout)
        except (OSError, socket.timeout):
            return port, False, None
        try:
            banner = _grab_banner(sock) if grab_banners else None
        finally:
            sock.close()
        return port, True, banner

    worker_count = max(1, min(workers, len(ports)))
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = [pool.submit(probe, p) for p in ports]
        for future in as_completed(futures):
            port, is_open, banner = future.result()
            if is_open:
                open_ports.append(port)
                if banner:
                    banners[port] = banner

    open_ports.sort()
    if open_ports:
        log.debug("%s: open ports %s", ip, open_ports)
    return open_ports, banners


def refine_service(port: int, banner: str | None) -> str:
    """Combine the port's known service name with any banner hint."""
    name = service_name(port)
    if not banner:
        return name
    lowered = banner.lower()
    for keyword, label in (
        ("ssh", "SSH"),
        ("http", "HTTP"),
        ("nginx", "HTTP (nginx)"),
        ("apache", "HTTP (Apache)"),
        ("postgres", "PostgreSQL"),
        ("mysql", "MySQL"),
        ("redis", "Redis"),
        ("mongodb", "MongoDB"),
        ("smtp", "SMTP"),
        ("ftp", "FTP"),
    ):
        if keyword in lowered:
            return label
    return name
