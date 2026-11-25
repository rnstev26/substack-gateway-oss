#!/bin/bash
# Start the local Substack gateway as a stdio MCP server, with the session
# cookie read from the macOS Keychain. bash 3.2-safe.
#
# Store or replace the cookie (prompts for the value; nothing lands in history):
#   security add-generic-password -U -s substack-gateway -a substack.sid -w
#
# Usage: local/substack-gateway-stdio.sh [--allow-schedule]
# stdout belongs to the MCP protocol: this script never writes to it.

set -eu

service="substack-gateway"
account="substack.sid"
root=$(cd "$(dirname "$0")/.." && pwd)
py="$root/.venv/bin/python"

if [ ! -x "$py" ]; then
    echo "substack-gateway-stdio: no venv; run 'uv sync --all-packages' in $root" >&2
    exit 1
fi

# Presence check without -w, so the value is not read here.
if ! security find-generic-password -s "$service" -a "$account" >/dev/null 2>&1; then
    echo "substack-gateway-stdio: no Keychain item (service $service, account $account)" >&2
    exit 2
fi

# The cookie travels only through this pipe, on fd 3, to the gateway process.
exec 3< <(security find-generic-password -s "$service" -a "$account" -w)
cd "$root"
exec "$py" "$root/local/stdio_server.py" "$@"
