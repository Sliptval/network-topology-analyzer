"""Port-to-service naming and device-type heuristics.

Keeping this knowledge in one table makes it easy to extend and easy to test.
"""

from __future__ import annotations

from .models import Device, DeviceType

# Well-known and commonly-seen ports mapped to a human-friendly service name.
SERVICE_NAMES: dict[int, str] = {
    20: "FTP-Data",
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    67: "DHCP",
    68: "DHCP",
    69: "TFTP",
    80: "HTTP",
    110: "POP3",
    111: "RPCbind",
    123: "NTP",
    135: "MSRPC",
    137: "NetBIOS",
    138: "NetBIOS",
    139: "NetBIOS",
    143: "IMAP",
    161: "SNMP",
    162: "SNMP-Trap",
    389: "LDAP",
    443: "HTTPS",
    445: "SMB",
    465: "SMTPS",
    500: "IKE/IPsec",
    514: "Syslog",
    515: "LPD/Printer",
    587: "SMTP-Submission",
    631: "IPP/Printer",
    636: "LDAPS",
    993: "IMAPS",
    995: "POP3S",
    1080: "SOCKS",
    1433: "MSSQL",
    1521: "Oracle-DB",
    1723: "PPTP",
    1883: "MQTT",
    2049: "NFS",
    2375: "Docker",
    2376: "Docker-TLS",
    3000: "Grafana/Node",
    3306: "MySQL",
    3389: "RDP",
    5000: "UPnP/Flask",
    5060: "SIP",
    5432: "PostgreSQL",
    5601: "Kibana",
    5672: "AMQP",
    5900: "VNC",
    6379: "Redis",
    6443: "Kubernetes-API",
    7070: "RealServer",
    8006: "Proxmox",
    8080: "HTTP-Alt",
    8086: "InfluxDB",
    8443: "HTTPS-Alt",
    8883: "MQTT-TLS",
    9000: "PHP-FPM/MinIO",
    9090: "Prometheus",
    9093: "Alertmanager",
    9100: "Printer/Node-Exporter",
    9200: "Elasticsearch",
    11211: "Memcached",
    27017: "MongoDB",
    32400: "Plex",
    51820: "WireGuard",
}

# Ports that strongly imply a particular kind of device.
_SERVER_PORTS = {22, 3306, 5432, 6379, 27017, 9200, 1433, 2049, 6443, 8006}
_PRINTER_PORTS = {515, 631, 9100}
_NETWORK_PORTS = {161, 179, 23}  # SNMP, BGP, Telnet-managed gear
_IOT_PORTS = {1883, 8883, 5000}  # MQTT and common IoT control panels


def service_name(port: int) -> str:
    """Return a friendly service name, falling back to 'port/<n>'."""
    return SERVICE_NAMES.get(port, f"port/{port}")


def services_for_ports(ports: list[int]) -> list[str]:
    """Map a list of open ports to a de-duplicated list of service names."""
    seen: set[str] = set()
    result: list[str] = []
    for port in sorted(ports):
        name = service_name(port)
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result


def classify_device(device: Device) -> DeviceType:
    """Guess a device type from its open ports, vendor and hostname.

    Heuristic and best-effort; the goal is a useful default, not certainty.
    """
    ports = set(device.ports)
    vendor = (device.vendor or "").lower()
    hostname = (device.hostname or "").lower()

    if any(k in vendor for k in ("cisco", "tp-link", "netgear", "ubiquiti", "mikrotik")):
        return DeviceType.NETWORK
    if ports & _PRINTER_PORTS or "printer" in hostname:
        return DeviceType.PRINTER
    if any(k in vendor for k in ("espressif", "sonos", "philips", "withings", "hue")):
        return DeviceType.IOT
    if ports & _NETWORK_PORTS and not (ports & _SERVER_PORTS):
        return DeviceType.NETWORK
    if ports & _IOT_PORTS:
        return DeviceType.IOT
    if ports & _SERVER_PORTS:
        return DeviceType.SERVER
    if "raspberry" in vendor:
        return DeviceType.SERVER
    if 3389 in ports or 445 in ports:
        return DeviceType.DESKTOP
    return DeviceType.UNKNOWN
