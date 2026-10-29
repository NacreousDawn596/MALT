#!/usr/bin/env bash
# Build a portable, self-contained Linux distribution using PyInstaller onedir.
#
# Usage (on a Debian/Ubuntu system — not NixOS, see note below):
#   scripts/build-linux-portable.sh
#
# Produces:
#   dist/malt/malt            (CLI + REPL + debugger + LSP)
#   dist/malt-gui/malt-gui    (Qt6 notebook GUI)
#
# IMPORTANT: this must run on a Debian/Ubuntu (or older-glibc) system to
# produce a binary that runs on a wide range of Linux distros. Building on
# NixOS is not supported here because numpy/scipy carry RPATHs into the Nix
# store, so the output would not be portable. Use the CI release job
# (.github/workflows/release.yml, `ubuntu-22.04`) or the Nix flake instead.
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "==> installing build dependencies (into a venv)" >&2
  python3 -m venv .build-venv
  # shellcheck disable=SC1091
  . .build-venv/bin/activate
  pip install --upgrade pip
  pip install pyinstaller numpy scipy matplotlib pyqt6
fi

VERSION="$(grep -oP '__version__ = "\K[^"]+' src/malt/__init__.py)"
echo "==> building portable Linux dist (version $VERSION)"

rm -rf dist build

echo "==> CLI bundle (onedir)"
pyinstaller --noconfirm --clean --name malt \
  --collect-all numpy --collect-all scipy --collect-all matplotlib \
  --collect-all PyQt6 packaging/entrypoints/malt_cli.py

echo "==> GUI bundle (onedir)"
pyinstaller --noconfirm --clean --windowed --name malt-gui \
  --collect-all numpy --collect-all scipy --collect-all matplotlib \
  --collect-all PyQt6 packaging/entrypoints/malt_gui.py

if [[ ! -x "dist/malt/malt" ]]; then
  echo "error: dist/malt/malt was not produced" >&2
  exit 1
fi
if [[ ! -x "dist/malt-gui/malt-gui" ]]; then
  echo "error: dist/malt-gui/malt-gui was not produced" >&2
  exit 1
fi

echo "==> artifacts:"
echo "  $(pwd)/dist/malt/malt"
echo "  $(pwd)/dist/malt-gui/malt-gui"
