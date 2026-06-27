# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.4.0] - 2026-06-28

### Added
- `daemon` mode: periodic scans with alerting and a standard-library REST API
  (`/api/devices`, `/api/traffic`, `/api/status`, `/api/alerts`, `/metrics`).
- Prometheus text-exposition export and a `/metrics` endpoint.
- `scripts/setup-daemon.sh` to install nettop as a systemd service.
- Slow-latency, high-bandwidth, new-device and offline alert rules.

### Changed
- Discovery now probes liveness ports through a single selector window, cutting
  sweep time on networks with many down hosts by roughly 4x.
- Reverse-DNS lookups are bounded by a hard wall-clock timeout so a slow
  resolver can no longer stall a scan.

## [0.3.0] - 2026-05-12

### Added
- `diff` command to compare two scans and report new/removed devices and port
  changes.
- `export` and `visualize` commands.
- Markdown, ASCII-topology and YAML exporters.
- `monitor` command for repeated scans on an interval.

## [0.2.0] - 2026-04-20

### Added
- SQLite history store; `device --history` reads past sightings.
- Optional nmap backend for OS and service/version detection, with automatic
  fallback to the built-in scanner.
- MAC vendor lookup and device-type classification.

## [0.1.0] - 2026-04-02

### Added
- First working release: `scan`, `device` and `doctor` commands.
- Built-in, dependency-free host discovery and TCP port scanning.
- `text`, `json` and `csv` output.
