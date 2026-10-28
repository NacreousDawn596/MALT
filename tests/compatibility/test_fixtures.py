"""Compatibility fixtures: every test runs the actual ``.m`` source through MALT."""

from __future__ import annotations

import math
import os

import numpy as np
import pytest

from conftest import arr, norm_out, run_file, scalar

FIXTURES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures")


def _run(name: str):
    return run_file(os.path.join(FIXTURES, name))


def test_01_arithmetic():
    ns, out = _run("01_arithmetic.m")
    assert scalar(ns, "a") == 14
    assert scalar(ns, "b") == 20
    assert scalar(ns, "c") == 8
    assert scalar(ns, "d") == 2.5
    assert norm_out(out) == "14\n20\n8\n2.5"


def test_02_matrix():
    ns, out = _run("02_matrix.m")
    A = arr(ns, "A")
    assert A.shape == (2, 2)
    np.testing.assert_array_equal(A, [[1, 2], [3, 4]])
    # size(A) -> [2 2]; A(1,2)=2; A(2,1)=3
    norm = norm_out(out)
    assert "2 2" in norm
    assert "2" in norm
    assert "3" in norm


def test_03_matrix_multiply():
    ns, _ = _run("03_matrix_multiply.m")
    np.testing.assert_array_equal(arr(ns, "C"), [[19, 22], [43, 50]])
    np.testing.assert_array_equal(arr(ns, "D"), [[5, 12], [21, 32]])


def test_04_linear_solve():
    ns, _ = _run("04_linear_solve.m")
    x = arr(ns, "x")
    np.testing.assert_allclose(x, [[1], [2]], atol=1e-10)
    A = np.array([[2, 3], [4, -1]])
    b = np.array([[8], [2]])
    assert np.linalg.norm(A @ x - b) < 1e-10


def test_05_indexing():
    ns, out = _run("05_indexing.m")
    # Verify each indexing form directly through the runtime.
    from conftest import run_source

    ns2, _ = run_source(
        "A = [10 20 30; 40 50 60];\n"
        "c1 = A(1,2);\n"
        "c2 = A(:,2);\n"
        "c3 = A(2,:);\n"
        "c4 = A(end);\n"
    )
    assert scalar(ns2, "c1") == 20
    np.testing.assert_array_equal(arr(ns2, "c2"), [[20], [50]])
    np.testing.assert_array_equal(arr(ns2, "c3"), [[40, 50, 60]])
    assert scalar(ns2, "c4") == 60


def test_06_loops():
    ns, out = _run("06_loops.m")
    assert scalar(ns, "total") == 55
    assert norm_out(out) == "55"


def test_07_conditionals():
    ns, out = _run("07_conditionals.m")
    assert scalar(ns, "result") == -1
    assert norm_out(out) == "-1"


def test_08_functions():
    ns, out = _run("08_functions.m")
    assert scalar(ns, "x") == 7
    assert scalar(ns, "y") == 12
    assert norm_out(out) == "7\n12"


def test_09_anonymous():
    ns, out = _run("09_anonymous.m")
    assert norm_out(out) == "10"


def test_10_integral():
    ns, out = _run("10_integral.m")
    assert abs(scalar(ns, "result") - 1 / 3) < 1e-8


def test_11_ode45():
    ns, out = _run("11_ode45.m")
    y = arr(ns, "y")
    assert abs(float(y[-1].reshape(-1)[0]) - math.exp(-4)) < 1e-5


def test_12_complex():
    ns, out = _run("12_complex.m")
    z = scalar(ns, "z")
    assert abs(z) == 5
    assert z.real == 3
    assert z.imag == 4


def test_13_error():
    from malt.errors import IndexError_

    with pytest.raises(IndexError_):
        _run("13_error.m")


def test_14_semicolon():
    ns, out = _run("14_semicolon.m")
    assert norm_out(out) == "20\n30"


def test_15_reshape():
    ns, out = _run("15_reshape.m")
    B = arr(ns, "B")
    np.testing.assert_array_equal(B, [[1, 3, 5], [2, 4, 6]])


def test_16_transpose():
    ns, out = _run("16_transpose.m")
    B = arr(ns, "B")
    C = arr(ns, "C")
    np.testing.assert_allclose(B, [[1 - 2j], [3 - 4j]])
    np.testing.assert_allclose(C, [[1 + 2j], [3 + 4j]])


def test_17_random():
    ns, out = _run("17_random.m")
    A = arr(ns, "A")
    B = arr(ns, "B")
    np.testing.assert_array_equal(A, B)
    assert norm_out(out) == "1"
