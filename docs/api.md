# Runtime and API reference

This document describes MALT's public Python API, compiler options, error
model, and compatibility guarantees. It is the contract for embedding MALT or
building tools on top of it.

## Versioning

MALT uses `major.minor.patch`. `malt.__version__` reports the running version.
Within a `0.x` series the public API below may evolve, but a breaking change is
accompanied by a changelog entry and a `minor` bump. Anything not listed here
(anything under `malt.runtime`, `malt.codegen`, `malt.lexer`, `malt.parser`,
`malt.semantic`, `malt.ir`, `malt.repl`) is an implementation detail and may
change without notice.

## Public Python API

```python
import malt
from malt.compiler import compile_source, cache_info, cache_clear
from malt.executor import execute, make_namespace
from malt import errors
from malt.diagnostics import render_error, source_excerpt
```

### Compilation

```python
unit = compile_source(source: str, filename: str = "<malt>",
                      optimization_level: int = 1) -> CompilationUnit
```

Compiles MATLAB source into an in-memory CPython code object. Returns a
`CompilationUnit` with attributes:

| attribute | meaning |
| --- | --- |
| `filename` | original source filename |
| `source` | original source text |
| `statements` | the parsed AST |
| `generated_source` | readable generated Python |
| `code` | the compiled code object |
| `source_map` | generated-line → source-location map |
| `diagnostics` | per-loop JIT specialization decisions |
| `warnings` | non-fatal `Diagnostic` objects (see below) |
| `show_generated()` | generated Python with a header |
| `coverage_report()` | human-readable JIT coverage summary |

Compilation is memoized: `compile_source` is cached by
`(source, filename, optimization_level)`. Only immutable artifacts are cached —
never execution results or workspaces.

```python
cache_info()   # -> (hits, misses, maxsize, currsize)
cache_clear()  # drop all cached compilation units
```

### Execution

```python
ns = execute(unit, namespace=None) -> dict
```

Executes a compiled unit in a fresh (or supplied) workspace namespace and
returns it. Each execution gets a fresh namespace unless one is supplied, so
repeated execution does not leak mutable state.

```python
ns = make_namespace()  # a fresh workspace: restricted builtins + constants
```

### Errors

```python
from malt.errors import (
    MaltError,            # base class
    LexError,             # malformed tokens
    ParseError,           # malformed syntax
    SemanticError,        # break/continue placement, duplicate functions
    CodegenError,         # internal code-generation failure
    RuntimeError_,        # runtime failure (note the trailing underscore)
    IndexError_,          # bad subscript
    DimensionError,       # shape mismatch
    UndefinedVariableError,  # unassigned name
    UnsupportedFeatureError,  # an unsupported construct
)
```

Every `MaltError` has:

- `.message` — the human-readable message.
- `.location` — a `SourceLocation` (`filename`, `line`, `column`) or `None`.
- `.category` — the stable category string (see the error model below).
- `.code` — a stable, tool-friendly identifier such as `E2001`.
- `.hint` — optional guidance rendered on a `help:` line, or `None`.

`render_error(error, source=...) -> str` renders a diagnostic with `file:line`,
an error code, a source excerpt, and a caret indicator. It is what the CLI
prints; it never includes a raw Python traceback (pass `--debug` to `malt run`
to re-raise). Pass `style="json"` for a machine-readable JSON object (see
`render_error_json`), and `color=True`/`False` to force or suppress ANSI color.

### Warnings

```python
from malt.errors import Diagnostic
```

Non-fatal diagnostics are collected (not raised) during compilation and
exposed on `unit.warnings`. Each `Diagnostic` has `.severity`, `.code` (e.g.
`W1001`), `.message`, `.location`, and `.hint`. The compiler currently emits
warnings for shadowing a builtin function (`W1001`) and shadowing the
imaginary unit `i`/`j` (`W1002`).

### CLI

`malt.cli.main(argv: list[str]) -> int` is the entry point; it returns the
process exit code. The documented commands are `eval`, `run`, `compile`,
`debug`, and `repl` (see `malt --help`).

Diagnostic flags shared by `eval`/`run`/`compile`/`debug`:

- `--color {auto,always,never}` (or `--no-color`) — ANSI color control;
  `auto` colorizes only when stderr is a TTY and `NO_COLOR` is unset.
- `--diagnostic-format {text,json}` — human-readable or structured output.
- `--no-warnings` — suppress non-fatal warnings.
- `--werror` — treat warnings as errors (non-zero exit).

`malt compile` additionally supports `--source-map PATH`, which writes a V3
source map (base64-VLQ) mapping generated Python lines back to the MATLAB
source, and appends a `# sourceMappingURL=` comment to the generated output.

`malt debug FILE.m` runs under the source-level debugger (see
`malt.debugger.Debugger`); `-b/--break LINE` sets an initial breakpoint.

## Compiler options / optimization levels

`--optimization-level {0,1,2}` selects the execution strategy. All three levels
are semantically equivalent and covered by differential tests; only the
internal representation and speed differ.

| level | behavior |
| --- | --- |
| 0 | Scalars are 1×1 NumPy arrays; no scalar fast paths. The slow, always-correct reference. |
| 1 (default) | Native-Python scalars for intermediate values; scalar fast paths in operators and indexing. |
| 2 | Adds JIT-specialized scalar `for` loops (native-arithmetic loop bodies driven by `range`/`colon`). |

Level 0 and 1 never skip a semantic check. Level 2 only specializes a loop that
provably matches the scalar-reduction pattern; everything else falls back to the
level-1 loop. Use `--explain` to see the per-loop decision.

## Error model

Errors are raised, not returned. The category strings are stable and are what
`try/catch` exposes as `err.identifier`:

| category | raised for |
| --- | --- |
| `lex error` | invalid character, unterminated string |
| `parse error` | malformed syntax, missing `end` |
| `semantic error` | `break`/`continue` outside a loop, reserved identifier |
| `index exceeds array dimensions` | out-of-range or non-integer subscript |
| `dimension mismatch` | incompatible operand/assignment shapes |
| `undefined variable` | reading an unassigned name |
| `runtime error` | other runtime failures |

Runtime errors are source-located: the executor maps a Python exception raised
inside generated code back to the original `.m` line via the source map, so a
user never has to read generated Python to diagnose their MATLAB program.

Error codes are stable (`E1001` lex, `E1002` parse, `E1003` semantic, `E1004`
codegen, `E2000` runtime, `E2001` index, `E2002` dimension, `E2003` undefined
variable, `E3000` unsupported); warning codes use a `W` prefix.

## Compatibility guarantees

- **Guaranteed**: the CLI commands and flags, the Python API above, the
  error-model category strings, the documented language semantics
  (`docs/semantics.md`), and the compatibility matrix
  (`docs/compatibility-matrix.md`).
- **Not guaranteed**: the generated Python text (it is inspectable via
  `--show-generated` but is an implementation detail), the internal module
  layout under `malt.runtime`, and exact `disp` formatting (numerical values
  match; column alignment may differ from MathWorks MATLAB).
- **Intentionally different from MATLAB**: case-sensitivity, a single
  double/complex numeric type, no array auto-growth, no char arithmetic,
  presentation policy, and MALT-specific RNG sequences — see the compatibility
  matrix.

The execution environment is **not** a security sandbox: `__builtins__` is
restricted and the language surface does not expose imports/`eval`/`exec`, but
executing untrusted code safely requires an operating-system-level boundary.
