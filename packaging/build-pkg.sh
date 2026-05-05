#!/usr/bin/env bash
#
# Build a signed and notarized pdfslim .pkg installer.
#
# Usage:
#   packaging/build-pkg.sh <version>
#
# Example:
#   packaging/build-pkg.sh 0.1.0
#
# Output: dist/pdfslim-<version>.pkg (signed by Developer ID Installer
# cert, notarized by Apple, with notarization ticket stapled).

set -euo pipefail

VERSION="${1:-}"
if [ -z "$VERSION" ]; then
    echo "usage: $0 <version>" >&2
    exit 1
fi

# Project signing identities. The cert lives in the login keychain;
# the notarization profile was registered with 'xcrun notarytool
# store-credentials pdfslim-notary'.
SIGNING_IDENTITY="Developer ID Installer: Red Black Tree d.o.o. (SJ4RVBA27V)"
NOTARY_PROFILE="pdfslim-notary"
PKG_IDENTIFIER="rs.rbt.pdfslim"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG_DIR="$ROOT/packaging"
PAYLOAD="$PKG_DIR/payload-staging"
SCRIPTS_DIR="$PKG_DIR/scripts"
DIST_DIR="$ROOT/dist"
COMPONENT_PKG="$DIST_DIR/pdfslim-component.pkg"
UNSIGNED_PKG="$DIST_DIR/pdfslim-${VERSION}-unsigned.pkg"
FINAL_PKG="$DIST_DIR/pdfslim-${VERSION}.pkg"

PYTHON="$(command -v python3 || true)"
if [ -z "$PYTHON" ]; then
    echo "error: python3 not found on PATH" >&2
    exit 1
fi

echo "==> regenerating workflow bundles from bin/generate-workflows.py"
"$PYTHON" "$ROOT/bin/generate-workflows.py"

echo "==> staging payload at $PAYLOAD"
rm -rf "$PAYLOAD"
mkdir -p "$PAYLOAD/Library/Services" "$PAYLOAD/usr/local/bin"
for wf in "$ROOT/quick-actions/"*.workflow; do
    cp -R "$wf" "$PAYLOAD/Library/Services/"
done
cp "$PKG_DIR/pdfslim-uninstall" "$PAYLOAD/usr/local/bin/pdfslim-uninstall"
chmod +x "$PAYLOAD/usr/local/bin/pdfslim-uninstall"

echo "==> ensuring scripts are executable"
chmod +x "$SCRIPTS_DIR"/preinstall "$SCRIPTS_DIR"/postinstall

echo "==> building component pkg"
mkdir -p "$DIST_DIR"
pkgbuild \
    --root "$PAYLOAD" \
    --identifier "$PKG_IDENTIFIER" \
    --version "$VERSION" \
    --install-location "/" \
    --scripts "$SCRIPTS_DIR" \
    "$COMPONENT_PKG"

echo "==> assembling distribution pkg"
productbuild \
    --distribution "$PKG_DIR/Distribution.xml" \
    --resources "$PKG_DIR/resources" \
    --package-path "$DIST_DIR" \
    "$UNSIGNED_PKG"

echo "==> signing pkg with Developer ID Installer cert"
productsign \
    --sign "$SIGNING_IDENTITY" \
    "$UNSIGNED_PKG" \
    "$FINAL_PKG"

echo "==> submitting for notarization (this can take a few minutes)"
xcrun notarytool submit "$FINAL_PKG" \
    --keychain-profile "$NOTARY_PROFILE" \
    --wait

echo "==> stapling notarization ticket"
xcrun stapler staple "$FINAL_PKG"

echo "==> verifying signature and notarization"
spctl --assess --type install --verbose "$FINAL_PKG"
pkgutil --check-signature "$FINAL_PKG"

echo
echo "done. signed and notarized pkg:"
echo "  $FINAL_PKG"
