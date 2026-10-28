"""Output, display formatting, and file export."""

from __future__ import annotations

import sys
from typing import Any

import numpy as np

from .arrays import as_array


def _fmt_scalar(v: Any) -> str:
    if isinstance(v, complex):
        re = v.real
        im = v.imag
        if im >= 0:
            return f"{_fmt_real(re)} + {_fmt_real(im)}i"
        return f"{_fmt_real(re)} - {_fmt_real(-im)}i"
    return _fmt_real(float(v))


def _fmt_real(v: float) -> str:
    if v == 0:
        return "0"
    if abs(v - round(v)) < 1e-12 and abs(v) < 1e15:
        return str(int(round(v)))
    s = repr(v)
    return s


def format_array(x: Any) -> str:
    """Format a numeric array in a MATLAB-like column-aligned layout."""
    a = as_array(x)
    if isinstance(a, str):
        return a
    if a.dtype == bool:
        a = a.astype(float)
    a = np.asarray(a)
    if a.ndim > 2:
        parts = []
        for k in range(a.shape[2]):
            parts.append(f"(:,:,{k + 1}) =\n{_format_2d(a[:, :, k])}")
        return "\n\n".join(parts)
    return _format_2d(a)


def _format_2d(a: np.ndarray) -> str:
    if a.ndim == 0:
        return _fmt_scalar(a.reshape(-1)[0])
    a = a.reshape(-1, a.shape[-1]) if a.ndim == 1 else a
    rows, cols = a.shape
    cells = [[_fmt_scalar(a[i, j]) for j in range(cols)] for i in range(rows)]
    widths = [
        max(len(cells[i][j]) for i in range(rows)) for j in range(cols)
    ]
    lines = []
    for i in range(rows):
        parts = []
        for j in range(cols):
            parts.append(" " + cells[i][j].rjust(widths[j]))
        lines.append("".join(parts))
    return "\n".join(lines)


def disp(x: Any) -> None:
    a = as_array(x)
    if isinstance(a, str):
        print(a, file=sys.stdout)
        return
    print(format_array(a), file=sys.stdout)


def display(x: Any) -> None:
    disp(x)


def fprintf(fmt: Any, *args: Any) -> None:
    fmt = str(fmt)
    converted: list[Any] = []
    for arg in args:
        a = as_array(arg)
        if isinstance(a, str):
            converted.append(a)
        elif a.size == 1:
            v = a.reshape(-1)[0]
            if isinstance(v, complex):
                converted.append(complex(v))
            else:
                converted.append(v.item() if hasattr(v, "item") else v)
        else:
            for v in a.flatten(order="F"):
                converted.append(v.item() if hasattr(v, "item") else v)
    text = fmt % tuple(converted) if converted else fmt
    print(text, end="", file=sys.stdout)


def sprintf(fmt: Any, *args: Any) -> str:
    fmt = str(fmt)
    converted: list[Any] = []
    for arg in args:
        a = as_array(arg)
        if isinstance(a, str):
            converted.append(a)
        elif a.size == 1:
            v = a.reshape(-1)[0]
            converted.append(v.item() if hasattr(v, "item") else v)
        else:
            for v in a.flatten(order="F"):
                converted.append(v.item() if hasattr(v, "item") else v)
    return fmt % tuple(converted) if converted else fmt


def clc() -> None:
    print("\033[2J\033[H", end="", file=sys.stdout)


def clear(namespace: Any, *names: Any) -> None:
    """Clear workspace variables."""
    if not names:
        for key in list(namespace.keys()):
            if not key.startswith("_"):
                namespace.pop(key, None)
        return
    for n in names:
        namespace.pop(str(n), None)


def saveas(fig: Any, filename: Any) -> None:
    path = str(filename)
    fig.savefig(path)
    print(f"figure saved to {path}", file=sys.stdout)


def exportgraphics(fig: Any, filename: Any) -> None:
    saveas(fig, filename)
