import json

import pytest

from nettop import export
from nettop.models import ScanResult


def test_all_formats_registered():
    assert set(export.available_formats()) == {
        "text",
        "json",
        "yaml",
        "csv",
        "ascii",
        "markdown",
        "prometheus",
    }


def test_json_roundtrip(sample_scan):
    rendered = export.render(sample_scan, "json")
    data = json.loads(rendered)
    assert data["network"] == "192.168.1.0/24"
    assert data["device_count"] == 3
    assert data["online_count"] == 3
    restored = ScanResult.from_dict(data)
    assert [d.ip for d in restored.devices] == [
        "192.168.1.1",
        "192.168.1.5",
        "192.168.1.20",
    ]
    assert restored.devices[1].services == ["SSH", "PostgreSQL", "Redis"]


def test_csv_has_header_and_rows(sample_scan):
    rendered = export.render(sample_scan, "csv")
    lines = rendered.strip().splitlines()
    assert lines[0].startswith("ip,mac,hostname")
    assert len(lines) == 4  # header + 3 devices
    assert "db-server" in rendered


def test_text_contains_devices_and_summary(sample_scan):
    rendered = export.render(sample_scan, "text")
    assert "192.168.1.5" in rendered
    assert "db-server" in rendered
    assert "Summary" in rendered
    assert "Traffic" in rendered


def test_ascii_has_gateway_root(sample_scan):
    rendered = export.render(sample_scan, "ascii")
    assert "gateway" in rendered
    assert "192.168.1.1" in rendered
    assert "db-server" in rendered


def test_markdown_structure(sample_scan):
    rendered = export.render(sample_scan, "markdown")
    assert rendered.startswith("# Network Documentation")
    assert "## Devices" in rendered
    assert "| IP |" in rendered
    assert "`192.168.1.5`" in rendered


def test_prometheus_metrics(sample_scan):
    rendered = export.render(sample_scan, "prometheus")
    assert 'nettop_devices_total{network="192.168.1.0/24"} 3' in rendered
    assert "nettop_device_up" in rendered
    assert 'nettop_bandwidth_mbps{source="192.168.1.5"' in rendered


def test_yaml_is_parseable_or_fallback(sample_scan):
    rendered = export.render(sample_scan, "yaml")
    assert "network:" in rendered
    assert "192.168.1.0/24" in rendered


def test_unknown_format_raises(sample_scan):
    with pytest.raises(ValueError):
        export.render(sample_scan, "toml")
