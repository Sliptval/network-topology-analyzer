import pytest

from nettop.utils import net


def test_parse_cidr_expands_hosts():
    hosts = net.parse_targets("192.168.1.0/30")
    # /30 -> two usable hosts
    assert hosts == ["192.168.1.1", "192.168.1.2"]


def test_parse_single_ip():
    assert net.parse_targets("10.0.0.5") == ["10.0.0.5"]


def test_parse_range():
    hosts = net.parse_targets("192.168.1.10-192.168.1.12")
    assert hosts == ["192.168.1.10", "192.168.1.11", "192.168.1.12"]


def test_parse_mixed_and_dedup():
    hosts = net.parse_targets("10.0.0.1, 10.0.0.1, 10.0.0.2")
    assert hosts == ["10.0.0.1", "10.0.0.2"]


def test_parse_rejects_giant_network():
    with pytest.raises(net.NetworkError):
        net.parse_targets("10.0.0.0/8")


def test_parse_rejects_bad_ip():
    with pytest.raises(net.NetworkError):
        net.parse_targets("999.1.1.1")


def test_normalize_mac_variants():
    assert net.normalize_mac("aa-bb-cc-dd-ee-ff") == "AA:BB:CC:DD:EE:FF"
    assert net.normalize_mac("aabb.ccdd.eeff") == "AA:BB:CC:DD:EE:FF"
    assert net.normalize_mac("not-a-mac") == ""


def test_vendor_lookup():
    assert net.vendor_for_mac("B8:27:EB:00:00:01") == "Raspberry Pi"
    assert net.vendor_for_mac("FF:FF:FF:00:00:00") is None
    assert net.vendor_for_mac(None) is None


def test_os_guess_from_ttl():
    assert net.os_guess_from_ttl(64) == "Linux/Unix"
    assert net.os_guess_from_ttl(128) == "Windows"
    assert net.os_guess_from_ttl(255) == "Network device"
    assert net.os_guess_from_ttl(None) is None
