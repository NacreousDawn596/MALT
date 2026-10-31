"""Sparse matrices and iterative solvers (SciPy-backed)."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import sparse as _sp
from scipy.sparse import linalg as _spla

from . import graphics as _graphics
from .arrays import as_array, scalar_value


def sparse(A: Any) -> Any:
    a = as_array(A)
    if _sp.issparse(a):
        return a
    return _sp.csr_matrix(np.asarray(a, dtype=float))


def full(S: Any) -> np.ndarray:
    if _sp.issparse(S):
        return S.toarray()
    return np.asarray(S)


def speye(n: Any) -> Any:
    return _sp.eye(int(scalar_value(n)), format="csr")


def speye_mn(m: Any, n: Any) -> Any:
    return _sp.eye(int(scalar_value(m)), int(scalar_value(n)), format="csr")


def spalloc(m: Any, n: Any, nz: Any) -> Any:
    return _sp.csr_matrix((int(scalar_value(m)), int(scalar_value(n))))


def sprand(n: Any, density: Any = 0.1) -> Any:
    n = int(scalar_value(n))
    d = float(scalar_value(density))
    return _sp.random(n, n, density=d, format="csr")


def sprandn(n: Any, density: Any = 0.1) -> Any:
    n = int(scalar_value(n))
    d = float(scalar_value(density))
    return _sp.random(n, n, density=d, format="csr", data_rvs=np.random.randn)


def spdiags(diags: Any, offsets: Any, m: Any, n: Any) -> Any:
    d = np.asarray(as_array(diags))
    off = np.asarray(as_array(offsets)).flatten().astype(int)
    return _sp.diags(d, off, shape=(int(scalar_value(m)), int(scalar_value(n))), format="csr")


def nnz(S: Any) -> np.ndarray:
    return np.array([[float(S.nnz if _sp.issparse(S) else np.count_nonzero(np.asarray(S)))]])


def spy(S: Any) -> None:
    a = S if _sp.issparse(S) else _sp.csr_matrix(np.asarray(as_array(S), dtype=float))
    _graphics.plt.spy(a)
    _graphics.plt.gca().set_title("Sparsity pattern")


def _dense_vec(b: Any) -> np.ndarray:
    b = as_array(b)
    if _sp.issparse(b):
        b = b.toarray()
    return np.asarray(b, dtype=float).flatten()


def _solve(method: str, A: Any, b: Any, *args: Any) -> np.ndarray:
    a = A if _sp.issparse(A) else np.asarray(as_array(A), dtype=float)
    bb = _dense_vec(b)
    fn = getattr(_spla, method)
    x, _ = fn(a, bb)
    return np.asarray(x).reshape(-1, 1)


def gmres(A: Any, b: Any) -> np.ndarray:
    return _solve("gmres", A, b)


def pcg(A: Any, b: Any) -> np.ndarray:
    return _solve("cg", A, b)


def bicg(A: Any, b: Any) -> np.ndarray:
    return _solve("bicg", A, b)


def bicgstab(A: Any, b: Any) -> np.ndarray:
    return _solve("bicgstab", A, b)


def cgs(A: Any, b: Any) -> np.ndarray:
    return _solve("cgs", A, b)


def minres(A: Any, b: Any) -> np.ndarray:
    return _solve("minres", A, b)


def lsqr(A: Any, b: Any) -> np.ndarray:
    return _solve("lsqr", A, b)


def qmr(A: Any, b: Any) -> np.ndarray:
    return _solve("qmr", A, b)
