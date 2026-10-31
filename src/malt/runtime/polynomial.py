"""Polynomials, interpolation, and numerical calculus (SciPy-backed)."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import integrate as _integrate
from scipy import interpolate as _interp
from scipy import optimize as _opt
from scipy import signal as _sig

from ..errors import RuntimeError_  # noqa: F401  (re-exported for callers)
from .arrays import as_array, scalar_value


def conv(a: Any, b: Any, *shape: Any) -> np.ndarray:
    a = np.asarray(as_array(a)).flatten()
    b = np.asarray(as_array(b)).flatten()
    if shape:
        m = str(shape[0]).lower()
        if m == "same":
            return np.asarray(np.convolve(a, b, mode="same")).reshape(1, -1)
        if m == "valid":
            return np.asarray(np.convolve(a, b, mode="valid")).reshape(1, -1)
    return np.asarray(np.convolve(a, b, mode="full")).reshape(1, -1)


def deconv(b: Any, a: Any) -> np.ndarray:
    q, r = np.polydiv(np.asarray(as_array(b)).flatten(), np.asarray(as_array(a)).flatten())
    return np.asarray(q).reshape(1, -1)


def poly(roots: Any) -> np.ndarray:
    return np.asarray(np.poly(np.asarray(as_array(roots)).flatten())).reshape(1, -1)


def polyval(p: Any, x: Any) -> np.ndarray:
    return np.asarray(np.polyval(np.asarray(as_array(p)).flatten(), np.asarray(as_array(x)))).reshape(1, -1)


def polyvalm(p: Any, A: Any) -> np.ndarray:
    from scipy.linalg import fractional_matrix_power  # noqa: F401
    p = np.asarray(as_array(p)).flatten()
    A = np.asarray(as_array(A))
    return np.asarray(np.polyval(p, A))


def polyder(p: Any) -> np.ndarray:
    return np.asarray(np.polyder(np.asarray(as_array(p)).flatten())).reshape(1, -1)


def polyint(p: Any, k: Any = None) -> np.ndarray:
    p = np.asarray(as_array(p)).flatten()
    if k is None:
        return np.asarray(np.polyint(p)).reshape(1, -1)
    return np.asarray(np.polyint(p, float(scalar_value(k)))).reshape(1, -1)


def residue(b: Any, a: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    r, p, k = _sig.residue(np.asarray(as_array(b)).flatten(), np.asarray(as_array(a)).flatten())
    return r.reshape(-1, 1), p.reshape(-1, 1), np.asarray(k).reshape(1, -1)


# ---------------------------------------------------------------------------
# Interpolation
# ---------------------------------------------------------------------------


def _interp_kind(method: str) -> str:
    return {
        "linear": "linear", "nearest": "nearest", "next": "next", "previous": "previous",
        "spline": "cubic", "cubic": "cubic", "pchip": "cubic", "makima": "cubic",
    }.get(method.lower(), "linear")


def interp1(x: Any, v: Any, xq: Any, method: Any = "linear") -> np.ndarray:
    x = np.asarray(as_array(x)).flatten()
    v = np.asarray(as_array(v))
    xq = np.asarray(as_array(xq)).flatten()
    kind = _interp_kind(str(method))
    if str(method).lower() == "pchip":
        f = _interp.PchipInterpolator(x, v.flatten())
    elif str(method).lower() == "makima":
        f = _interp.Akima1DInterpolator(x, v.flatten())
    else:
        f = _interp.interp1d(x, v.flatten(), kind=kind, fill_value="extrapolate", assume_sorted=False)
    return np.asarray(f(xq))


def spline(x: Any, y: Any, xq: Any) -> np.ndarray:
    x = np.asarray(as_array(x)).flatten()
    y = np.asarray(as_array(y)).flatten()
    xq = np.asarray(as_array(xq)).flatten()
    f = _interp.CubicSpline(x, y)
    return np.asarray(f(xq))


def pchip(x: Any, y: Any, xq: Any) -> np.ndarray:
    f = _interp.PchipInterpolator(np.asarray(as_array(x)).flatten(), np.asarray(as_array(y)).flatten())
    return np.asarray(f(np.asarray(as_array(xq)).flatten()))


def makima(x: Any, y: Any, xq: Any) -> np.ndarray:
    f = _interp.Akima1DInterpolator(np.asarray(as_array(x)).flatten(), np.asarray(as_array(y)).flatten())
    return np.asarray(f(np.asarray(as_array(xq)).flatten()))


def interp2(X: Any, Y: Any, V: Any, Xq: Any, Yq: Any, method: Any = "linear") -> np.ndarray:
    x = np.asarray(as_array(X)).flatten()
    y = np.asarray(as_array(Y)).flatten()
    v = np.asarray(as_array(V))
    xq = np.asarray(as_array(Xq)).flatten()
    yq = np.asarray(as_array(Yq)).flatten()
    kind = _interp_kind(str(method))
    f = _interp.RegularGridInterpolator((x, y), v.T, method=kind, bounds_error=False, fill_value=np.nan)
    return np.asarray(f(np.column_stack([xq, yq])))


def interp3(X: Any, Y: Any, Z: Any, V: Any, Xq: Any, Yq: Any, Zq: Any, method: Any = "linear") -> np.ndarray:
    x = np.asarray(as_array(X)).flatten()
    y = np.asarray(as_array(Y)).flatten()
    z = np.asarray(as_array(Z)).flatten()
    v = np.asarray(as_array(V))
    pts = np.column_stack([
        np.asarray(as_array(Xq)).flatten(), np.asarray(as_array(Yq)).flatten(),
        np.asarray(as_array(Zq)).flatten(),
    ])
    kind = _interp_kind(str(method))
    f = _interp.RegularGridInterpolator((x, y, z), np.transpose(v, (2, 1, 0)), method=kind, bounds_error=False, fill_value=np.nan)
    return np.asarray(f(pts))


# ---------------------------------------------------------------------------
# Numerical calculus
# ---------------------------------------------------------------------------


def gradient(F: Any, *spacing: Any) -> Any:
    f = np.asarray(as_array(F), dtype=float)
    if spacing:
        sp = [float(np.asarray(as_array(s)).reshape(-1)[0]) for s in spacing]
        g = np.gradient(f, *sp)
    else:
        g = np.gradient(f)
    return g[0] if len(g) == 1 else g


def del2(U: Any) -> np.ndarray:
    u = np.asarray(as_array(U), dtype=float)
    g = np.gradient(u)
    if isinstance(g, np.ndarray):
        g = [g]
    lapl = np.zeros_like(u)
    for d in g:
        g2 = np.gradient(d)
        if isinstance(g2, np.ndarray):
            g2 = [g2]
        lapl = lapl + g2[0]
    return lapl


def trapz(Y: Any, X: Any = None, dim: Any = None) -> np.ndarray:
    y = np.asarray(as_array(Y), dtype=float)
    axis = 0 if dim is None else int(scalar_value(dim)) - 1
    if X is None:
        return np.asarray(np.trapezoid(y, axis=axis))
    x = np.asarray(as_array(X)).flatten()
    return np.asarray(np.trapezoid(y, x, axis=axis))


def integral2(fun: Any, xmin: Any, xmax: Any, ymin: Any, ymax: Any) -> np.ndarray:
    x0 = float(scalar_value(xmin))
    x1 = float(scalar_value(xmax))
    y0 = float(scalar_value(ymin))
    y1 = float(scalar_value(ymax))
    val, _ = _integrate.dblquad(lambda y, x: float(fun(np.array([[x]]), np.array([[y]])).reshape(-1)[0]), x0, x1, y0, y1)
    return np.array([[val]])


def integral3(fun: Any, xmin: Any, xmax: Any, ymin: Any, ymax: Any, zmin: Any, zmax: Any) -> np.ndarray:
    x0 = float(scalar_value(xmin))
    x1 = float(scalar_value(xmax))
    y0 = float(scalar_value(ymin))
    y1 = float(scalar_value(ymax))
    z0 = float(scalar_value(zmin))
    z1 = float(scalar_value(zmax))
    val, _ = _integrate.tplquad(lambda z, y, x: float(fun(np.array([[x]]), np.array([[y]]), np.array([[z]])).reshape(-1)[0]), x0, x1, y0, y1, z0, z1)
    return np.array([[val]])


# ---------------------------------------------------------------------------
# Optimization (base)
# ---------------------------------------------------------------------------


def _scalar_f(fun: Any):
    def f(x: Any) -> float:
        return float(fun(np.array([[x]])).reshape(-1)[0])

    return f


def fminsearch(fun: Any, x0: Any) -> np.ndarray:
    x0 = np.asarray(as_array(x0)).flatten().astype(float)

    def f(v: np.ndarray) -> float:
        return float(fun(v.reshape(-1, 1)).reshape(-1)[0])

    res = _opt.minimize(f, x0, method="Nelder-Mead")
    return res.x.reshape(-1, 1)


def fminbnd(fun: Any, x1: Any, x2: Any) -> np.ndarray:
    f = _scalar_f(fun)
    res = _opt.minimize_scalar(f, bounds=(float(scalar_value(x1)), float(scalar_value(x2))), method="bounded")
    return np.array([[res.x]])


def fsolve(fun: Any, x0: Any) -> np.ndarray:
    x0 = np.asarray(as_array(x0)).flatten().astype(float)

    def f(v: np.ndarray) -> np.ndarray:
        return np.asarray(as_array(fun(v.reshape(-1, 1)))).flatten().astype(float)

    root, info, ier, msg = _opt.fsolve(f, x0, full_output=True)
    return root.reshape(-1, 1)


def lsqnonneg(C: Any, d: Any) -> np.ndarray:
    x, _ = _opt.nnls(np.asarray(as_array(C)), np.asarray(as_array(d)).flatten())
    return x.reshape(-1, 1)


def fminunc(fun: Any, x0: Any) -> np.ndarray:
    x0 = np.asarray(as_array(x0)).flatten().astype(float)

    def f(v: np.ndarray) -> float:
        return float(fun(v.reshape(-1, 1)).reshape(-1)[0])

    res = _opt.minimize(f, x0, method="BFGS")
    return res.x.reshape(-1, 1)
