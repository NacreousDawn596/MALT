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
# Additional trigonometry
# ---------------------------------------------------------------------------


def _deg(fn, x):
    a = as_array(x)
    return fn(np.deg2rad(a))


def sind(x: Any) -> np.ndarray:
    return _deg(np.sin, x)


def cosd(x: Any) -> np.ndarray:
    return _deg(np.cos, x)


def tand(x: Any) -> np.ndarray:
    return _deg(np.tan, x)


def asind(x: Any) -> np.ndarray:
    return np.rad2deg(np.arcsin(as_array(x)))


def acosd(x: Any) -> np.ndarray:
    return np.rad2deg(np.arccos(as_array(x)))


def atand(x: Any) -> np.ndarray:
    return np.rad2deg(np.arctan(as_array(x)))


def atan2d(y: Any, x: Any) -> np.ndarray:
    return np.rad2deg(np.arctan2(as_array(y), as_array(x)))


def sec(x: Any) -> np.ndarray:
    return 1.0 / np.cos(as_array(x))


def csc(x: Any) -> np.ndarray:
    return 1.0 / np.sin(as_array(x))


def cot(x: Any) -> np.ndarray:
    return 1.0 / np.tan(as_array(x))


def asec(x: Any) -> np.ndarray:
    return np.arccos(1.0 / as_array(x))


def acsc(x: Any) -> np.ndarray:
    return np.arcsin(1.0 / as_array(x))


def acot(x: Any) -> np.ndarray:
    return np.arctan(1.0 / as_array(x))


def asinh(x: Any) -> np.ndarray:
    return np.arcsinh(as_array(x))


def acosh(x: Any) -> np.ndarray:
    return np.arccosh(as_array(x))


def atanh(x: Any) -> np.ndarray:
    return np.arctanh(as_array(x))


def deg2rad(x: Any) -> np.ndarray:
    return np.deg2rad(as_array(x))


def rad2deg(x: Any) -> np.ndarray:
    return np.rad2deg(as_array(x))


def unwrap(p: Any) -> np.ndarray:
    return np.unwrap(as_array(p))


def cplxpair(a: Any) -> np.ndarray:
    x = np.asarray(as_array(a), dtype=complex).reshape(-1)
    reals = sorted(float(v.real) for v in x if abs(v.imag) < 1e-12)
    pairs = sorted(
        ((float(v.real), float(v.imag)) for v in x if abs(v.imag) >= 1e-12),
        key=lambda t: (t[0], abs(t[1])),
    )
    out: list[complex] = list(reals)
    for r, i in pairs:
        out.extend([r + 1j * i, r - 1j * i])
    return np.asarray(out, dtype=complex).reshape(-1, 1)


def complex_(a: Any, b: Any = None) -> np.ndarray:  # noqa: A001 - MATLAB name
    if b is None:
        return as_array(a).astype(complex)
    return np.asarray(as_array(a)) + 1j * np.asarray(as_array(b))


# ---------------------------------------------------------------------------
# Powers and roots
# ---------------------------------------------------------------------------


def cbrt(x: Any) -> np.ndarray:
    return np.cbrt(as_array(x))


def realsqrt(x: Any) -> np.ndarray:
    a = as_array(x)
    if np.iscomplexobj(a):
        raise RuntimeError_("realsqrt produces complex results")
    return np.sqrt(a)


def reallog(x: Any) -> np.ndarray:
    a = as_array(x)
    if np.iscomplexobj(a):
        raise RuntimeError_("reallog produces complex results")
    return np.log(a)


def hypot(a: Any, b: Any) -> np.ndarray:
    return np.hypot(as_array(a), as_array(b))


def expm1(x: Any) -> np.ndarray:
    return np.expm1(as_array(x))


def log1p(x: Any) -> np.ndarray:
    return np.log1p(as_array(x))


def nthroot(x: Any, n: Any) -> np.ndarray:
    a = np.asarray(as_array(x), dtype=float)
    n = int(scalar_value(n))
    return np.sign(a) * np.abs(a) ** (1.0 / n)


# ---------------------------------------------------------------------------
# Integer and combinatorial math
# ---------------------------------------------------------------------------


def idivide(a: Any, b: Any, opt: Any = None) -> np.ndarray:
    x = np.asarray(as_array(a), dtype=float)
    y = np.asarray(as_array(b), dtype=float)
    mode = "fix" if opt is None else str(as_array(opt)).lower()
    if mode == "floor":
        return np.floor_divide(x, y)
    if mode == "ceil":
        return -np.floor_divide(-x, y)
    if mode == "round":
        return _round_half_away(x / y)
    return np.trunc(x / y)


