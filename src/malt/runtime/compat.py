"""MATLAB compatibility predicates and string helpers."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..errors import RuntimeError_
from .arrays import as_array, is_scalar, scalar_value
from .cells import Cell, Struct


def _logical(b: bool) -> np.ndarray:
    return np.array([[1.0 if b else 0.0]])


def _is_numeric_array(a: Any) -> bool:
    if isinstance(a, (str, Cell, Struct)):
        return False
    if not isinstance(a, np.ndarray):
        return False
    return np.issubdtype(a.dtype, np.number) or a.dtype == bool


def isnumeric(x: Any) -> np.ndarray:
    return _logical(_is_numeric_array(as_array(x)))


def ischar(x: Any) -> np.ndarray:
    return _logical(isinstance(as_array(x), str))


def isempty(x: Any) -> np.ndarray:
    a = as_array(x)
    if isinstance(a, str):
        return _logical(len(a) == 0)
    if isinstance(a, Cell):
        return _logical(a.size == 0)
    if isinstance(a, Struct):
        return _logical(len(a._fields) == 0)
    return _logical(a.size == 0)


def isscalar(x: Any) -> np.ndarray:
    return _logical(is_scalar(x))


def isvector(x: Any) -> np.ndarray:
    a = as_array(x)
    if isinstance(a, str):
        return _logical(True)
    if not isinstance(a, np.ndarray):
        return _logical(False)
    return _logical(a.ndim == 2 and (a.shape[0] == 1 or a.shape[1] == 1))


def ismatrix(x: Any) -> np.ndarray:
    a = as_array(x)
    if isinstance(a, str):
        return _logical(True)
    if not isinstance(a, np.ndarray):
        return _logical(False)
    return _logical(a.ndim == 2)


def isrow(x: Any) -> np.ndarray:
    a = as_array(x)
    if isinstance(a, str):
        return _logical(True)
    if not isinstance(a, np.ndarray):
        return _logical(False)
    return _logical(a.ndim == 2 and a.shape[0] == 1)


def iscolumn(x: Any) -> np.ndarray:
    a = as_array(x)
    if isinstance(a, str):
        return _logical(False)
    if not isinstance(a, np.ndarray):
        return _logical(False)
    return _logical(a.ndim == 2 and a.shape[1] == 1)


def isreal(x: Any) -> np.ndarray:
    a = as_array(x)
    if not isinstance(a, np.ndarray):
        return _logical(True)
    return _logical(not np.iscomplexobj(a))


def isfloat(x: Any) -> np.ndarray:
    a = as_array(x)
    if not isinstance(a, np.ndarray):
        return _logical(False)
    return _logical(
        np.issubdtype(a.dtype, np.floating)
        or np.issubdtype(a.dtype, np.complexfloating)
    )


def islogical(x: Any) -> np.ndarray:
    a = as_array(x)
    if not isinstance(a, np.ndarray):
        return _logical(False)
    return _logical(a.dtype == bool)


def _elementwise(x: Any, fn: Any) -> np.ndarray:
    a = as_array(x)
    if isinstance(a, str):
        raise RuntimeError_("isnan/isinf/isfinite are not defined for strings")
    return fn(a)


def isnan(x: Any) -> np.ndarray:
    return _elementwise(x, np.isnan)


def isinf(x: Any) -> np.ndarray:
    return _elementwise(x, np.isinf)


def isfinite(x: Any) -> np.ndarray:
    return _elementwise(x, np.isfinite)


# ---------------------------------------------------------------------------
# String helpers
# ---------------------------------------------------------------------------


def _require_str(x: Any, name: str) -> str:
    a = as_array(x)
    if not isinstance(a, str):
        raise RuntimeError_(f"{name} requires a string")
    return a


def lower(s: Any) -> str:
    return _require_str(s, "lower").lower()


def upper(s: Any) -> str:
    return _require_str(s, "upper").upper()


def strcmp(a: Any, b: Any) -> np.ndarray:
    return _logical(_require_str(a, "strcmp") == _require_str(b, "strcmp"))


def strcmpi(a: Any, b: Any) -> np.ndarray:
    return _logical(
        _require_str(a, "strcmpi").lower() == _require_str(b, "strcmpi").lower()
    )


def strcat(*args: Any) -> str:
    return "".join(_require_str(a, "strcat").rstrip() for a in args)


def strjoin(parts: Any, delim: Any = " ") -> str:
    if not isinstance(parts, Cell):
        raise RuntimeError_("strjoin requires a cell array of strings")
    d = _require_str(delim, "strjoin")
    return d.join(str(parts._data[0, j]) for j in range(parts.shape[1]))


def strsplit(s: Any) -> Cell:
    text = _require_str(s, "strsplit")
    tokens = text.split()
    data = np.empty((1, len(tokens)), dtype=object)
    for i, t in enumerate(tokens):
        data[0, i] = t
    return Cell(data)


# ---------------------------------------------------------------------------
# Numeric-to-string conversion
# ---------------------------------------------------------------------------


def _fmt_num(v: float) -> str:
    if v == 0:
        return "0"
    if abs(v - round(v)) < 1e-12 and abs(v) < 1e15:
        return str(int(round(v)))
    return repr(v)


def num2str(x: Any) -> str:
    a = as_array(x)
    if isinstance(a, str):
        return a
    if a.size == 1:
        v = scalar_value(a)
        if isinstance(v, complex):
            if v.imag == 0:
                return _fmt_num(v.real)
            sign = "+" if v.imag >= 0 else "-"
            return f"{_fmt_num(v.real)}{sign}{_fmt_num(abs(v.imag))}i"
        return _fmt_num(float(v))
    flat = [str(v) for v in a.flatten()]
    return "  ".join(flat)
