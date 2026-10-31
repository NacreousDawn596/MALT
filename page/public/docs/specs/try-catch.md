# try/catch — specification

Status: **implemented** (see `tests/compatibility/test_try_catch.py`).

## Syntax

```
try
    statements…
catch
    statements…
end
```

or, capturing the error:

```
try
    statements…
catch err
    statements…
end
```

`catch` may appear at most once, immediately after the `try` block.

## Semantics

1. The `try` block executes normally.
2. If any statement in the `try` block raises an error, execution transfers
   immediately to the `catch` block. The error is considered **handled**: it is
   not propagated to the caller, the REPL is not torn down, and the remaining
   `try` statements are skipped.
3. If no error occurs, the `catch` block is skipped entirely.
4. `catch err` binds `err` to an error value in the enclosing workspace scope.
   The `catch` variable persists after the block (like any assignment).
5. A `catch` without a variable catches and discards the error.

## The error value

`err` is an error object with two fields:

| field | meaning | example |
| --- | --- | --- |
| `err.message` | human-readable message | `"index 10 is outside the valid range 1..4"` |
| `err.identifier` | stable category | `"index exceeds array dimensions"` |

These are the categories from `docs/semantics.md` §7 (`IndexError_`,
`DimensionError`, `UndefinedVariableError`, `RuntimeError_`, …). The exact
message text is not part of the compatibility contract; the category
(`identifier`) and the fact that an error was caught are.

## Scope rules

- The `catch` block runs in the same workspace scope as the `try` block (there
  is no new scope for `try/catch`).
- Variables assigned in the `try` block **before** the error remain in the
  workspace; variables assigned after the error are not.
- A `return`/`break`/`continue` inside `try` or `catch` behaves as in any other
  block (a `break`/`continue` must be inside an enclosing loop).

## Error mapping

Because MALT compiles to Python, the generated `try/except` catches the
underlying Python exception and normalizes it to the error value described
above. A raw Python traceback is never exposed; the error's `message` is the
MALT diagnostic text and its `identifier` is the MALT category.

## Differences from MATLAB

- MATLAB's `err` is a full `MException` object with `.stack`, `.cause`, `rethrow`,
  etc. MALT's `err` exposes only `.message` and `.identifier`.
- MATLAB supports `catch err` with `err` usable for `rethrow(err)`; `rethrow` is
  not implemented.

## Tests

`tests/compatibility/test_try_catch.py` covers: catching a runtime error,
skip-on-success, `catch err` binding + field access, workspace persistence
before the error, propagation when `try` succeeds, and `break` inside `catch`.
