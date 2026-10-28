"""Semantic regression corpus.

Each fixture is a minimal ``.m`` reproducer for a bug that was discovered (mostly
by the Octave differential suite) and fixed. The test runs the actual source
through the real compiler/runtime and asserts the independently-known correct
behavior, so a regression is caught even if the differential harness is
unavailable.
"""

from __future__ import annotations

import os

import numpy as np
import pytest

from conftest import arr, run_file, scalar

from malt.errors import IndexError_, MaltError

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _run(name):
    return run_file(os.path.join(FIXTURES, name))


def test_sum_reduces_first_nonsingleton_dim():
    ns, _ = _run("sum_first_nonsingleton.m")
    np.testing.assert_array_equal(arr(ns, "s"), [[5, 7, 9]])
    np.testing.assert_allclose(arr(ns, "m"), [[2.5, 3.5, 4.5]])
    np.testing.assert_array_equal(arr(ns, "mx"), [[4, 5, 6]])
    np.testing.assert_array_equal(arr(ns, "mn"), [[1, 2, 3]])
    np.testing.assert_array_equal(arr(ns, "p"), [[4, 10, 18]])


def test_cumsum_sort_along_dim1():
    ns, _ = _run("cumsum_dim1.m")
    np.testing.assert_array_equal(arr(ns, "c"), [[9, 2, 7], [10, 10, 10]])
    np.testing.assert_array_equal(arr(ns, "s"), [[1, 2, 3], [9, 8, 7]])


def test_round_half_away_from_zero():
    ns, _ = _run("round_half_away.m")
    assert scalar(ns, "a") == 3
    assert scalar(ns, "b") == -3
    assert scalar(ns, "c") == 2
    assert scalar(ns, "d") == 2


def test_eig_sorted_ascending():
    ns, _ = _run("eig_sorted.m")
    np.testing.assert_allclose(arr(ns, "d"), [[1], [3]], atol=1e-12)


def test_division_by_zero_is_inf_nan():
    ns, _ = _run("division_by_zero.m")
    assert np.isinf(scalar(ns, "a")) and scalar(ns, "a") > 0
    assert np.isnan(scalar(ns, "b"))
    assert np.isinf(scalar(ns, "c")) and scalar(ns, "c") < 0


def test_string_escape_sequences():
    ns, _ = _run("string_escapes.m")
    assert ns["s"] == "a\nb"
    assert ns["t"] == "x\ty"


def test_noninteger_index_errors():
    with pytest.raises(IndexError_):
        _run("noninteger_index.m")


def test_sum_empty_is_zero():
    ns, _ = _run("sum_empty.m")
    assert scalar(ns, "s") == 0


def test_empty_loop_var_is_empty():
    ns, _ = _run("empty_loop_var.m")
    y = np.asarray(ns["y"])
    assert y.size == 0


def test_column_major_reshape():
    ns, _ = _run("column_major_reshape.m")
    np.testing.assert_array_equal(arr(ns, "B"), [[1, 3, 5], [2, 4, 6]])


def test_try_catch_error_value():
    ns, _ = _run("try_catch_error_value.m")
    assert isinstance(ns["msg"], str) and ns["msg"]
    assert isinstance(ns["ident"], str) and ns["ident"]
