"""Output, display formatting, and file export."""

from __future__ import annotations

import re
import sys
from typing import Any

import numpy as np

from .arrays import as_array
from .cells import Cell, Struct


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
    if isinstance(x, Cell):
        return _format_cell(x)
    if isinstance(x, Struct):
        return _format_struct(x)
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


def _format_cell(c: Cell) -> str:
    rows = []
    data = c._data
    for i in range(data.shape[0]):
        parts = []
        for j in range(data.shape[1]):
            parts.append(f"[{format_array(data[i, j])}]")
        rows.append("{" + ", ".join(parts) + "}")
    return "\n".join(rows)


def _format_struct(s: Struct) -> str:
    lines = []
    for name, val in s._fields.items():
        lines.append(f"    {name}: {format_array(val)}")
    if not lines:
        return "struct with no fields"
    return "struct with fields:\n" + "\n".join(lines)


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



_SPEC_RE = re.compile(r"%(?:[-+ #0])?(?:\d+|\*)?(?:\.\d+|\.\*)?[diouxXeEfFgGcrs]")


def _cycle_format(fmt: str, values: list[Any]) -> str:
    """Apply a MATLAB-style format string, cycling it when there are more
    values than conversion specifiers (as MATLAB ``fprintf`` does)."""
    if not values:
        return ""
    tokens: list[tuple[str, str]] = []
    last = 0
    for m in _SPEC_RE.finditer(fmt):
        tokens.append(("lit", fmt[last : m.start()]))
        tokens.append(("spec", m.group()))
        last = m.end()
    tokens.append(("lit", fmt[last:]))
    n = sum(1 for k, _ in tokens if k == "spec")
    if n == 0:
        return fmt.replace("%%", "%")
    out: list[str] = []
    i = 0
    while i < len(values):
        for kind, text in tokens:
            if kind == "lit":
                out.append(text)
            else:
                if i < len(values):
                    out.append(text % values[i])
                    i += 1
                else:
                    break
    return "".join(out)


def _flatten_args(args: tuple[Any, ...]) -> list[Any]:
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
    return converted


def fprintf(fmt: Any, *args: Any) -> None:
    fmt = str(fmt)
    if not args:
        # No arguments: emit the format text literally.
        print(fmt, end="", file=sys.stdout)
        return
    print(_cycle_format(fmt, _flatten_args(args)), end="", file=sys.stdout)


def sprintf(fmt: Any, *args: Any) -> str:
    fmt = str(fmt)
    if not args:
        return fmt
    return _cycle_format(fmt, _flatten_args(args))


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
