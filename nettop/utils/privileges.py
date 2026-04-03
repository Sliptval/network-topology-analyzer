"""Privilege detection.

Raw-socket operations (ARP scanning, packet capture, OS fingerprinting) need
elevated rights. Rather than failing with a stack trace deep inside a scan, we
check up front and hand back a clear, actionable message.
"""

from __future__ import annotations

import ctypes
import os
import sys


def is_elevated() -> bool:
    """Return True when the process has admin/root rights."""
    if sys.platform == "win32":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:  # pragma: no cover - defensive
            return False
    try:
        return os.geteuid() == 0
    except AttributeError:  # pragma: no cover - platform without geteuid
        return False


def elevation_hint() -> str:
    """A platform-appropriate suggestion for gaining privileges."""
    if sys.platform == "win32":
        return "Run this terminal as Administrator."
    return "Re-run with sudo, e.g. 'sudo nettop ...'."
