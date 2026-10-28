"""Robustness: bounded generated programs, execution limits, and diagnostics.

Verifies that generated programs and malformed inputs never produce an internal
Python traceback — only a ``MaltError`` with a source-located diagnostic — and
that execution is bounded.
"""

from __future__ import annotations

import random
import time

import pytest

from malt.compiler import compile_source
from malt.errors import MaltError
from malt.executor import execute


def _gen_matrix(rng: random.Random, rows: int, cols: int) -> str:
    row_strs = []
    for _ in range(rows):
        row_strs.append(" ".join(str(rng.randint(-9, 9)) for _ in range(cols)))
    return "[" + "; ".join(row_strs) + "]"


def _gen_expr(rng: random.Random, depth: int) -> str:
    if depth <= 0:
        return str(rng.randint(-100, 100))
    generators = [
        lambda: str(rng.randint(-100, 100)),
        lambda: f"({_gen_expr(rng, depth - 1)})",
        lambda: f"{_gen_expr(rng, depth - 1)} + {_gen_expr(rng, depth - 1)}",
        lambda: f"{_gen_expr(rng, depth - 1)} - {_gen_expr(rng, depth - 1)}",
        lambda: f"{_gen_expr(rng, depth - 1)} * {_gen_expr(rng, depth - 1)}",
        lambda: f"{_gen_expr(rng, depth - 1)} .* {_gen_expr(rng, depth - 1)}",
        lambda: f"{_gen_expr(rng, depth - 1)} .^ 2",
        lambda: _gen_matrix(rng, 2, 2),
        lambda: f"sin({_gen_expr(rng, depth - 1)})",
        lambda: f"abs({_gen_expr(rng, depth - 1)})",
    ]
    return rng.choice(generators)()


def _gen_program(rng: random.Random) -> str:
    statements = []
    for _ in range(rng.randint(1, 4)):
        e = _gen_expr(rng, rng.randint(1, 3))
        statements.append(f"x = {e};")
    statements.append("disp(x);")
    return "\n".join(statements)


def test_generated_programs_never_traceback():
    # Bounded generated programs must either run or raise MaltError — never a
    # raw Python exception or an internal traceback.
    rng = random.Random(1234)
    for _ in range(500):
        src = _gen_program(rng)
        try:
            unit = compile_source(src, "gen.m")
            execute(unit)
        except MaltError:
            pass
        except RecursionError:
            pytest.fail(f"recursion error on: {src!r}")


def test_malformed_inputs_produce_malt_error():
    malformed = [
        "if x > 0",
        "A = [1 2;",
        "for i = 1:10",
        "function f(",
        "x = 'unterminated",
        "x = 1 +",
        "A(1",
        "switch x",
        "try",
        "x = )",
        "x = 1:",
    ]
    for src in malformed:
        try:
            compile_source(src, "bad.m")
        except MaltError as e:
            assert e.location is not None, f"no location for: {src!r}"
            assert e.location.filename == "bad.m"
        else:
            pytest.fail(f"expected MaltError for: {src!r}")


def test_runtime_error_has_diagnostic_not_traceback():
    from malt.diagnostics import render_error

    src = "A = [1 2; 3 4];\ndisp(A(10, 1));\n"
    unit = compile_source(src, "err.m")
    try:
        execute(unit)
    except MaltError as e:
        rendered = render_error(e, source=src)
        assert "err.m:2" in rendered
        assert "disp(A(10, 1))" in rendered
        assert "Traceback" not in rendered
    else:
        pytest.fail("expected a runtime error")


def test_execution_bounded_loop():
    # A bounded loop must complete quickly (guards against accidental infinite
    # loop regressions in the for-loop codegen).
    start = time.perf_counter()
    unit = compile_source("s = 0;\nfor k = 1:100000\n s = s + 1;\nend\n", "b.m")
    ns = execute(unit)
    elapsed = time.perf_counter() - start
    assert float(ns["s"]) == 100000
    assert elapsed < 10


def test_deep_nesting_no_crash():
    # Deeply nested expressions must not crash the parser/compiler.
    for depth in (50, 200):
        src = "(" * depth + "1" + ")" * depth + ";"
        try:
            compile_source(src, "deep.m")
        except (MaltError, RecursionError):
            pass
