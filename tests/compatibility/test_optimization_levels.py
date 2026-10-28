"""Optimization-level differential tests and compilation-cache tests."""

from __future__ import annotations

import numpy as np
import pytest

from malt.compiler import cache_clear, cache_info, compile_source
from malt.executor import execute

PROGRAMS = [
    "a = 2 + 3 * 4;\nb = 10 / 4;\nc = 2 ^ 10;\n",
    "x = -5;\nif x > 0\n r = 1;\nelse\n r = -1;\nend\n",
    "A = [1 2; 3 4];\nB = A * A;\nC = A .* A;\nD = A \\ [1; 1];\n",
    "z = 3 + 4i;\nw = conj(z);\nm = abs(z);\n",
    "n = 100;\ns = 0;\nfor k = 1:n\n s = s + k * k;\nend\n",
    "f = @(x) x .^ 2;\nr = f(9);\n",
    "v = zeros(1, 10);\nfor k = 1:10\n v(k) = k;\nend\n",
    "function [p, q] = stats(a, b)\n p = a + b;\n q = a * b;\nend\n[x, y] = stats(3, 4);\n",
]


def _run_levels(src: str):
    u0 = compile_source(src, "t.m", optimization_level=0)
    u1 = compile_source(src, "t.m", optimization_level=1)
    return execute(u0), execute(u1)


_CONSTANTS = {"pi", "eps", "Inf", "NaN", "true", "false", "i", "j"}


def _vals(ns):
    out = {}
    for k, v in ns.items():
        if k.startswith("_") or k in _CONSTANTS:
            continue
        if callable(v) and not isinstance(v, np.ndarray):
            continue
        out[k] = v if isinstance(v, (str, complex)) else np.asarray(v)
    return out


@pytest.mark.parametrize("src", PROGRAMS)
def test_optimization_levels_equivalent(src):
    ns0, ns1 = _run_levels(src)
    v0, v1 = _vals(ns0), _vals(ns1)
    assert set(v0) == set(v1)
    for name in v0:
        a, b = v0[name], v1[name]
        if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
            np.testing.assert_allclose(
                np.asarray(a, dtype=complex), np.asarray(b, dtype=complex), atol=1e-12
            )
        else:
            assert a == b or abs(float(a) - float(b)) < 1e-12


def test_optimization_level_0_is_slow_path():
    # Level 0 keeps scalars as 1x1 arrays; level 1 uses native scalars.
    src = "a = 1 + 2;\n"
    ns0, _ = _run_levels(src)
    assert isinstance(ns0["a"], np.ndarray)


def test_cache_hit_and_miss():
    cache_clear()
    src = "A = [1 2; 3 4];\nB = A * A;\n"
    compile_source(src, "c.m")
    before = cache_info()
    compile_source(src, "c.m")  # hit
    after = cache_info()
    assert after.hits == before.hits + 1


def test_cache_distinguishes_source():
    cache_clear()
    compile_source("a = 1;\n", "c.m")
    compile_source("a = 2;\n", "c.m")
    assert cache_info().misses == 2


def test_cache_distinguishes_options():
    cache_clear()
    compile_source("a = 1;\n", "c.m", optimization_level=0)
    compile_source("a = 1;\n", "c.m", optimization_level=1)
    assert cache_info().misses == 2


def test_cache_eviction_bounds():
    cache_clear()
    for i in range(300):
        compile_source(f"a = {i};\n", "c.m")
    assert cache_info().currsize <= 128


def test_cached_code_isolated_execution():
    cache_clear()
    src = "s = 0;\nfor k = 1:5\n s = s + k;\nend\n"
    u = compile_source(src, "c.m")
    n1 = execute(u)
    n2 = execute(u)
    # independent workspaces (fresh namespaces)
    assert n1 is not n2
    assert float(np.asarray(n1["s"])) == 15
    assert float(np.asarray(n2["s"])) == 15
