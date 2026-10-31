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


def _sort_eig(w: np.ndarray, v: np.ndarray | None):
    # MATLAB returns eigenvalues sorted ascending (by real part, then
    # imaginary part); NumPy does not guarantee an order.
    order = np.lexsort((np.imag(w), np.real(w)))
    w = w[order]
    if v is not None:
        v = v[:, order]
    return w, v


def eig(A: Any, nout: int = 1) -> Any:
    a = as_array(A)
    w, v = np.linalg.eig(a)
    # MATLAB returns real eigenvalues/vectors when the imaginary parts are
    # numerically zero (e.g. for real symmetric matrices).
    if np.allclose(w.imag, 0, atol=1e-12):
        w = w.real
    if nout >= 2 and np.allclose(v.imag, 0, atol=1e-12):
        v = v.real
    w, v = _sort_eig(w, v)
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
    w = np.linalg.eigvals(as_array(A))
    if np.allclose(w.imag, 0, atol=1e-12):
        w = w.real
    w, _ = _sort_eig(w, None)
    return w.reshape(-1, 1)


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


# ---------------------------------------------------------------------------
# Matrix decompositions and functions
# ---------------------------------------------------------------------------


def schur(A: Any, nout: int = 1) -> Any:
    from scipy.linalg import schur as _schur

    t, z = _schur(as_array(A), output="real")
    if nout >= 2:
        return t, z
    return t


def hess(A: Any) -> np.ndarray:
    from scipy.linalg import hessenberg

    h, _ = hessenberg(as_array(A), calc_q=False)
    return h


def expm(A: Any) -> np.ndarray:
    from scipy.linalg import expm as _expm

    return _expm(as_array(A))


def logm(A: Any) -> np.ndarray:
    from scipy.linalg import logm as _logm

    return _logm(as_array(A))


def sqrtm(A: Any) -> np.ndarray:
    from scipy.linalg import sqrtm as _sqrtm

    return _sqrtm(as_array(A))


def funm(A: Any, fun: Any) -> np.ndarray:
    from scipy.linalg import funm as _funm

    a = as_array(A)
    fn = str(fun).lower()
    table = {"exp": np.exp, "sin": np.sin, "cos": np.cos, "log": np.log, "sqrt": np.sqrt}
    if fn in table:
        return _funm(a, table[fn])
    return _funm(a, lambda z: np.asarray(fun(np.asarray(z))).item())


def null(A: Any) -> np.ndarray:
    from scipy.linalg import null_space

    return null_space(as_array(A))


def orth(A: Any) -> np.ndarray:
    from scipy.linalg import orth as _orth

    return _orth(as_array(A))


def rref(A: Any) -> np.ndarray:
    a = as_array(A).astype(float)
    m, n = a.shape
    r = 0
    pivots = []
    for c in range(n):
        if r >= m:
            break
        row = np.argmax(np.abs(a[r:, c])) + r
        if abs(a[row, c]) < 1e-12:
            continue
        a[[r, row]] = a[[row, r]]
        a[r] = a[r] / a[r, c]
        for i in range(m):
            if i != r and abs(a[i, c]) > 1e-12:
                a[i] = a[i] - a[i, c] * a[r]
        pivots.append(c)
        r += 1
    return a


def linsolve(A: Any, B: Any) -> np.ndarray:
    from scipy.linalg import solve

    return solve(as_array(A), as_array(B))


def balance(A: Any) -> np.ndarray:
    from scipy.linalg import matrix_balance

    b, _ = matrix_balance(as_array(A))
    return b


def rcond(A: Any) -> np.ndarray:
    return np.array([[1.0 / np.linalg.cond(as_array(A))]])


def normest(A: Any) -> np.ndarray:
    return np.array([[np.linalg.norm(as_array(A), ord=2)]])


def condest(A: Any) -> np.ndarray:
    return cond(A, 1)


# ---------------------------------------------------------------------------
# Structural predicates
# ---------------------------------------------------------------------------


def _square(A: Any) -> np.ndarray:
    a = as_array(A)
    if isinstance(a, str):
        a = np.asarray(a)
    a = np.atleast_2d(a)
    return a


def issymmetric(A: Any) -> np.ndarray:
    a = _square(A)
    r = a.shape[0] == a.shape[1] and np.allclose(a, a.T, atol=1e-12)
    return np.array([[1.0 if r else 0.0]])


def ishermitian(A: Any) -> np.ndarray:
    a = _square(A)
    r = a.shape[0] == a.shape[1] and np.allclose(a, a.conj().T, atol=1e-12)
    return np.array([[1.0 if r else 0.0]])


def isdiag(A: Any) -> np.ndarray:
    a = np.asarray(as_array(A), dtype=float)
    off = a - np.diag(np.diag(a))
    return np.array([[1.0 if np.allclose(off, 0, atol=1e-12) else 0.0]])


def istril(A: Any) -> np.ndarray:
    a = np.asarray(as_array(A), dtype=float)
    return np.array([[1.0 if np.allclose(np.triu(a, 1), 0, atol=1e-12) else 0.0]])


def istriu(A: Any) -> np.ndarray:
    a = np.asarray(as_array(A), dtype=float)
    return np.array([[1.0 if np.allclose(np.tril(a, -1), 0, atol=1e-12) else 0.0]])


def isbanded(A: Any, lower: Any, upper: Any) -> np.ndarray:
    a = np.asarray(as_array(A), dtype=float)
    n = a.shape[0]
    lo = int(scalar_value(lower))
    up = int(scalar_value(upper))
    ok = True
    for i in range(n):
        for j in range(n):
            if j - i > up or i - j > lo:
                if abs(a[i, j]) > 1e-12:
                    ok = False
    return np.array([[1.0 if ok else 0.0]])
