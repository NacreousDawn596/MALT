"""Elementary math, array construction, and reductions."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..errors import RuntimeError_
from .arrays import as_array, scalar_value

_ELEMENTWISE_UFUNCS: dict[str, Any] = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "asin": np.arcsin,
    "acos": np.arccos,
    "atan": np.arctan,
    "sinh": np.sinh,
    "cosh": np.cosh,
    "tanh": np.tanh,
    "exp": np.exp,
    "log": np.log,
    "log10": np.log10,
    "log2": np.log2,
    "sqrt": np.sqrt,
    "abs": np.abs,
    "real": np.real,
    "imag": np.imag,
    "conj": np.conj,
    "angle": np.angle,
    "floor": np.floor,
    "ceil": np.ceil,
    "round": np.round,
    "sign": np.sign,
}


def _ufunc(name: str):
    def call(x: Any) -> np.ndarray:
        a = as_array(x)
        if isinstance(a, str):
            raise RuntimeError_(f"{name} is not defined for strings")
        return _ELEMENTWISE_UFUNCS[name](a)

    call.__name__ = name
    return call


sin = _ufunc("sin")
cos = _ufunc("cos")
tan = _ufunc("tan")
asin = _ufunc("asin")
acos = _ufunc("acos")
atan = _ufunc("atan")
sinh = _ufunc("sinh")
cosh = _ufunc("cosh")
tanh = _ufunc("tanh")
exp = _ufunc("exp")
log = _ufunc("log")
log10 = _ufunc("log10")
log2 = _ufunc("log2")
sqrt = _ufunc("sqrt")
abs = _ufunc("abs")
real = _ufunc("real")
imag = _ufunc("imag")
conj = _ufunc("conj")
angle = _ufunc("angle")
floor = _ufunc("floor")
ceil = _ufunc("ceil")
sign = _ufunc("sign")


def _round_half_away(v: Any) -> Any:
    """MATLAB ``round``: ties are rounded away from zero (not banker's)."""
    return np.sign(v) * np.floor(np.abs(v) + 0.5)


def round(x: Any) -> np.ndarray:  # noqa: A001 - shadows builtin on purpose
    a = as_array(x)
    if isinstance(a, str):
        raise RuntimeError_("round is not defined for strings")
    if np.iscomplexobj(a):
        return _round_half_away(a.real) + 1j * _round_half_away(a.imag)
    return _round_half_away(a)


def atan2(y: Any, x: Any) -> np.ndarray:
    return np.arctan2(as_array(y), as_array(x))


def fix(x: Any) -> np.ndarray:
    """Round toward zero."""
    a = as_array(x)
    return np.where(a >= 0, np.floor(a), np.ceil(a))


def rem(a: Any, b: Any) -> np.ndarray:
    return np.remainder(as_array(a), as_array(b))


def mod(a: Any, b: Any) -> np.ndarray:
    return np.mod(as_array(a), as_array(b))


# ---------------------------------------------------------------------------
# Array construction
# ---------------------------------------------------------------------------


def zeros(*dims: Any) -> np.ndarray:
    shape = _shape_from_args(dims)
    return np.zeros(shape, dtype=float)


def ones(*dims: Any) -> np.ndarray:
    shape = _shape_from_args(dims)
    return np.ones(shape, dtype=float)


def _shape_from_args(dims: tuple[Any, ...]) -> tuple[int, ...]:
    if not dims:
        return (1, 1)
    if len(dims) == 1:
        a = as_array(dims[0])
        if a.size == 1:
            n = int(a.reshape(-1)[0])
            return (n, n)  # MATLAB: single scalar arg -> square matrix
        return tuple(int(v) for v in a.flatten())
    return tuple(int(scalar_value(d)) for d in dims)


def eye(*dims: Any) -> np.ndarray:
    if not dims:
        return np.eye(1)
    if len(dims) == 1:
        n = int(scalar_value(dims[0]))
        return np.eye(n)
    if len(dims) == 2:
        m = int(scalar_value(dims[0]))
        n = int(scalar_value(dims[1]))
        return np.eye(m, n)
    raise RuntimeError_("eye accepts at most two dimensions")


def rand(*dims: Any) -> np.ndarray:
    if not dims:
        return np.array([[np.random.rand()]])
    shape = tuple(int(scalar_value(d)) for d in dims)
    return np.random.rand(*shape)


def randn(*dims: Any) -> np.ndarray:
    if not dims:
        return np.array([[np.random.randn()]])
    shape = tuple(int(scalar_value(d)) for d in dims)
    return np.random.randn(*shape)


def rng(seed: Any) -> None:
    np.random.seed(int(scalar_value(seed)))


def reshape(A: Any, *dims: Any) -> np.ndarray:
    a = as_array(A)
    if len(dims) == 1:
        shape = tuple(int(v) for v in as_array(dims[0]).flatten())
    else:
        shape = tuple(int(scalar_value(d)) for d in dims)
    # column-major, matching MATLAB reshape
    return np.reshape(a, shape, order="F")


def repmat(A: Any, m: Any, n: Any | None = None) -> np.ndarray:
    a = as_array(A)
    m = int(scalar_value(m))
    n = int(scalar_value(n)) if n is not None else m
    return np.tile(a, (m, n))


def diag(A: Any, k: Any = 0) -> np.ndarray:
    a = as_array(A)
    k = int(scalar_value(k))
    if a.ndim == 2 and min(a.shape) > 1:
        return np.diag(a, k).reshape(-1, 1)
    return np.diag(a.flatten(), k)


def flipud(A: Any) -> np.ndarray:
    return np.flipud(as_array(A))


def fliplr(A: Any) -> np.ndarray:
    return np.fliplr(as_array(A))


# ---------------------------------------------------------------------------
# Reductions
# ---------------------------------------------------------------------------


def _reduce_dim(x: Any, dim: Any | None):
    a = as_array(x)
    if isinstance(a, str):
        raise RuntimeError_("reductions are not defined for strings")
    if dim is not None:
        d = int(scalar_value(dim)) - 1
    else:
        d = _first_non_singleton(a)
    return a, d


def _first_non_singleton(a: np.ndarray) -> int:
    """MATLAB reduces along the first dimension whose size is not 1 (a size-0
    dimension is non-singleton, so ``sum`` of an empty array is 0)."""
    for i in range(a.ndim):
        if a.shape[i] != 1:
            return i
    return 0


def sum_(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.sum(a, axis=d, keepdims=True)


def prod(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.prod(a, axis=d, keepdims=True)


def mean(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.mean(a, axis=d, keepdims=True)


def min_(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.min(a, axis=d, keepdims=True)


def max_(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.max(a, axis=d, keepdims=True)


def cumsum(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.cumsum(a, axis=d)


def cumprod(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.cumprod(a, axis=d)


def sort(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.sort(a, axis=d)


def any_(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.any(a, axis=d, keepdims=True).astype(float)


def all_(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.all(a, axis=d, keepdims=True).astype(float)
