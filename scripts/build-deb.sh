#!/usr/bin/env bash
# Build a Debian/Ubuntu `.deb` package for MALT.
#
# Usage:
#   scripts/build-deb.sh [--arch amd64]
#
# The package installs the MALT source under /opt/malt, a launcher under
# /usr/bin, and (optionally) a desktop entry + icon. Python dependencies are
# declared in the package's Depends field (python3-numpy, python3-scipy,
# python3-matplotlib) rather than bundled.
set -euo pipefail

cd "$(dirname "$0")/.."

ARCH="${ARCH:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --arch) ARCH="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 1 ;;
  esac
done

# --- prerequisites ---------------------------------------------------------
if command -v dpkg-deb >/dev/null 2>&1; then
  DPKG_DEB=(dpkg-deb)
elif command -v nix >/dev/null 2>&1; then
  # NixOS: pull dpkg-deb from nixpkgs on demand.
  DPKG_DEB=(nix shell nixpkgs#dpkg -c dpkg-deb)
else
  echo "error: dpkg-deb not found (install dpkg-dev, or run under Nix)" >&2
  exit 1
fi

if [[ -z "$ARCH" ]]; then
  ARCH="$(dpkg --print-architecture 2>/dev/null || uname -m)"
  # Normalize common uname values to Debian architecture names.
  case "$ARCH" in
    x86_64) ARCH=amd64 ;;
    aarch64) ARCH=arm64 ;;
  esac
fi

VERSION="$(python3 -c 'import re;print(re.search(r"__version__ = \"([^\"]+)\"", open("src/malt/__init__.py").read()).group(1))' 2>/dev/null || grep -oP '__version__ = "\K[^"]+' src/malt/__init__.py)"

DEB_NAME="malt_${VERSION}_${ARCH}.deb"
BUILD_DIR="$(mktemp -d)"
ROOT="$BUILD_DIR/malt_${VERSION}_${ARCH}"
PKG_ROOT="$ROOT/pkg"

echo "==> building $DEB_NAME (version $VERSION, arch $ARCH)"

# --- stage files -----------------------------------------------------------
mkdir -p "$PKG_ROOT/opt/malt/lib" "$PKG_ROOT/usr/bin"
cp -r src/malt "$PKG_ROOT/opt/malt/lib/malt"
find "$PKG_ROOT/opt/malt/lib/malt" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$PKG_ROOT/opt/malt/lib/malt" -type f -name "*.pyc" -delete

install -m 755 packaging/linux/debian/usr/bin/malt "$PKG_ROOT/usr/bin/malt"
install -m 755 packaging/linux/debian/usr/bin/malt-gui "$PKG_ROOT/usr/bin/malt-gui"

mkdir -p "$PKG_ROOT/usr/share/applications" "$PKG_ROOT/usr/share/icons/hicolor/256x256/apps"
install -m 644 packaging/linux/debian/usr/share/applications/malt.desktop \
  "$PKG_ROOT/usr/share/applications/malt.desktop"
install -m 644 assets/logo.png "$PKG_ROOT/usr/share/icons/hicolor/256x256/apps/malt.png"

# --- metadata --------------------------------------------------------------
mkdir -p "$PKG_ROOT/DEBIAN"
sed -e "s/@VERSION@/$VERSION/g" -e "s/@ARCH@/$ARCH/g" \
  packaging/linux/debian/DEBIAN/control > "$PKG_ROOT/DEBIAN/control"

# --- build -----------------------------------------------------------------
"${DPKG_DEB[@]}" --build --root-owner-group "$PKG_ROOT" "$DEB_NAME"

if [[ ! -f "$DEB_NAME" ]]; then
  echo "error: expected artifact $DEB_NAME was not produced" >&2
  exit 1
fi

rm -rf "$BUILD_DIR"
echo "==> wrote $(pwd)/$DEB_NAME"
