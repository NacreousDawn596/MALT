# Language support

This documents the **targeted** MATLAB subset that MALT implements and tests.
MALT does **not** claim full MATLAB compatibility.

Legend: ✅ implemented and tested · ⚠️ implemented with limitations · ➖ planned ·
❌ unsupported.

## Lexical syntax

| Feature | Status | Notes |
| --- | --- | --- |
| Integers | ✅ | |
| Floating point / scientific notation | ✅ | `1e5`, `2.5e-3`, `.5` |
| Imaginary literals | ✅ | `4i`, `3.5j`, `3+4i` |
| Single-quoted strings | ✅ | `''` escapes a quote |
| Identifiers | ✅ | start with a letter, then letters/digits/`_` |
| Comments | ✅ | `%` to end of line |
| Block comments | ❌ | not part of the target |

## Operators

| Operator | Meaning | Status |
| --- | --- | --- |
| `+ - * / \ ^` | arithmetic / matrix ops | ✅ |
| `.* ./ .\ .^` | element-wise ops | ✅ |
| `' .'` | conjugate / non-conjugating transpose | ✅ |
| `== ~= < <= > >=` | comparisons | ✅ |
| `& \|` | element-wise logical | ✅ |
| `&& \|\|` | short-circuit logical (scalar) | ✅ |
| `~` | logical not | ✅ |
| `:` | colon / range | ✅ |
| `=` | assignment | ✅ |
| `+= -= *= .*= /= ./= \= .\= ^= .^=` | augmented assignment | ✅ extension |

## Data model

| Feature | Status | Notes |
| --- | --- | --- |
| Scalars (1x1), row/column vectors, matrices | ✅ | always ≥2-D NumPy |
| Higher-dimensional arrays | ⚠️ | constructible, limited indexing |
| Logical arrays | ✅ | |
| Complex arrays | ✅ | |
| Empty arrays | ⚠️ | produced by empty colon, limited support |
| Cell arrays `{}` | ⚠️ | literals, `c{idx}` content access/assign, `iscell`; no `c(idx)` slices, `c{:}`, or `cell(n)` |
| Structs | ⚠️ | `struct`, dot read/write, `fieldnames`/`isfield`/`isstruct`; no struct arrays |

## Indexing

| Form | Status |
| --- | --- |
| `A(i)`, `A(i,j)`, `A(i,j,k)` | ✅ |
| `A(:)`, `A(:,j)`, `A(i,:)` | ✅ |
| `A(end)`, `A(1:2:end)`, `A(end,:)` | ✅ |
| `A([1 3 5])` | ✅ |
| `A(A > 3)` logical indexing | ✅ |
| Indexed assignment `A(i,j) = v` | ✅ |
| Two-vector subscript submatrix | ✅ |

## Control flow

`if`/`elseif`/`else`/`end`, `for`, `while`, `break`, `continue`, `return`,
`switch`/`case`/`otherwise`, `try`/`catch` — ✅.
`parfor` — ❌.

## Functions

| Feature | Status |
| --- | --- |
| `function [a, b] = f(x, y)` (multi-output) | ✅ |
| `function y = f(x)` (single output) | ✅ |
| Local scope | ✅ |
| Function handles `@name` | ✅ |
| Anonymous functions `@(x) x.^2` | ✅ |
| `feval`, `func2str`, `str2func` | ✅ |
| `nargin`/`nargout`, `varargin`/`varargout` | ❌ |
| Nested functions | ❌ |
| Script local functions | ✅ |

## Numerical functions

Elementary: `sin cos tan asin acos atan atan2 sinh cosh tanh exp log log10 log2
sqrt abs real imag conj angle floor ceil round fix sign rem mod` — ✅.

Construction: `zeros ones eye rand randn linspace logspace reshape repmat diag
meshgrid peaks flipud fliplr rng` — ✅.

Reductions: `sum prod mean min max cumsum cumprod sort size length numel ndims
isequal any all` — ✅.

Type predicates: `isnumeric ischar isempty isscalar isvector ismatrix isrow
iscolumn isreal isfloat islogical isnan isinf isfinite iscell isstruct` — ✅.

String helpers: `lower upper strcmp strcmpi strcat strjoin strsplit num2str` — ✅.

Linear algebra: `det inv rank trace norm cond eig svd mldivide (\ ) mrdivide (/)
pinv chol lu qr polyfit` — ✅ (eig/svd/lu/qr support output-count semantics).

Calculus/ODE: `integral fzero roots ode45` — ✅ (`ode45` is SciPy's RK45 /
Dormand–Prince).

## Graphics

Phase 1: `plot figure subplot title xlabel ylabel legend grid hold xlim ylim
axis` — ✅.
Phase 2: `scatter bar histogram stem stairs semilogy semilogx loglog errorbar
fill` — ✅.
Phase 3: `imagesc image colorbar contour contourf mesh surf view zlabel` — ✅.

Saving: `saveas exportgraphics` — ✅ (PNG validated in tests).

## I/O and REPL

`disp fprintf sprintf clc clear` — ✅. `who whos help exit quit` in the REPL — ✅.
`load save fread fwrite fopen fclose` — ❌.

The REPL also provides readline history (persisted), tab-completion, and
multi-line block input. A Qt6 GUI REPL is available via `malt gui`.
A source-level debugger (`malt debug`) and an LSP server (`malt lsp`) are
documented in `docs/api.md` and `docs/editor-integration.md`.

## Presentation policy

An unsuppressed assignment or expression in a **script** displays the value
only (no `name =` prefix); in the **REPL** the same convention applies.
This is a deliberate, documented deviation from MATLAB's `x = …` echo and is
covered by compatibility test 14.

## Known limitations

- Cell arrays support `{...}` literals and `c{idx}` content access/assignment
  but not parenthesized *slice* access (`c(idx)`), colon content (`c{:}`), or
  the `cell(n)` constructor. Structs support scalar structs and dot access but
  not struct arrays. See `docs/specs/cell-arrays.md` and `docs/specs/structs.md`.
- The execution namespace is not a security sandbox; see the architecture doc.
- Matrix literals with spaced binary `+` between elements are interpreted as
  unary signs (`[1 +2]` works; `[1 + 2]` is not `[3]`).
- Scalar loop bodies and per-element indexed assignment remain far slower than
  NumPy-vectorized equivalents (a MATLAB-style loop is not a vectorized
  expression); see `benchmarks/` for measured numbers.
