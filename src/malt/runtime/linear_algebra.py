"""Linear algebra built on NumPy/SciPy with MATLAB output semantics."""

from __future__ import annotations

from typing import Any

import numpy as np

from .arrays import as_array, scalar_value


def det(A: Any) -> np.ndarray:
    return np.array([[np.linalg.det(as_array(A))]])


def inv(A: Any) -> np.ndarray:
    return np.linalg.inv(as_array(A))


def rank(A: Any, tol: Any | None = None) -> np.ndarray:
    a = as_array(A)
    r = np.linalg.matrix_rank(a, tol=None if tol is None else float(scalar_value(tol)))
    return np.array([[float(r)]])


def trace(A: Any) -> np.ndarray:
    return np.array([[float(np.trace(as_array(A)))]])


def norm(A: Any, p: Any | None = None) -> np.ndarray:
    a = as_array(A)
    if p is None:
        return np.array([[np.linalg.norm(a)]])
    pval = int(scalar_value(p))
    order: Any
    if pval == 1:
        order = 1
    elif pval == 2:
        order = 2
    else:
        order = np.inf if pval in (float("inf"), -1) else pval
    return np.array([[np.linalg.norm(a, ord=order)]])


def cond(A: Any, p: Any | None = None) -> np.ndarray:
    a = as_array(A)
    pval = 2 if p is None else int(scalar_value(p))
    return np.array([[np.linalg.cond(a, pval)]])


def eig(A: Any, nout: int = 1) -> Any:
    a = as_array(A)
    w, v = np.linalg.eig(a)
    if nout >= 2:
        return v, np.diag(w)
    return w.reshape(-1, 1)


def svd(A: Any, nout: int = 1) -> Any:
    a = as_array(A)
    u, s, vt = np.linalg.svd(a, full_matrices=True)
    if nout >= 2:
        return u, np.diag(s) if s.size == a.shape[0] else (u, s.reshape(-1, 1))
    if nout == 1:
        return s.reshape(-1, 1)
    return u, s, vt.T


def eigvals(A: Any) -> np.ndarray:
    return np.linalg.eigvals(as_array(A)).reshape(-1, 1)


def lu(A: Any, nout: int = 1) -> Any:
    from scipy.linalg import lu as _lu

    p, lower, upper = _lu(as_array(A))
    if nout >= 3:
        return p, lower, upper
    if nout == 2:
        return lower, upper
    return np.concatenate([lower, upper], axis=1)


def chol(A: Any) -> np.ndarray:
    return np.linalg.cholesky(as_array(A))


def qr(A: Any, nout: int = 1) -> Any:
    q, r = np.linalg.qr(as_array(A))
    if nout >= 2:
        return q, r
    return q


def polyfit(x: Any, y: Any, n: Any) -> np.ndarray:
    return np.polyfit(as_array(x).flatten(), as_array(y).flatten(), int(scalar_value(n))).reshape(1, -1)


def pinv(A: Any) -> np.ndarray:
    return np.linalg.pinv(as_array(A))
