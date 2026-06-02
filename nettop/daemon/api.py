"""A tiny REST API built on the standard library.

No framework, no extra dependency. It serves the last stored scan so other
tools can pull the current topology over HTTP:

    GET  /api/status         -> daemon + last-scan summary
    GET  /api/devices        -> list of devices
    GET  /api/devices/<ip>   -> a single device
    GET  /api/traffic        -> observed connections
    GET  /api/alerts         -> active alerts
    GET  /metrics            -> Prometheus exposition
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from ..export import prometheus_export
from ..storage import Database
from ..utils.logging import get_logger

log = get_logger(__name__)


def make_handler(database: Database, network: str | None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "nettop"

        def log_message(self, fmt: str, *args) -> None:  # noqa: A003
            log.debug("api %s - %s", self.address_string(), fmt % args)

        def _send(self, status: int, payload, content_type="application/json") -> None:
            if content_type == "application/json":
                body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            else:
                body = payload.encode() if isinstance(payload, str) else payload
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path.rstrip("/") or "/"
            result = database.latest_scan(network)

            if path in ("/", "/api", "/api/status"):
                self._send(
                    200,
                    {
                        "service": "nettop",
                        "network": network,
                        "last_scan": result.scan_timestamp if result else None,
                        "devices": len(result.devices) if result else 0,
                        "online": result.online_count if result else 0,
                    },
                )
                return

            if result is None:
                self._send(503, {"error": "no scan data yet"})
                return

            if path == "/api/devices":
                self._send(200, [d.to_dict() for d in result.devices])
            elif path.startswith("/api/devices/"):
                ip = path.rsplit("/", 1)[-1]
                match = next((d for d in result.devices if d.ip == ip), None)
                if match is None:
                    self._send(404, {"error": f"device {ip} not found"})
                else:
                    self._send(200, match.to_dict())
            elif path == "/api/traffic":
                self._send(200, [c.to_dict() for c in result.connections])
            elif path == "/api/alerts":
                self._send(200, [a.to_dict() for a in result.alerts])
            elif path == "/metrics":
                self._send(200, prometheus_export.render(result), "text/plain")
            else:
                self._send(404, {"error": "not found"})

    return Handler


def serve(bind: str, database: Database, network: str | None) -> ThreadingHTTPServer:
    host, _, port = bind.partition(":")
    server = ThreadingHTTPServer(
        (host or "127.0.0.1", int(port or 8080)),
        make_handler(database, network),
    )
    log.info("REST API listening on http://%s", bind)
    return server
