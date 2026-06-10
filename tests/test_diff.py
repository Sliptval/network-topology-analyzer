from nettop.diff import diff_scans
from nettop.models import Device, ScanResult


def _scan(*devices: Device) -> ScanResult:
    return ScanResult(network="10.0.0.0/24", devices=list(devices))


def test_detects_new_and_removed_devices():
    before = _scan(Device(ip="10.0.0.1"), Device(ip="10.0.0.2"))
    after = _scan(Device(ip="10.0.0.1"), Device(ip="10.0.0.3"))
    result = diff_scans(before, after)
    assert [d.ip for d in result.new_devices] == ["10.0.0.3"]
    assert [d.ip for d in result.removed_devices] == ["10.0.0.2"]
    assert result.has_changes


def test_detects_port_changes():
    before = _scan(Device(ip="10.0.0.1", ports=[22, 80]))
    after = _scan(Device(ip="10.0.0.1", ports=[22, 443]))
    result = diff_scans(before, after)
    assert len(result.port_changes) == 1
    change = result.port_changes[0]
    assert change.opened == [443]
    assert change.closed == [80]


def test_no_changes():
    before = _scan(Device(ip="10.0.0.1", ports=[22]))
    after = _scan(Device(ip="10.0.0.1", ports=[22]))
    result = diff_scans(before, after)
    assert not result.has_changes
