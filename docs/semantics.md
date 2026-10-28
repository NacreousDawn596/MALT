# MALT language semantics

This document specifies the exact behavior of the MALT language subset. It is
the normative reference for what MALT does — and, where it differs, for how it
differs from MATLAB. It is written to be testable: every "MUST" below is
enforced by a test in `tests/`.

## 1. Execution model

A `.m` file is compiled in memory and executed as a sequence of statements in a
single flat workspace. All statements execute in source order.

### 1.1 Scripts and functions

- A file with no leading `function` is a **script**. It executes top-to-bottom.
- A file may define **local functions** with `function`. All function
  definitions are hoisted; they may be defined after their call site in the
  source.
- A `function` has its own local scope: parameters and assigned variables are
  local, and it does not see the script workspace. It may read constants
  (`pi`, `Inf`, …) but not caller locals.

### 1.2 Workspace

The workspace is a flat mapping from identifier to value. Assigning `x = …`
creates or overwrites `x`. A failed statement must not corrupt unrelated
variables (see §7).

## 2. Numeric types

MALT has exactly **one** numeric type: the IEEE-754 double (`float64`), plus its
complex extension (`complex128`). There are no integers, singles, or integer
overflow semantics: every numeric literal is a double.

| Type | Representation | Notes |
| --- | --- | --- |
| double | Python `float` (or a 1×1 `float64` array) | the only real type |
| complex | Python `complex` (or a 1×1 `complex128` array) | `1i`, `3+4i` |
| logical | `1.0` / `0.0` doubles | `true`/`false`, comparisons |

- `true` is `1.0`, `false` is `0.0`. Logical results are doubles, not booleans.
- Constants: `pi`, `eps` (machine epsilon), `Inf`, `NaN`, `true`, `false`, `i`,
  `j` (imaginary unit). These are ordinary variables and **can be shadowed**
  by user assignment, exactly as in MATLAB.
- Arithmetic on doubles: `2 + 3` → `5.0`. Integer-valued results are doubles;
  there is no integer overflow because there are no integers.
- **Difference from MATLAB**: MALT has no single/uint8/etc. type classes; every
  numeric is a double. `isa(x, 'double')` is effectively always true for
  numeric `x`.

### 2.1 Scalar vs array representation (implementation detail)

Internally, at optimization level ≥ 1, scalar *intermediate* values are native
Python numbers; they are re-wrapped into 1×1 arrays only at semantic boundaries
(display, indexing, `size`/`numel`, matrix construction, function arguments).
Level 0 keeps scalars as 1×1 arrays throughout. Both are observationally
equivalent (§6.1).

## 3. Arrays and shapes

Every array is a NumPy `ndarray` with **at least two dimensions**.

| MATLAB value | shape |
| --- | --- |
| scalar `2` | `1×1` |
| row vector `[1 2 3]` | `1×3` |
| column vector `[1; 2; 3]` | `3×1` |
| matrix `[1 2; 3 4]` | `2×2` |
| N-D `zeros(3,4,5)` | `3×4×5` |
| empty `[]` / empty colon | `1×0` (or `0×0`) |

- `size(x)` reports all dimensions ≥ 2: a scalar is `1 1`, a row vector `1 3`.
- `numel(x)` is the total element count; `ndims(x)` is `max(2, ndim)`.
- `length(x)` is `max(size(x))`.
- **Column-major order**: `reshape`, linear indexing, and iteration order
  traverse elements down columns. `reshape([1 2 3 4 5 6], 2, 3)` is
  `[1 3 5; 2 4 6]` — this is **not** NumPy's row-major default.

### 3.1 Matrix literals

`[a b; c d]` builds rows by horizontal concatenation (`a b` or `a, b`) and
stacks rows vertically (`;`). Spaces and commas are equivalent column
separators. `[1 2 3]` is a 1×3 row vector; `[1; 2; 3]` is 3×1.

## 4. Operators

| op | semantics |
| --- | --- |
| `+` `-` | element-wise (with scalar expansion) |
| `*` | **matrix multiplication**; scalar `*` anything is element-wise scalar expansion |
| `/` | matrix right division (`A / B` ≈ `(B' \ A')'`) |
| `\` | matrix left division (`A \ b` solves `A x = b`) |
| `^` | matrix power (scalar exponent); scalar `^` scalar is scalar power |
| `.*` `./` `.\` `.^` | element-wise multiply/divide/power |
| `'` | conjugate transpose |
| `.'` | non-conjugating transpose |
| `==` `~=` `<` `<=` `>` `>=` | element-wise comparison → logical doubles |
| `&` `\|` | element-wise AND/OR (nonzero is true) |
| `&&` `\|\|` | short-circuit scalar AND/OR → logical double |
| `~` | logical not |

Precedence (tightest to loosest): transpose/power → unary `+ - ~` →
`* / \ .* ./ .\` → `+ -` → `:` → relational → `&` → `|` → `&&` → `||`.

### 4.1 Semantics of `\` and `/`

- `A \ b` for square nonsingular `A` uses a direct solve (LU), never a
  matrix inverse. For rectangular `A` it uses least squares.
- `A / B` is computed as `(B' \ A')'`, matching MATLAB's right-division
  convention.
- A **singular** solve falls back to least squares rather than raising
  (MATLAB-like warning behavior); the REPL is never torn down by a singular
  system.

