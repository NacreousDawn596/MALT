"""MATLAB one-based indexing and indexed assignment."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..errors import IndexError_, RuntimeError_
from .arrays import _config, as_array, py_scalar

# Sentinel for the ``:`` colon argument.
COLON = slice(None)


def _to_int_index(v: Any) -> int:
    """Convert a numeric scalar to a validated 1-based integer index."""
    if isinstance(v, (complex, np.complexfloating)):
        if v.imag != 0:
            raise IndexError_("subscript indices must be real positive integers")
        r = float(v.real)
    else:
        r = float(v)
    if not r.is_integer():
        raise IndexError_("subscript indices must be integers")
    return int(r)


def _scalar_idx(s: Any, n: int) -> int | None:
    """Convert a scalar subscript to a 0-based int (bounds-checked).

    Returns ``None`` if ``s`` is not a scalar subscript. Native numeric types
    are checked first because they are the common case in scalar loops.
    """
    if isinstance(s, (int, float, complex, np.number)):
        v = s
    elif isinstance(s, np.ndarray):
        if s.size != 1:
            return None
        v = s.reshape(-1)[0]
    else:
        return None
    i = _to_int_index(v)
    if i < 1 or i > n:
        raise IndexError_(f"index {i} is outside the valid range 1..{n}")
    return i - 1


def _flat_get(a: np.ndarray, i: int) -> Any:
    """Column-major linear scalar read (``i`` 0-based), no reshape for vectors."""
    if a.ndim == 2:
        if a.shape[0] == 1:
            return a[0, i]
        if a.shape[1] == 1:
            return a[i, 0]
        return a[i % a.shape[0], i // a.shape[0]]
    return a.reshape(-1, order="F")[i]


def _flat_set(a: np.ndarray, i: int, v: Any) -> None:
    """Column-major linear scalar write (``i`` 0-based), in place."""
    if a.ndim == 2:
        if a.shape[0] == 1:
            a[0, i] = v
            return
        if a.shape[1] == 1:
            a[i, 0] = v
            return
        a[i % a.shape[0], i // a.shape[0]] = v
        return
    a.reshape(-1, order="F")[i] = v


def _resolve_index(s: Any) -> tuple[Any, str]:
    """Resolve a subscript into (numpy index, kind).

    kind is one of 'scalar', 'colon', 'vector'.
    """
    if s is COLON:
        return slice(None), "colon"
    a = as_array(s)
    if a.size == 1:
        return _to_int_index(a.reshape(-1)[0]) - 1, "scalar"
    if a.dtype == bool:
        idx = np.flatnonzero(a.flatten())
        return idx, "vector"
    return (a.flatten() - 1), "vector"


def end_(A: Any, dim: int) -> np.ndarray:
    """Return the ``end`` index for dimension ``dim`` (1-based; 0 == linear)."""
    a = as_array(A)
    if isinstance(a, str):
        n = len(a)
    elif dim == 0:
        n = a.size
    else:
        if dim <= a.ndim:
            n = a.shape[dim - 1]
        else:
            n = 1
    return np.array([[float(n)]])


def index(A: Any, *subs: Any) -> Any:
    a = as_array(A)
    if isinstance(a, str):
        if len(subs) == 1:
            return _string_index(a, subs[0])
        raise IndexError_("too many indices for a string")
    if len(subs) == 1:
        if _config.optimized:
            i = _scalar_idx(subs[0], a.size)
            if i is not None:
                return _fast_linear_read(a, i)
        return _linear_index(a, subs[0])
    return _subscript_index(a, list(subs))


def _fast_linear_read(a: np.ndarray, i: int) -> Any:
    """Column-major linear scalar read returning a native Python scalar."""
    v = _flat_get(a, i)
    return v.item() if isinstance(v, np.generic) else v


def _string_index(s: str, sub: Any) -> str:
    if sub is COLON:
        return s
    a = as_array(sub)
    if a.dtype == bool:
        raise IndexError_("logical indexing not supported for strings")
    idx = a.astype(int)
    out = "".join(s[int(i) - 1] for i in idx.flatten())
    return out


def _linear_index(a: np.ndarray, s: Any) -> np.ndarray:
    if s is COLON:
        return a.reshape(-1, order="F").reshape(-1, 1)
    i = _scalar_idx(s, a.size) if _config.optimized else None
    if i is not None:
        # ``reshape(order='F')`` is a view for vectors and a copy for matrices;
        # reading either yields the correct MATLAB (column-major) element.
        return np.array([[a.reshape(-1, order="F")[i]]])
    sa = as_array(s)
    if sa.dtype == bool:
        mask = sa.flatten()
        if mask.size != a.size:
            raise IndexError_(
                f"logical index has {mask.size} elements but array has {a.size}"
            )
        return a.reshape(-1, order="F")[mask].reshape(-1, 1)
    idx = sa.astype(int)
    flat_idx = idx.flatten() - 1
    _check_bounds(flat_idx, a.size)
    vals = a.reshape(-1, order="F")[flat_idx]
    if idx.size == 1:
        return vals.reshape(1, 1)
    return vals.reshape(idx.shape)


def _subscript_index(a: np.ndarray, subs: list[Any]) -> np.ndarray:
    # Allow trailing single ':' subscripts for higher-dim arrays.
    while len(subs) < a.ndim and len(subs) > 0:
        subs.append(COLON)
    if len(subs) > a.ndim:
        # Trailing singleton dimensions are allowed if they are ':'
        extra = subs[a.ndim :]
        if all(x is COLON for x in extra):
            subs = subs[: a.ndim]
        else:
            raise IndexError_(
                f"too many indices ({len(subs)}) for array with {a.ndim} dimensions"
            )

    resolved = [_resolve_index(s) for s in subs]
    kinds = [k for _, k in resolved]

    # Bounds-check numeric indices against each dimension.
    for dim, (r, k) in enumerate(resolved):
        if k == "scalar":
            if r < 0 or r >= a.shape[dim]:
                raise IndexError_(
                    f"index {r + 1} is outside the valid range 1..{a.shape[dim]}"
                )
        elif k == "vector":
            if r.size and (r.min() < 0 or r.max() >= a.shape[dim]):
                bad = r[(r < 0) | (r >= a.shape[dim])][0]
                raise IndexError_(
                    f"index {int(bad) + 1} is outside the valid range 1..{a.shape[dim]}"
                )

    if all(k == "vector" for k in kinds) and len(kinds) == 2:
        # MATLAB submatrix semantics for two index vectors: outer product.
        r = resolved[0][0]
        c = resolved[1][0]
        result = a[np.ix_(r, c)]
    else:
        idx_tuple = tuple(r for r, _ in resolved)
        result = a[idx_tuple]

    result = np.asarray(result)
    if result.ndim == 0:
        return result.reshape(1, 1)
    if result.ndim == 1:
        # Determine orientation from which dimension was collapsed.
        if kinds[-1] == "scalar" and any(k != "scalar" for k in kinds[:-1]):
            return result.reshape(-1, 1)
        return result.reshape(1, -1)
    return result


def _check_bounds(flat_idx: np.ndarray, n: int) -> None:
    if flat_idx.size == 0:
        return
    if flat_idx.min() < 0 or flat_idx.max() >= n:
        bad = flat_idx[(flat_idx < 0) | (flat_idx >= n)][0]
        raise IndexError_(
            f"index {int(bad) + 1} is outside the valid range 1..{n}"
        )


def assign(A: Any, value: Any, *subs: Any) -> np.ndarray:
    a = as_array(A)
    if isinstance(a, str):
        raise IndexError_("cannot index-assign into a string")
    if len(subs) == 1 and _config.optimized:
        i = _scalar_idx(subs[0], a.size)
        if i is not None:
            _set_linear(a, i, py_scalar(value))
            return a
    value = as_array(value)
    if len(subs) == 1:
        _linear_assign(a, value, subs[0])
    else:
        _subscript_assign(a, value, list(subs))
    return a


def _linear_assign(a: np.ndarray, value: np.ndarray, s: Any) -> None:
    if s is COLON:
        a[:] = value.reshape(a.shape) if value.size == a.size else _expand(a, value)
        return
    i = _scalar_idx(s, a.size) if _config.optimized else None
    if i is not None:
        _set_linear(a, i, value.reshape(-1)[0])
        return
    sa = as_array(s)
    if sa.dtype == bool:
        mask = sa.flatten()
        a.reshape(-1, order="F")[mask] = value.flatten()
        return
    idx = sa.astype(int).flatten() - 1
    _check_bounds(idx, a.size)
    a.reshape(-1, order="F")[idx] = value.flatten()


def _set_linear(a: np.ndarray, i: int, v: Any) -> None:
    """Write element ``i`` (0-based, column-major linear) in place."""
    _flat_set(a, i, v)


def _expand(a: np.ndarray, value: np.ndarray) -> np.ndarray:
    if value.size == 1:
        return np.full(a.shape, value.reshape(-1)[0])
    raise RuntimeError_("dimension mismatch in indexed assignment")


def _subscript_assign(a: np.ndarray, value: np.ndarray, subs: list[Any]) -> None:
    while len(subs) < a.ndim:
        subs.append(COLON)
    resolved = [_resolve_index(s) for s in subs]
    idx_tuple = tuple(r for r, _ in resolved)

    # Compute the shape of the selected region to decide how to place value.
    target = a[idx_tuple]
    target = np.asarray(target)
    v = value
    if target.size == 1 and v.size >= 1:
        v = v.reshape(target.shape) if v.size == target.size else _scalar_broadcast(v, target.shape)
    elif target.size == v.size and target.shape != v.shape:
        v = v.reshape(target.shape)
    elif v.size == 1:
        v = np.full(target.shape, v.reshape(-1)[0])
    elif target.size != v.size:
        raise RuntimeError_(
            "dimension mismatch in indexed assignment: "
            f"selected {target.shape}, assigned {v.shape}"
        )
    a[idx_tuple] = v


def _scalar_broadcast(v: np.ndarray, shape: tuple[int, ...]) -> np.ndarray:
    if v.size == 1:
        return np.full(shape, v.reshape(-1)[0])
    raise RuntimeError_("dimension mismatch in indexed assignment")


def call(f: Any, *args: Any) -> Any:
    """Dynamically call a function handle or index an array."""
    if callable(f) and not isinstance(f, (np.ndarray, str)):
        return f(*args)
    return index(f, *args)
