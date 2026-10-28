"""MATLAB operator semantics, implemented explicitly on top of NumPy.

Scalar-scalar operations take a fast path that uses native Python arithmetic
and returns a native Python scalar, avoiding the per-operation allocation of a
1x1 NumPy array. ``as_array`` re-wraps values at the semantic boundaries
(display, indexing, size, function calls, matrix construction), preserving
MATLAB-visible behaviour.
"""

from __future__ import annotations

import operator as _pyop
from typing import Any

import numpy as np

from ..errors import DimensionError, RuntimeError_
from .arrays import _config, as_array, is_scalar_like, py_scalar

# Native Python numeric types that flow through scalar fast paths.
_NATIVE = (int, float, complex)

# Python-native operators for the scalar fast path. The keys are the same
# operator names used by ``_binop``; operands are already swapped for ``.\``.
_PYOP = {
    "+": _pyop.add,
    "-": _pyop.sub,
    ".*": _pyop.mul,
    "./": _pyop.truediv,
    ".\\": _pyop.truediv,
    ".^": _pyop.pow,
    "==": _pyop.eq,
    "~=": _pyop.ne,
    "<": _pyop.lt,
    "<=": _pyop.le,
    ">": _pyop.gt,
    ">=": _pyop.ge,
}


def _arith_binop(a: Any, b: Any, f: Any, opname: str) -> Any:
    """Element-wise arithmetic: native scalar result for scalar operands."""
    if _config.optimized and is_scalar_like(a) and is_scalar_like(b):
        return _PYOP[opname](py_scalar(a), py_scalar(b))
    xa = as_array(a)
    xb = as_array(b)
    if isinstance(xa, str) or isinstance(xb, str):
        raise RuntimeError_(f"operator '{opname}' is not defined for strings")
    try:
        return f(xa, xb)
    except ValueError as e:
        raise DimensionError(f"dimension mismatch in {opname}: {e}") from e


def _cmp_binop(a: Any, b: Any, f: Any, opname: str) -> Any:
    """Comparison: returns 1.0/0.0 for scalars, float array otherwise."""
    if _config.optimized and is_scalar_like(a) and is_scalar_like(b):
        return 1.0 if _PYOP[opname](py_scalar(a), py_scalar(b)) else 0.0
    return _arith_binop(a, b, f, opname).astype(float)  # type: ignore[union-attr]


def plus(a: Any, b: Any) -> Any:
    if _config.optimized and isinstance(a, _NATIVE) and isinstance(b, _NATIVE):
        return a + b
    return _arith_binop(a, b, np.add, "+")


def minus(a: Any, b: Any) -> Any:
    if _config.optimized and isinstance(a, _NATIVE) and isinstance(b, _NATIVE):
        return a - b
    return _arith_binop(a, b, np.subtract, "-")


def uneg(a: Any) -> Any:
    if _config.optimized and isinstance(a, _NATIVE):
        return -a
    if _config.optimized and is_scalar_like(a):
        return -py_scalar(a)
    return -as_array(a)


def uplus(a: Any) -> Any:
    return a


def logical_not(a: Any) -> Any:
    if _config.optimized and isinstance(a, _NATIVE):
        return 0.0 if a != 0 else 1.0
    if _config.optimized and is_scalar_like(a):
        return 0.0 if py_scalar(a) != 0 else 1.0
    return (as_array(a) == 0).astype(float)


def times(a: Any, b: Any) -> Any:
    """Element-wise multiplication ``.*``."""
    if _config.optimized and isinstance(a, _NATIVE) and isinstance(b, _NATIVE):
        return a * b
    return _arith_binop(a, b, np.multiply, ".*")


def rdivide(a: Any, b: Any) -> Any:
    """Element-wise right division ``./``."""
    if _config.optimized and isinstance(a, _NATIVE) and isinstance(b, _NATIVE):
        return a / b
    return _arith_binop(a, b, np.divide, "./")


def ldivide(a: Any, b: Any) -> Any:
    """Element-wise left division ``.\\`` (b ./ a)."""
    if _config.optimized and isinstance(a, _NATIVE) and isinstance(b, _NATIVE):
        return b / a
    return _arith_binop(b, a, np.divide, ".\\")


