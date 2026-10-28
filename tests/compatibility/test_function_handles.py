"""Function handles (``@name``, ``func2str``, ``str2func``, ``feval``)."""

from __future__ import annotations

import numpy as np
import pytest
from conftest import run_source, scalar

from malt.errors import RuntimeError_


def test_handle_to_builtin():
    ns, _ = run_source("f = @sin;\ny = f(0.5);\n")
    np.testing.assert_allclose(scalar(ns, "y"), np.sin(0.5))


def test_handle_to_anon():
    ns, _ = run_source("g = @(x) x.^2 + 1;\nz = g(3);\n")
    assert scalar(ns, "z") == 10


def test_func2str_named_handle():
    ns, _ = run_source("f = @cos;\ns = func2str(f);\n")
    assert ns["s"] == "cos"


def test_str2func_and_feval():
    ns, _ = run_source("g = str2func('sqrt');\ny = feval(g, 16);\n")
    assert scalar(ns, "y") == 4


def test_feval_named_handle():
    ns, _ = run_source("f = @sin;\nw = feval(f, 1.0);\n")
    np.testing.assert_allclose(scalar(ns, "w"), np.sin(1.0))


def test_func2str_requires_handle():
    with pytest.raises(RuntimeError_):
        run_source("x = 5;\ns = func2str(x);\n")


def test_str2func_unknown_name():
    with pytest.raises(RuntimeError_):
        run_source("g = str2func('not_a_real_function_xyz');\n")
