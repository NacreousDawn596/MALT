"""MATLAB operator semantics, implemented explicitly on top of NumPy."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..errors import DimensionError, RuntimeError_
from .arrays import as_array, is_scalar


def _binop(a: Any, b: Any, f: Any, opname: str) -> np.ndarray:
    xa = as_array(a)
    xb = as_array(b)
    if isinstance(xa, str) or isinstance(xb, str):
        raise RuntimeError_(f"operator '{opname}' is not defined for strings")
    try:
        return f(xa, xb)
    except ValueError as e:
        raise DimensionError(f"dimension mismatch in {opname}: {e}") from e


def plus(a: Any, b: Any) -> np.ndarray:
    return _binop(a, b, np.add, "+")


def minus(a: Any, b: Any) -> np.ndarray:
    return _binop(a, b, np.subtract, "-")


def uneg(a: Any) -> np.ndarray:
    xa = as_array(a)
    return -xa


def uplus(a: Any) -> np.ndarray:
    return as_array(a)


def logical_not(a: Any) -> np.ndarray:
    xa = as_array(a)
    return (xa == 0).astype(float)


def times(a: Any, b: Any) -> np.ndarray:
    """Element-wise multiplication ``.*``."""
    return _binop(a, b, np.multiply, ".*")


def rdivide(a: Any, b: Any) -> np.ndarray:
    """Element-wise right division ``./``."""
    return _binop(a, b, np.divide, "./")


def ldivide(a: Any, b: Any) -> np.ndarray:
    """Element-wise left division ``.\\`` (b ./ a)."""
    return _binop(b, a, np.divide, ".\\")


def mtimes(a: Any, b: Any) -> np.ndarray:
    """Matrix multiplication ``*`` with scalar expansion."""
    xa = as_array(a)
    xb = as_array(b)
    if is_scalar(xa) or is_scalar(xb):
        return np.multiply(xa, xb)
    try:
        return np.matmul(xa, xb)
    except ValueError as e:
        raise DimensionError(f"inner matrix dimensions must agree in *: {e}") from e


def mldivide(a: Any, b: Any) -> np.ndarray:
    """MATLAB left division ``A \\ b`` (solve)."""
    xa = as_array(a)
    xb = as_array(b)
    if is_scalar(xa):
        return np.divide(xb, xa)
    if xa.ndim == 2 and xb.ndim == 2:
        if xa.shape[0] == xa.shape[1]:
            try:
                return np.linalg.solve(xa, xb)
            except np.linalg.LinAlgError:
                # singular: fall through to least squares (MATLAB-like warning)
                return np.linalg.lstsq(xa, xb, rcond=None)[0]
        return np.linalg.lstsq(xa, xb, rcond=None)[0]
    raise DimensionError("left division requires 2-D operands")


def mrdivide(a: Any, b: Any) -> np.ndarray:
    """MATLAB right division ``A / B`` (solve A = X B, i.e. X = A * inv(B))."""
    xa = as_array(a)
    xb = as_array(b)
    if is_scalar(xb):
        return np.divide(xa, xb)
    return mldivide(xb.conj().T, xa.conj().T).conj().T


def mpower(a: Any, b: Any) -> np.ndarray:
    """Matrix power ``^`` (scalar power for scalars)."""
    xa = as_array(a)
    xb = as_array(b)
    if is_scalar(xa) and is_scalar(xb):
        return np.array([[xa.reshape(-1)[0] ** xb.reshape(-1)[0]]])
    if is_scalar(xb):
        e = xb.reshape(-1)[0]
        if isinstance(e, complex) or float(e) != int(e):
            raise RuntimeError_("matrix power requires an integer exponent")
        return np.linalg.matrix_power(xa, int(np.real(e)))
    raise RuntimeError_("matrix power with matrix exponent is not supported")


def power(a: Any, b: Any) -> np.ndarray:
    """Element-wise power ``.^``."""
    return _binop(a, b, np.power, ".^")


def ctranspose(a: Any) -> np.ndarray:
    """Conjugate transpose ``'``."""
    xa = as_array(a)
    return xa.conj().T


def transpose(a: Any) -> np.ndarray:
    """Non-conjugating transpose ``.'``."""
    xa = as_array(a)
    return xa.T


def eq(a: Any, b: Any) -> np.ndarray:
    return (_binop(a, b, np.equal, "==")).astype(float)


def ne(a: Any, b: Any) -> np.ndarray:
    return (_binop(a, b, np.not_equal, "~=")).astype(float)


def lt(a: Any, b: Any) -> np.ndarray:
    return (_binop(a, b, np.less, "<")).astype(float)


def le(a: Any, b: Any) -> np.ndarray:
    return (_binop(a, b, np.less_equal, "<=")).astype(float)


def gt(a: Any, b: Any) -> np.ndarray:
    return (_binop(a, b, np.greater, ">")).astype(float)


def ge(a: Any, b: Any) -> np.ndarray:
    return (_binop(a, b, np.greater_equal, ">=")).astype(float)


def and_(a: Any, b: Any) -> np.ndarray:
    xa = as_array(a)
    xb = as_array(b)
    return ((xa != 0) & (xb != 0)).astype(float)


def or_(a: Any, b: Any) -> np.ndarray:
    xa = as_array(a)
    xb = as_array(b)
    return ((xa != 0) | (xb != 0)).astype(float)


def short_and(a: Any, b: Any) -> np.ndarray:
    return and_(a, b)


def short_or(a: Any, b: Any) -> np.ndarray:
    return or_(a, b)
