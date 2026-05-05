#!/usr/bin/env bash
#
# Install the PDF Slim Services.
#
# What this does:
#   1. Verifies Ghostscript ('gs') is on PATH
#   2. Regenerates the .workflow bundles (worker is embedded in each)
#   3. Installs the .workflow bundles into ~/Library/Services/
#   4. Refreshes the Services menu
#
# Re-running is safe (idempotent overwrite).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SERVICES_DIR="$HOME/Library/Services"

# Services launch with a minimal PATH; cover the common Homebrew
# prefixes so the gs check below mirrors the runtime conditions inside
# the workflow.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

echo "==> verifying ghostscript"
if ! command -v gs >/dev/null 2>&1; then
    cat >&2 <<'EOF'

error: Ghostscript ('gs') is not installed or not on PATH.

Install with Homebrew:

    brew install ghostscript

If you do not have Homebrew, install it from https://brew.sh first.

Once 'gs --version' works in your shell, re-run this installer.
EOF
    exit 1
fi
echo "    found: $(gs --version) at $(command -v gs)"

echo "==> regenerating Service bundles"
PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
    for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
        if [ -x "$candidate" ]; then PYTHON="$candidate"; break; fi
    done
fi
if [ -z "$PYTHON" ] || [ ! -x "$PYTHON" ]; then
    echo "error: no python3 found (needed only to regenerate workflows)" >&2
    exit 1
fi
"$PYTHON" "$ROOT/bin/generate-workflows.py"

echo "==> installing Services into $SERVICES_DIR"
mkdir -p "$SERVICES_DIR"
for wf in "$ROOT/quick-actions/"*.workflow; do
    name="$(basename "$wf")"
    # rm -rf the destination so 'cp -R' lands cleanly. macOS sometimes
    # auto-injects .DS_Store into bundles when Finder displays them; if we
    # don't fully wipe the destination, 'cp -R src dst' nests src inside dst.
    rm -rf "$SERVICES_DIR/$name"
    cp -R "$wf" "$SERVICES_DIR/$name"
    echo "    installed $name"
done

echo "==> refreshing Services menu"
/System/Library/CoreServices/pbs -update >/dev/null 2>&1 || true
killall Finder >/dev/null 2>&1 || true

cat <<EOF

done.

usage:
  - right-click any PDF in Finder
  - choose Services:
      PDF Slim - Light (Print, 300dpi)   ~89% reduction, archival quality
      PDF Slim - Medium (eBook, 150dpi)  ~94% reduction, sweet spot
  - the compressed file appears alongside the original with a _light or _medium suffix

uninstall:
  ./uninstall.sh
EOF
