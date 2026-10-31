"""Base statistics (SciPy-backed)."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import signal as _sig
from scipy import stats as _stats

from .arrays import as_array, scalar_value
from .functions import _reduce_dim


def median(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.median(a, axis=d, keepdims=True)


def std(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.std(a, axis=d, keepdims=True, ddof=0)


def var(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.var(a, axis=d, keepdims=True, ddof=0)


def mad(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return np.mean(np.abs(a - np.mean(a, axis=d, keepdims=True)), axis=d, keepdims=True)


def skewness(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return _stats.skew(a, axis=d, bias=False, keepdims=True)


def kurtosis(x: Any, dim: Any | None = None) -> np.ndarray:
    a, d = _reduce_dim(x, dim)
    return _stats.kurtosis(a, axis=d, bias=False, fisher=True, keepdims=True)


def mode(x: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    m, _ = _stats.mode(a)
    return np.array([[float(np.asarray(m).reshape(-1)[0])]])


def cov(x: Any, y: Any = None) -> np.ndarray:
    a = np.asarray(as_array(x))
    if y is None:
        return np.asarray(np.cov(a, rowvar=False))
    b = np.asarray(as_array(y)).flatten()
    return np.asarray(np.cov(a.flatten(), b))


def corrcoef(x: Any, y: Any = None) -> np.ndarray:
    a = np.asarray(as_array(x))
    if y is None:
        return np.asarray(np.corrcoef(a, rowvar=False))
    b = np.asarray(as_array(y)).flatten()
    return np.asarray(np.corrcoef(a.flatten(), b))


def prctile(x: Any, p: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    p = np.asarray(as_array(p)).flatten()
    return np.asarray(np.percentile(a, p))


def quantile(x: Any, p: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    p = np.asarray(as_array(p)).flatten()
    return np.asarray(np.quantile(a, p))


def iqr(x: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return np.array([[float(np.percentile(a, 75) - np.percentile(a, 25))]])


# ---------------------------------------------------------------------------
# Moving statistics (sliding window)
# ---------------------------------------------------------------------------


def _moving(a: np.ndarray, k: int, fn: Any) -> np.ndarray:
    k = int(k)
    if k % 2 == 0:
        k += 1
    half = k // 2
    n = a.shape[0]
    out = np.empty(n)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        out[i] = fn(a[lo:hi])
    return out


def movmean(x: Any, k: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return _moving(a, scalar_value(k), np.mean)


def movmedian(x: Any, k: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return _moving(a, scalar_value(k), np.median)


def movsum(x: Any, k: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return _moving(a, scalar_value(k), np.sum)


def movstd(x: Any, k: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return _moving(a, scalar_value(k), lambda v: np.std(v))


def movvar(x: Any, k: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return _moving(a, scalar_value(k), lambda v: np.var(v))


def movmax(x: Any, k: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return _moving(a, scalar_value(k), np.max)


def movmin(x: Any, k: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return _moving(a, scalar_value(k), np.min)


# ---------------------------------------------------------------------------
# Detrend, normalization, and missing-data helpers
# ---------------------------------------------------------------------------


def detrend(x: Any, order: Any = 1) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return np.asarray(_sig.detrend(a, type="linear" if int(scalar_value(order)) == 1 else "constant"))


def ismissing(A: Any) -> np.ndarray:
    a = np.asarray(as_array(A), dtype=float)
    return np.asarray(np.isnan(a), dtype=float)


def rmmissing(A: Any) -> np.ndarray:
    a = np.asarray(as_array(A), dtype=float)
    return a[~np.isnan(a).any(axis=1)]


def fillmissing(A: Any, method: Any = "previous") -> np.ndarray:
    a = np.asarray(as_array(A), dtype=float).copy()
    m = str(method).lower()
    mask = np.isnan(a)
    idx = np.arange(a.shape[1])
    if m == "linear":
        for r in range(a.shape[0]):
            row = a[r]
            good = ~mask[r]
            if good.sum() == 0:
                continue
            row[mask[r]] = np.interp(idx[mask[r]], idx[good], row[good])
    elif m in ("next", "bfill"):
        a[mask] = np.nan
        a = np.where(mask, np.nan, a)
        for r in range(a.shape[0]):
            for c in range(a.shape[1] - 2, -1, -1):
                if np.isnan(a[r, c]):
                    a[r, c] = a[r, c + 1]
    else:  # previous / ffill / nearest
        for r in range(a.shape[0]):
            last = np.nan
            for c in range(a.shape[1]):
                if np.isnan(a[r, c]):
                    a[r, c] = last if not np.isnan(last) else 0.0
                else:
                    last = a[r, c]
    return a


def isoutlier(A: Any) -> np.ndarray:
    a = np.asarray(as_array(A)).flatten()
    med = np.median(a)
    mad = np.median(np.abs(a - med))
    thresh = 3 * 1.4826 * mad if mad != 0 else np.inf
    return np.asarray(np.abs(a - med) > thresh, dtype=float)


def filloutliers(A: Any) -> np.ndarray:
    a = np.asarray(as_array(A), dtype=float).flatten()
    out = a.copy()
    med = np.median(a)
    mad = np.median(np.abs(a - med))
    thresh = 3 * 1.4826 * mad if mad != 0 else np.inf
    idx = np.abs(a - med) > thresh
    out[idx] = med
    return out.reshape(1, -1)


def rms(x: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return np.array([[float(np.sqrt(np.mean(a ** 2)))]])


def meansqr(x: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return np.array([[float(np.mean(a ** 2))]])
