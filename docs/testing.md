# Testing

## Running the suite

```bash
nix develop -c pytest
```

or, within the dev shell, just `pytest`.

## What is tested

- `tests/unit/` — lexer, parser, codegen, fuzzing.
- `tests/integration/` — CLI (`eval`, `run`, `compile`, `--version`, errors).
- `tests/compatibility/` — the 17 required `.m` fixtures plus Hypothesis
  property tests (arithmetic, transposes, reshape, matmul, seeded RNG, well
  conditioned solves, valid generated Python).
- `tests/graphics/` — 9 graphical fixtures, inspected via real Matplotlib
  artists (line counts/data, titles, labels, legends, grids, collections,
  images, 3D surfaces, saved PNG bytes, figure lifecycle).
- `tests/errors/` — syntax/undefined/index/dimension errors and diagnostics.
- `tests/security/` — restricted builtins, no `import`/`eval`/`exec` in
  generated code, keyword-identifier rejection, undefined-variable handling.

## Design principles

- Every compatibility fixture is stored as an actual `.m` file and executed
  through the real compiler/runtime — never a hand-written Python equivalent.
- Output testing is separated from value testing: numeric arrays, shapes, and
  complex components are asserted directly; stdout is checked separately and
  with normalized whitespace where formatting may vary.
- Numerical assertions use explicit tolerances (`np.testing.assert_allclose`).
- Graphics are tested headlessly with the `Agg` backend; no display is required.
- No test result is fabricated; unsupported features raise controlled errors.

## Linting and type checking

```bash
nix develop -c ruff check src/malt tests
nix develop -c mypy src/malt
```

## Fuzzing

`tests/unit/test_fuzz.py` feeds the parser hundreds of deterministic random
inputs and asserts it never hangs and never raises a non-`MaltError` exception.
`tests/unit/test_fuzz.py::test_fuzz_bounded_runs_quickly` guards runtime.

## Headless vs. interactive graphics

Automated tests always use the headless `Agg` backend. Interactive desktop
window tests are a separate, optional concern (see `docs/nixos.md`); they are
not part of the default suite and require `MPLBACKEND=Qt5Agg` and a display.
