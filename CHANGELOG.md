# Changelog

All notable changes to MALT are documented here. This project follows
`major.minor.patch`; within `0.x`, breaking changes bump the minor version.

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
