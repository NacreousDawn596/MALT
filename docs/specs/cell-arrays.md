# Cell arrays — specification (future)

Status: **planned** (not yet implemented). Written before implementation, per
the project's compatibility policy.

## Syntax

Cell arrays use curly braces:

```
c = {1, 'text', [1 2; 3 4]};
```

- `{...}` builds a cell array (heterogeneous elements).
- `c{1}` accesses element 1 (the *content*, not a wrapped cell).
- `c(1)` accesses a 1×1 cell array (a *slice*).
- `c{1} = value` assigns the content of cell 1.
- `c(1) = {value}` assigns a cell slice.

## Semantics (to implement)

1. A cell array is a container of arbitrary values, each wrapped in a cell.
2. `c{idx}` unwraps the content (like MATLAB `c{idx}`); `c(idx)` returns a cell
   array (like MATLAB `c(idx)`).
3. Indexing is one-based, column-major, with `end` and colon support, exactly
   as for numeric arrays (see `docs/semantics.md` §5).
4. `size`, `numel`, `ndims`, `length` report the cell array's dimensions.
5. `iscell(x)` is true for cell arrays, false otherwise.
6. `{}` builds an empty cell array.

## Representation

A cell array is a NumPy `ndarray` of `object` dtype (one Python object per
cell). Numeric arrays remain `float64`/`complex128`; cell arrays are the only
`object`-dtype arrays.

## Differences from MATLAB

- No `cellfun`, `arrayfun`, or comma-separated list expansion (`c{:}`) in the
  initial milestone.

## Tests (to write)

- Construction and `size`/`numel`.
- `c{idx}` content access vs `c(idx)` slice access.
- `c{idx} = value` and `c(idx) = {value}` assignment.
- Mixed-type content (numbers, strings, nested cells).
- `iscell` and empty `{}`.
