# Changelog

All notable changes to MALT are documented here. This project follows
`major.minor.patch`; within `0.x`, breaking changes bump the minor version.

## [0.2.0] — unreleased

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
