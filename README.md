<h1 align="center">nettop</h1>

<p align="center">
  <strong>A clear map of your network — one command, right in the terminal.</strong>
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#commands">Commands</a> ·
  <a href="#output-formats">Output formats</a> ·
  <a href="#daemon-mode--rest-api">Daemon &amp; API</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg" alt="Cross-platform">
  <img src="https://img.shields.io/badge/dependencies-stdlib%20only-brightgreen.svg" alt="Standard library only">
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.ru.md">Русский</a>
</p>

---

**nettop** scans a network, finds the devices on it, works out their operating
systems and services, watches the traffic between them, and prints the result
in whatever shape you need: a terminal table, JSON, YAML, CSV, an ASCII
topology graph, ready-to-commit Markdown docs, or Prometheus metrics.

It is **CLI-first** on purpose. There is no web interface to run and no service
to babysit — just a single command that fits into scripts, cron jobs, CI
pipelines and monitoring stacks. It runs on the standard library alone, so a
plain `pip install` gives you a working tool with nothing else to set up. If
`nmap` and `tcpdump` happen to be installed, nettop uses them for richer OS
fingerprinting and traffic capture; if they are not, it falls back to its own
scanner and keeps going.

```
┌───────────────────────────────────────────────────┐
│ Network scan: 192.168.1.0/24                      │
│ 2026-05-18T09:14:02Z  |  8 device(s)  |  8 online │
└───────────────────────────────────────────────────┘

  IP           │ HOSTNAME            │ OS             │ TYPE    │ ST │ PORTS
  ─────────────┼─────────────────────┼────────────────┼─────────┼────┼────────────────────
  192.168.1.1  │ router              │ Network device │ network │ ✓  │ 53, 80, 443
  192.168.1.5  │ db-server           │ Linux/Unix     │ server  │ ✓  │ 22, 5432, 6379
  192.168.1.6  │ web-server          │ Linux/Unix     │ server  │ ✓  │ 22, 80, 443, 9090
  192.168.1.10 │ nas                 │ Linux/Unix     │ server  │ ✓  │ 22, 139, 445, 5000
  192.168.1.20 │ pi-hole             │ Linux/Unix     │ server  │ ✓  │ 53, 80, 22
  192.168.1.30 │ living-room-speaker │ -              │ iot     │ ✓  │ 1400, 1443
  192.168.1.40 │ office-printer      │ -              │ printer │ ✓  │ 631, 9100
  192.168.1.55 │ workstation         │ Windows        │ desktop │ ✓  │ 135, 139, 445, 3389

Summary
  Devices by type:
    server     4
    desktop    1
    iot        1
    network    1
    printer    1
```

## Why

Most admins never have a complete picture of their own network — what is
connected, which ports are open, who talks to whom, how much traffic is moving.
The usual answers are either too low-level to give you the whole map (`nmap`,
`tcpdump` used one host at a time), too heavy to stand up for a quick look
(Zabbix, Nagios), or tied to a GUI you cannot use on a headless box
(Wireshark).

nettop fills the gap in the middle: run one command, get an understandable map
of the network in a format you can actually use. It works immediately, with no
configuration, and it is built for the terminal.

## Features

- **Device discovery** — ping sweep plus TCP probing finds live hosts, including
  ones that drop ICMP. No root required.
- **Port & service detection** — a curated port set with optional banner
  grabbing, mapped to friendly service names.
- **OS and vendor hints** — TTL-based OS family guess and MAC-vendor lookup out
  of the box; full fingerprinting when `nmap` is available.
- **Device classification** — servers, desktops, network gear, IoT and printers
  are told apart automatically.
- **Seven output formats** — `text`, `json`, `yaml`, `csv`, `ascii`,
  `markdown`, `prometheus`.
- **History & diffing** — every scan is stored in SQLite; `diff` shows exactly
  what changed between two of them.
- **Traffic analysis** — per-link bandwidth from a live `tcpdump` capture.
- **Daemon mode** — periodic scans, alerting, a REST API and a Prometheus
  `/metrics` endpoint, all on the standard library.
- **Honest error handling** — missing privileges, missing tools and unreachable
  networks produce a clear message, not a stack trace.

## Install

### From source

```bash
git clone https://github.com/Sliptval/network-topology-analyzer.git
cd network-topology-analyzer
pip install .
```

This puts a `nettop` command on your PATH. You can also run it straight from a
checkout without installing:

```bash
python -m nettop --help
# or
./nettop-cli --help
```

