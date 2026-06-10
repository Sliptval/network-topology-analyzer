from nettop.daemon.alerting import AlertEngine
from nettop.models import Connection, Device, ScanResult


def test_new_device_alert():
    before = ScanResult(network="10.0.0.0/24", devices=[Device(ip="10.0.0.1")])
    after = ScanResult(
        network="10.0.0.0/24",
        devices=[Device(ip="10.0.0.1"), Device(ip="10.0.0.2", hostname="new-host")],
    )
    alerts = AlertEngine().evaluate(before, after)
    types = {a.alert_type for a in alerts}
    assert "new_device" in types


def test_offline_alert():
    before = ScanResult(
        network="10.0.0.0/24",
        devices=[Device(ip="10.0.0.1"), Device(ip="10.0.0.2")],
    )
    after = ScanResult(network="10.0.0.0/24", devices=[Device(ip="10.0.0.1")])
    alerts = AlertEngine().evaluate(before, after)
    assert any(a.alert_type == "offline" for a in alerts)


def test_high_bandwidth_alert():
    scan = ScanResult(
        network="10.0.0.0/24",
        connections=[
            Connection(source_ip="10.0.0.1", dest_ip="10.0.0.2", bandwidth_mbps=900)
        ],
    )
    alerts = AlertEngine(high_bandwidth_mbps=500).evaluate(None, scan)
    assert any(a.alert_type == "high_bandwidth" for a in alerts)


def test_slow_latency_alert():
    scan = ScanResult(
        network="10.0.0.0/24",
        devices=[Device(ip="10.0.0.1", latency_ms=350)],
    )
    alerts = AlertEngine(slow_latency_ms=200).evaluate(None, scan)
    assert any(a.alert_type == "slow_latency" for a in alerts)


def test_no_false_positives():
    scan = ScanResult(network="10.0.0.0/24", devices=[Device(ip="10.0.0.1")])
    assert AlertEngine().evaluate(None, scan) == []
