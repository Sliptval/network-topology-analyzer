from nettop.models import Device, ScanResult, Status
from nettop.storage import Database


def test_save_and_load_latest(tmp_path):
    db = Database(tmp_path / "test.db")
    scan = ScanResult(
        network="192.168.0.0/24",
        devices=[Device(ip="192.168.0.5", hostname="host-a")],
    )
    scan_id = db.save_scan(scan)
    assert scan_id == 1

    latest = db.latest_scan()
    assert latest is not None
    assert latest.network == "192.168.0.0/24"
    assert latest.devices[0].hostname == "host-a"
    db.close()


def test_latest_filtered_by_network(tmp_path):
    db = Database(tmp_path / "test.db")
    db.save_scan(ScanResult(network="10.0.0.0/24", devices=[Device(ip="10.0.0.1")]))
    db.save_scan(ScanResult(network="10.0.1.0/24", devices=[Device(ip="10.0.1.1")]))

    latest = db.latest_scan("10.0.0.0/24")
    assert latest is not None
    assert latest.devices[0].ip == "10.0.0.1"
    db.close()


def test_device_history(tmp_path):
    db = Database(tmp_path / "test.db")
    db.save_scan(
        ScanResult(
            network="10.0.0.0/24",
            devices=[Device(ip="10.0.0.9", status=Status.ONLINE)],
        )
    )
    db.save_scan(
        ScanResult(
            network="10.0.0.0/24",
            devices=[Device(ip="10.0.0.9", status=Status.ONLINE, hostname="nas")],
        )
    )
    history = db.device_history("10.0.0.9")
    assert len(history) == 2
    db.close()
