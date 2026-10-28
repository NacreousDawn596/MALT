"""Property-based tests using Hypothesis."""

from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from malt.compiler import compile_source
from malt.executor import execute


@settings(max_examples=100, deadline=None)
@given(
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=-1000, max_value=1000),
)
def test_scalar_arithmetic_matches_reference(a, b):
    unit = compile_source(f"r = {a} + {b} * 2;", "p.m")
    ns = execute(unit)
    assert float(np.asarray(ns["r"])) == a + b * 2


@settings(max_examples=50, deadline=None)
@given(
    st.integers(min_value=1, max_value=8),
    st.integers(min_value=1, max_value=8),
    st.integers(min_value=1, max_value=8),
)
def test_transpose_twice_restores_matrix(m, n, p):
    if m * n * p > 64:
        return
    vals = " ".join(str(i) for i in range(1, m * n + 1))
    src = f"A = reshape([{vals}], {m}, {n});\nB = A'';\n"
    unit = compile_source(src, "p.m")
    ns = execute(unit)
    np.testing.assert_array_equal(ns["B"], ns["A"])


@settings(max_examples=50, deadline=None)
@given(
    st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=20)
)
def test_reshape_preserves_order(vals):
    total = len(vals)
    src = " ".join(str(v) for v in vals)
    unit = compile_source(
        f"A = reshape([{src}], 1, {total});\n"
        f"B = reshape(A, {total}, 1);\n"
        f"C = reshape(B, 1, {total});\n",
        "p.m",
    )
    ns = execute(unit)
    np.testing.assert_array_equal(
        ns["C"].reshape(1, -1), np.array(vals, dtype=float).reshape(1, -1)
    )


@settings(max_examples=30, deadline=None)
@given(
    st.lists(
        st.lists(st.integers(min_value=0, max_value=9), min_size=2, max_size=2),
        min_size=2,
        max_size=2,
    )
)
def test_matrix_multiplication_dimensions(rows):
    a = np.array(rows, dtype=float)
    src = (
        f"A = [{rows[0][0]} {rows[0][1]}; {rows[1][0]} {rows[1][1]}];\n"
        f"B = A * eye(2);\n"
    )
    unit = compile_source(src, "p.m")
    ns = execute(unit)
    np.testing.assert_allclose(ns["B"], a, atol=1e-12)


@settings(max_examples=50, deadline=None)
@given(st.integers(min_value=1, max_value=100))
def test_seeded_random_deterministic(seed):
    unit = compile_source(
        f"rng({seed});\nA = rand(3, 3);\nrng({seed});\nB = rand(3, 3);\n",
        "p.m",
    )
    ns = execute(unit)
    np.testing.assert_array_equal(ns["A"], ns["B"])


@settings(max_examples=200, deadline=None)
@given(st.integers(min_value=1, max_value=500))
def test_compiled_expressions_are_valid_python(n):
    # A wide range of expressions must always produce compilable Python.
    src = f"x = {n} + {n} * 2 - {n} / 3 + ({n} ^ 2) .^ 2;\n"
    unit = compile_source(src, "p.m")
    compile(unit.generated_source, "<check>", "exec")


@settings(max_examples=100, deadline=None)
@given(st.integers(min_value=-50, max_value=50))
def test_solve_well_conditioned_residual(x):
    unit = compile_source(
        "A = [3 1; 1 3];\n"
        f"b = [{x}; 0];\n"
        "y = A \\ b;\n"
        "r = A * y - b;\n",
        "p.m",
    )
    ns = execute(unit)
    assert np.linalg.norm(ns["r"]) < 1e-8
