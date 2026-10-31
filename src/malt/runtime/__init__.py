"""MALT runtime: MATLAB-compatible semantics implemented on NumPy/SciPy.

This module exposes a flat namespace of functions that generated code calls
as ``_ml.<name>(...)``. All numeric values are NumPy arrays with at least two
dimensions (MATLAB shape conventions: scalars are 1x1).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ..errors import RuntimeError_  # noqa: E402
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
    blkdiag,
    cat,
    circshift,
    colon,
    find,
    flip,
    for_columns,
    for_init,
    hankel,
    hilb,
    horzcat,
    invhilb,
    ipermute,
    is_scalar,
    is_string,
    is_true,
    isequal,
    issorted,
    jit_for,
    jit_loop,
    kron,
    length,
    linspace,
    logspace,
    magic,
    matrix,
    meshgrid,
    ndgrid,
    ndims,
    numel,
    pascal,
    peaks,
    permute,
    repelem,
    rot90,
    scalar_value,
    set_optimization_level,
    size,
    sortrows,
    squeeze,
    toeplitz,
    tril,
    triu,
    unique,
    vander,
    vertcat,
)
from .calculus import fzero, integral, roots  # noqa: E402
from .cells import (  # noqa: E402
    Cell,
    Struct,
    cell_assign,
    cell_index,
    cell_literal,
    fieldnames,
    iscell,
    isfield,
    isstruct,
    struct,
)
from .compat import (  # noqa: E402
    ischar,
    iscolumn,
    isempty,
    isfinite,
    isfloat,
    isinf,
    islogical,
    ismatrix,
    isnan,
    isnumeric,
    isreal,
    isrow,
    isscalar,
    isvector,
    lower,
    num2str,
    strcat,
    strcmp,
    strcmpi,
    strjoin,
    strsplit,
    upper,
)
from .controlsys import (  # noqa: E402
    acker,
    append,
    bandwidth,
    bode,
    c2d,
    care,
    ctrb,
    d2c,
    damp,
    dare,
    dcgain,
    dlqr,
    evalfr,
    feedback,
    freqresp,
    gensig,
    impulse,
    initial,
    isproper,
    isstable,
    lqr,
    lsim,
    lyap,
    margin,
    minreal,
    nyquist,
    obsv,
    parallel,
    pid,
    place,
    pole,
    series,
    ss,
    ss2tf,
    ss2zp,
    ssdata,
    step,
    stepinfo,
    tf,
    tf2ss,
    tf2zp,
    tfdata,
    zero,
    zp2tf,
)
from .functions import (  # noqa: E402
    abs,
    acos,
    acosd,
    acosh,
    acot,
    acsc,
    angle,
    asec,
    asin,
    asind,
    asinh,
    atan,
    atan2,
    atan2d,
    atand,
    atanh,
    bounds,
    cbrt,
    ceil,
    conj,
    cos,
    cosd,
    cosh,
    cot,
    cplxpair,
    csc,
    cummax,
    cummin,
    cumprod,
    cumsum,
    deg2rad,
    diag,
    diff,
    exp,
    expm1,
    eye,
    factor,
    factorial,
    fix,
    fliplr,
    flipud,
    floor,
    gcd,
    hypot,
    idivide,
    imag,
    isprime,
    lcm,
    log,
    log1p,
    log2,
    log10,
    maxk,
    mean,
    mink,
    mod,
    nchoosek,
    normalize,
    nthroot,
    ones,
    perms,
    primes,
    prod,
    rad2deg,
    rand,
    randn,
    real,
    reallog,
    realsqrt,
    rem,
    repmat,
    rescale,
    reshape,
    rng,
    round,
    sec,
    sign,
    sin,
    sind,
    sinh,
    sort,
    sqrt,
    tan,
    tand,
    tanh,
    unwrap,
    zeros,
)
from .functions import (
    all_ as all,
)
from .functions import (
    any_ as any,
)
from .functions import (
    complex_ as complex,
)
from .functions import (
    max_ as max,
)
from .functions import (
    min_ as min,
)
from .functions import (
    range_ as range,
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
from .handles import FunctionHandle  # noqa: E402
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
    balance,
    chol,
    cond,
    condest,
    det,
    eig,
    eigvals,
    expm,
    funm,
    hess,
    inv,
    isbanded,
    isdiag,
    ishermitian,
    issymmetric,
    istril,
    istriu,
    linsolve,
    logm,
    lu,
    norm,
    normest,
    null,
    orth,
    pinv,
    polyfit,
    qr,
    rank,
    rcond,
    rref,
    schur,
    sqrtm,
    svd,
    trace,
)
from .ode import ode15s, ode23, ode23s, ode45, ode113  # noqa: E402
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
from .polynomial import (  # noqa: E402
    conv,
    deconv,
    del2,
    fminbnd,
    fminsearch,
    fminunc,
    fsolve,
    gradient,
    integral2,
    integral3,
    interp1,
    interp2,
    interp3,
    lsqnonneg,
    makima,
    pchip,
    poly,
    polyder,
    polyint,
    polyval,
    polyvalm,
    residue,
    spline,
    trapz,
)
from .signalproc import (  # noqa: E402
    butter,
    cheby1,
    cheby2,
    conv2,
    decimate,
    downsample,
    ellip,
    fft,
    fft2,
    fftn,
    fftshift,
    filter,
    filtfilt,
    findpeaks,
    fir1,
    freqz,
    hilbert,
    ifft,
    ifft2,
    ifftn,
    ifftshift,
    medfilt1,
    nextpow2,
    periodogram,
    pwelch,
    resample,
    sgolayfilt,
    spectrogram,
    upsample,
    xcorr,
)
from .sparse import (  # noqa: E402
    bicg,
    bicgstab,
    cgs,
    full,
    gmres,
    lsqr,
    minres,
    nnz,
    pcg,
    qmr,
    spalloc,
    sparse,
    spdiags,
    speye,
    sprand,
    sprandn,
    spy,
)
from .special import (  # noqa: E402
    airy,
    besseli,
    besselj,
    besselk,
    bessely,
    beta,
    betaln,
    cross,
    cumtrapz,
    dot,
    ellipj,
    ellipke,
    erf,
    erfc,
    erfcinv,
    erfinv,
    expint,
    gamma,
    gammaln,
    legendre,
    psi,
)
from .stats import (  # noqa: E402
    corrcoef,
    cov,
    detrend,
    fillmissing,
    filloutliers,
    iqr,
    ismissing,
    isoutlier,
    kurtosis,
    mad,
    meansqr,
    median,
    mode,
    movmax,
    movmean,
    movmedian,
    movmin,
    movstd,
    movsum,
    movvar,
    prctile,
    quantile,
    rmmissing,
    rms,
    skewness,
    std,
    var,
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


class MaltCatchError:
    """The value bound to a ``catch err`` variable.

    Exposes ``.message`` and ``.identifier``, mirroring the two most useful
    fields of MATLAB's ``MException`` (see ``docs/specs/try-catch.md``).
    """

    __slots__ = ("message", "identifier")

    def __init__(self, message: str, identifier: str) -> None:
        self.message = message
        self.identifier = identifier


def catch_error(e: BaseException) -> MaltCatchError:
    """Normalize a caught Python exception into a MALT error value."""
    from ..errors import MaltError

    if isinstance(e, MaltError):
        return MaltCatchError(e.message, e.category)
    return MaltCatchError(str(e), type(e).__name__)


def getfield(obj: Any, name: str) -> Any:
    """Field access (``obj.field``). Supported on structs and error values."""
    if isinstance(obj, Struct):
        fields = obj._fields
        if name in fields:
            return fields[name]
        raise RuntimeError_(f"reference to non-existent field '{name}'")
    if isinstance(obj, MaltCatchError):
        return getattr(obj, name)
    raise RuntimeError_(
        f"field access '.' is only supported on structs and error values, "
        f"not {type(obj).__name__}"
    )


def setfield(obj: Any, name: str, value: Any) -> Struct:
    """Field assignment (``obj.field = value``). Requires a struct."""
    if not isinstance(obj, Struct):
        raise RuntimeError_(
            f"field assignment '.' requires a struct, not {type(obj).__name__}"
        )
    obj._fields[name] = as_array(value)
    return obj


def make_handle(name: str, fn: Any) -> FunctionHandle:
    return FunctionHandle(name, fn)


def func2str(h: Any) -> str:
    if isinstance(h, FunctionHandle):
        return h.name
    if callable(h) and hasattr(h, "__name__"):
        return h.__name__
    raise RuntimeError_("func2str requires a function handle")


def str2func(name: Any) -> FunctionHandle:
    if not isinstance(name, str):
        raise RuntimeError_("str2func requires a string")
    fn = globals().get(name)
    if fn is None:
        raise RuntimeError_(f"str2func: unknown function '{name}'")
    return FunctionHandle(name, fn)


def feval(h: Any, *args: Any) -> Any:
    if isinstance(h, FunctionHandle):
        return h(*args)
    if callable(h):
        return h(*args)
    raise RuntimeError_("feval requires a function handle")


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
