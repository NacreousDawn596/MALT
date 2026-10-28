"""Differential tests: MALT results vs. NumPy/SciPy reference implementations."""

from __future__ import annotations

import numpy as np
from conftest import arr, run_source, scalar


def test_matmul_matches_numpy():
    src = (
        "rng(7);\nA = rand(6, 6);\nB = rand(6, 6);\nC = A * B;\n"
    )
    ns, _ = run_source(src)
    # Recompute the same matrices with the same seed.
    np.random.seed(7)
    a = np.random.rand(6, 6)
    b = np.random.rand(6, 6)
    np.testing.assert_allclose(arr(ns, "C"), a @ b, atol=1e-12)


def test_elementwise_matches_numpy():
    src = "x = linspace(0, 10, 50);\ny = sin(x) + cos(x);\nz = y .* y;\n"
    ns, _ = run_source(src)
    x = np.linspace(0, 10, 50)
    y = np.sin(x) + np.cos(x)
    np.testing.assert_allclose(np.ravel(arr(ns, "z")), y * y, atol=1e-12)


def test_linear_solve_matches_numpy():
    src = "A = [4 1; 1 3];\nb = [1; 2];\nx = A \\ b;\n"
    ns, _ = run_source(src)
    a = np.array([[4, 1], [1, 3]])
    b = np.array([[1], [2]])
    np.testing.assert_allclose(arr(ns, "x"), np.linalg.solve(a, b), atol=1e-12)


def test_lstsq_matches_scipy():
    # Rectangular (over-determined) system uses least squares.
    src = "A = [1 1; 1 2; 1 3];\nb = [1; 2; 2];\nx = A \\ b;\n"
    ns, _ = run_source(src)
    a = np.array([[1, 1], [1, 2], [1, 3]])
    b = np.array([[1], [2], [2]])
    expected, *_ = np.linalg.lstsq(a, b, rcond=None)
    np.testing.assert_allclose(arr(ns, "x"), expected, atol=1e-10)


def test_transpose_matches_numpy():
    src = "A = [1+2i 3+4i; 5+6i 7+8i];\nB = A';\nC = A.';\n"
    ns, _ = run_source(src)
    a = np.array([[1 + 2j, 3 + 4j], [5 + 6j, 7 + 8j]])
    np.testing.assert_allclose(arr(ns, "B"), a.conj().T, atol=1e-12)
    np.testing.assert_allclose(arr(ns, "C"), a.T, atol=1e-12)


def test_eig_matches_numpy():
    src = "A = [2 1; 1 2];\n[V, D] = eig(A);\n"
    ns, _ = run_source(src)
    a = np.array([[2, 1], [1, 2]])
    w, v = np.linalg.eig(a)
    # eigenvalues of [2 1;1 2] are 3 and 1
    np.testing.assert_allclose(np.sort(np.diag(arr(ns, "D"))), np.sort(w), atol=1e-12)


def test_integral_matches_scipy():
    from scipy.integrate import quad

    ns, _ = run_source("r = integral(@(x) x.^2, 0, 1);\n")
    expected, _ = quad(lambda x: x**2, 0, 1)
    assert abs(scalar(ns, "r") - expected) < 1e-8


def test_ode45_matches_scipy():
    from scipy.integrate import solve_ivp

    ns, _ = run_source(
        "function dydt = f(t, y)\n dydt = -2*y;\nend\n[t, y] = ode45(@f, [0 2], 1);\n"
    )
    sol = solve_ivp(lambda t, y: -2 * y, (0, 2), [1.0], method="RK45", rtol=1e-8)
    y = arr(ns, "y")
    assert abs(float(y[-1].reshape(-1)[0]) - sol.y[0, -1]) < 1e-5


def test_det_matches_numpy():
    ns, _ = run_source("d = det([3 0; 0 4]);\n")
    assert abs(scalar(ns, "d") - np.linalg.det(np.array([[3, 0], [0, 4]]))) < 1e-12


def test_reshape_column_major_matches_matlab():
    ns, _ = run_source("B = reshape([1 2 3 4 5 6], 2, 3);\n")
    np.testing.assert_array_equal(
        arr(ns, "B"), np.reshape(np.arange(1, 7), (2, 3), order="F")
    )