### Optional external tools

nettop works with none of these, but installs cleaner data when they are
present:

| Tool      | Adds                                   | Debian/Ubuntu            | macOS               |
| --------- | -------------------------------------- | ------------------------ | ------------------- |
| `nmap`    | OS fingerprinting, service versions    | `apt install nmap`       | `brew install nmap` |
| `tcpdump` | live traffic capture (`--traffic`)     | `apt install tcpdump`    | preinstalled        |

Check your environment at any time:

```bash
nettop doctor
```

## Quick start

```bash
# Scan a subnet (auto-detects your local network if you omit --network)
nettop scan --network 192.168.1.0/24

# A deeper scan with banner/version detection, saved as JSON
nettop scan --network 192.168.1.0/24 --deep --output json --save scan.json

# Everything you know about one host
nettop device 192.168.1.5 --ports --services

# Draw the topology
nettop visualize

# Generate network documentation you can commit to a wiki
nettop export --format markdown --output network-docs.md
```

## Commands

| Command      | What it does                                                        |
| ------------ | ------------------------------------------------------------------- |
| `scan`       | Discover devices, ports and services on a network.                  |
| `device`     | Detailed information about a single host (with `--history`).        |
| `monitor`    | Repeated scans on an interval, reporting changes as they happen.    |
| `diff`       | Compare two saved scans and list what changed.                      |
| `export`     | Re-render the last stored scan in another format.                   |
| `visualize`  | ASCII topology graph of the last scan.                              |
| `trace`      | Trace the network route to a host.                                  |
| `daemon`     | Background monitoring with alerts and an optional REST API.         |
| `doctor`     | Check the environment, privileges and optional tools.               |

Run `nettop <command> --help` for the full option list of any command.

### scan

```bash
nettop scan --network 192.168.1.0/24            # text table (default)
nettop scan --network 192.168.1.0/24 --ports --deep
nettop scan --network 10.0.0.1-10.0.0.50 --output json
nettop scan --network 192.168.1.0/24 --traffic --duration 30s
```

`--network` accepts CIDR (`192.168.1.0/24`), a hyphen range
(`10.0.0.1-10.0.0.50`), a single IP, or a comma-separated mix. Omit it and
nettop uses the local network it detects.

### device

```bash
nettop device 192.168.1.5                  # last known details from history
nettop device 192.168.1.5 --ports          # probe it live right now
nettop device 192.168.1.5 --history        # every past sighting
```

### diff

```bash
nettop diff scan-monday.json scan-friday.json
```

```
Topology changes

New devices (1):
  + 192.168.1.42  laptop

Port changes:
  192.168.1.5  opened: 6379
```

## Output formats

Every format is available from `scan --output <fmt>` and from
`export --format <fmt>`.

<details>
<summary><strong>ASCII topology</strong> — <code>nettop visualize</code></summary>

```
192.168.1.0/24
└─ [gateway] 192.168.1.1
   ├─ db-server (192.168.1.5) [server]
   │  ├─ os: Linux/Unix
   │  └─ services: SSH, PostgreSQL, Redis
   ├─ web-server (192.168.1.6) [server]
   │  ├─ os: Linux/Unix
   │  └─ services: SSH, HTTP, HTTPS, Prometheus
   ├─ nas (192.168.1.10) [server]
   │  ├─ os: Linux/Unix
   │  └─ services: SSH, NetBIOS, SMB, UPnP/Flask
   └─ workstation (192.168.1.55) [desktop]
      ├─ os: Windows
      └─ services: MSRPC, NetBIOS, SMB, RDP
```
</details>

<details>
<summary><strong>Markdown documentation</strong> — <code>--format markdown</code></summary>

```markdown
# Network Documentation — `192.168.1.0/24`

_Generated 2026-05-18T09:14:02Z · 8 device(s), 8 online._

## Devices

| IP | Hostname | Type | OS | Open ports |
| --- | --- | --- | --- | --- |
| `192.168.1.1` | router | network | Network device | 53, 80, 443 |
| `192.168.1.5` | db-server | server | Linux/Unix | 22, 5432, 6379 |
```
</details>

<details>
<summary><strong>Prometheus metrics</strong> — <code>--format prometheus</code></summary>

