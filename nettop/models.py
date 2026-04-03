"""Core data model.

These dataclasses are the common currency of the whole program. The scanner
produces them, storage persists them, exporters render them. Keeping them in
one small module means every other part of the codebase agrees on what a
"device" or a "connection" actually is.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _utcnow() -> str:
    """Return the current UTC time as an ISO-8601 string with a Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class DeviceType(str, Enum):
    SERVER = "server"
    DESKTOP = "desktop"
    NETWORK = "network"
    IOT = "iot"
    PRINTER = "printer"
    MOBILE = "mobile"
    UNKNOWN = "unknown"


class Status(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class Protocol(str, Enum):
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Bandwidth:
    received_mbps: float = 0.0
    sent_mbps: float = 0.0
    latency_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Device:
    """A single host discovered on the network."""

    ip: str
    mac: str | None = None
    hostname: str | None = None
    os: str | None = None
    vendor: str | None = None
    device_type: DeviceType = DeviceType.UNKNOWN
    status: Status = Status.ONLINE
    ports: list[int] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    bandwidth: Bandwidth | None = None
    latency_ms: float | None = None
    last_seen: str = field(default_factory=_utcnow)
    uptime_seconds: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["device_type"] = self.device_type.value
        data["status"] = self.status.value
        if self.bandwidth is not None:
            data["bandwidth"] = self.bandwidth.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Device":
        data = dict(data)
        bw = data.pop("bandwidth", None)
        device_type = data.pop("device_type", DeviceType.UNKNOWN.value)
        status = data.pop("status", Status.ONLINE.value)
        known = {f for f in cls.__dataclass_fields__}  # noqa: SIM118
        clean = {k: v for k, v in data.items() if k in known}
        device = cls(
            device_type=DeviceType(device_type),
            status=Status(status),
            **clean,
        )
        if bw:
            device.bandwidth = Bandwidth(**bw)
        return device


@dataclass
class Connection:
    """Observed traffic between two hosts."""

    source_ip: str
    dest_ip: str
    protocol: Protocol = Protocol.TCP
    bandwidth_mbps: float = 0.0
    latency_ms: float | None = None
    packets: int = 0
    bytes: int = 0
    timestamp: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["protocol"] = self.protocol.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Connection":
        data = dict(data)
        protocol = data.pop("protocol", Protocol.TCP.value)
        known = {f for f in cls.__dataclass_fields__}  # noqa: SIM118
        clean = {k: v for k, v in data.items() if k in known}
        return cls(protocol=Protocol(protocol), **clean)


@dataclass
class Alert:
    """Something worth telling the operator about."""

    device_ip: str
    alert_type: str  # offline / high_bandwidth / slow_latency / new_device / back_online
    message: str
    severity: Severity = Severity.WARNING
    created_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        return data


@dataclass
class ScanResult:
    """The complete outcome of one scan - the unit exporters consume."""

    network: str
    scan_timestamp: str = field(default_factory=_utcnow)
    duration_seconds: float = 0.0
    devices: list[Device] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    alerts: list[Alert] = field(default_factory=list)

    @property
    def online_count(self) -> int:
        return sum(1 for d in self.devices if d.status is Status.ONLINE)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scan_timestamp": self.scan_timestamp,
            "network": self.network,
            "duration_seconds": round(self.duration_seconds, 2),
            "device_count": len(self.devices),
            "online_count": self.online_count,
            "devices": [d.to_dict() for d in self.devices],
            "connections": [c.to_dict() for c in self.connections],
            "alerts": [a.to_dict() for a in self.alerts],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScanResult":
        return cls(
            network=data.get("network", "unknown"),
            scan_timestamp=data.get("scan_timestamp", _utcnow()),
            duration_seconds=data.get("duration_seconds", 0.0),
            devices=[Device.from_dict(d) for d in data.get("devices", [])],
            connections=[Connection.from_dict(c) for c in data.get("connections", [])],
            alerts=[
                Alert(
                    device_ip=a.get("device_ip", ""),
                    alert_type=a.get("alert_type", ""),
                    message=a.get("message", ""),
                    severity=Severity(a.get("severity", "warning")),
                    created_at=a.get("created_at", _utcnow()),
                )
                for a in data.get("alerts", [])
            ],
        )
