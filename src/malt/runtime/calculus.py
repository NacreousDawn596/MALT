"""Numerical integration and root finding."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import integrate as _integrate
from scipy import optimize as _optimize

from ..errors import RuntimeError_
from .arrays import as_array, scalar_value


def _wrap_fun(fun: Any):
    """Wrap a MATLAB function handle into a Python scalar->scalar function."""
    if not callable(fun):
        raise RuntimeError_("expected a function handle")

    def f(x: float) -> float:
        r = fun(np.array([[x]], dtype=float))
        r = as_array(r)
        v = r.reshape(-1)[0]
        return float(v.real) if isinstance(v, complex) else float(v)

    return f


def integral(fun: Any, a: Any, b: Any) -> np.ndarray:
    a = float(scalar_value(a))
    b = float(scalar_value(b))
    f = _wrap_fun(fun)
    value, _ = _integrate.quad(f, a, b)
    return np.array([[value]])


def fzero(fun: Any, x0: Any, options: Any | None = None) -> np.ndarray:
    x0 = float(scalar_value(x0))
    f = _wrap_fun(fun)
    # Try to bracket the root; fall back to a scalar method.
    for delta in (1.0, 10.0, 100.0, 0.1):
        try:
            root = _optimize.brentq(f, x0 - delta, x0 + delta)
            return np.array([[root]])
        except ValueError:
            continue
    root = _optimize.fsolve(lambda x: f(x[0]), [x0])[0]
    return np.array([[root]])


def roots(p: Any) -> np.ndarray:
    p = as_array(p).flatten()
    return np.roots(p).reshape(-1, 1)