```
# HELP nettop_devices_online Devices currently online.
# TYPE nettop_devices_online gauge
nettop_devices_online{network="192.168.1.0/24"} 8
nettop_device_up{network="192.168.1.0/24",ip="192.168.1.5",hostname="db-server"} 1
nettop_device_open_ports{network="192.168.1.0/24",ip="192.168.1.5"} 3
nettop_bandwidth_mbps{source="192.168.1.6",dest="192.168.1.5",protocol="tcp"} 42.7
```
</details>

<details>
<summary><strong>JSON</strong> — <code>--output json</code></summary>

```json
{
  "scan_timestamp": "2026-05-18T09:14:02Z",
  "network": "192.168.1.0/24",
  "online_count": 8,
  "devices": [
    {
      "ip": "192.168.1.5",
      "hostname": "db-server",
      "os": "Linux/Unix",
      "status": "online",
      "ports": [22, 5432, 6379],
      "services": ["SSH", "PostgreSQL", "Redis"]
    }
  ]
}
```
</details>

The `docs/examples/home-lab.json` file in this repo is a full sample scan — try
the exporters on it without scanning anything:

```bash
nettop export --input docs/examples/home-lab.json --format markdown
nettop visualize --input docs/examples/home-lab.json
```

## Daemon mode & REST API

Run continuous monitoring with alerting and, optionally, a small HTTP API:

```bash
nettop daemon --config config/default.yaml
nettop daemon --network 192.168.1.0/24 --interval 5m --api 127.0.0.1:8080
```

The API is built on the standard library — no framework, no extra dependency:

| Endpoint             | Returns                                    |
| -------------------- | ------------------------------------------ |
| `GET /api/status`    | Daemon and last-scan summary               |
| `GET /api/devices`   | Every device from the latest scan          |
| `GET /api/devices/<ip>` | One device                              |
| `GET /api/traffic`   | Observed connections                       |
| `GET /api/alerts`    | Active alerts                              |
| `GET /metrics`       | Prometheus exposition                      |

Alerts fire when a device goes offline, a new device appears, a link exceeds a
bandwidth threshold, or latency climbs past a limit — all configurable in the
YAML config.

### Prometheus & Grafana

Point Prometheus at the daemon:

```yaml
scrape_configs:
  - job_name: nettop
    static_configs:
      - targets: ["127.0.0.1:8080"]
```

Then chart `nettop_devices_online`, `nettop_device_up` or
`nettop_bandwidth_mbps` in Grafana.

### Run it as a service

```bash
sudo scripts/setup-daemon.sh /etc/nettop/config.yaml
systemctl status nettop
journalctl -u nettop -f
```

## Configuration

A config file is optional — every setting has a default and can be passed as a
flag. It is mainly there so the daemon does not need a dozen arguments. See
[`config/default.yaml`](config/default.yaml) for the full, commented example.

```yaml
network: 192.168.1.0/24
scan_interval: 5m
alerts:
  offline: true
  new_device: true
  high_bandwidth_mbps: 500
  slow_latency_ms: 200
api:
  enabled: true
  bind: 127.0.0.1:8080
```

## How it works

```
nettop/
├── cli.py            Command parsing and dispatch; turns errors into tidy messages
├── models.py         Device, Connection, Alert, ScanResult — the shared vocabulary
├── services.py       Port → service names and device-type heuristics
├── scanner/          Host discovery, port scanning, the optional nmap backend
├── traffic/          tcpdump capture and per-link bandwidth
├── storage/          SQLite history store
├── export/           One module per output format, behind a small registry
├── daemon/           Monitor loop, alert rules and the REST API
└── utils/            Address parsing, ARP/vendor lookup, privileges, logging
```

Each stage produces the same dataclasses, so the scanner, the database and the
exporters all speak the same language. Discovery and port scanning run in thread
pools; a `/24` typically completes in a few seconds even when most of it is
down.

## Requirements

- **Python 3.10 or newer.** No required third-party packages.
- Optional: `pyyaml` for prettier YAML output and YAML config files (a built-in
  fallback covers everything otherwise).
- Optional: `nmap` for OS/version detection, `tcpdump` for traffic capture.
- Scanning works unprivileged. OS fingerprinting and traffic capture need
  root/Administrator; nettop checks and tells you when they do.

## Development

```bash
pip install -e ".[dev]"
pytest
```

The unit tests cover address handling, every exporter, the diff engine, alert
rules, classification and storage.

## Responsible use

Only scan networks you own or are authorised to test. Port scanning and packet
capture on networks you do not control may be against the rules — or the law.
See [docs/legal.md](docs/legal.md).

## License

Released under the [MIT License](LICENSE).
