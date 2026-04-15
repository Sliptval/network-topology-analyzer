"""Output formatters.

Every exporter takes a :class:`~nettop.models.ScanResult` and returns a string.
The registry lets the CLI pick one by name without importing each module.
"""

from __future__ import annotations

from typing import Callable

from ..models import ScanResult
from . import (
    ascii_export,
    csv_export,
    json_export,
    markdown_export,
    prometheus_export,
    text_export,
    yaml_export,
)

Exporter = Callable[[ScanResult], str]

_REGISTRY: dict[str, Exporter] = {
    "text": text_export.render,
    "json": json_export.render,
    "yaml": yaml_export.render,
    "csv": csv_export.render,
    "ascii": ascii_export.render,
    "markdown": markdown_export.render,
    "prometheus": prometheus_export.render,
}


def available_formats() -> list[str]:
    return list(_REGISTRY)


def render(result: ScanResult, fmt: str) -> str:
    try:
        exporter = _REGISTRY[fmt]
    except KeyError:
        raise ValueError(
            f"Unknown format '{fmt}'. Choose from: {', '.join(_REGISTRY)}"
        ) from None
    return exporter(result)
