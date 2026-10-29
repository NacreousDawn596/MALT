# NixOS setup

MALT targets NixOS first. Everything is pinned through `flake.lock`; nothing is
installed globally and nothing is downloaded at runtime.

## Prerequisites

- Nix with flakes enabled (`experimental-features = flakes nix-command`).
- A Nixpkgs revision pinned in `flake.nix` (currently `nixos-unstable`,
  `f4b794aaffc0e3d45da81088d492b118224bb476`).

## Development shell

```bash
nix develop
```

This drops you into a shell with:

- Python 3.13
- NumPy, SciPy, Matplotlib (built with Qt5 + Tk GUI backends)
- pytest, Hypothesis, ruff, mypy, git

The shell sets `MPLBACKEND=Agg` (headless) by default so that tests never
require a display, and puts `src/` on `PYTHONPATH`.

## Running

```bash
nix develop -c python -m malt --help
nix develop -c python -m malt run examples/graphics/sine_plot.m
nix develop -c python -m malt repl
```

## Interactive graphics

To open real figure windows, select a GUI backend and provide a display server:

```bash
MPLBACKEND=Qt5Agg nix develop -c python -m malt run examples/graphics/sine_plot.m
```

`malt run` (and `malt eval`) automatically display any open figures when the
process finishes — the equivalent of MATLAB's implicit `show`. Under the
default headless `Agg` backend this is a silent no-op, so scripts that only
render to PNG via `saveas`/`exportgraphics` are unaffected.

Qt support is compiled into the Matplotlib override (`enableQt = true`);
Tk is available too (`enableTk = true`). The dev shell also sets
`QT_QPA_PLATFORM_PLUGIN_PATH` to the store's Qt 5 platform plugins, so the
`xcb` platform plugin resolves (Qt renders through XWayland on GNOME Wayland).
Which backend works depends on your desktop environment. On headless NixOS
hosts, use `Agg` and `saveas`/`exportgraphics`.

## Building / installing (optional)

```bash
nix build .#default     # builds the malt wrapper derivation
```

This produces a `result/bin/malt` wrapper without modifying the host system.

## Constraints honoured

- No `sudo pip install`; no global Python packages.
- No assumptions about `/usr/lib` or FHS layouts.
- No hardcoded Qt plugin paths.
- No runtime dependency downloads.
- Reproducible builds via `flake.lock`.
