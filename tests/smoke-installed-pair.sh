#!/bin/sh
set -eu

installer_dir=${1:?Usage: smoke-installed-pair.sh INSTALLER_DIRECTORY}
test_root=$(mktemp -d)
export UV_TOOL_DIR="$test_root/uv-tools"
export UV_TOOL_BIN_DIR="$test_root/uv-bin"
export PERFCOMPARATOR_STATE_DIR="$test_root/state"
mkdir -p "$PERFCOMPARATOR_STATE_DIR"

sh "$installer_dir/install.sh"
perfcomparator="$UV_TOOL_BIN_DIR/perfcomparator"
perfcomparatorweb="$UV_TOOL_BIN_DIR/perfcomparatorweb"

"$perfcomparator" start --no-open-browser
web_url=$(sed -n 's/.*"url": "\([^"]*\)".*/\1/p' "$PERFCOMPARATOR_STATE_DIR/web.json")
curl --fail --silent "$web_url/" | grep -q 'Moteur PCE'
if "$perfcomparator" engine stop >/dev/null 2>&1; then
    echo "PCE stopped while PCWEB was still active." >&2
    exit 1
fi
"$perfcomparator" stop

"$perfcomparator" engine start
"$perfcomparatorweb" start --no-open-browser
"$perfcomparatorweb" status
if "$perfcomparator" engine stop >/dev/null 2>&1; then
    echo "PCE stopped while independently started PCWEB was active." >&2
    exit 1
fi
"$perfcomparatorweb" stop
"$perfcomparator" engine stop

echo "Installed PCE/PCWEB lifecycle smoke test passed."
