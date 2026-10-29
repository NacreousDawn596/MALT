# Packaging

This directory contains the packaging configuration for building distributable
MALT artifacts. Build scripts live in `scripts/`.

## Layout

```text
packaging/
  icons/
    malt.ico                    # Windows icon (multi-size, derived from assets/logo.png)
  linux/
    debian/                     # Debian package tree
      DEBIAN/control            # metadata (version/arch substituted at build time)
      usr/bin/malt              # launcher (sets PYTHONPATH, execs python3 -m malt)
      usr/bin/malt-gui          # launcher (execs malt gui)
      usr/share/applications/malt.desktop
  windows/
    malt_cli.py                 # PyInstaller entry (console CLI)
    malt_gui.py                 # PyInstaller entry (windowed GUI)
    malt-installer.iss          # Inno Setup script (per-user, PATH task, shortcuts)
  README.md
```

## Version source of truth

The version lives in `src/malt/__init__.py` (`__version__`) and is mirrored in
`pyproject.toml` and `flake.nix`. The build scripts read it from
`src/malt/__init__.py` — do not hardcode it in packaging files.

## Linux: Debian package (`.deb`)

```bash
scripts/build-deb.sh --arch amd64
# -> malt_<version>_amd64.deb
```

Requires `dpkg-deb` (install `dpkg-dev`, or run under Nix — the script uses
`nix shell nixpkgs#dpkg` automatically). The package installs the source under
`/opt/malt` and declares Python dependencies in `Depends`.

Smoke-test on a real Debian/Ubuntu system:

```bash
scripts/test-package.sh malt_<version>_amd64.deb
```

## Nix

The flake is the native Nix packaging path (no PyInstaller):

```bash
nix build .#default
nix run .#default -- --version
nix flake check
```

## Linux: portable onedir (PyInstaller)

```bash
scripts/build-linux-portable.sh
# -> dist/malt/malt, dist/malt-gui/malt-gui
```

Build on a Debian/Ubuntu system (the CI uses `ubuntu-22.04` for a wide glibc
compatibility baseline). Do **not** build on NixOS — numpy/scipy carry Nix
store RPATHs there, so the result would not be portable. NixOS users use the
flake.

## Windows

Build on a Windows x64 runner (PyInstaller cannot cross-compile from Linux):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1
# -> dist\malt.exe, dist\malt-gui.exe, dist\MALT-Setup-<version>-x64.exe
```

Requires Python 3.11+, and Inno Setup 6.

## CI

`.github/workflows/release.yml` builds each artifact on its native runner
(Debian on `ubuntu-24.04`, Windows on `windows-latest`, Nix on `ubuntu-latest`),
smoke-tests it, and uploads it. It is gated to manual dispatch or a version tag
and never publishes a GitHub release automatically.
