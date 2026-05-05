#!/usr/bin/env bash
#
# Uninstall the PDF Slim Services.

set -euo pipefail

SERVICES_DIR="$HOME/Library/Services"

BUNDLES=(
    "PDF Slim - Light (Print, 300dpi).workflow"
    "PDF Slim - Medium (eBook, 150dpi).workflow"
)

echo "==> removing PDF Slim Services"
for b in "${BUNDLES[@]}"; do
    rm -rf "$SERVICES_DIR/$b"
done

echo "==> refreshing Services menu"
/System/Library/CoreServices/pbs -update >/dev/null 2>&1 || true
killall Finder >/dev/null 2>&1 || true

echo "done."
