"""Special functions (gamma, error, Bessel, elliptic, and friends) via SciPy."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import integrate as _integrate
from scipy import special as _sp

from ..errors import RuntimeError_
from .arrays import as_array


def _arr(x: Any) -> np.ndarray:
    a = as_array(x)
    if isinstance(a, str):
        raise RuntimeError_("function is not defined for strings")
    return a


def _unary(name: str):
    fn = getattr(_sp, name)

    def call(x: Any) -> np.ndarray:
        return np.asarray(fn(_arr(x)))

    call.__name__ = name
    return call


gamma = _unary("gamma")
gammaln = _unary("gammaln")
erf = _unary("erf")
erfc = _unary("erfc")
erfinv = _unary("erfinv")
erfcinv = _unary("erfcinv")
psi = _unary("psi")


def expint(x: Any) -> np.ndarray:
    return np.asarray(_sp.exp1(_arr(x)))


def beta(a: Any, b: Any) -> np.ndarray:
    return np.asarray(_sp.beta(_arr(a), _arr(b)))


def betaln(a: Any, b: Any) -> np.ndarray:
    return np.asarray(_sp.betaln(_arr(a), _arr(b)))


def besselj(nu: Any, x: Any) -> np.ndarray:
    return np.asarray(_sp.jv(_arr(nu), _arr(x)))


def bessely(nu: Any, x: Any) -> np.ndarray:
    return np.asarray(_sp.yv(_arr(nu), _arr(x)))


def besseli(nu: Any, x: Any) -> np.ndarray:
    return np.asarray(_sp.iv(_arr(nu), _arr(x)))


def besselk(nu: Any, x: Any) -> np.ndarray:
    return np.asarray(_sp.kv(_arr(nu), _arr(x)))


def airy(x: Any) -> np.ndarray:
    return np.asarray(_sp.airy(_arr(x))[0])


def ellipke(m: Any) -> np.ndarray:
    return np.asarray(_sp.ellipk(_arr(m)))


def ellipj(u: Any, m: Any) -> np.ndarray:
    return np.asarray(_sp.ellipj(_arr(u), _arr(m)))


def legendre(n: Any, x: Any) -> np.ndarray:
    n = int(np.asarray(as_array(n)).reshape(-1)[0])
    x = _arr(x)
    vals = [_sp.lpmv(0, m, x) for m in range(n + 1)]
    return np.asarray(vals)


def cross(a: Any, b: Any) -> np.ndarray:
    a = _arr(a)
    b = _arr(b)
    if a.ndim == 1 or b.ndim == 1:
        return np.cross(a.reshape(-1), b.reshape(-1))
    return np.cross(a, b, axisa=-1, axisb=-1)


def dot(a: Any, b: Any) -> np.ndarray:
    return np.asarray(np.dot(_arr(a), _arr(b)))


def cumtrapz(y: Any, x: Any = None, dim: Any = 1) -> np.ndarray:
    y = _arr(y)
    if x is None:
        return np.asarray(_integrate.cumtrapz(y, axis=int(np.asarray(as_array(dim)).reshape(-1)[0]) - 1))
    x = _arr(x)
    return np.asarray(_integrate.cumtrapz(y, x, axis=int(np.asarray(as_array(dim)).reshape(-1)[0]) - 1))
