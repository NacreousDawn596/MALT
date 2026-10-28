"""MATLAB-compatible array core: shape conventions, construction, colon."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ..errors import RuntimeError_


def as_array(x: Any) -> Any:
    """Normalize a value into MATLAB-visible form.

    Numeric scalars and arrays are promoted to at least 2-D numpy arrays with
    MATLAB shape conventions (scalars are 1x1, vectors keep their orientation).
    Strings and function handles pass through untouched.
    """
    if isinstance(x, str):
        return x
    if callable(x) and not isinstance(x, np.ndarray):
        return x
    if isinstance(x, np.ndarray):
        if x.ndim == 0:
            return x.reshape(1, 1)
        if x.ndim == 1:
            return x.reshape(1, -1)
        return x
    if isinstance(x, (list, tuple)):
        arr = np.asarray(x)
        if arr.dtype == object:
            return arr
        if arr.ndim == 0:
            return arr.reshape(1, 1)
        if arr.ndim == 1:
            return arr.reshape(1, -1)
        return arr
    if isinstance(x, complex):
        return np.array([[x]], dtype=complex)
    if isinstance(x, (bool, np.bool_)):
        return np.array([[1.0 if x else 0.0]])
    if isinstance(x, (int, float, np.integer, np.floating)):
        return np.array([[float(x)]])
    return x


def is_string(x: Any) -> bool:
    return isinstance(x, str)


def is_scalar(x: Any) -> bool:
    a = as_array(x)
    if isinstance(a, str):
        return False
    return a.size == 1


def is_logical(x: Any) -> bool:
    a = as_array(x)
    if isinstance(a, str):
        return False
    return a.dtype == bool


def numel(x: Any) -> np.ndarray:
    a = as_array(x)
    if isinstance(a, str):
        return np.array([[len(a)]], dtype=float)
    return np.array([[a.size]], dtype=float)


def ndims(x: Any) -> np.ndarray:
    a = as_array(x)
    if isinstance(a, str):
        return np.array([[2]], dtype=float)
    return np.array([[max(2, a.ndim)]], dtype=float)


def size(x: Any, *dims: Any) -> np.ndarray:
    a = as_array(x)
    if isinstance(a, str):
        shp = (1, len(a))
    else:
        shp = a.shape
    if len(dims) == 0:
        if a.ndim < 2 and not isinstance(a, str):
            shp = (1, 1) if a.size == 0 or a.ndim == 0 else shp
        # MATLAB always reports at least two dimensions for matrices
        if len(shp) < 2:
            shp = shp + (1,)
        return np.array([shp], dtype=float)
    if len(dims) == 1:
        d = int(scalar_value(dims[0]))
        if 1 <= d <= len(shp):
            return np.array([[float(shp[d - 1])]])
        return np.array([[1.0]])
    out = []
    for d in dims:
        d = int(scalar_value(d))
        out.append(float(shp[d - 1]) if 1 <= d <= len(shp) else 1.0)
    return np.array([out], dtype=float)


def length(x: Any) -> np.ndarray:
    a = as_array(x)
    if isinstance(a, str):
        return np.array([[len(a)]], dtype=float)
    if a.ndim < 2:
        return np.array([[a.size]], dtype=float)
    return np.array([[float(max(a.shape))]])


def scalar_value(x: Any) -> Any:
    a = as_array(x)
    if isinstance(a, str):
        raise RuntimeError_("expected a numeric scalar")
    if a.size != 1:
        raise RuntimeError_("expected a scalar, got a non-scalar array")
    v = a.reshape(-1)[0]
    return v.item() if hasattr(v, "item") else v


def _scalar(x: Any) -> Any:
    return scalar_value(x)


def matrix(rows: list[list[Any]]) -> np.ndarray:
    """Build a MATLAB matrix from a list of row lists (each a list of values)."""
    if not rows:
        return np.empty((0, 0))
    built_rows = []
    for row in rows:
        if not row:
            continue
        items = [as_array(v) for v in row]
        built_rows.append(np.hstack(items))
    if not built_rows:
        return np.empty((0, 0))
    return np.vstack(built_rows)


def hcat(*items: Any) -> np.ndarray:
    arrs = [as_array(x) for x in items]
    return np.hstack(arrs)


def vcat(*items: Any) -> np.ndarray:
    arrs = [as_array(x) for x in items]
    return np.vstack(arrs)


def colon(start: Any, step_end: Any, end: Any | None = None) -> np.ndarray:
    """MATLAB colon operator: ``a:b`` or ``a:s:b``.

    Returns a row vector. Empty results are 1x0.
    """
    if end is None:
        a = _scalar(start)
        s = 1.0
        b = _scalar(step_end)
    else:
        a = _scalar(start)
        s = _scalar(step_end)
        b = _scalar(end)

    a = float(np.real(a) if isinstance(a, complex) else a)
    s = float(np.real(s) if isinstance(s, complex) else s)
    b = float(np.real(b) if isinstance(b, complex) else b)

    if s == 0.0:
        raise RuntimeError_("colon step must be nonzero")

    if s > 0:
        if b < a:
            return np.empty((1, 0))
    else:
        if b > a:
            return np.empty((1, 0))

    n = int(math.floor((b - a) / s + 1e-12)) + 1
    if n <= 0:
        return np.empty((1, 0))
    vals = a + np.arange(n, dtype=float) * s
    # Correct any floating-point overshoot so the endpoint is exact.
    if s > 0:
        vals = np.minimum(vals, b)
    else:
        vals = np.maximum(vals, b)
    return vals.reshape(1, -1)


def is_true(x: Any) -> bool:
    """MATLAB ``if`` condition: scalar truthiness (nonzero is true)."""
    a = as_array(x)
    if isinstance(a, str):
        return len(a) > 0
    if a.size != 1:
        raise RuntimeError_(
            "condition must be a scalar; use any()/all() for array conditions"
        )
    v = a.reshape(-1)[0]
    if isinstance(v, complex):
        return v.real != 0 or v.imag != 0
    return bool(v != 0)


def to_bool(x: Any) -> np.ndarray:
    a = as_array(x)
    if isinstance(a, str):
        raise RuntimeError_("cannot convert string to logical")
    return (a != 0).astype(float)


def isequal(a: Any, b: Any, *rest: Any) -> np.ndarray:
    def eq(x: Any, y: Any) -> bool:
        xa = as_array(x)
        ya = as_array(y)
        if isinstance(xa, str) or isinstance(ya, str):
            return xa == ya
        if xa.shape != ya.shape:
            return False
        return bool(np.all(xa == ya))

    if not eq(a, b):
        return np.array([[0.0]])
    for r in rest:
        if not eq(a, r):
            return np.array([[0.0]])
    return np.array([[1.0]])


def for_columns(x: Any):
    """Yield the columns of an array, matching MATLAB ``for`` iteration."""
    a = as_array(x)
    if isinstance(a, str):
        yield a
        return
    if a.ndim < 2:
        a = a.reshape(1, -1)
    ncols = a.shape[1] if a.ndim >= 2 else 1
    for j in range(ncols):
        yield a[:, j].reshape(a.shape[0], 1) if a.ndim >= 2 else a[j].reshape(1, 1)


def linspace(a: Any, b: Any, n: Any = 100) -> np.ndarray:
    a = float(_scalar(a))
    b = float(_scalar(b))
    n = int(_scalar(n))
    if n < 1:
        return np.empty((1, 0))
    if n == 1:
        return np.array([[b]], dtype=float)
    return np.linspace(a, b, n).reshape(1, -1)


def logspace(a: Any, b: Any, n: Any = 50) -> np.ndarray:
    a = float(_scalar(a))
    b = float(_scalar(b))
    n = int(_scalar(n))
    return np.logspace(a, b, n).reshape(1, -1)


def meshgrid(x: Any, y: Any) -> tuple[np.ndarray, np.ndarray]:
    xa = as_array(x).flatten()
    ya = as_array(y).flatten()
    X, Y = np.meshgrid(xa, ya)
    return X, Y


def peaks(n: Any = 49) -> np.ndarray:
    n = int(_scalar(n))
    x = np.linspace(-3, 3, n)
    y = np.linspace(-3, 3, n)
    X, Y = np.meshgrid(x, y)
    Z = (
        3 * (1 - X) ** 2 * np.exp(-(X**2) - (Y + 1) ** 2)
        - 10 * (X / 5 - X**3 - Y**5) * np.exp(-(X**2) - Y**2)
        - 1 / 3 * np.exp(-((X + 1) ** 2) - Y**2)
    )
    return Z
