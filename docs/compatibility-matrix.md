# Compatibility matrix

Status legend:

- ✅ **Implemented** — behaves like MATLAB and is tested (including differential
  tests against Octave where applicable).
- ⚠️ **Partially implemented** — the documented subset works; some forms or
  options are missing.
- ❌ **Unsupported** — parses or is rejected with a clear error; not executed.
- 🔸 **Intentionally different** — a deliberate, documented divergence (not a
  bug). Each has a test.

The normative semantics are in `docs/semantics.md`; the tests are in `tests/`
(compatibility and `tests/differential/`).

## Lexical and operators

| Feature | Status | Notes |
| --- | --- | --- |
| Integers, floats, scientific notation | ✅ | |
| Imaginary literals `4i`, `3+4i` | ✅ | |
| Single-quoted strings + escapes (`\n`, `\t`, `''`) | ✅ | |
| Comments `%` | ✅ | |
| Block comments `%{ %}` | ❌ | |
| `+ - * / \ ^` (matrix ops) | ✅ | |
| `.* ./ .\ .^` (element-wise) | ✅ | |
| `'` / `.'` (conj / plain transpose) | ✅ | |
| `== ~= < <= > >= & \| ~` | ✅ | |
| `&& \|\|` (short-circuit) | ✅ | |
| `:` (colon) | ✅ | exact MATLAB semantics incl. empty/float/negative step |
| `=` assignment | ✅ | |
| augmented assignment `+= -= *= …` | 🔸 | a MALT extension; not MATLAB |
| field access `a.b` | ⚠️ | on structs and `try/catch` error values |
| case-insensitivity | 🔸 | MALT identifiers are case-sensitive; MATLAB is not |

## Arrays and indexing

| Feature | Status | Notes |
| --- | --- | --- |
| Scalars (1×1), vectors, matrices, N-D | ✅ | |
| Empty arrays | ✅ | `1:0` is `1×0` |
| Column-major `reshape` | ✅ | |
| `A(i)`, `A(i,j)`, `A(:,j)`, `A(i,:)`, `A(:)` | ✅ | |
| `end` (per-subscript) | ✅ | |
| `A([i j k])`, `A(mask)` logical indexing | ✅ | |
| Indexed assignment `A(i,j)=v` | ✅ | |
| Out-of-bounds index | ✅ | errors (like MATLAB) |
| Non-integer / complex index | ✅ | errors (like MATLAB) |
| Array auto-growth on out-of-range assignment | 🔸 | MALT errors; MATLAB grows the array |
| Cell arrays `{}` | ⚠️ | `{}` literals, `c{idx}` content access/assign, `iscell`; no `c(idx)` slices, `c{:}`, or `cell(n)` |
| Structs | ⚠️ | `struct`, dot read/write, `fieldnames`, `isfield`, `isstruct`; no struct arrays |

## Control flow

| Feature | Status | Notes |
| --- | --- | --- |
| `if`/`elseif`/`else` | ✅ | scalar condition |
| `for` (over columns) | ✅ | loop var persists (incl. empty) |
| `while` | ✅ | |
| `break` / `continue` | ✅ | |
| `return` | ✅ | |
| `switch`/`case`/`otherwise` | ✅ | |
| `try`/`catch [err]` | ✅ | `err.message`, `err.identifier` |
| `parfor` / `spmd` | ❌ | |

## Functions

| Feature | Status | Notes |
| --- | --- | --- |
| `function [a,b] = f(x,y)` (multi-output) | ✅ | |
| Local scope, hoisted script functions | ✅ | |
| Anonymous functions `@(x) …` | ✅ | |
| Function handles `@name` | ✅ | `@name`, `func2str`, `str2func`, `feval` |
| `nargin`/`nargout`, `varargin`/`varargout` | ❌ | |
| Nested functions | ❌ | |

## Numerical functions

| Feature | Status | Notes |
| --- | --- | --- |
| Elementary math (sin, cos, exp, log, sqrt, abs, …) | ✅ | |
| `round` (half away from zero) | ✅ | |
| `zeros ones eye rand randn linspace logspace rng` | ✅ | |
| `reshape repmat diag meshgrid peaks` | ✅ | |
| Reductions `sum prod mean min max cumsum cumprod sort` | ✅ | first non-singleton dimension |
| `any all` | ✅ | logical reduction along first non-singleton dimension |
| `size length numel ndims isequal` | ✅ | |
| Type predicates `isnumeric ischar isempty isscalar isvector ismatrix isrow iscolumn isreal isfloat islogical isnan isinf isfinite` | ✅ | |
| String helpers `lower upper strcmp strcmpi strcat strjoin strsplit num2str` | ✅ | |
| Linear algebra `det inv rank trace norm cond eig svd lu qr chol pinv polyfit` | ✅ | |
| `\` `/` (solve; singular → least squares) | ✅ | |
| `eig`/`eigvals` (sorted ascending, real when applicable) | ✅ | |
| `integral fzero roots ode45` | ✅ | SciPy-backed |
| Complex arithmetic | ✅ | |
| Division by zero (`1/0`, `0/0`) | ✅ | Inf / NaN like MATLAB |

## Graphics

| Feature | Status | Notes |
| --- | --- | --- |
| `figure subplot plot scatter bar histogram stem stairs` | ✅ | |
| `semilogx semilogy loglog errorbar fill` | ✅ | |
| `imagesc image colorbar contour contourf mesh surf view zlabel` | ✅ | |
| `title xlabel ylabel legend grid hold xlim ylim zlim axis` | ✅ | |
| `saveas exportgraphics` (PNG) | ✅ | |

## I/O and environment

| Feature | Status | Notes |
| --- | --- | --- |
| `disp fprintf sprintf clc clear` | ✅ | `fprintf` cycles the format string |
| `who whos help exit quit` (REPL) | ✅ | |
| `load save fopen fread fwrite` | ❌ | |

## Error and diagnostic behavior

| Feature | Status | Notes |
| --- | --- | --- |
| Source-aware errors (file/line + excerpt) | ✅ | |
| Error categories (index/dimension/undefined/…) | ✅ | |
| Char arithmetic (`'a' + 1`) | 🔸 | MATLAB does ASCII arithmetic; MALT rejects |
| Singular `\` solve | ✅ | least-squares fallback, no crash |

## Intentionally different (summary)

1. **Case-sensitivity** — MATLAB identifiers/functions are case-insensitive;
   MALT is case-sensitive.
2. **One numeric type** — double/complex only; no integer/single classes.
3. **No array auto-growth** on out-of-range indexed assignment.
4. **Presentation policy** — unsuppressed statements display the value only
   (no `name =` echo).
5. **Augmented assignment** (`+=`, …) is a MALT extension.
6. **Char arithmetic** (`'a' + 1`) is not implemented.
7. **Display formatting** is column-aligned but not byte-identical to MATLAB's
   `disp`; `fprintf` is used for canonical output in tests.
8. **RNG sequences** reproduce within MALT but are not bit-identical to
   MathWorks MATLAB.
