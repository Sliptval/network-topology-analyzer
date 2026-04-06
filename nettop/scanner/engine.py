"""Scan orchestration.

The engine ties the pieces together: expand the target spec, discover live
hosts, probe their ports, enrich with ARP/vendor/hostname data and classify the
result into :class:`Device` objects. If nmap is present and requested it is used
for richer detection, otherwise the pure-Python path runs.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from ..models import Device, DeviceType, ScanResult, Status
from ..services import classify_device, services_for_ports
from ..utils import net
from ..utils.logging import get_logger
from . import discovery, nmap_scanner, ports as portscan

log = get_logger(__name__)


@dataclass
class ScanOptions:
    network: str
    scan_ports: bool = True
    deep: bool = False
    resolve_hostnames: bool = True
    use_nmap: bool = True
    os_detect: bool = False
    timeout_ms: int = 1000
    port_timeout: float = 0.6
    workers: int = 128
    custom_ports: tuple[int, ...] | None = field(default=None)


class ScanEngine:
    """Runs a scan and returns a :class:`ScanResult`."""

    def __init__(self, options: ScanOptions) -> None:
        self.options = options

    def run(self) -> ScanResult:
        started = time.monotonic()
        result = ScanResult(network=self.options.network)

        if self.options.use_nmap and nmap_scanner.is_available():
            try:
                result.devices = self._scan_with_nmap()
            except RuntimeError as exc:
                log.warning("nmap backend failed (%s); using built-in scanner", exc)
                result.devices = self._scan_builtin()
        else:
            if self.options.use_nmap:
                log.info("nmap not found; using built-in scanner")
            result.devices = self._scan_builtin()

        result.duration_seconds = time.monotonic() - started
        log.info(
            "Scan complete: %d device(s) in %.1fs",
            len(result.devices),
            result.duration_seconds,
        )
        return result

    # -- built-in (no external tools required) ----------------------------

    def _scan_builtin(self) -> list[Device]:
        targets = net.parse_targets(self.options.network)
        live = discovery.discover(
            targets,
            timeout_ms=self.options.timeout_ms,
            workers=self.options.workers,
        )
        arp_table = net.read_arp_table()

        port_list = self._port_list()
        devices: list[Device] = []

        def build(host: discovery.LiveHost) -> Device:
            open_ports: list[int] = []
            banners: dict[int, str] = {}
            if self.options.scan_ports:
                open_ports, banners = portscan.scan_ports(
                    host.ip,
                    port_list,
                    timeout=self.options.port_timeout,
                    grab_banners=self.options.deep,
                )
            mac = arp_table.get(host.ip)
            services = [
                portscan.refine_service(p, banners.get(p)) for p in open_ports
            ]
            device = Device(
                ip=host.ip,
                mac=mac,
                vendor=net.vendor_for_mac(mac),
                os=net.os_guess_from_ttl(host.ttl),
                ports=open_ports,
                services=_dedup(services),
                status=Status.ONLINE,
                latency_ms=host.latency_ms,
                metadata={"discovered_via": host.reachable_via},
            )
            if self.options.resolve_hostnames:
                device.hostname = net.resolve_hostname(host.ip)
            device.device_type = classify_device(device)
            return device

        worker_count = max(1, min(self.options.workers, len(live) or 1))
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = [pool.submit(build, host) for host in live]
            for future in as_completed(futures):
                devices.append(future.result())

        devices.sort(key=lambda d: tuple(int(o) for o in d.ip.split(".")))
        return devices

    # -- nmap-backed -------------------------------------------------------

    def _scan_with_nmap(self) -> list[Device]:
        hosts = nmap_scanner.scan(
            self.options.network,
            deep=self.options.deep,
            os_detect=self.options.os_detect,
        )
        arp_table = net.read_arp_table()
        devices: list[Device] = []
        for host in hosts:
            mac = host.mac or arp_table.get(host.ip)
            services = (
                [host.services[p] for p in host.ports if p in host.services]
                or services_for_ports(host.ports)
            )
            device = Device(
                ip=host.ip,
                mac=mac,
                hostname=host.hostname,
                os=host.os,
                vendor=host.vendor or net.vendor_for_mac(mac),
                ports=host.ports,
                services=_dedup(services),
                status=Status.ONLINE,
                metadata={"discovered_via": "nmap"},
            )
            device.device_type = classify_device(device)
            devices.append(device)
        devices.sort(key=lambda d: tuple(int(o) for o in d.ip.split(".")))
        return devices

    def _port_list(self) -> tuple[int, ...]:
        if self.options.custom_ports:
            return self.options.custom_ports
        return portscan.EXTENDED_PORTS if self.options.deep else portscan.DEFAULT_PORTS


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
