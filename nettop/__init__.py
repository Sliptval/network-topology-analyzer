"""nettop - a command-line network topology analyzer.

Scan a network, discover devices and services, watch traffic between hosts
and render the result in whatever format fits your workflow: a terminal
table, JSON, YAML, CSV, an ASCII topology graph, Markdown docs or Prometheus
metrics.

The whole tool is CLI-first. There is no web UI to babysit; it is meant to be
dropped into scripts, cron jobs and monitoring pipelines on headless servers.
"""

__all__ = ["__version__"]

__version__ = "0.4.0"
