"""Structured differential tests: shape + real/imag comparison vs Octave.

Regression tests for every semantic discrepancy the differential suite has
caught are also here, asserting against independently-known correct values
(not just cross-runtime agreement).
"""

from __future__ import annotations

import numpy as np
import pytest
from conftest import arr, run_source, scalar

from . import (
    check_structured,
    compare_structured,
    octave_available,
    run_structured_malt,
    run_structured_octave,
)

pytestmark = pytest.mark.skipif(not octave_available(), reason="Octave not installed")


# ---------------------------------------------------------------------------
# Structured semantic comparison (shape + values)
# ---------------------------------------------------------------------------


def test_matrix_and_shape():
    check_structured(
        "A = [1 2; 3 4];\nemit(A);\nemit(size(A));\nemit(A');\nemit(A.');\nemit(A * A);\nemit(A .* A);\n"
    )


def test_indexing():
    check_structured(
        "A = [10 20 30; 40 50 60];\nemit(A(1,2));\nemit(A(:,2));\nemit(A(2,:));\nemit(A(end));\nemit(A(:));\nemit(A([1 3 5]));\n"
    )


def test_colon_and_reshape():
    check_structured(
        "emit(1:5);\nemit(1:2:10);\nemit(10:-1:1);\nemit(0:0.5:2);\nemit(reshape([1 2 3 4 5 6], 2, 3));\n"
    )


def test_complex():
    check_structured(
        "z = 3 + 4i;\nemit(abs(z));\nemit(real(z));\nemit(imag(z));\nemit(conj(z));\nemit(angle(z));\nemit(z * z);\n"
    )


def test_reductions():
    check_structured(
        "A = [1 2 3; 4 5 6];\nemit(sum(A));\nemit(sum(A, 2));\nemit(mean(A));\nemit(max(A));\nemit(min(A));\nemit(prod(A));\nemit(cumsum(A));\nemit(sort(A));\n"
    )


def test_transpose_complex():
    check_structured(
        "A = [1+2i 3+4i; 5+6i 7+8i];\nemit(A');\nemit(A.');\n"
    )


def test_nan_and_inf():
    check_structured("emit(0/0);\nemit(1/0);\nemit(-1/0);\nemit(Inf);\nemit(NaN);\nemit(1/-0);\n")


def test_linear_algebra():
    check_structured(
        "A = [4 1; 1 3];\nb = [1; 2];\nemit(A \\ b);\nemit(eig([2 1; 1 2]));\nemit(det([3 0; 0 4]));\nemit(inv([2 0; 0 4]));\n"
    )


def test_round_half_away_from_zero():
    check_structured("emit(round(2.5));\nemit(round(-2.5));\nemit(round(1.5));\nemit(round(-1.5));\nemit(round(2.4));\n")


# ---------------------------------------------------------------------------
# Optimization levels 0 / 1 / 2
# ---------------------------------------------------------------------------

_LEVEL_BODIES = [
    "n = 100;\ns = 0;\nfor k = 1:n\n s = s + k;\nend\nemit(s);\nemit(k);\n",
    "s = 0;\np = 1;\nfor k = 1:6\n s = s + k;\n p = p * k;\nend\nemit(s);\nemit(p);\n",
    "A = [1 2; 3 4];\nB = A * A;\nemit(B);\nemit(A .* A);\n",
    "z = 3 + 4i;\nemit(abs(z));\nemit(conj(z));\n",
]


@pytest.mark.parametrize("body", _LEVEL_BODIES)
def test_all_optimization_levels_match_octave(body):
    octave = run_structured_octave(body)
    for lvl in (0, 1, 2):
        malt = run_structured_malt(body, optimization_level=lvl)
        compare_structured(malt, octave)


# ---------------------------------------------------------------------------
# Regression tests: assert independently-known correct values
# ---------------------------------------------------------------------------


def test_regression_sum_dim1():
    ns, _ = run_source("A = [1 2 3; 4 5 6];\ns = sum(A);\nm = mean(A);\n")
    np.testing.assert_array_equal(arr(ns, "s"), [[5, 7, 9]])
    np.testing.assert_allclose(arr(ns, "m"), [[2.5, 3.5, 4.5]])


def test_regression_sum_vector_is_scalar():
    ns, _ = run_source("s = sum([1 2 3]);\nc = sum([1; 2; 3]);\n")
    assert scalar(ns, "s") == 6
    assert scalar(ns, "c") == 6


def test_regression_round():
    ns, _ = run_source("a = round(2.5);\nb = round(-2.5);\nc = round(2.4);\n")
    assert scalar(ns, "a") == 3
    assert scalar(ns, "b") == -3
    assert scalar(ns, "c") == 2


def test_regression_eig_sorted():
    ns, _ = run_source("A = [2 1; 1 2];\nd = eig(A);\n")
    np.testing.assert_allclose(arr(ns, "d"), [[1], [3]], atol=1e-12)


def test_regression_division_by_zero():
    ns, _ = run_source("a = 1 / 0;\nb = 0 / 0;\nc = -1 / 0;\n")
    assert np.isinf(scalar(ns, "a")) and scalar(ns, "a") > 0
    assert np.isnan(scalar(ns, "b"))
    assert np.isinf(scalar(ns, "c")) and scalar(ns, "c") < 0


def test_regression_string_escapes():
    ns, out = run_source("disp('a\\nb');\ndisp('tab\\there');\n")
    assert "a\nb" in out
    assert "tab\there" in out


def test_regression_sum_empty_is_zero():
    ns, _ = run_source("s = sum(1:0);\nt = sum([1 2; 3 4] * 0 - 99);\n")
    assert scalar(ns, "s") == 0


def test_regression_non_integer_index_errors():
    import pytest as _pytest

    from malt.errors import IndexError_ as _Idx

    with _pytest.raises(_Idx):
        run_source("A = [1 2; 3 4];\nx = A(1.5);\n")
