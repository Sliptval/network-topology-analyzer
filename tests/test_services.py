from nettop.models import Device, DeviceType
from nettop.services import classify_device, service_name, services_for_ports


def test_service_name_known_and_unknown():
    assert service_name(22) == "SSH"
    assert service_name(5432) == "PostgreSQL"
    assert service_name(12345) == "port/12345"


def test_services_for_ports_dedup_and_sorted():
    services = services_for_ports([443, 80, 443])
    assert services == ["HTTP", "HTTPS"]


def test_classify_server():
    device = Device(ip="10.0.0.1", ports=[22, 5432])
    assert classify_device(device) is DeviceType.SERVER


def test_classify_printer():
    device = Device(ip="10.0.0.2", ports=[9100])
    assert classify_device(device) is DeviceType.PRINTER


def test_classify_network_by_vendor():
    device = Device(ip="10.0.0.3", vendor="Cisco", ports=[80])
    assert classify_device(device) is DeviceType.NETWORK


def test_classify_iot():
    device = Device(ip="10.0.0.4", ports=[1883])
    assert classify_device(device) is DeviceType.IOT


def test_classify_unknown():
    device = Device(ip="10.0.0.5", ports=[])
    assert classify_device(device) is DeviceType.UNKNOWN
