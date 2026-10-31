# Architecture

## Compilation pipeline

```
MATLAB SOURCE (.m)
      |
      v
  LEXER  (src/malt/lexer.py, tokens.py)
      |   tokens with source locations and whitespace metadata
      v
  PARSER (src/malt/parser.py)
      |   recursive descent; operator precedence; block structure
      v
  AST    (src/malt/ast_nodes.py)
      |   immutable, location-annotated expression/statement nodes
      v
  SEMANTIC ANALYSIS (src/malt/semantic.py)
      |   break/continue placement, duplicate functions
      v
  CODE GENERATION (src/malt/codegen.py)
      |   MATLAB AST -> readable Python source + source map
      v
  CPYTHON COMPILATION (src/malt/compiler.py)
      |   compile(source, "<malt-generated:...>", mode="exec")
      v
  IN-MEMORY CODE OBJECT (src/malt/ir.py)
      |
      v
  CONTROLLED EXECUTION (src/malt/executor.py)
      |   restricted builtins + the `_ml` runtime namespace
      +--> MATLAB-COMPATIBLE RUNTIME (src/malt/runtime/)
      +--> NumPy / SciPy / Matplotlib
```

Every value in the MATLAB-visible workspace is either a Python `str` or a
NumPy `ndarray` with **at least two dimensions**. Scalars are 1x1, row vectors
1xN, column vectors Nx1 — so NumPy's one-dimensional convention never leaks
into MATLAB-visible semantics.

Internally (optimization level 1, the default), scalar *intermediate* values
flow as native Python numbers; `as_array` re-wraps them into 1x1 arrays only at
semantic boundaries (display, indexing, `size`/`numel`, function arguments,
matrix construction). This avoids allocating a 1x1 NumPy array for every scalar
arithmetic operation in a loop.

## Key design decisions

### Code generation strategy

The initial implementation lowers the MATLAB AST to *readable Python source*
strings, then compiles that source with CPython's `compile(..., mode="exec")`.
This was chosen over building a Python `ast.AST` directly because it is easier
to inspect (`--show-generated`), debug, and test. Identifiers are validated
against a reserved-word check and emitted verbatim only when safe; string and
numeric literals are emitted via `repr()`. Generated code never performs
string concatenation of untrusted expressions.

A per-statement **source map** (`(generated line, SourceLocation)`) is emitted
alongside the code. At runtime, the executor maps exceptions raised inside
generated code back to the original `.m` file and line.

### Runtime namespace

Generated code only references two names:

- `_ml` — the `malt.runtime` module, a flat namespace of functions whose
  MATLAB semantics differ from Python (`_ml.mtimes`, `_ml.index`, `_ml.colon`,
  `_ml.disp`, …).
- `__builtins__` — a minimal whitelist of Python builtins.

The `_` prefix is reserved; MATLAB identifiers must begin with a letter, so a
generated temporary or runtime name can never collide with a user variable.

### Indexing and `end`

`A(i)`, `A(i, j)`, `A(:, j)`, `A(A > 3)` are all lowered to `_ml.index(...)`
or `_ml.call(...)`. `_ml.call` dispatches dynamically: a callable (function
handle) is invoked, anything else is indexed. The `end` keyword is lowered to
`_ml.end_(base, dim)`, where `dim` is the 1-based subscript position (or 0 for
linear indexing), resolved by the code generator from context.

### Multi-output functions

- User functions compile to Python functions returning a tuple of all declared
  outputs; a single-output call site takes `[0]`.
- Runtime builtins with output-count semantics (`eig`, `svd`, `ode45`, `lu`,
  `qr`) take an explicit `nout` argument, so `eig(A)` and `[V, D] = eig(A)`
  behave differently, exactly as in MATLAB.

### Graphics

`runtime/graphics.py` wraps Matplotlib with a MATLAB-compatible API and its own
graphics state (current figure/axes, hold state, last mappable). The backend is
chosen at import from `MPLBACKEND`; when unset, it defaults to `Qt5Agg` on
Linux and Windows, and `Agg` elsewhere. The test suite inspects
real Matplotlib artists, not printed output.

## Correctness invariants

1. `MATLAB SOURCE → PROPER COMPILER PIPELINE → IN-MEMORY CPYTHON EXECUTION`.
2. Every claimed feature has a test that exercises the actual `.m` source
   through the actual runtime.
3. Runtime errors are source-aware: they carry the original filename and line,
   and generic Python exceptions are converted to `MaltError` subclasses.

## Performance

- **Scalar fast paths.** Element-wise and matrix operators detect scalar
  operands and use native Python arithmetic, avoiding 1x1 array allocation per
  operation. `for_columns` yields native scalars for row-vector loop ranges.
- **Indexing fast paths.** Scalar subscripts are bounds-checked and applied
  directly (`_flat_get`/`_flat_set` use column-major index arithmetic for row
  vectors, column vectors, and matrices without `reshape`/`flatten`), avoiding
  per-iteration allocation in indexed-assignment loops.
- **JIT-specialized scalar loops (level 2).** A `for k = a:s:b` loop whose body
  is a sequence of scalar accumulations `X = X op f(k)` (each RHS references
  only `k` and literals, never the accumulator) is lowered to a
  native-arithmetic Python function and driven by `_ml.jit_for` (one
  accumulator) or `_ml.jit_loop` (several independent accumulators). The
  runtime selects a Python `range` for integer ranges and falls back to
  `colon`/`for_columns` otherwise. This is conservative and semantically safe:
  the accumulator only ever combines with the scalar loop variable, which is
  element-wise in both MATLAB and native Python. Eligibility is explicit and
  everything else falls back to the general loop.
- **Compilation cache.** `compile_source` memoizes immutable artifacts (AST,
  generated source, code object, source map) keyed on
  `(source, filename, optimization_level)`; execution results and workspaces
  are never cached.
- **Optimization toggle.** `malt run --optimization-level 0|1|2`.
  Level 0 keeps scalars as 1x1 arrays (the slow, always-correct reference);
  level 1 uses native-scalar fast paths; level 2 additionally enables the
  JIT-specialized loop lowering. All three levels are covered by differential
  tests.

See `benchmarks/README.md` for measured before/after numbers and methodology.
