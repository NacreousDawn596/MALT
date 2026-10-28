# Structs — specification (future)

Status: **planned** (not yet implemented). Written before implementation, per
the project's compatibility policy.

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

## Semantics (to implement)

1. `struct('f1', v1, 'f2', v2, …)` builds a 1×1 struct with the given fields.
   Field names are string keys; values are arbitrary.
2. `struct([])` builds an empty struct with no fields.
3. `s.field` reads a field; `s.field = value` writes/creates a field.
4. `fieldnames(s)` returns a cell array of field names.
5. `isfield(s, 'name')` is true if the field exists.
6. Struct arrays (1×N) are built with `struct('f', {v1, v2, …})` — deferred to a
   later milestone.

## Representation

A struct is a Python object (an `object`-dtype 1×1 array, or a dedicated
`Struct` type) holding a dict of field → value. `FieldAccess` (already in the
AST for `try/catch` error values) is generalized to read/write these fields.

## Differences from MATLAB

- Struct arrays (non-scalar structs) are deferred.
- `rmfield`, `orderfields`, `setfield`, `getfield` are deferred.

## Tests (to write)

- Construction, field read/write, `fieldnames`, `isfield`.
- Field access on non-struct values raises a runtime error.
- Nested structs.
