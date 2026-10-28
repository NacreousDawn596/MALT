"""Cell arrays and structs.

MATLAB ``{}`` builds a cell array (a rectangular grid whose elements hold
arbitrary values), and ``struct``/dot access provide named-field records.
Generated code calls ``_ml.cell_literal``, ``_ml.cell_index``,
``_ml.cell_assign`` and ``_ml.getfield``/``_ml.setfield``.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..errors import IndexError_, RuntimeError_
from . import indexing as _indexing
from .arrays import as_array


class Cell:
    """A MATLAB cell array.

    Backed by a 2-D object array; elements are arbitrary values (scalars,
    matrices, strings, structs, or nested cells).
    """

    __slots__ = ("_data",)

    def __init__(self, data: np.ndarray) -> None:
        self._data = data

    @property
    def shape(self) -> tuple[int, ...]:
        return self._data.shape

    @property
    def size(self) -> int:
        return self._data.size

    @property
    def ndim(self) -> int:
        return self._data.ndim


class Struct:
    """A MATLAB struct: named fields with dot access (``s.field``)."""

    __slots__ = ("_fields",)

    def __init__(self, fields: dict[str, Any] | None = None) -> None:
        object.__setattr__(self, "_fields", dict(fields) if fields else {})

    def __getattr__(self, name: str) -> Any:
        fields = object.__getattribute__(self, "_fields")
        if name in fields:
            return fields[name]
        raise AttributeError(f"reference to non-existent field '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        object.__getattribute__(self, "_fields")[name] = value


def _logical(b: bool) -> np.ndarray:
    return np.array([[1.0 if b else 0.0]])


def cell_literal(rows: list[list[Any]]) -> Cell:
    if not rows:
        return Cell(np.empty((0, 0), dtype=object))
    ncols = max(len(row) for row in rows)
    data = np.empty((len(rows), ncols), dtype=object)
    for i, row in enumerate(rows):
        for j in range(ncols):
            data[i, j] = row[j] if j < len(row) else np.empty((0, 0))
    return Cell(data)


def iscell(x: Any) -> np.ndarray:
    return _logical(isinstance(x, Cell))


def isstruct(x: Any) -> np.ndarray:
    return _logical(isinstance(x, Struct))


def _scalar_sub(s: Any, n: int) -> int:
    i = _indexing._scalar_idx(s, n)
    if i is None:
        raise IndexError_("cell index must be a scalar or colon")
    return i


def _check_cell(C: Any) -> Cell:
    if not isinstance(C, Cell):
        raise RuntimeError_("content indexing '{...}' requires a cell array")
    return C


def cell_index(C: Any, *subs: Any) -> Any:
    cell = _check_cell(C)
    data = cell._data
    if len(subs) == 1:
        if subs[0] is _indexing.COLON:
            raise RuntimeError_("colon content indexing 'c{:}' is not supported")
        return data.flat[_scalar_sub(subs[0], data.size)]
    if len(subs) == 2:
        if subs[0] is _indexing.COLON or subs[1] is _indexing.COLON:
            raise RuntimeError_("colon content indexing is not supported")
        i = _scalar_sub(subs[0], data.shape[0])
        j = _scalar_sub(subs[1], data.shape[1])
        return data[i, j]
    raise RuntimeError_("cell indexing supports at most 2 dimensions")


def cell_assign(C: Any, value: Any, *subs: Any) -> Cell:
    cell = _check_cell(C)
    data = cell._data
    if len(subs) == 1:
        if subs[0] is _indexing.COLON:
            raise RuntimeError_("colon content assignment is not supported")
        data.flat[_scalar_sub(subs[0], data.size)] = value
        return cell
    if len(subs) == 2:
        if subs[0] is _indexing.COLON or subs[1] is _indexing.COLON:
            raise RuntimeError_("colon content assignment is not supported")
        i = _scalar_sub(subs[0], data.shape[0])
        j = _scalar_sub(subs[1], data.shape[1])
        data[i, j] = value
        return cell
    raise RuntimeError_("cell assignment supports at most 2 dimensions")


def struct(*args: Any) -> Struct:
    if len(args) % 2 != 0:
        raise RuntimeError_("struct() requires alternating field names and values")
    fields: dict[str, Any] = {}
    for i in range(0, len(args), 2):
        name = args[i]
        if not isinstance(name, str):
            raise RuntimeError_("struct field names must be strings")
        fields[name] = as_array(args[i + 1])
    return Struct(fields)


def fieldnames(s: Any) -> Cell:
    if not isinstance(s, Struct):
        raise RuntimeError_("fieldnames requires a struct")
    names = list(s._fields.keys())
    data = np.empty((1, len(names)), dtype=object)
    for i, n in enumerate(names):
        data[0, i] = n
    return Cell(data)


def isfield(s: Any, name: str) -> np.ndarray:
    if not isinstance(s, Struct):
        return _logical(False)
    return _logical(name in s._fields)
