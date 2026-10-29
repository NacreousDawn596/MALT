# MALT

A MATLAB-compatible language runtime powered by CPython.

MALT accepts MATLAB-like `.m` source, parses it into a proper AST, compiles it
into executable Python in memory, and runs it on CPython with NumPy, SciPy, and
Matplotlib as numerical and graphical backends.

It is **not** a MATLAB clone, a regex transpiler, or a wrapper around the
commercial MATLAB Engine. It is a standalone language implementation whose
source language is a documented MATLAB subset, whose execution backend is
CPython, and whose numerical/graphical backends are NumPy/SciPy/Matplotlib.

## Features

- A real lexer and recursive-descent parser producing an immutable, location
  annotated AST (operators, precedence, matrix literals, indexing, blocks).
- Explicit semantic analysis and code generation to CPython (in memory — no
  intermediate `.py` files).
- MATLAB semantics implemented deliberately on top of NumPy:
  - one-based indexing, `end`, colon expressions,
  - matrix vs. element-wise operators (`*`, `.*`, `^`, `.^`, `/`, `./`, `\`, `.\`),
  - conjugate vs. non-conjugating transpose (`'`, `.'`),
  - column-major `reshape`, MATLAB shape conventions (scalars are 1x1),
  - control flow, user functions, multiple outputs, anonymous functions.
- Numerical computing: elementary math, array construction, reductions,
  linear algebra, numerical integration, root finding, adaptive ODE solving
  (`ode45` via Dormand–Prince), complex arithmetic, seeded RNG.
- A Matplotlib graphics engine: figures, 2-D/3-D plotting, subplots, legends,
  labels, style strings, `hold`/`grid`/`axis`, `imagesc`, `surf`, `colorbar`,
  and PNG export — with a headless (Agg) mode for tests and CI.
- A persistent interactive REPL with a live workspace.

## Quick start (NixOS)

```bash
nix develop                      # reproducible dev shell
nix develop -c pytest            # run the full test suite
nix develop -c python -m malt --help
nix develop -c python -m malt run examples/graphics/sine_plot.m
nix develop -c python -m malt eval "1 + 2 * 3"
nix develop -c python -m malt repl
```

Interactive figure windows require a display server and a GUI backend:

```bash
MPLBACKEND=Qt5Agg nix develop -c python -m malt run examples/graphics/sine_plot.m
```

`malt run` auto-displays any open figures on exit (like MATLAB). Under the
default headless `Agg` backend that is a silent no-op — use
`saveas`/`exportgraphics` to render PNGs there.

## CLI

```
malt eval "expression"          # evaluate a MATLAB expression
malt run program.m              # run a MATLAB script
malt run program.m --show-generated
malt run program.m --optimization-level 0|1|2
malt compile program.m          # emit generated Python to stdout
malt compile program.m -o out.py
malt compile program.m --source-map program.map   # V3 source map
malt repl                       # interactive session
malt debug program.m            # source-level debugger (break/next/print/…)
malt debug program.m -b 12      # stop at line 12
malt lsp                        # language server (for VS Code/Neovim/Helix)
```

`--optimization-level` selects execution strategy: `0` = 1x1-array scalars
(reference), `1` = native-scalar fast paths (default), `2` = JIT-specialized
scalar loops.

## Benchmarks

```bash
nix develop -c python benchmarks/run.py        # full suite
nix develop -c python benchmarks/workbenches.py # targeted before/after + NumPy comparisons
```

See `benchmarks/README.md` for methodology and measured numbers.

## Project layout

```
src/malt/
  lexer.py tokens.py parser.py ast_nodes.py   # front end
  semantic.py ir.py codegen.py compiler.py    # middle end
  executor.py diagnostics.py errors.py        # execution + diagnostics
  runtime/                                   # MATLAB-compatible runtime
    arrays.py operators.py indexing.py functions.py
    linear_algebra.py calculus.py ode.py io.py graphics.py
  repl/session.py
tests/       unit, integration, compatibility, graphics, errors, security
examples/    basics, linear_algebra, calculus, differential_equations, graphics
docs/        architecture, language-support, nixos, testing
```

## Documentation

- [Language semantics](docs/semantics.md) — the normative language reference
- [Compatibility matrix](docs/compatibility-matrix.md) — implemented / partial / unsupported / different
- [Runtime and API](docs/api.md) — Python API, compiler options, error model
- [Architecture](docs/architecture.md)
- [Supported language features](docs/language-support.md)
- [NixOS setup](docs/nixos.md)
- [Testing](docs/testing.md)
- [Feature specifications](docs/specs/) — try/catch, cell arrays, structs

## Status

MALT is an early, correct-but-incomplete implementation. It is **not** fully
MATLAB-compatible and makes no claim to be. See `docs/language-support.md` for
the precise, tested feature surface and its known limitations.
