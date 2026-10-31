# Structs — specification

Status: **implemented** (subset; see limitations below).

## Syntax

MATLAB structs are built with the `struct` function (not with a literal):

```
s = struct('name', 'value', 'field2', value2);
```

Field access uses dot notation:

```
s.name
s.field2
s.name = 'new value';
```

## Semantics

1. `struct('f1', v1, 'f2', v2, …)` builds a 1×1 struct with the given fields.
   Field names are string keys; values are arbitrary.
2. `s.field` reads a field; `s.field = value` writes/creates a field.
3. `fieldnames(s)` returns a cell array (row) of field names.
4. `isfield(s, 'name')` is true if the field exists.
5. `isstruct(x)` is true for structs, false otherwise.
6. Reading a missing field raises a runtime error.

## Representation

A struct is a `malt.runtime.cells.Struct` object holding a dict of field →
value. `FieldAccess` (already in the AST for `try/catch` error values) is
generalized: `codegen` emits `_ml.getfield` for reads and `_ml.setfield` for
assignments, both dispatching on `Struct` (and `MaltCatchError` for the error
case).

## Differences from MATLAB (current limitations)

- Struct arrays (non-scalar structs, e.g. `struct('f', {v1, v2})`) are deferred.
- `struct([])` empty-struct construction is not implemented.
- `rmfield`, `orderfields`, and `fieldnames` on non-struct values are deferred
  (`fieldnames` currently raises for non-structs).
- `getfield`/`setfield` as *functions* exist but nested dynamic-field paths
  (`getfield(s, 'a', 'b')`) are not supported.

## Tests

- `tests/compatibility/test_cell_struct.py`: construction, field read/write,
  `fieldnames`, `isfield`, `isstruct`, missing-field errors, and nested
  numeric/string fields.
