"""JIT semantic-equivalence stress tests (optimization level 2).

Level 0 (1x1-array scalars, no fast paths) is treated as the reference
implementation. Every test runs the same MATLAB source at levels 0, 1 and 2 and
asserts the results are equivalent — not merely that the final accumulator
matches, but that loop-variable persistence, scope, exception behaviour, and
colon iteration are preserved.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from malt.compiler import compile_source
from malt.errors import MaltError
from malt.executor import execute
from malt.runtime.arrays import colon, jit_for


def _run(src: str, lvl: int) -> dict:
    return execute(compile_source(src, "t.m", optimization_level=lvl))


def _vals(ns):
    return {
        k: (np.asarray(v) if not isinstance(v, (str, complex)) else v)
        for k, v in ns.items()
        if not k.startswith("_") and not callable(v)
        and k not in {"pi", "eps", "Inf", "NaN", "true", "false", "i", "j"}
    }


def _assert_equiv(src: str, atol: float = 1e-12):
    namespaces = [_run(src, lvl) for lvl in (0, 1, 2)]
    ref = _vals(namespaces[0])
    for ns in namespaces[1:]:
        v = _vals(ns)
        assert set(ref) == set(v), (set(ref), set(v))
        for name in ref:
            a, b = ref[name], v[name]
            if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
                np.testing.assert_allclose(
                    np.asarray(a, dtype=complex), np.asarray(b, dtype=complex), atol=atol
                )
            else:
                assert a == b or abs(a - b) < atol


# ---------------------------------------------------------------------------
# Accumulator initialization
# ---------------------------------------------------------------------------


def test_init_scalar_literal():
    _assert_equiv("total = 0;\nfor k = 1:5\n total = total + k;\nend\n")


def test_init_expression():
    _assert_equiv("total = 2 * 3;\nfor k = 1:5\n total = total + k;\nend\n")


def test_init_from_function_result():
    # det() returns a 1x1 array, so the accumulator starts as a matrix scalar.
    _assert_equiv("total = det([2 0; 0 3]);\nfor k = 1:5\n total = total + k;\nend\n")


def test_init_negative():
    _assert_equiv("total = -10;\nfor k = 1:5\n total = total + k;\nend\n")


def test_init_complex_literal():
    _assert_equiv("z = 1 + 1i;\nfor k = 1:3\n z = z + k * 1i;\nend\n")


# ---------------------------------------------------------------------------
# Integer vs floating-point iteration values
# ---------------------------------------------------------------------------


def test_integer_range():
    _assert_equiv("total = 0;\nfor k = 1:10\n total = total + k;\nend\n")


def test_float_literal_init_integer_range():
    _assert_equiv("total = 0.0;\nfor k = 1:10\n total = total + k;\nend\n")


def test_variable_endpoint():
    _assert_equiv("n = 10;\ntotal = 0;\nfor k = 1:n\n total = total + k;\nend\n")


def test_non_integer_step_falls_back():
    _assert_equiv("total = 0;\nfor k = 0:0.5:2\n total = total + k;\nend\n")


def test_float_endpoint_integer_step():
    # end=10.0 (float but integer-valued): JIT range path must match colon.
    _assert_equiv("total = 0;\nfor k = 1:10.0\n total = total + k;\nend\n")


def test_multiplication_accumulator():
    _assert_equiv("p = 1;\nfor k = 1:6\n p = p * k;\nend\n")


def test_elementwise_power_accumulator():
    _assert_equiv("s = 0;\nfor k = 1:4\n s = s + k .^ 2;\nend\n")


# ---------------------------------------------------------------------------
# Complex numbers
# ---------------------------------------------------------------------------


def test_complex_accumulation():
    _assert_equiv("z = 0;\nfor k = 1:3\n z = z + k * 1i;\nend\n")


def test_complex_multiplication():
    _assert_equiv("z = 1;\nfor k = 1:3\n z = z * (1 + 1i);\nend\n")


# ---------------------------------------------------------------------------
# Overflow / large values
# ---------------------------------------------------------------------------


def test_large_finite_accumulation_stays_double():
    ns2 = _run("total = 0;\nfor k = 1:100000\n total = total + k;\nend\n", 2)
    assert ns2["total"] == 5000050000.0
    assert not isinstance(ns2["total"], int)


def test_large_accumulation_all_levels():
    _assert_equiv("total = 0;\nfor k = 1:20000\n total = total + k;\nend\n")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


def test_body_exception_propagates_all_levels():
    # Accumulating into a string raises a runtime error on every level.
    for lvl in (0, 1, 2):
        with pytest.raises(MaltError):
            _run("total = 'abc';\nfor k = 1:3\n total = total + k;\nend\n", lvl)


def test_body_exception_has_source_location():
    from malt.diagnostics import render_error

    src = "total = 0;\nfor k = 1:3\n total = total + (1 / (k - 2));\nend\n"
    unit = compile_source(src, "err.m", optimization_level=2)
    try:
        execute(unit)
    except MaltError as e:
        rendered = render_error(e, source=src)
        assert "err.m" in rendered
    else:
        raise AssertionError("expected a runtime error")


# ---------------------------------------------------------------------------
# Variable scope and side effects
# ---------------------------------------------------------------------------


def test_accumulator_and_loopvar_persist():
    src = "a = 10;\ntotal = 0;\nfor k = 1:5\n total = total + k;\nend\nresult = a + total;\nlast = k;\n"
    for lvl in (0, 1, 2):
        ns = _run(src, lvl)
        assert float(np.asarray(ns["a"]).reshape(-1)[0]) == 10
        assert float(np.asarray(ns["result"]).reshape(-1)[0]) == 25
        assert float(np.asarray(ns["last"]).reshape(-1)[0]) == 5


def test_loop_variable_type_matches_level_1():
    # After the JIT loop, the loop variable is a native scalar like level 1.
    ns1 = _run("total = 0;\nfor k = 1:5\n total = total + k;\nend\n", 1)
    ns2 = _run("total = 0;\nfor k = 1:5\n total = total + k;\nend\n", 2)
    assert type(ns2["k"]) is type(ns1["k"])


def test_unrelated_variable_unaffected():
    _assert_equiv("x = 42;\ntotal = 0;\nfor k = 1:5\n total = total + k;\nend\n")


def test_body_with_function_call_not_jitted():
    # sin(k) is a function call -> not eligible for JIT, but must still work.
    _assert_equiv("total = 0;\nfor k = 1:10\n total = total + sin(k);\nend\n")


def test_multi_statement_body_not_jitted():
    _assert_equiv(
        "total = 0;\nfor k = 1:5\n total = total + k;\n t = k * 2;\nend\n"
    )


# ---------------------------------------------------------------------------
# Loop-variable persistence and empty ranges
# ---------------------------------------------------------------------------


def test_loop_variable_after_loop():
    _assert_equiv("total = 0;\nfor k = 1:7\n total = total + k;\nend\ny = k;\n")


def test_empty_range_accumulator_unchanged():
    _assert_equiv("total = 5;\nfor k = 1:0\n total = total + k;\nend\n")


def test_descending_empty_range():
    _assert_equiv("total = 5;\nfor k = 10:1\n total = total + k;\nend\n")


# ---------------------------------------------------------------------------
# Exact colon semantics — boundary cases
# ---------------------------------------------------------------------------


_COLON_CASES = [
    (1, 10),
    (1, 2, 10),
    (10, -1, 1),
    (10, -2, 1),
    (1, 1),
    (5, 5),
    (1, 0),
    (10, 1),
    (10, -1, 20),
    (0, 2, 5),
    (1, 2),
    (3, 3, 3),
    (2, 5),
]


@pytest.mark.parametrize("args", _COLON_CASES)
def test_jit_iteration_matches_colon(args):
    # Sum the range via the JIT and compare to the actual colon sequence.
    if len(args) == 2:
        start, end = args
        src_step = "1"
    else:
        start, step, end = args
        src_step = repr(step)

    src = (
        f"total = 0;\nfor k = {start}:{src_step}:{end}\n total = total + k;\nend\n"
    )
    ns2 = _run(src, 2)
    got = float(np.asarray(ns2["total"]))

    if len(args) == 2:
        expected = colon(start, end).sum()
    else:
        expected = colon(start, step, end).sum()
    assert got == expected


@given(
    st.integers(min_value=-50, max_value=50),
    st.integers(min_value=-10, max_value=10).filter(lambda x: x != 0),
    st.integers(min_value=-50, max_value=50),
)
@settings(max_examples=200, deadline=None)
def test_jit_range_matches_colon_property(start, step, end):
    # The JIT's range()-based iteration must match the colon sequence exactly
    # for arbitrary integer-valued (start, step, end) triples.
    def body(acc, k):
        return acc + k

    # Use the integer fast path directly (start/step/end are Python ints).
    acc, _ = jit_for(0, start, step, end, body)
    expected = float(colon(start, step, end).sum())
    assert acc == expected
