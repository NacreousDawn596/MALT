# Cell arrays — specification

Status: **implemented** (subset; see limitations below).

## Syntax

Cell arrays use curly braces:

```
c = {1, 'text', [1 2; 3 4]};
```

- `{...}` builds a cell array (heterogeneous elements).
- `c{1}` accesses element 1 (the *content*, not a wrapped cell).
- `c{idx} = value` assigns the content of cell `idx`.
- `iscell(x)` is true for cell arrays, false otherwise.
- `{}` builds a 0×0 empty cell array.

## Semantics

1. A cell array is a container of arbitrary values, each stored in one cell.
2. `c{idx}` unwraps the content. A single index is linear (column-major);
   `c{i, j}` is a 2-D subscript.
3. Indexing is one-based, column-major, with `end` support, exactly as for
   numeric arrays (see `docs/semantics.md` §5).
4. `size`, `numel`, `ndims`, `length` report the cell array's dimensions.
5. `iscell(x)` is true for cell arrays, false otherwise.

## Representation

A cell array is a `malt.runtime.cells.Cell` wrapping a NumPy `ndarray` of
`object` dtype (one Python object per cell). The `Cell` type also exposes
`.shape`, `.size`, and `.ndim` so the existing `size`/`numel`/`ndims`/`length`
functions work transparently.

## Differences from MATLAB (current limitations)

- `c(idx)` (parenthesized *slice* access returning a sub-cell) is **not**
  implemented; only `c{idx}` content access/assignment is supported.
- `c(idx) = {value}` cell-slice assignment is not implemented.
- No `cellfun`, `arrayfun`, or comma-separated list expansion (`c{:}`).
- Colon content access/assignment (`c{:}`) is not supported.
- `cell(n)` / `cell(m, n)` constructors are not yet provided; use `{...}`.

## Tests

- `tests/compatibility/test_cell_struct.py`: literal construction, linear and
  subscript content access, `end`, assignment, mixed-type content, `iscell`,
  and error cases.
