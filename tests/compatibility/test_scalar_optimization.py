"""Scalar-execution correctness: native-scalar fast paths preserve semantics."""

from __future__ import annotations

import numpy as np
import pytest
from conftest import arr, norm_out, run_source, scalar

from malt.errors import MaltError


def test_scalar_integer_arithmetic():
    ns, out = run_source("a = 2 + 3;\nb = 2 * 3;\nc = 2 - 5;\nd = 2^3;\ne = 10 / 4;\n")
    assert scalar(ns, "a") == 5
    assert scalar(ns, "b") == 6
    assert scalar(ns, "c") == -3
    assert scalar(ns, "d") == 8
    assert scalar(ns, "e") == 2.5


def test_scalar_float_arithmetic():
    ns, _ = run_source("a = 0.1 + 0.2;\nb = 1.5 * 2.0;\nc = 7.0 / 2.0;\n")
    assert abs(scalar(ns, "a") - 0.3) < 1e-12
    assert scalar(ns, "b") == 3.0
    assert scalar(ns, "c") == 3.5


def test_scalar_complex_arithmetic():
    ns, _ = run_source("z = 3 + 4i;\nw = z * z;\nm = abs(z);\n")
    assert scalar(ns, "m") == 5
    w = scalar(ns, "w")
    assert abs(w.real - (-7)) < 1e-12
    assert abs(w.imag - 24) < 1e-12


def test_scalar_logical_expressions():
    ns, out = run_source(
        "a = 1 < 2;\nb = 2 <= 2;\nc = (3 > 4);\nd = 1 & 1;\ne = 0 | 1;\n"
    )
    assert scalar(ns, "a") == 1
    assert scalar(ns, "b") == 1
    assert scalar(ns, "c") == 0
    assert scalar(ns, "d") == 1
    assert scalar(ns, "e") == 1


def test_scalar_expansion_into_matrix():
    ns, _ = run_source("A = [1 2; 3 4];\nB = A * 2;\nC = 2 * A;\nD = A + 1;\n")
    np.testing.assert_array_equal(arr(ns, "B"), [[2, 4], [6, 8]])
    np.testing.assert_array_equal(arr(ns, "C"), [[2, 4], [6, 8]])
    np.testing.assert_array_equal(arr(ns, "D"), [[2, 3], [4, 5]])


def test_scalar_assignment_into_matrix():
    ns, _ = run_source("A = zeros(2, 2);\nA(1, 1) = 5;\nA(2, 2) = 7;\n")
    np.testing.assert_array_equal(arr(ns, "A"), [[5, 0], [0, 7]])


def test_scalar_returned_from_function():
    ns, _ = run_source(
        "function y = twice(x)\n y = 2 * x;\nend\nr = twice(21);\n"
    )
    assert scalar(ns, "r") == 42


def test_scalar_passed_to_numerical_functions():
    ns, _ = run_source(
        "a = sin(0);\nb = cos(0);\nc = sqrt(9);\nd = exp(0);\ne = log(1);\n"
    )
    assert abs(scalar(ns, "a")) < 1e-15
    assert scalar(ns, "b") == 1
    assert scalar(ns, "c") == 3
    assert scalar(ns, "d") == 1
    assert scalar(ns, "e") == 0


def test_scalar_used_in_indexing():
    ns, _ = run_source("A = [10 20 30; 40 50 60];\nx = A(1, 2);\ny = A(6);\n")
    assert scalar(ns, "x") == 20
    assert scalar(ns, "y") == 60  # column-major linear index 6


def test_scalar_display():
    ns, out = run_source("x = 42;\ndisp(x);\n")
    assert "42" in norm_out(out)


def test_scalar_exception():
    from conftest import compile_source as _cs

    from malt.executor import execute as _ex

    unit = _cs("x = undefined_variable;\n", "e.m")
    with pytest.raises(MaltError):
        _ex(unit)


def test_division_by_zero_is_inf_not_error():
    # MATLAB semantics: 1/0 is Inf, 0/0 is NaN (not a runtime error).
    import numpy as np

    ns, _ = run_source("a = 1 / 0;\nb = 0 / 0;\n")
    assert np.isinf(scalar(ns, "a"))
    assert np.isnan(scalar(ns, "b"))


def test_repeated_execution_no_state_leakage():
    src = "total = 0;\nfor k = 1:100\n total = total + k;\nend\n"
    ns1, _ = run_source(src)
    ns2, _ = run_source(src)
    assert scalar(ns1, "total") == 5050
    assert scalar(ns2, "total") == 5050
    # independent workspaces
    assert ns1 is not ns2


def test_scalar_matches_vectorized_reference():
    # A scalar accumulation must equal its closed form.
    ns, _ = run_source("n = 10000;\ns = 0;\nfor k = 1:n\n s = s + k;\nend\n")
    n = 10000
    assert scalar(ns, "s") == n * (n + 1) / 2


def test_mixed_scalar_matrix_operators():
    ns, _ = run_source(
        "A = [1 2; 3 4];\nv = A * [1; 1];\nw = A(1, 1) + A(2, 2);\n"
    )
    np.testing.assert_array_equal(arr(ns, "v"), [[3], [7]])
    assert scalar(ns, "w") == 5
