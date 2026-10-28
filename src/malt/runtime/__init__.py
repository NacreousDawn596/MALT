"""MALT runtime: MATLAB-compatible semantics implemented on NumPy/SciPy.

This module exposes a flat namespace of functions that generated code calls
as ``_ml.<name>(...)``. All numeric values are NumPy arrays with at least two
dimensions (MATLAB shape conventions: scalars are 1x1).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from . import arrays as _arrays
from . import calculus as _calculus
from . import functions as _functions
from . import graphics as _graphics
from . import indexing as _indexing
from . import io as _io
from . import linear_algebra as _linalg
from . import ode as _ode
from . import operators as _operators
from .control import ReturnSignal  # noqa: F401

# ---------------------------------------------------------------------------
# Namespace plumbing for `clear` / `who` / `whos`.
# ---------------------------------------------------------------------------

_CURRENT_NAMESPACE: dict[str, Any] | None = None


def set_current_namespace(ns: dict[str, Any] | None) -> None:
    global _CURRENT_NAMESPACE
    _CURRENT_NAMESPACE = ns


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def constants() -> dict[str, Any]:
    return {
        "pi": np.array([[math.pi]]),
        "eps": np.array([[np.finfo(float).eps]]),
        "Inf": np.array([[np.inf]]),
        "NaN": np.array([[np.nan]]),
        "true": np.array([[1.0]]),
        "false": np.array([[0.0]]),
        "i": np.array([[1j]]),
        "j": np.array([[1j]]),
    }


# ---------------------------------------------------------------------------
# Re-exported names
# ---------------------------------------------------------------------------

from .arrays import (  # noqa: E402
    as_array,
    colon,
    for_columns,
    is_logical,
    is_scalar,
    is_string,
    is_true,
    isequal,
    jit_for,
    length,
    linspace,
    logspace,
    matrix,
    meshgrid,
    ndims,
    numel,
    peaks,
    scalar_value,
    set_optimization_level,
    size,
)
from .calculus import fzero, integral, roots  # noqa: E402
from .functions import (  # noqa: E402
    abs,
    acos,
    angle,
    asin,
    atan,
    atan2,
    ceil,
    conj,
    cos,
    cosh,
    cumprod,
    cumsum,
    diag,
    exp,
    eye,
    fix,
    fliplr,
    flipud,
    floor,
    imag,
    log,
    log2,
    log10,
    mean,
    mod,
    ones,
    prod,
    rand,
    randn,
    real,
    rem,
    repmat,
    reshape,
    rng,
    round,
    sign,
    sin,
    sinh,
    sort,
    sqrt,
    tan,
    tanh,
    zeros,
)
from .functions import (
    max_ as max,
)
from .functions import (
    min_ as min,
)
from .functions import (
    sum_ as sum,
)
from .graphics import (  # noqa: E402
    axis,
    bar,
    clf,
    close,
    colorbar,
    contour,
    contourf,
    current_figure,
    drawnow,
    errorbar,
    figure,
    figure_count,
    fill,
    gca,
    gcf,
    grid,
    histogram,
    hold,
    image,
    imagesc,
    legend,
    loglog,
    mesh,
    parse_style,
    plot,
    scatter,
    semilogx,
    semilogy,
    show,
    stairs,
    stem,
    subplot,
    surf,
    title,
    view,
    xlabel,
    xlim,
    ylabel,
    ylim,
    zlabel,
    zlim,
)
from .indexing import COLON, assign, call, end_, index  # noqa: E402
from .io import (  # noqa: E402
    clc,
    disp,
    display,
    exportgraphics,
    format_array,
    fprintf,
    saveas,
    sprintf,
)
from .linear_algebra import (  # noqa: E402
    chol,
    cond,
    det,
    eig,
    eigvals,
    inv,
    lu,
    norm,
    pinv,
    polyfit,
    qr,
    rank,
    svd,
    trace,
)
from .ode import ode45  # noqa: E402
from .operators import (  # noqa: E402
    and_,
    ctranspose,
    eq,
    ge,
    gt,
    ldivide,
    le,
    logical_not,
    lt,
    minus,
    mldivide,
    mpower,
    mrdivide,
    mtimes,
    ne,
    or_,
    plus,
    power,
    rdivide,
    short_and,
    short_or,
    times,
    transpose,
    uneg,
    uplus,
)

# ---------------------------------------------------------------------------
# Workspace commands
# ---------------------------------------------------------------------------


def clear(*names: Any) -> None:
    ns = _CURRENT_NAMESPACE
    if ns is None:
        return
    if not names:
        for key in list(ns.keys()):
            if not key.startswith("_"):
                ns.pop(key, None)
        return
    for n in names:
        ns.pop(str(n), None)


def who() -> None:
    ns = _CURRENT_NAMESPACE or {}
    for name in sorted(ns.keys()):
        if not name.startswith("_"):
            _io.disp(name)


def whos() -> None:
    ns = _CURRENT_NAMESPACE or {}
    for name in sorted(ns.keys()):
        if name.startswith("_"):
            continue
        val = ns[name]
        a = as_array(val)
        if isinstance(a, str):
            info = "char"
        elif isinstance(a, np.ndarray):
            info = f"{a.dtype} {'x'.join(str(s) for s in a.shape)}"
        else:
            info = type(a).__name__
        print(f"{name:<12} {info}", file=__import__("sys").stdout)


def help_(topic: str | None = None) -> None:
    if topic is None:
        print("MALT — MATLAB-compatible runtime")
        print("Commands: clear, clc, who, whos, help, exit, quit")
        return
    print(f"help: {topic}")


help = help_


__all__ = [name for name in dir() if not name.startswith("_")]
