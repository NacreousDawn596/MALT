# Changelog

All notable changes to MALT are documented here. This project follows
`major.minor.patch`; within `0.x`, breaking changes bump the minor version.

## [0.4.5] — 2026-10-30

### Added
- The Qt6 notebook GUI (`malt gui`) now embeds native Matplotlib figures in
  cells via `FigureCanvasQTAgg` (QtAgg + PyQt6), with a figure lifecycle that
  handles creation, cross-cell modification, closure, and re-execution without
  duplicate canvases.
- The website download section now offers per-platform download buttons (Debian
  `.deb`, Windows installer + standalone executables, portable Linux tarball)
  and a hero "Download" link.

## [0.4.4] — 2026-10-30

### Changed
- Graphics backend defaults now use Matplotlib `Qt5Agg` on Linux and Windows
  when `MPLBACKEND` is unset; `MPLBACKEND` still takes precedence (for example,
  `Agg` on headless systems/CI).

### Fixed
- Repository-wide release/version references updated for `0.4.4`, including the
  website in `page/`.

## [0.4.3] — 2026-10-29

### Fixed
- Windows installer: fixed a `Type mismatch` in the Inno Setup `[Code]` section
  (`StringChange` is a procedure, not a function) and corrected an off-by-one in
  `EnvRemovePath`'s PATH-entry removal arithmetic.

## [0.4.2] — 2026-10-29

### Fixed
- Windows installer: fixed a Pascal comment in the Inno Setup `[Code]` section
  that broke compilation (the `{app}` reference closed the block comment early).
- Release workflow now publishes a GitHub Release with the built artifacts on
  tag push (`.deb`, Windows installer, portable Linux tarball).

## [0.4.1] — 2026-10-29

### Fixed
- Packaging build fixes: PyInstaller now discovers the `malt` package via
  `--paths src`, and the Windows Inno Setup script resolves its `dist/` and
  icon paths relative to the script (not the repository root).

## [0.4.0] — 2026-10-29

### Added
- **Diagnostics** — stable error codes (`E####`) and warning codes (`W####`),
  an optional `help:` hint line, ANSI color (`--color`, `--no-color`,
  `NO_COLOR`/`FORCE_COLOR`), and a structured `--diagnostic-format json`.
- **Warning channel** — non-fatal `Diagnostic` objects surfaced during
  compilation: shadowing a builtin (`W1001`) and shadowing the imaginary unit
  `i`/`j` (`W1002`), with `--no-warnings` and `--werror`.
- **Source maps** — V3 (base64-VLQ) source maps via `compile --source-map`,
  mapping generated Python lines back to MATLAB source, plus a
  `sourceMappingURL` directive.
- **Source spans** — statements carry end positions, so diagnostics underline
  the full offending statement rather than a single character.
- **Debugger** — `malt debug FILE.m` with `break`/`next`/`step`/`continue`/
  `print`/`list`/`where`/`quit`, operating on MATLAB source via the source map.
- **REPL** — readline history (persisted to `~/.malt_history`), tab-completion
  of builtins and variables, multi-line block input, and `whos`/`clear`.
- **Language server** — `malt lsp` speaks LSP over stdio (diagnostics, hover,
  completion) with no external dependencies (see `docs/editor-integration.md`).
- **Qt6 notebook GUI** — `malt gui`, an Apple-style notebook (Jupyter/Colab-
  like): draggable frameless window, editable and re-runnable cells, syntax
  highlighting, execution counters, run-all, and insert/move/delete controls.
- **Packaging** — a Debian `.deb`, a Windows `.exe` installer (PyInstaller +
  Inno Setup), a portable Linux onedir build, and Nix flake `apps`/GUI
  launcher/desktop entry (see `docs/installation.md`).

## [0.3.0] — 2026-10-29

### Added
- Cell arrays: `{...}` literals, `c{idx}` content access (linear and 2-D
  subscripts), `c{idx} = value` content assignment, `c{end}`, and `iscell`.
- Structs: `struct('f', v, …)`, dot-field read (`s.f`) and write (`s.f = v`),
  `fieldnames`, `isfield`, `isstruct`, and missing-field errors.
- Function handles: `func2str`, `str2func`, `feval`, and a named-handle wrapper
  so `@sin` round-trips through `func2str`/`str2func`.
- Compatibility predicates: `isnumeric ischar isempty isscalar isvector
  ismatrix isrow iscolumn isreal isfloat islogical isnan isinf isfinite`.
- `any`/`all` logical reductions (first non-singleton dimension).
- String helpers: `lower upper strcmp strcmpi strcat strjoin strsplit num2str`.
- Spec docs for cell arrays and structs moved from "planned" to "implemented".

### Limitations
- Cell *slice* access (`c(idx)`) and `cell(n)`/`cell(m,n)` constructors are not
  implemented; struct arrays (`struct('f', {v1, v2})`) are deferred.

## 0.2.0 — unreleased development milestone

> Version 0.2.0 was never tagged or published. The work below shipped in the
> codebase and is included in the 0.3.0 release.

### Added
- `switch`/`case`/`otherwise` and `try`/`catch` with `err.message`/`err.identifier`.
- A `.` field-access operator (on error values).
- JIT-specialized scalar loops (`--optimization-level 2`), including
  multi-accumulator loops, plus `--explain` diagnostics and a coverage report.
- A compilation cache (`compile_source` memoization).
- Differential testing against GNU Octave: structured (shape + real/imag),
  randomized (Hypothesis), and error-compatibility suites.
- `docs/semantics.md`, `docs/compatibility-matrix.md`, `docs/api.md`, and
  feature specs for try/catch, cell arrays, and structs.
- A benchmark suite (`benchmarks/`) with per-stage timings and dispersion.

### Fixed
- Reductions (`sum`, `mean`, `min`, `max`, `prod`, `cumsum`, `cumprod`, `sort`)
  now reduce along the first non-singleton dimension (previously all-elements).
- `round` now rounds half away from zero (was banker's rounding).
- `eig`/`eigvals` now return eigenvalues sorted ascending (and real when
  applicable).
- Division by zero is now `Inf`/`NaN` (was `ZeroDivisionError`).
- String escape sequences (`\n`, `\t`, …) are now processed.
- Non-integer and complex subscripts now error (were silently truncated).
- `sum` of an empty array is now `0`.
- `fprintf` with empty-array arguments no longer emits the literal format string.
- Empty loop bodies and empty ranges now behave correctly (loop variable set to
  the empty array).

### Performance
- Scalar loop: ~644 ms → ~18 ms/100k at level 2 (~35x).
- Indexed assignment: ~5.47 s → ~1.05 s/100k (~5x).
- Cached compilation of identical source: ~0.55 ms → ~1 µs.

## [0.1.0] — 2026-10

Initial release: lexer, recursive-descent parser, immutable AST, semantic
analysis, readable Python code generation, in-memory CPython compilation, a
NumPy/SciPy runtime with MATLAB array semantics, a Matplotlib graphics engine,
and a persistent REPL, all on a reproducible NixOS flake.
