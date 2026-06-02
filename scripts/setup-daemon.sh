#!/usr/bin/env bash
#
# Generate and install a systemd unit that runs nettop in daemon mode.
# Run as root (or with sudo).
#
set -euo pipefail

CONFIG="${1:-/etc/nettop/config.yaml}"
UNIT="/etc/systemd/system/nettop.service"
BIN="$(command -v nettop || true)"

if [[ -z "${BIN}" ]]; then
    echo "nettop is not on PATH. Install it first (scripts/install.sh)." >&2
    exit 1
fi

if [[ ! -f "${CONFIG}" ]]; then
    echo "Config file '${CONFIG}' not found." >&2
    echo "Copy config/default.yaml there and edit it, or pass a path as \$1." >&2
    exit 1
fi

echo "Writing ${UNIT}"
cat > "${UNIT}" <<EOF
[Unit]
Description=nettop network topology monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=${BIN} daemon --config ${CONFIG}
Restart=on-failure
RestartSec=10
# Capturing traffic needs elevated rights; scanning alone does not.
# AmbientCapabilities=CAP_NET_RAW CAP_NET_ADMIN

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now nettop.service

echo "nettop.service installed and started."
echo "  systemctl status nettop"
echo "  journalctl -u nettop -f"
