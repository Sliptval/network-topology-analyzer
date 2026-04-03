"""Logging setup.

A single place to configure logging so every module can just call
``get_logger(__name__)`` and inherit consistent formatting and level.
"""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def configure(level: str = "INFO", *, quiet: bool = False) -> None:
    """Configure the root logger once.

    Logs go to stderr so they never contaminate machine-readable output
    (JSON, CSV, ...) written to stdout.
    """
    global _CONFIGURED
    if _CONFIGURED:
        logging.getLogger().setLevel(_resolve_level(level, quiet=quiet))
        return

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(_resolve_level(level, quiet=quiet))
    _CONFIGURED = True


def _resolve_level(level: str, *, quiet: bool) -> int:
    if quiet:
        return logging.ERROR
    return getattr(logging, level.upper(), logging.INFO)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
