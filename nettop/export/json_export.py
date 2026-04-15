"""JSON output - the canonical machine-readable format."""

from __future__ import annotations

import json

from ..models import ScanResult


def render(result: ScanResult) -> str:
    return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