### 4.2 Broadcasting

Scalar expansion follows MATLAB: a 1×1 (or scalar) operand broadcasts to the
other operand's shape for `+ - * .* ./ .\ .^ ^`. NumPy broadcasting is used but
only after verifying the shapes are MATLAB-compatible (singleton or equal).

## 5. Indexing

Indexing is **one-based** and **column-major** for linear indexing.

| form | result |
| --- | --- |
| `A(i)` | linear index `i` in column-major order; scalar `i` → 1×1 |
| `A(i, j)` | subscript; both scalar → 1×1 |
| `A(:, j)` | all rows of column `j` → `m×1` |
| `A(i, :)` | all columns of row `i` → `1×n` |
| `A(:)` | all elements as a `numel×1` column |
| `A(1:2:end)` | linear indices 1,3,5,… |
| `A([i j k])` | linear index vector (result shaped like the index vector) |
| `A(mask)` | logical indexing → column of selected elements |
| `A(end)` | last element; `A(end, :)` last row; `A(:, end)` last column |

- `end` is resolved per-subscript: in `A(end, :)` it is `size(A,1)`, in
  `A(:, end)` it is `size(A,2)`, in `A(end)` it is `numel(A)`.
- Indices are bounds-checked. Out-of-range indices raise an indexing error, and
  a **non-real** or fractional subscript is rejected.
- **Indexed assignment** `A(i,j) = v` mutates `A` in place (never a detached
  copy). `A(:, j) = column` and `A(i) = v` are supported. Assignment
  dimension-mismatch raises a dimension error.
- **Difference from MATLAB**: assignment into a matrix with a scalar index
  beyond the current bounds does **not** auto-grow the array (MATLAB grows
  arrays on out-of-range assignment); MALT raises an index error.

## 6. Control flow and loops

- `if … elseif … else … end`: the condition must be a scalar; nonzero (including
  nonzero complex) is true, zero is false. Non-scalar conditions raise.
- `while cond … end`: same scalar-condition rule.
- `for var = range … end`: iterates over the **columns** of `range`.

### 6.1 Colon and `for` iteration

`a:b` and `a:s:b` produce a **row vector**:

- `a:s:b` with `s > 0`: `[a, a+s, …, last ≤ b]`; empty if `b < a`.
- `a:s:b` with `s < 0`: `[a, a+s, …, last ≥ b]`; empty if `b > a`.
- `s == 0` is an error.
- The number of elements is `floor((b-a)/s) + 1` (0 when negative).

`for k = expr` iterates columns of `expr`; for a row vector this yields each
scalar element in order. After the loop, `k` holds the **last** iterated value,
or the empty array if the range was empty. `break` exits, `continue` skips.

**JIT note (level 2)**: for a loop whose range is integer-valued, MALT
specializes the iteration to Python `range()`. This is provably equivalent to
`colon` for integer-valued `(a, s, b)` (integers up to 2^53 are exactly
representable as doubles); any non-integer value falls back to `colon`. The loop
variable is yielded as a native scalar in both cases.

## 7. Errors and diagnostics

Error categories (all are `MaltError` subclasses):

| category | triggered by |
| --- | --- |
| `ParseError` | malformed syntax |
| `SemanticError` | `break`/`continue` outside a loop, duplicate functions, reserved identifiers |
| `IndexError_` | out-of-range or invalid subscript |
| `DimensionError` | shape mismatch in operators or assignment |
| `UndefinedVariableError` | reading an unassigned name |
| `RuntimeError_` | everything else at runtime |

- Errors carry the **original `.m` filename and line** (and a source excerpt /
  caret via the diagnostic renderer). Runtime errors are mapped back through a
  generated-source → source line map; a raw Python traceback is never shown by
  default (`--debug` re-raises it).
- A runtime error does not corrupt unrelated workspace variables in the REPL.

## 8. Functions

- `function [a, b] = f(x, y)` … `end` defines `f` with outputs `[a, b]`.
- A function returns all its declared outputs; a call site takes as many as it
  lists (`x = f(…)` takes the first; `[x, y] = f(…)` takes both). Requesting
  more outputs than declared is an error.
- Anonymous functions `@(x) expr` capture enclosing variables and are
  single-expression.
- Function handles: `@name` references a function; `f = @name; f(args)` calls it.

## 9. Differences from MATLAB (deliberate, documented)

1. **One numeric type** (double/complex only); no integer/single classes.
2. **No array auto-growth** on out-of-range indexed assignment.
3. **Presentation policy**: an unsuppressed assignment/expression in a script
   displays the value only (no `name =` echo); the REPL follows the same rule.
4. **Unsupported**: `switch` is supported, but `try/catch`, cell arrays `{}`,
   and structs are not (see `docs/language-support.md` and the pending specs in
   `docs/specs/`).
5. **Display formatting** is column-aligned but not byte-identical to MATLAB's
   `disp` (numerical values match; string formatting may differ).
6. **`&&`/`||` short-circuit** but, unlike MATLAB, are limited to scalar
   operands (non-scalar raises) — this matches MATLAB's own scalar requirement.
7. Seeded `rng` reproduces results **within MALT**, but the sequence is not
   bit-identical to MathWorks MATLAB's.

These are intentional; every one is tested. Anything else that behaves
differently is a bug, not a documented difference.
