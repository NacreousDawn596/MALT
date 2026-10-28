"""Cell arrays and structs (see docs/specs/cell-arrays.md, docs/specs/structs.md)."""

from __future__ import annotations

import numpy as np
import pytest
from conftest import arr, run_source, scalar

from malt.errors import RuntimeError_


def _getcell(ns, name):
    from malt.runtime.cells import Cell

    v = ns[name]
    assert isinstance(v, Cell)
    return v


def test_cell_literal_scalars():
    ns, _ = run_source("c = {1, 2, 3};\n")
    c = _getcell(ns, "c")
    assert c.shape == (1, 3)
    assert [c._data[0, j] for j in range(3)] == [1.0, 2.0, 3.0]


def test_cell_2d_literal():
    ns, _ = run_source("c = {1, 2; 3, 4};\n")
    c = _getcell(ns, "c")
    assert c.shape == (2, 2)


def test_cell_linear_content_index():
    ns, _ = run_source("c = {10, 20, 30, 40};\nx = c{3};\n")
    assert scalar(ns, "x") == 30


def test_cell_subscript_content_index():
    ns, _ = run_source("c = {1, 2; 3, 4};\nx = c{2, 1};\n")
    assert scalar(ns, "x") == 3


def test_cell_end_index():
    ns, _ = run_source("c = {10, 20, 30};\nx = c{end};\n")
    assert scalar(ns, "x") == 30


def test_cell_holds_matrix_and_string():
    ns, _ = run_source("d = {[1 2; 3 4], 'hello'};\np = d{1};\nq = d{2};\n")
    np.testing.assert_array_equal(arr(ns, "p"), [[1, 2], [3, 4]])
    assert ns["q"] == "hello"


def test_cell_content_assignment():
    ns, _ = run_source("c = {1, 2, 3};\nc{2} = 99;\nx = c{2};\n")
    assert scalar(ns, "x") == 99


def test_cell_2d_assignment():
    ns, _ = run_source("c = {1, 2; 3, 4};\nc{1, 2} = 'x';\nv = c{1, 2};\n")
    assert ns["v"] == "x"


def test_iscell():
    ns, _ = run_source("c = {1};\na = [1];\nr1 = iscell(c);\nr2 = iscell(a);\n")
    assert scalar(ns, "r1") == 1
    assert scalar(ns, "r2") == 0


def test_cell_content_of_non_cell_errors():
    with pytest.raises(RuntimeError_):
        run_source("a = [1 2];\nx = a{1};\n")


def test_struct_constructor_and_access():
    ns, _ = run_source("s = struct('name', 'malt', 'version', 0.3);\nn = s.name;\nv = s.version;\n")
    assert ns["n"] == "malt"
    assert scalar(ns, "v") == 0.3


def test_struct_field_assignment():
    ns, _ = run_source("s = struct('a', 1);\ns.b = 42;\nx = s.b;\n")
    assert scalar(ns, "x") == 42


def test_struct_missing_field_errors():
    with pytest.raises(RuntimeError_):
        run_source("s = struct('a', 1);\nx = s.zzz;\n")


def test_isstruct_isfield():
    ns, _ = run_source(
        "s = struct('a', 1);\nc = {1};\n"
        "r1 = isstruct(s);\nr2 = isstruct(c);\n"
        "r3 = isfield(s, 'a');\nr4 = isfield(s, 'b');\n"
    )
    assert scalar(ns, "r1") == 1
    assert scalar(ns, "r2") == 0
    assert scalar(ns, "r3") == 1
    assert scalar(ns, "r4") == 0


def test_fieldnames():
    ns, _ = run_source("s = struct('a', 1);\ns.b = 2;\nfn = fieldnames(s);\n")
    fn = _getcell(ns, "fn")
    assert [fn._data[0, j] for j in range(fn.shape[1])] == ["a", "b"]


def test_struct_numeric_field_is_array():
    ns, _ = run_source("s = struct('x', 5);\nv = s.x;\n")
    np.testing.assert_array_equal(arr(ns, "v"), [[5.0]])
