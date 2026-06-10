import pytest

from nettop.models import Bandwidth, Connection, Device, DeviceType, ScanResult, Status


@pytest.fixture
def sample_scan() -> ScanResult:
    devices = [
        Device(
            ip="192.168.1.1",
            mac="00:00:0C:11:22:33",
            hostname="router",
            os="Network device",
            vendor="Cisco",
            device_type=DeviceType.NETWORK,
            ports=[53, 80, 443],
            services=["DNS", "HTTP", "HTTPS"],
            latency_ms=1.2,
        ),
        Device(
            ip="192.168.1.5",
            mac="00:0C:29:AB:CD:EF",
            hostname="db-server",
            os="Linux/Unix",
            vendor="VMware",
            device_type=DeviceType.SERVER,
            ports=[22, 5432, 6379],
            services=["SSH", "PostgreSQL", "Redis"],
            bandwidth=Bandwidth(received_mbps=25.3, sent_mbps=18.1, latency_ms=2.3),
            latency_ms=2.3,
        ),
        Device(
            ip="192.168.1.20",
            hostname=None,
            device_type=DeviceType.UNKNOWN,
            status=Status.ONLINE,
            ports=[],
        ),
    ]
    connections = [
        Connection(source_ip="192.168.1.5", dest_ip="192.168.1.1", bandwidth_mbps=15.2),
    ]
    return ScanResult(
        network="192.168.1.0/24",
        scan_timestamp="2024-01-15T14:23:45Z",
        devices=devices,
        connections=connections,
    )
