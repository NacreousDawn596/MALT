"""Extended math, arrays, LA, poly, stats, control, signal, and sparse functions."""

from __future__ import annotations

import numpy as np
import pytest
from conftest import run_source

import malt.runtime as _ml


def test_core_math():
    assert _ml.sec(0).reshape(-1)[0] == pytest.approx(1.0)
    assert _ml.sind(90).reshape(-1)[0] == pytest.approx(1.0)
    assert _ml.gamma(5).reshape(-1)[0] == pytest.approx(24.0)
    assert _ml.factorial(5).reshape(-1)[0] == pytest.approx(120.0)
    assert _ml.gcd(12, 18).reshape(-1)[0] == pytest.approx(6.0)
    assert _ml.isprime(17).reshape(-1)[0] == 1.0
    assert _ml.isprime(16).reshape(-1)[0] == 0.0
    np.testing.assert_array_equal(_ml.primes(10).reshape(-1), [2, 3, 5, 7])
    np.testing.assert_array_equal(_ml.diff([1, 3, 6]).reshape(-1), [2, 3])


def test_special_functions():
    assert _ml.erf(1).reshape(-1)[0] == pytest.approx(0.8427007929)
    assert _ml.erfc(0).reshape(-1)[0] == pytest.approx(1.0)
    assert _ml.beta(1, 1).reshape(-1)[0] == pytest.approx(1.0)
    assert _ml.besselj(0, 0).reshape(-1)[0] == pytest.approx(1.0)


def test_array_manipulation():
    np.testing.assert_array_equal(_ml.triu([[1, 2], [3, 4]]), [[1, 2], [0, 4]])
    np.testing.assert_array_equal(_ml.tril([[1, 2], [3, 4]]), [[1, 0], [3, 4]])
    np.testing.assert_array_equal(_ml.unique([3, 1, 2, 1]).reshape(-1), [1, 2, 3])
    np.testing.assert_array_equal(_ml.find([0, 1, 0, 2]).reshape(-1), [2, 4])
    np.testing.assert_array_equal(_ml.kron([1, 2], [3, 4]).reshape(-1), [3, 4, 6, 8])
    assert _ml.magic(3).shape == (3, 3)


def test_linear_algebra_extra():
    r = _ml.rref([[1, 2], [3, 4]])
    np.testing.assert_allclose(r, [[1, 0], [0, 1]])
    assert _ml.issymmetric(np.eye(2)).reshape(-1)[0] == 1.0
    assert _ml.ishermitian(np.eye(2)).reshape(-1)[0] == 1.0
    assert _ml.istriu([[1, 2], [0, 3]]).reshape(-1)[0] == 1.0


def test_poly_interp():
    np.testing.assert_array_equal(_ml.conv([1, 1], [1, 2]).reshape(-1), [1, 3, 2])
    np.testing.assert_array_equal(_ml.polyval([1, 0, 0], [2]).reshape(-1), [4])
    assert _ml.interp1([0, 1], [0, 10], [0.5]).reshape(-1)[0] == pytest.approx(5.0)


def test_stats():
    assert _ml.median([1, 2, 100]).reshape(-1)[0] == pytest.approx(2.0)
    assert _ml.std([1, 2, 3]).reshape(-1)[0] == pytest.approx(0.8164965809)
    c = _ml.corrcoef([1, 2, 3], [1, 2, 3])
    assert c[0, 1] == pytest.approx(1.0)
    assert _ml.iqr([1, 2, 3, 4, 100]).reshape(-1)[0] == pytest.approx(2.0)


def test_control_extra():
    sys = _ml.tf(1, [1, 1])
    assert _ml.isstable(sys).reshape(-1)[0] == 1.0
    assert _ml.dcgain(sys).reshape(-1)[0] == pytest.approx(1.0)
    p = _ml.pid(2, 1, 0.5)
    np.testing.assert_allclose(p.num, [0.5, 2.0, 1.0])
    np.testing.assert_allclose(p.den, [1.0, 0.0])
    mag, _ = _ml.bode(sys)
    assert mag.size > 0


def test_signal():
    f = _ml.fft([1, 0, 0]).reshape(-1)
    np.testing.assert_allclose(f.real, [1, 1, 1])
    y = _ml.filter([1], [1, -0.5], [1, 0, 0, 0])
    np.testing.assert_allclose(y, [1.0, 0.5, 0.25, 0.125])
    h = _ml.hilbert([1, 0, 1, 0]).reshape(-1)
    assert h.size == 4


def test_sparse():
    S = _ml.speye(3)
    assert _ml.nnz(S).reshape(-1)[0] == 3.0
    x = _ml.gmres(S, [1, 2, 3])
    np.testing.assert_allclose(x.reshape(-1), [1, 2, 3])


def test_extended_via_source():
    ns, _ = run_source("x = sind(30);\ny = factorial(4);\nz = gcd(48, 36);\n")
    assert ns["x"] == pytest.approx(0.5)
    assert ns["y"] == pytest.approx(24.0)
    assert ns["z"] == pytest.approx(12.0)
