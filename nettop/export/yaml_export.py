"""YAML output.

PyYAML is used when available; otherwise a small, correct emitter handles the
shapes this program actually produces (scalars, lists and dicts). Keeping a
fallback means YAML export works even in a minimal install.
"""

from __future__ import annotations

from ..models import ScanResult

try:  # pragma: no cover - exercised via availability, not both branches
    import yaml as _pyyaml
except ImportError:  # pragma: no cover
    _pyyaml = None


def render(result: ScanResult) -> str:
    data = result.to_dict()
    if _pyyaml is not None:
        return _pyyaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    return _dump(data).rstrip() + "\n"


def _dump(value: object, indent: int = 0) -> str:
    pad = "  " * indent
    if isinstance(value, dict):
        if not value:
            return f"{pad}{{}}\n"
        lines = []
        for key, val in value.items():
            if isinstance(val, (dict, list)) and val:
                lines.append(f"{pad}{key}:")
                lines.append(_dump(val, indent + 1))
            else:
                lines.append(f"{pad}{key}: {_scalar(val)}")
        return "\n".join(lines) + "\n"
    if isinstance(value, list):
        if not value:
            return f"{pad}[]\n"
        lines = []
        for item in value:
            if isinstance(item, (dict, list)) and item:
                rendered = _dump(item, indent + 1)
                # Splice the '- ' marker onto the first rendered line.
                first, _, rest = rendered.partition("\n")
                marker = f"{pad}- {first.strip()}"
                lines.append(marker)
                if rest.strip():
                    lines.append(rest.rstrip("\n"))
            else:
                lines.append(f"{pad}- {_scalar(item)}")
        return "\n".join(lines) + "\n"
    return f"{pad}{_scalar(value)}\n"


def _scalar(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if text == "" or any(c in text for c in ":#{}[],&*!|>'\"%@`") or text.strip() != text:
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return text
