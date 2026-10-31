"""MATLAB-compatible array core: shape conventions, construction, colon."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ..errors import RuntimeError_


class _Config:
    __slots__ = ("optimized",)

    def __init__(self) -> None:
        self.optimized = True


# Mutable holder so the optimization flag is read live by other runtime modules
# (importing a plain bool would snapshot its value).
_config = _Config()


def set_optimization_level(level: int) -> None:
    _config.optimized = level >= 1


def as_array(x: Any) -> Any:
    """Normalize a value into MATLAB-visible form.

    Numeric scalars and arrays are promoted to at least 2-D numpy arrays with
    MATLAB shape conventions (scalars are 1x1, vectors keep their orientation).
    Strings and function handles pass through untouched.

    The common case (an existing 2-D ndarray) is checked first so that scalar
    arithmetic in tight loops does not pay for the string/callable/type checks.
    """
    if isinstance(x, np.ndarray):
        if x.ndim == 2:
            return x
        if x.ndim == 0:
            return x.reshape(1, 1)
        if x.ndim == 1:
            return x.reshape(1, -1)
        return x
    if isinstance(x, str):
        return x
    if callable(x):
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


def is_scalar_like(x: Any) -> bool:
    """True for native Python numbers and 0-d/1x1 NumPy arrays."""
    if isinstance(x, np.ndarray):
        return x.size == 1
    if isinstance(x, str):
        return False
    return isinstance(x, (int, float, complex, bool, np.number))


def py_scalar(x: Any) -> Any:
    """Extract a native Python scalar from a scalar-like value (no copy)."""
    if isinstance(x, np.ndarray):
        if x.ndim == 2 and x.shape == (1, 1):
            return x[0, 0]
        if x.ndim == 0:
            return x.item()
        return x.reshape(-1)[0].item()
    if isinstance(x, np.generic):
        return x.item()
    return x


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
    """Yield the columns of an array, matching MATLAB ``for`` iteration.

    Row vectors yield native Python scalars (one per element) so that scalar
    loop bodies avoid per-iteration 1x1 array allocation.
    """
    a = as_array(x)
    if isinstance(a, str):
        yield a
        return
    if a.ndim == 2 and a.shape[0] == 1:
        if _config.optimized:
            # Row vector: yield each element as a native Python scalar.
            for v in a[0].tolist():
                yield v
            return
        for j in range(a.shape[1]):
            yield a[:, j : j + 1]
        return
    if a.ndim == 2:
        for j in range(a.shape[1]):
            yield a[:, j].reshape(a.shape[0], 1)
        return
    if a.ndim < 2:
        a = a.reshape(1, -1)
        for v in a[0].tolist():
            yield v
        return
    for j in range(a.shape[1]):
        yield a[:, j].reshape(a.shape[0], 1)


def for_init() -> np.ndarray:
    """Empty row vector used to initialize a loop variable before a ``for``.

    MATLAB assigns the loop variable to the empty array when a loop iterates
    zero times, so the variable is pre-bound to an empty value in all cases.
    """
    return np.empty((1, 0))


def _as_int(x: Any) -> int | None:
    """Return the integer value of ``x`` if it is integer-valued, else None."""
    if isinstance(x, np.ndarray):
        if x.size != 1:
            return None
        x = x.reshape(-1)[0]
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return int(x) if x.is_integer() else None
    if isinstance(x, complex):
        return int(x.real) if (x.imag == 0 and x.real.is_integer()) else None
    return None


def jit_for(acc: Any, start: Any, step: Any, end: Any, body: Any) -> tuple[Any, Any]:
    """Runtime-specialized loop used by JIT-compiled scalar reductions.

    Iterates the MATLAB colon range ``start:step:end``, applying ``body(acc, k)``
    each iteration. Integer ranges use Python ``range``; non-integer ranges fall
    back to ``colon`` + ``for_columns``. Returns ``(acc, last_k)`` where
    ``last_k`` is a native scalar (matching ``for_columns``) or an empty array
    for an empty range.
    """
    s = _as_int(start)
    t = _as_int(step)
    e = _as_int(end)
    if s is not None and t is not None and e is not None and t != 0:
        last: int | None = None
        if t > 0:
            for k in range(s, e + 1, t):
                acc = body(acc, k)
                last = k
        else:
            for k in range(s, e - 1, t):
                acc = body(acc, k)
                last = k
        return acc, (float(last) if last is not None else np.empty((1, 0)))
    # General fallback with MATLAB colon semantics.
    last = None
    for k in for_columns(colon(start, step, end)):
        acc = body(acc, k)
        last = k
    return acc, (last if last is not None else np.empty((1, 0)))


def jit_loop(accs: tuple, start: Any, step: Any, end: Any, body: Any) -> tuple[Any, Any]:
    """Multi-accumulator JIT loop.

    ``accs`` is a tuple of accumulator values; ``body(*accs, k)`` returns the
    updated tuple. Returns ``(accs, last_k)``, where ``last_k`` is a native
    scalar or an empty array for an empty range.
    """
    s = _as_int(start)
    t = _as_int(step)
    e = _as_int(end)
    if s is not None and t is not None and e is not None and t != 0:
        last: int | None = None
        if t > 0:
            for k in range(s, e + 1, t):
                accs = body(*accs, k)
                last = k
        else:
            for k in range(s, e - 1, t):
                accs = body(*accs, k)
                last = k
        return accs, (float(last) if last is not None else np.empty((1, 0)))
    last = None
    for k in for_columns(colon(start, step, end)):
        accs = body(*accs, k)
        last = k
    return accs, (last if last is not None else np.empty((1, 0)))


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


# ---------------------------------------------------------------------------
# Matrix and array manipulation (MATLAB-compatible subset)
# ---------------------------------------------------------------------------


def triu(A: Any, k: Any = 0) -> np.ndarray:
    return np.triu(as_array(A), int(_scalar(k)))


def tril(A: Any, k: Any = 0) -> np.ndarray:
    return np.tril(as_array(A), int(_scalar(k)))


def kron(A: Any, B: Any) -> np.ndarray:
    return np.kron(as_array(A), as_array(B))


def rot90(A: Any, k: Any = 1) -> np.ndarray:
    return np.rot90(as_array(A), int(_scalar(k)))


def flip(A: Any, dim: Any = None) -> np.ndarray:
    a = as_array(A)
    if dim is None:
        return np.flip(a)
    return np.flip(a, axis=int(_scalar(dim)) - 1)


def circshift(A: Any, k: Any, dim: Any = None) -> np.ndarray:
    a = as_array(A)
    k = int(_scalar(k))
    if dim is None:
        return np.roll(a, k, axis=0)
    return np.roll(a, k, axis=int(_scalar(dim)) - 1)


def unique(A: Any) -> np.ndarray:
    a = as_array(A)
    return np.unique(a).reshape(-1, 1)


def find(A: Any) -> np.ndarray:
    a = as_array(A)
    idx = np.flatnonzero(a)
    return (idx + 1).reshape(-1, 1)  # MATLAB is 1-based


def cat(dim: Any, *arrays: Any) -> np.ndarray:
    d = int(_scalar(dim)) - 1
    return np.concatenate([as_array(a) for a in arrays], axis=d)


def horzcat(*arrays: Any) -> np.ndarray:
    return np.hstack([as_array(a) for a in arrays])


def vertcat(*arrays: Any) -> np.ndarray:
    return np.vstack([as_array(a) for a in arrays])


def sortrows(A: Any, col: Any = None) -> np.ndarray:
    a = np.asarray(as_array(A))
    c = 0 if col is None else int(_scalar(col)) - 1
    return a[a[:, c].argsort(kind="stable")]


def issorted(A: Any) -> np.ndarray:
    a = np.asarray(as_array(A)).flatten()
    return np.array([[1.0 if np.all(np.diff(a) >= 0) else 0.0]])


def toeplitz(c: Any, r: Any = None) -> np.ndarray:
    from scipy.linalg import toeplitz as _t

    c = np.asarray(as_array(c)).flatten()
    if r is None:
        r = c
    else:
        r = np.asarray(as_array(r)).flatten()
    return _t(c, r)


def hankel(c: Any, r: Any = None) -> np.ndarray:
    from scipy.linalg import hankel as _h

    c = np.asarray(as_array(c)).flatten()
    if r is None:
        r = np.zeros_like(c)
    else:
        r = np.asarray(as_array(r)).flatten()
    return _h(c, r)


def vander(v: Any, n: Any = None) -> np.ndarray:
    v = np.asarray(as_array(v)).flatten()
    if n is None:
        return np.vander(v, increasing=False)
    return np.vander(v, N=int(_scalar(n)), increasing=False)


def hilb(n: Any) -> np.ndarray:
    from scipy.linalg import hilbert

    return hilbert(int(_scalar(n)))


def invhilb(n: Any) -> np.ndarray:
    from scipy.linalg import invhilbert

    return invhilbert(int(_scalar(n)))


def magic(n: Any) -> np.ndarray:
    n = int(_scalar(n))
    if n == 2:
        raise RuntimeError_("magic(2) is not defined")
    if n % 2 == 1:
        a = np.zeros((n, n))
        i, j = 0, n // 2
        for num in range(1, n * n + 1):
            a[i, j] = num
            ni, nj = (i - 1) % n, (j + 1) % n
            if a[ni, nj]:
                i = (i + 1) % n
            else:
                i, j = ni, nj
        return a
    if n % 4 == 0:
        a = np.arange(1, n * n + 1).reshape(n, n)
        for i in range(n):
            for j in range(n):
                if i % 4 in (0, 3) and j % 4 in (0, 3):
                    a[i, j] = n * n + 1 - a[i, j]
                elif i % 4 in (1, 2) and j % 4 in (1, 2):
                    a[i, j] = n * n + 1 - a[i, j]
        return a
    # singly-even (n = 4k+2)
    m = n // 2
    sub = magic(m)
    top = np.hstack([sub, sub + 2 * m * m])
    bot = np.hstack([sub + 3 * m * m, sub + m * m])
    a = np.vstack([top, bot])
    return a


def pascal(n: Any) -> np.ndarray:
    n = int(_scalar(n))
    from scipy.linalg import pascal as _p

    return _p(n, kind="symmetric")


def blkdiag(*matrices: Any) -> np.ndarray:
    from scipy.linalg import block_diag

    return block_diag(*[np.asarray(as_array(m)) for m in matrices])


def repelem(A: Any, n: Any) -> np.ndarray:
    a = np.asarray(as_array(A))
    n = int(_scalar(n))
    return np.repeat(a, n, axis=0)


def ndgrid(*vectors: Any) -> tuple[np.ndarray, ...]:
    vs = [np.asarray(as_array(v)).flatten() for v in vectors]
    grids = np.meshgrid(*vs, indexing="ij")
    return grids


def squeeze(A: Any) -> np.ndarray:
    a = as_array(A)
    a = np.squeeze(a)
    if a.ndim == 0:
        return a.reshape(1, 1)
    if a.ndim == 1:
        return a.reshape(-1, 1)
    return a


def permute(A: Any, order: Any) -> np.ndarray:
    a = as_array(A)
    order = tuple(int(x) - 1 for x in np.asarray(as_array(order)).flatten())
    return np.transpose(a, order)


def ipermute(A: Any, order: Any) -> np.ndarray:
    a = as_array(A)
    order = tuple(int(x) - 1 for x in np.asarray(as_array(order)).flatten())
    inverse = [0] * len(order)
    for i, o in enumerate(order):
        inverse[o] = i
    return np.transpose(a, tuple(inverse))
