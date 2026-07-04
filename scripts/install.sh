#!/usr/bin/env bash
#
# Install nettop and check for the optional external tools it can use.
#
# Recent Debian/Ubuntu releases mark the system Python as "externally
# managed" (PEP 668) and refuse a plain `pip install`. This script tries a
# normal user install first and, if that is blocked, falls back to a private
# virtualenv under ~/.local/share/nettop with a `nettop` launcher symlinked
# into ~/.local/bin - no extra packages or root access required.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${HOME}/.local/bin"
VENV_DIR="${HOME}/.local/share/nettop/venv"

echo "Installing nettop from ${ROOT}"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required but was not found on PATH." >&2
    exit 1
fi

install_with_venv() {
    echo "System Python is externally managed; installing into a private virtualenv instead."
    python3 -m venv "${VENV_DIR}"
    "${VENV_DIR}/bin/pip" install --quiet --upgrade pip
    "${VENV_DIR}/bin/pip" install --quiet "${ROOT}"

    mkdir -p "${BIN_DIR}"
    ln -sf "${VENV_DIR}/bin/nettop" "${BIN_DIR}/nettop"

    if [[ ":${PATH}:" != *":${BIN_DIR}:"* ]]; then
        echo
        echo "Note: ${BIN_DIR} is not on your PATH yet. Add this to your shell profile:"
        echo "    export PATH=\"${BIN_DIR}:\$PATH\""
    fi
}

if output=$(python3 -m pip install --user "${ROOT}" 2>&1); then
    echo "${output}"
elif grep -qi "externally-managed-environment" <<<"${output}"; then
    install_with_venv
else
    echo "${output}" >&2
    exit 1
fi

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