def mtimes(a: Any, b: Any) -> Any:
    """Matrix multiplication ``*`` with scalar expansion."""
    if _config.optimized and isinstance(a, _NATIVE) and isinstance(b, _NATIVE):
        return a * b
    if _config.optimized and is_scalar_like(a) and is_scalar_like(b):
        return py_scalar(a) * py_scalar(b)
    xa = as_array(a)
    xb = as_array(b)
    if xa.size == 1 or xb.size == 1:
        return np.multiply(xa, xb)
    try:
        return np.matmul(xa, xb)
    except ValueError as e:
        raise DimensionError(f"inner matrix dimensions must agree in *: {e}") from e


def mldivide(a: Any, b: Any) -> Any:
    """MATLAB left division ``A \\ b`` (solve)."""
    if _config.optimized and isinstance(a, _NATIVE) and isinstance(b, _NATIVE):
        return b / a
    if _config.optimized and is_scalar_like(a) and is_scalar_like(b):
        return py_scalar(b) / py_scalar(a)
    xa = as_array(a)
    xb = as_array(b)
    if xa.size == 1:
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


def mrdivide(a: Any, b: Any) -> Any:
    """MATLAB right division ``A / B`` (solve A = X B, i.e. X = A * inv(B))."""
    if _config.optimized and isinstance(a, _NATIVE) and isinstance(b, _NATIVE):
        return a / b
    if _config.optimized and is_scalar_like(a) and is_scalar_like(b):
        return py_scalar(a) / py_scalar(b)
    xa = as_array(a)
    xb = as_array(b)
    if xb.size == 1:
        return np.divide(xa, xb)
    return mldivide(xb.conj().T, xa.conj().T).conj().T


def mpower(a: Any, b: Any) -> Any:
    """Matrix power ``^`` (scalar power for scalars)."""
    if _config.optimized and isinstance(a, _NATIVE) and isinstance(b, _NATIVE):
        return a**b
    if _config.optimized and is_scalar_like(a) and is_scalar_like(b):
        return py_scalar(a) ** py_scalar(b)
    xa = as_array(a)
    xb = as_array(b)
    if xb.size == 1:
        e = xb.reshape(-1)[0]
        if isinstance(e, complex) or float(e) != int(e):
            raise RuntimeError_("matrix power requires an integer exponent")
        return np.linalg.matrix_power(xa, int(np.real(e)))
    raise RuntimeError_("matrix power with matrix exponent is not supported")


def power(a: Any, b: Any) -> Any:
    """Element-wise power ``.^``."""
    if _config.optimized and isinstance(a, _NATIVE) and isinstance(b, _NATIVE):
        return a**b
    return _arith_binop(a, b, np.power, ".^")


def ctranspose(a: Any) -> Any:
    """Conjugate transpose ``'``."""
    if _config.optimized and is_scalar_like(a):
        return np.conj(py_scalar(a))
    return as_array(a).conj().T


def transpose(a: Any) -> Any:
    """Non-conjugating transpose ``.'``."""
    if _config.optimized and is_scalar_like(a):
        return py_scalar(a)
    return as_array(a).T


def eq(a: Any, b: Any) -> Any:
    return _cmp_binop(a, b, np.equal, "==")


def ne(a: Any, b: Any) -> Any:
    return _cmp_binop(a, b, np.not_equal, "~=")


def lt(a: Any, b: Any) -> Any:
    return _cmp_binop(a, b, np.less, "<")


def le(a: Any, b: Any) -> Any:
    return _cmp_binop(a, b, np.less_equal, "<=")


def gt(a: Any, b: Any) -> Any:
    return _cmp_binop(a, b, np.greater, ">")


def ge(a: Any, b: Any) -> Any:
    return _cmp_binop(a, b, np.greater_equal, ">=")


def and_(a: Any, b: Any) -> Any:
    if _config.optimized and is_scalar_like(a) and is_scalar_like(b):
        return 1.0 if (py_scalar(a) != 0 and py_scalar(b) != 0) else 0.0
    xa = as_array(a)
    xb = as_array(b)
    return ((xa != 0) & (xb != 0)).astype(float)


def or_(a: Any, b: Any) -> Any:
    if _config.optimized and is_scalar_like(a) and is_scalar_like(b):
        return 1.0 if (py_scalar(a) != 0 or py_scalar(b) != 0) else 0.0
    xa = as_array(a)
    xb = as_array(b)
    return ((xa != 0) | (xb != 0)).astype(float)


def short_and(a: Any, b: Any) -> Any:
    return and_(a, b)


def short_or(a: Any, b: Any) -> Any:
    return or_(a, b)
