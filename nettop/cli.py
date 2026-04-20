"""Command-line interface.

Parses ``nettop <command> [options]``, dispatches to a handler and takes care of
turning expected failures into tidy one-line errors instead of tracebacks.
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from pathlib import Path

from . import __version__, export
from .config import load_config, parse_duration
from .diff import diff_scans, render_diff
from .models import Device, ScanResult, Status
from .scanner import ScanEngine, ScanOptions
from .storage import Database
from .utils import net
from .utils.logging import configure, get_logger
from .utils.privileges import elevation_hint, is_elevated

log = get_logger(__name__)

TOOLS = ("nmap", "arp-scan", "tcpdump", "arp")


class CommandError(Exception):
    """A clean, user-facing error. Printed without a traceback."""


# --------------------------------------------------------------------------- #
# Argument parser
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nettop",
        description="A clear map of your network, one command away.",
        epilog="Run 'nettop <command> --help' for command-specific options.",
    )
    parser.add_argument("--version", action="version", version=f"nettop {__version__}")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="enable DEBUG logging"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="only log errors"
    )
    parser.add_argument(
        "--db",
        metavar="PATH",
        help="path to the SQLite history database (default: per-user data dir)",
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # scan
    p_scan = sub.add_parser("scan", help="discover devices, ports and services")
    p_scan.add_argument("--network", "-n", help="CIDR, range or IP list to scan")
    p_scan.add_argument("--ports", action="store_true", help="scan ports (default on)")
    p_scan.add_argument("--no-ports", action="store_true", help="skip port scanning")
    p_scan.add_argument(
        "--deep", action="store_true", help="wider port set + banner/version detection"
    )
    p_scan.add_argument(
        "--traffic", action="store_true", help="also capture traffic (needs privileges)"
    )
    p_scan.add_argument(
        "--duration", default="10s", help="traffic capture duration (e.g. 30s, 1m)"
    )
    p_scan.add_argument(
        "--no-nmap", action="store_true", help="force the built-in scanner"
    )
    p_scan.add_argument(
        "--output", "-o", default="text", help="output format", choices=export.available_formats()
    )
    p_scan.add_argument("--save", metavar="FILE", help="also write output to a file")
    p_scan.add_argument(
        "--no-store", action="store_true", help="do not record the scan in history"
    )
    p_scan.set_defaults(func=cmd_scan)

    # device
    p_device = sub.add_parser("device", help="detailed information about one host")
    p_device.add_argument("ip", help="device IP address")
    p_device.add_argument("--ports", action="store_true", help="rescan ports live")
    p_device.add_argument("--services", action="store_true", help="show services")
    p_device.add_argument("--history", action="store_true", help="show past sightings")
    p_device.add_argument(
        "--output", "-o", default="text", choices=("text", "json")
    )
    p_device.set_defaults(func=cmd_device)

    # diff
    p_diff = sub.add_parser("diff", help="compare two saved scans (JSON files)")
    p_diff.add_argument("before", help="earlier scan JSON")
    p_diff.add_argument("after", help="later scan JSON")
    p_diff.add_argument("--changes", action="store_true", help="only show changes")
    p_diff.add_argument("--output", "-o", default="text", choices=("text", "json"))
    p_diff.set_defaults(func=cmd_diff)

    # export
    p_export = sub.add_parser("export", help="re-render the last scan in another format")
    p_export.add_argument(
        "--format", "-f", default="markdown", choices=export.available_formats()
    )
    p_export.add_argument("--network", "-n", help="which network's last scan to export")
    p_export.add_argument("--input", "-i", help="read a scan JSON instead of history")
    p_export.add_argument("--output", "-o", metavar="FILE", help="write to a file")
    p_export.set_defaults(func=cmd_export)

    # visualize
    p_vis = sub.add_parser("visualize", help="ASCII topology of the last scan")
    p_vis.add_argument("--network", "-n", help="which network's last scan to draw")
    p_vis.add_argument("--input", "-i", help="read a scan JSON instead of history")
    p_vis.add_argument("--format", default="ascii", choices=("ascii",))
    p_vis.set_defaults(func=cmd_visualize)

    # monitor
    p_mon = sub.add_parser("monitor", help="repeated scans on an interval")
    p_mon.add_argument("--network", "-n", help="network to monitor")
    p_mon.add_argument("--interval", default="30s", help="time between scans")
    p_mon.add_argument("--count", type=int, default=0, help="stop after N scans (0 = forever)")
    p_mon.add_argument("--format", default="text", choices=("text", "json"))
    p_mon.set_defaults(func=cmd_monitor)

    # trace
    p_trace = sub.add_parser("trace", help="trace the route to a host")
    p_trace.add_argument("target", help="destination IP or hostname")
    p_trace.add_argument("--max-hops", type=int, default=30)
    p_trace.set_defaults(func=cmd_trace)

    # daemon
    p_daemon = sub.add_parser("daemon", help="background monitoring with optional API")
    p_daemon.add_argument("--config", help="YAML/JSON config file")
    p_daemon.add_argument("--network", "-n", help="network to monitor")
    p_daemon.add_argument("--interval", help="time between scans (overrides config)")
    p_daemon.add_argument("--api", metavar="HOST:PORT", help="serve the REST API")
    p_daemon.add_argument(
        "--export-prometheus",
        metavar="HOST:PORT",
        help="serve Prometheus metrics (same server as --api if both set to one bind)",
    )
    p_daemon.set_defaults(func=cmd_daemon)

    # doctor / check
    p_doctor = sub.add_parser("doctor", help="check environment and dependencies")
    p_doctor.set_defaults(func=cmd_doctor)

    return parser


# --------------------------------------------------------------------------- #
# Command handlers
# --------------------------------------------------------------------------- #

def _resolve_network(explicit: str | None) -> str:
    if explicit:
        return explicit
    guesses = net.local_networks()
    if len(guesses) == 1:
        log.info("No --network given; using detected local network %s", guesses[0])
        return guesses[0]
    if len(guesses) > 1:
        raise CommandError(
            "Multiple local networks detected: "
            + ", ".join(guesses)
            + ". Pass one with --network."
        )
    raise CommandError(
        "Could not detect a local network. Pass one explicitly, "
        "e.g. --network 192.168.1.0/24"
    )


def cmd_scan(args: argparse.Namespace, db: Database) -> int:
    network = _resolve_network(args.network)
    scan_ports = not args.no_ports
    options = ScanOptions(
        network=network,
        scan_ports=scan_ports,
        deep=args.deep,
        use_nmap=not args.no_nmap,
        os_detect=args.deep and is_elevated(),
    )
    result = ScanEngine(options).run()

    if args.traffic:
        _attach_traffic(result, args.duration)

    if not args.no_store:
        db.save_scan(result)

    rendered = export.render(result, args.output)
    _write_output(rendered, args.save)
    return 0


def _attach_traffic(result: ScanResult, duration: str) -> None:
    from .traffic import TrafficCapture, capture_available

    available, reason = capture_available()
    if not available:
        log.warning("Skipping traffic capture: %s", reason)
        return
    seconds = parse_duration(duration)
    result.connections = TrafficCapture().capture(seconds)


def cmd_device(args: argparse.Namespace, db: Database) -> int:
    try:
        net._validate_ip(args.ip)
    except net.NetworkError as exc:
        raise CommandError(str(exc)) from exc

    device: Device | None = None
    if args.ports:
        options = ScanOptions(network=args.ip, deep=args.services, use_nmap=False)
        result = ScanEngine(options).run()
        device = result.devices[0] if result.devices else None
    else:
        latest = db.latest_scan()
        if latest:
            device = next((d for d in latest.devices if d.ip == args.ip), None)

    if device is None and not args.history:
        raise CommandError(
            f"No data for {args.ip}. Run a scan first, or use --ports to probe it now."
        )

    if args.output == "json":
        payload: dict = {"ip": args.ip}
        if device:
            payload["device"] = device.to_dict()
        if args.history:
            payload["history"] = db.device_history(args.ip)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if device:
        print(_render_device_detail(device))
    if args.history:
        history = db.device_history(args.ip)
        print("\nHistory:")
        if not history:
            print("  (no recorded sightings)")
        for row in history:
            print(
                f"  {row['scan_timestamp']}  {row['status']:<8} "
                f"{row.get('hostname') or '-'}"
            )
    return 0


def _render_device_detail(device: Device) -> str:
    lines = [
        f"Device {device.ip}",
        "─" * (7 + len(device.ip)),
        f"  Hostname : {device.hostname or '-'}",
        f"  MAC      : {device.mac or '-'}",
        f"  Vendor   : {device.vendor or '-'}",
        f"  OS       : {device.os or '-'}",
        f"  Type     : {device.device_type.value}",
        f"  Status   : {device.status.value}",
    ]
    if device.latency_ms is not None:
        lines.append(f"  Latency  : {device.latency_ms:.1f} ms")
    if device.ports:
        lines.append(f"  Ports    : {', '.join(str(p) for p in device.ports)}")
    if device.services:
        lines.append(f"  Services : {', '.join(device.services)}")
    return "\n".join(lines)


def cmd_diff(args: argparse.Namespace, db: Database) -> int:
    before = _load_scan_file(args.before)
    after = _load_scan_file(args.after)
    result = diff_scans(before, after)
    if args.output == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(render_diff(result), end="")
    return 0


def cmd_export(args: argparse.Namespace, db: Database) -> int:
    if args.input:
        result = _load_scan_file(args.input)
    else:
        result = db.latest_scan(args.network)
        if result is None:
            raise CommandError(
                "No stored scans to export. Run 'nettop scan' first, "
                "or pass --input <scan.json>."
            )
    rendered = export.render(result, args.format)
    _write_output(rendered, args.output)
    return 0


def cmd_visualize(args: argparse.Namespace, db: Database) -> int:
    if args.input:
        result = _load_scan_file(args.input)
    else:
        result = db.latest_scan(args.network)
        if result is None:
            raise CommandError("No stored scans to visualize. Run 'nettop scan' first.")
    print(export.render(result, "ascii"), end="")
    return 0


def cmd_monitor(args: argparse.Namespace, db: Database) -> int:
    network = _resolve_network(args.network)
    interval = parse_duration(args.interval)
    count = 0
    previous = db.latest_scan(network)
    log.info("Monitoring %s every %s (Ctrl-C to stop)", network, args.interval)
    try:
        while True:
            result = ScanEngine(ScanOptions(network=network)).run()
            db.save_scan(result)
            if args.format == "json":
                print(export.render(result, "json"))
            else:
                changed = ""
                if previous is not None:
                    d = diff_scans(previous, result)
                    if d.has_changes:
                        changed = (
                            f"  (+{len(d.new_devices)} new, "
                            f"-{len(d.removed_devices)} gone)"
                        )
                print(
                    f"[{result.scan_timestamp}] {result.online_count} online"
                    f"{changed}"
                )
            previous = result
            count += 1
            if args.count and count >= args.count:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
    return 0


def cmd_trace(args: argparse.Namespace, db: Database) -> int:
    import shutil
    import subprocess

    tool = "tracert" if sys.platform == "win32" else "traceroute"
    if shutil.which(tool) is None:
        raise CommandError(
            f"'{tool}' is not installed. Install it to use 'nettop trace'."
        )
    if sys.platform == "win32":
        cmd = [tool, "-h", str(args.max_hops), args.target]
    else:
        cmd = [tool, "-m", str(args.max_hops), args.target]
    log.info("Tracing route to %s", args.target)
    try:
        completed = subprocess.run(cmd, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise CommandError(f"trace failed: {exc}") from exc
    return completed.returncode


def cmd_daemon(args: argparse.Namespace, db: Database) -> int:
    import threading

    config = load_config(args.config) if args.config else load_config(None)
    network = _resolve_network(args.network or config.get("network"))
    interval_str = args.interval or config.get("scan_interval", "5m")
    interval = parse_duration(interval_str)

    from .daemon import Monitor

    monitor = Monitor(
        network, interval_seconds=interval, database=db, config=config
    )

    servers = []
    api_bind = args.api or (config.api.get("bind") if config.api.get("enabled") else None)
    if api_bind:
        from .daemon import api as api_module

        server = api_module.serve(api_bind, db, network)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)

    def _handle_signal(_sig, _frame):
        monitor.stop()

    signal.signal(signal.SIGINT, _handle_signal)
    try:
        signal.signal(signal.SIGTERM, _handle_signal)
    except (AttributeError, ValueError):  # pragma: no cover - platform dependent
        pass

    try:
        monitor.run_forever()
    finally:
        for server in servers:
            server.shutdown()
    return 0


def cmd_doctor(args: argparse.Namespace, db: Database) -> int:
    print("nettop environment check")
    print("─" * 24)
    print(f"  nettop version : {__version__}")
    print(f"  python         : {sys.version.split()[0]}")
    print(f"  platform       : {sys.platform}")
    print(f"  privileges     : {'elevated' if is_elevated() else 'normal (' + elevation_hint() + ')'}")
    print(f"  database       : {db.path}")
    print("  external tools :")
    for tool, present in net.which_tools(TOOLS).items():
        mark = "found" if present else "missing"
        print(f"    {tool:<10} {mark}")
    guesses = net.local_networks()
    print(f"  local networks : {', '.join(guesses) if guesses else 'none detected'}")
    print(
        "\nThe built-in scanner works without any external tools. "
        "Install nmap for OS/version detection and tcpdump for traffic capture."
    )
    return 0


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #

def _load_scan_file(path: str) -> ScanResult:
    file_path = Path(path)
    if not file_path.exists():
        raise CommandError(f"File not found: {path}")
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CommandError(f"{path} is not valid JSON: {exc}") from exc
    return ScanResult.from_dict(data)


def _write_output(rendered: str, path: str | None) -> None:
    sys.stdout.write(rendered)
    if not rendered.endswith("\n"):
        sys.stdout.write("\n")
    if path:
        Path(path).write_text(rendered, encoding="utf-8")
        log.info("Wrote output to %s", path)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def _force_utf8_output() -> None:
    """Emit UTF-8 regardless of the console code page.

    Windows consoles often default to a legacy code page (cp1251, cp437, ...)
    that cannot encode the box-drawing and status glyphs used in the tables.
    Reconfiguring the streams keeps output tidy and, crucially, stops the tool
    from crashing on a UnicodeEncodeError.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):  # pragma: no cover - defensive
                pass


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = build_parser()
    args = parser.parse_args(argv)

    level = "DEBUG" if args.verbose else "INFO"
    configure(level, quiet=args.quiet)

    if not getattr(args, "command", None):
        parser.print_help()
        return 1

    db = Database(args.db)
    try:
        return args.func(args, db)
    except CommandError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except net.NetworkError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
