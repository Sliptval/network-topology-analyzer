#!/usr/bin/env bash
#
# Install nettop and check for the optional external tools it can use.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Installing nettop from ${ROOT}"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required but was not found on PATH." >&2
    exit 1
fi

python3 -m pip install --user "${ROOT}"

echo
echo "Checking optional external tools:"
for tool in nmap arp-scan tcpdump; do
    if command -v "${tool}" >/dev/null 2>&1; then
        printf '  %-10s found\n' "${tool}"
    else
        printf '  %-10s missing (optional)\n' "${tool}"
    fi
done

cat <<'EOF'

Done. Try:
    nettop doctor
    nettop scan --network 192.168.1.0/24

The built-in scanner needs no external tools. For OS/version detection install
nmap; for traffic capture install tcpdump.
EOF
