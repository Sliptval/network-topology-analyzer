"""Configuration loading.

Configuration is optional: everything has a sensible default and can be set on
the command line. A YAML (or JSON) file is only needed for the daemon, where
repeating a dozen flags would be tedious.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:  # pragma: no cover
    import yaml as _pyyaml
except ImportError:  # pragma: no cover
    _pyyaml = None


DEFAULTS: dict[str, Any] = {
    "network": None,
    "database": None,  # None -> platform default
    "scan_interval": "5m",
    "log_level": "INFO",
    "alerts": {
        "offline": True,
        "new_device": True,
        "high_bandwidth_mbps": 500,
        "slow_latency_ms": 200,
    },
    "api": {"enabled": False, "bind": "127.0.0.1:8080"},
    "prometheus": {"enabled": False, "bind": "127.0.0.1:9100"},
}


@dataclass
class Config:
    data: dict[str, Any] = field(default_factory=lambda: dict(DEFAULTS))

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    @property
    def alerts(self) -> dict[str, Any]:
        return self.data.get("alerts", {})

    @property
    def api(self) -> dict[str, Any]:
        return self.data.get("api", {})

    @property
    def prometheus(self) -> dict[str, Any]:
        return self.data.get("prometheus", {})


def load_config(path: str | Path | None) -> Config:
    config = Config()
    if not path:
        return config
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")

    text = file_path.read_text(encoding="utf-8")
    if file_path.suffix in {".yaml", ".yml"}:
        if _pyyaml is None:
            raise RuntimeError(
                "PyYAML is required to read YAML config files. "
                "Install it with 'pip install pyyaml' or use a JSON config."
            )
        loaded = _pyyaml.safe_load(text) or {}
    else:
        loaded = json.loads(text)

    merged = _deep_merge(dict(DEFAULTS), loaded)
    return Config(data=merged)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(dict(base[key]), value)
        else:
            base[key] = value
    return base


def parse_duration(value: str) -> float:
    """Parse a duration like '30s', '5m', '2h' into seconds."""
    value = value.strip().lower()
    if not value:
        raise ValueError("empty duration")
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if value[-1] in units:
        number, unit = value[:-1], value[-1]
        return float(number) * units[unit]
    return float(value)