def gcd(a: Any, b: Any) -> np.ndarray:
    return np.asarray(np.gcd(np.asarray(as_array(a), dtype=int), np.asarray(as_array(b), dtype=int)), dtype=float)


def lcm(a: Any, b: Any) -> np.ndarray:
    return np.asarray(np.lcm(np.asarray(as_array(a), dtype=int), np.asarray(as_array(b), dtype=int)), dtype=float)


def factorial(n: Any) -> np.ndarray:
    from scipy import special as _sp

    a = as_array(n)
    return np.asarray(_sp.factorial(a), dtype=float)


def nchoosek(n: Any, k: Any) -> np.ndarray:
    from scipy import special as _sp

    a = as_array(n)
    if a.size == 1:
        kk = int(scalar_value(k))
        return np.asarray(_sp.comb(int(a.reshape(-1)[0]), kk, exact=True), dtype=float).reshape(1, 1)
    kk = int(scalar_value(k))
    from itertools import combinations

    rows = [list(c) for c in combinations(a.flatten(), kk)]
    if not rows:
        return np.empty((0, kk))
    return np.asarray(rows, dtype=float)


def perms(v: Any) -> np.ndarray:
    from itertools import permutations

    a = np.asarray(as_array(v)).reshape(-1)
    return np.asarray(list(permutations(a)), dtype=float)


def _sieve(n: int) -> list[int]:
    if n < 2:
        return []
    flags = [True] * (n + 1)
    flags[0] = flags[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if flags[i]:
            flags[i * i : n + 1 : i] = [False] * len(range(i * i, n + 1, i))
    return [i for i, f in enumerate(flags) if f]


def primes(n: Any) -> np.ndarray:
    return np.asarray(_sieve(int(scalar_value(n))), dtype=float).reshape(1, -1)


def _is_prime_scalar(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def isprime(x: Any) -> np.ndarray:
    a = np.asarray(as_array(x), dtype=int).flatten()
    return np.asarray([1.0 if _is_prime_scalar(int(v)) else 0.0 for v in a]).reshape(1, -1)


def factor(n: Any) -> np.ndarray:
    x = int(scalar_value(n))
    out: list[float] = []
    d = 2
    while d * d <= x:
        while x % d == 0:
            out.append(float(d))
            x //= d
        d += 1 if d == 2 else 2
    if x > 1:
        out.append(float(x))
    return np.asarray(out, dtype=float).reshape(1, -1)


# ---------------------------------------------------------------------------
# Additional reductions and shape helpers
# ---------------------------------------------------------------------------


def cummax(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.maximum.accumulate(a, axis=d)


def cummin(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.minimum.accumulate(a, axis=d)


def diff(x: Any, n: Any = 1, dim: Any = None) -> np.ndarray:
    a = as_array(x)
    n = int(scalar_value(n))
    if dim is None:
        dim = _first_non_singleton(a) + 1
    d = int(scalar_value(dim)) - 1
    for _ in range(n):
        a = np.diff(a, axis=d)
    return a


def maxk(A: Any, k: Any) -> np.ndarray:
    a = np.asarray(as_array(A)).flatten()
    k = int(scalar_value(k))
    idx = np.argsort(-a)[:k]
    return np.asarray(a[idx]).reshape(1, -1)


def mink(A: Any, k: Any) -> np.ndarray:
    a = np.asarray(as_array(A)).flatten()
    k = int(scalar_value(k))
    idx = np.argsort(a)[:k]
    return np.asarray(a[idx]).reshape(1, -1)


def bounds(A: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(A, dim)
    return np.asarray([np.min(a, axis=d, keepdims=True), np.max(a, axis=d, keepdims=True)])


def range_(A: Any, dim: Any | None = None) -> np.ndarray:  # noqa: A001 - MATLAB name
    a, d = _reduce_dim(A, dim)
    return np.max(a, axis=d, keepdims=True) - np.min(a, axis=d, keepdims=True)


def rescale(A: Any, lo: Any = 0, hi: Any = 1) -> np.ndarray:
    a = np.asarray(as_array(A), dtype=float)
    lo_v = float(scalar_value(lo))
    hi_v = float(scalar_value(hi))
    amin, amax = a.min(), a.max()
    if amax == amin:
        return np.full_like(a, (lo_v + hi_v) / 2)
    return lo_v + (a - amin) * (hi_v - lo_v) / (amax - amin)


def normalize(A: Any, p: Any = None) -> np.ndarray:
    a = np.asarray(as_array(A), dtype=float)
    if p is None:
        n = np.linalg.norm(a, 2)
    else:
        n = np.linalg.norm(a, float(scalar_value(p)))
    return a / n if n != 0 else a


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
