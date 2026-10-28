"""JIT-specialized loop correctness (optimization level 2)."""

from __future__ import annotations

from conftest import scalar

from malt.compiler import compile_source
from malt.executor import execute


def _run(src: str, level: int = 2):
    return execute(compile_source(src, "j.m", optimization_level=level))


def test_jit_scalar_accumulation():
    ns = _run("n = 100;\ntotal = 0;\nfor k = 1:n\n total = total + k;\nend\n")
    assert scalar(ns, "total") == 5050


def test_jit_matches_all_levels():
    src = "n = 1000;\ns = 0;\nfor k = 1:n\n s = s + k * k;\nend\n"
    results = []
    for lvl in (0, 1, 2):
        ns = _run(src, lvl)
        results.append(scalar(ns, "s"))
    assert results[0] == results[1] == results[2]


def test_jit_loop_variable_persists():
    # MATLAB leaves the loop variable set to its last value.
    ns = _run("for k = 1:5\nend\ny = k;\n")
    assert scalar(ns, "y") == 5


def test_jit_negative_step():
    ns = _run("s = 0;\nfor k = 10:-1:1\n s = s + k;\nend\n")
    assert scalar(ns, "s") == 55


def test_jit_step_value():
    ns = _run("s = 0;\nfor k = 1:2:10\n s = s + k;\nend\n")
    assert scalar(ns, "s") == 1 + 3 + 5 + 7 + 9


def test_jit_float_range_falls_back_to_colon():
    # Non-integer step is not JIT-specialized but must still be correct.
    ns = _run("s = 0;\nfor k = 0:0.5:2\n s = s + k;\nend\n")
    assert abs(scalar(ns, "s") - (0 + 0.5 + 1.0 + 1.5 + 2.0)) < 1e-12


def test_jit_empty_range():
    ns = _run("s = 0;\nfor k = 1:0\n s = s + k;\nend\n")
    assert scalar(ns, "s") == 0


def test_jit_multiplication():
    ns = _run("p = 1;\nfor k = 1:5\n p = p * k;\nend\n")
    assert scalar(ns, "p") == 120


def test_jit_does_not_specialize_complex_body():
    # A body that is not a simple accumulation must still run correctly.
    ns = _run("s = 0;\nfor k = 1:10\n s = s + k;\n t = k * 2;\nend\n")
    assert scalar(ns, "s") == 55


def test_jit_nested_across_levels():
    src = "n = 50;\ns = 0;\nfor i = 1:n\n for j = 1:n\n  s = s + i*j;\n end\nend\n"
    vals = [scalar(_run(src, lvl), "s") for lvl in (0, 1, 2)]
    assert vals[0] == vals[1] == vals[2]


def test_jit_multi_accumulator():
    ns = _run("s = 0;\np = 1;\nfor k = 1:5\n s = s + k;\n p = p * k;\nend\n")
    assert scalar(ns, "s") == 15
    assert scalar(ns, "p") == 120


def test_jit_multi_accumulator_matches_levels():
    src = "s = 0;\np = 1;\nt = 0;\nfor k = 1:6\n s = s + k;\n p = p * k;\n t = t + k*k;\nend\n"
    results = {}
    for lvl in (0, 1, 2):
        ns = _run(src, lvl)
        results[lvl] = (scalar(ns, "s"), scalar(ns, "p"), scalar(ns, "t"))
    assert results[0] == results[1] == results[2]


def test_jit_rejects_accumulator_reference_in_rhs():
    # s = s * s would be matmul-vs-elementwise unsafe; must not be JIT'd,
    # but must still produce the correct result via the general path.
    ns = _run("s = 2;\nfor k = 1:3\n s = s * s;\nend\n")
    assert scalar(ns, "s") == 2 ** (2**3)  # 2 -> 4 -> 16 -> 256
