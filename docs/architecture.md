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
chosen at import from `MPLBACKEND` (default `Agg` for headless operation). The
test suite inspects real Matplotlib artists, not printed output.

## Correctness invariants

1. `MATLAB SOURCE → PROPER COMPILER PIPELINE → IN-MEMORY CPYTHON EXECUTION`.
2. Every claimed feature has a test that exercises the actual `.m` source
   through the actual runtime.
3. Runtime errors are source-aware: they carry the original filename and line,
   and generic Python exceptions are converted to `MaltError` subclasses.
