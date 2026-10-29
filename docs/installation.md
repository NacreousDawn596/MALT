# Installation

MALT is distributed through native packages for each platform: a Debian
package, a Nix flake, and a Windows installer. There is no requirement to
install anything into your system Python.

## Supported platforms

| Platform | Architecture | Format | Status |
| --- | --- | --- | --- |
| Debian / Ubuntu | `amd64` | `.deb` | built and smoke-tested in CI |
| NixOS / Nix | `x86_64-linux` | flake | built and tested |
| Windows | `x64` | `.exe` installer | built and smoke-tested in CI |

`arm64` (Linux/Windows) is not yet produced — the native dependency bundles
have not been verified for it.

## Debian / Ubuntu (`.deb`)

Download `malt_<version>_amd64.deb` and install it:

```bash
sudo apt install ./malt_0.4.0_amd64.deb
```

This installs the source under `/opt/malt` and a `malt` launcher under
`/usr/bin`. It declares dependencies on Debian's `python3-numpy`,
`python3-scipy`, and `python3-matplotlib` packages (installed automatically by
`apt`). The Qt6 GUI additionally needs `python3-pyqt6` (a `Recommends`; install
it explicitly for `malt gui`).

Requires Python 3.11+ (Debian 12 `bookworm` or Ubuntu 24.04+).

```bash
malt --version
malt repl          # interactive session
malt gui           # Qt6 notebook GUI
malt eval "2 + 2"
malt debug file.m
malt lsp           # language server (stdio)
```

Uninstall with `sudo apt remove malt`; this removes the package files and
leaves your home directory untouched.

## Portable Linux (no install)

A self-contained PyInstaller bundle (onedir) is available as a download:

```bash
chmod +x dist/malt/malt
./dist/malt/malt --version
./dist/malt/malt repl
```

It bundles NumPy, SciPy, Matplotlib, and Qt6, so it does not touch your system
Python. It is built on a Debian baseline (older glibc) in CI for compatibility
across distributions; see `docs/installation.md` and `packaging/README.md`.
No AppImage is currently produced (the required old-glibc baseline image is
not part of the automated build).

## NixOS / Nix

MALT is a Nix flake, so NixOS uses the native Nix packaging path (no
PyInstaller, no `.deb`).

```bash
# Run without installing
nix run github:NacreousDawn596/MALT -- --version

# Install into your user profile
nix profile install github:NacreousDawn596/MALT
malt --version
which malt
```

The package exposes `malt` and a `malt-gui` launcher, plus a `.desktop` entry
and icon for the GUI. REPL history is written to `~/.malt_history` (never into
the Nix store).

To install via `configuration.nix`, add the flake as an input and include
`inputs.malt.packages.${system}.default` (or the `malt` app) in
`environment.systemPackages`.

## Windows

Download `MALT-Setup-<version>-x64.exe` and run it. Installation is per-user
(no administrator rights needed) and defaults to
`%LOCALAPPDATA%\Programs\MALT`.

The installer creates two Start Menu shortcuts:

- **MALT REPL** — opens a terminal running `malt repl`.
- **MALT GUI** — launches the Qt6 notebook without a console window.

It offers a task to add MALT to your **user** `PATH`. After a fresh install,
open a **new** Command Prompt or PowerShell session so the updated `PATH`
takes effect:

```powershell
malt --version
malt eval "2 + 2"
malt repl
malt debug example.m
malt --help
```

Uninstall via *Settings → Apps → MALT → Uninstall* (or `malt-uninstall` in the
install directory). Uninstall removes only the Start Menu shortcuts and the
`PATH` entry that MALT created; unrelated `PATH` entries and user files are
left intact.

## CLI, debugger, and LSP

```bash
malt eval "expr"                 # evaluate a MATLAB expression
malt run program.m               # run a script
malt compile program.m           # emit generated Python
malt debug program.m -b LINE     # source-level debugger
malt lsp                         # language server over stdio
```

`malt lsp` speaks LSP over stdin/stdout and writes only protocol messages to
stdout (never startup banners). Editor setup is in
[docs/editor-integration.md](editor-integration.md).

## Known limitations

- **Qt plugins** — the Linux `.deb` relies on distro Qt packages; on NixOS the
  shell/package sets the Qt5 and Qt6 plugin paths automatically. If `malt gui`
  or `malt run` (with a GUI backend) reports "could not find the Qt platform
  plugin", set `QT_QPA_PLATFORM_PLUGIN_PATH` to your Qt `platforms` directory.
- **Graphics backends** — headless systems use the `Agg` backend
  (`MPLBACKEND=Agg`) and can still export PNGs with `saveas`/`exportgraphics`.
  Interactive windows need a display server and a GUI backend
  (`MPLBACKEND=Qt5Agg`, or `malt gui` which uses Qt6).
- **Shared libraries** — the Windows installer bundles NumPy/SciPy/Matplotlib
  and Qt6; the Debian package uses system packages. The runtime is **not** an
  OS sandbox for untrusted code.
- **Python version** — the Debian package requires Python 3.11+.

## Verification

Release artifacts are built in CI (see `docs/installation.md` source and
`.github/workflows/release.yml`). When checksums are published with a release,
verify them with `sha256sum` (Linux) or `Get-FileHash` (Windows) against the
published values before running the installer.
