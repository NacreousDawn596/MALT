"""MATLAB-compatible graphics on top of Matplotlib."""

from __future__ import annotations

import os
import sys
from typing import Any

import matplotlib

if "MPLBACKEND" in os.environ:
    _backend = os.environ["MPLBACKEND"]
elif sys.platform in {"win32", "linux"}:
    _backend = "Qt5Agg"
else:
    _backend = "Agg"

matplotlib.use(_backend)
import matplotlib.pyplot as plt  # noqa: E402

from ..errors import RuntimeError_  # noqa: E402
from .arrays import as_array  # noqa: E402

# ---------------------------------------------------------------------------
# Style parsing
# ---------------------------------------------------------------------------

_COLORS = {
    "r": "red",
    "g": "green",
    "b": "blue",
    "c": "cyan",
    "m": "magenta",
    "y": "yellow",
    "k": "black",
    "w": "white",
}

_LINESTYLES = {
    "-": "solid",
    "--": "dashed",
    ":": "dotted",
    "-.": "dashdot",
}

_MARKERS = {
    "o": "o",
    "x": "x",
    "+": "+",
    "*": "*",
    "s": "s",
    "d": "D",
    "^": "^",
    "v": "v",
    "<": "<",
    ">": ">",
    "p": "p",
    "h": "h",
    ".": ".",
}


def parse_style(spec: str) -> dict[str, Any]:
    """Parse a MATLAB line-spec string into Matplotlib keyword arguments."""
    kwargs: dict[str, Any] = {}
    i = 0
    n = len(spec)
    # A marker may appear anywhere; a color/linestyle sequence is ordered.
    # We scan for the marker first (single char that is marker-only), then
    # color and linestyle tokens.
    marker = None
    for ch in spec:
        if ch in _MARKERS:
            marker = _MARKERS[ch]
            break
    if marker is not None:
        kwargs["marker"] = marker
    color = None
    linestyle = None
    while i < n:
        ch = spec[i]
        if ch in _COLORS:
            color = _COLORS[ch]
            i += 1
        elif ch == "-" and i + 1 < n and spec[i + 1] == ".":
            linestyle = _LINESTYLES["-."]
            i += 2
        elif ch == "-" and i + 1 < n and spec[i + 1] == "-":
            linestyle = _LINESTYLES["--"]
            i += 2
        elif ch == "-":
            linestyle = _LINESTYLES["-"]
            i += 1
        elif ch == ":":
            linestyle = _LINESTYLES[":"]
            i += 1
        elif ch == ".":
            linestyle = _LINESTYLES["-"]
            i += 1
        else:
            i += 1
    if color is not None:
        kwargs["color"] = color
    if linestyle is not None:
        kwargs["linestyle"] = linestyle
    return kwargs


def _split_plot_args(args: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    """Split plot-style positional/keyword arguments into (data, kwargs)."""
    data: list[Any] = []
    kwargs: dict[str, Any] = {}
    i = 0
    while i < len(args):
        a = args[i]
        if isinstance(a, str):
            nxt = args[i + 1] if i + 1 < len(args) else None
            # A string followed by a value is a property pair, otherwise a
            # line-spec (e.g. 'r--', 'bo').
            if nxt is not None and not isinstance(nxt, str):
                kwargs[_prop_key(a)] = nxt
                i += 2
                continue
            kwargs.update(parse_style(a))
            i += 1
            continue
        data.append(a)
        i += 1
    return data, kwargs


def _prop_key(k: str) -> str:
    return {
        "LineWidth": "linewidth",
        "MarkerSize": "markersize",
        "Color": "color",
        "LineStyle": "linestyle",
        "Marker": "marker",
    }.get(k, k.lower())


# ---------------------------------------------------------------------------
# Graphics state
# ---------------------------------------------------------------------------


class _State:
    def __init__(self) -> None:
        self.hold: dict[int, bool] = {}
        self._last_mappable: Any = None

    def current_axes(self) -> Any:
        ax = plt.gca()
        if not ax.get_label():
            pass
        return ax

    def hold_on(self) -> None:
        self.hold[self._fig_key()] = True

    def hold_off(self) -> None:
        self.hold[self._fig_key()] = False

    def is_hold(self) -> bool:
        return self.hold.get(self._fig_key(), False)

    def _fig_key(self) -> int:
        return id(plt.gcf())

    def prepare_plot(self) -> Any:
        ax = plt.gca()
        if not self.is_hold():
            # clear only the current axes (not other subplots)
            for line in list(ax.get_lines()):
                line.remove()
            for col in list(ax.collections):
                col.remove()
            for img in list(ax.images):
                img.remove()
            for cont in list(ax.containers):
                cont.remove()
            for p in list(ax.patches):
                p.remove()
        return ax

    def reset(self) -> None:
        plt.close("all")
        self.hold.clear()
        self._last_mappable = None


_state = _State()


def _arr(x: Any):
    a = as_array(x)
    if isinstance(a, str):
        raise RuntimeError_("graphics functions require numeric data")
    return a


def figure(n: Any = None) -> Any:
    if n is None:
        return plt.figure()
    return plt.figure(int(float(as_array(n).reshape(-1)[0])))


def gcf() -> Any:
    if not plt.get_fignums():
        plt.figure()
    return plt.gcf()


def gca() -> Any:
    return plt.gca()


def clf() -> None:
    plt.clf()


def close(*args: Any) -> None:
    if not args:
        plt.close()
        return
    a = as_array(args[0])
    if isinstance(a, str):
        if a == "all":
            plt.close("all")
        return
    plt.close(int(float(a.reshape(-1)[0])))


def hold(mode: Any = None) -> None:
    m = str(mode).lower()
    if m == "on":
        _state.hold_on()
    elif m == "off":
        _state.hold_off()
    else:
        raise RuntimeError_("hold expects 'on' or 'off'")


def plot(*args: Any) -> Any:
    data, kwargs = _split_plot_args(list(args))
    ax = _state.prepare_plot()
    if len(data) == 0:
        raise RuntimeError_("plot requires data")
    if len(data) == 1:
        y = _arr(data[0]).flatten()
        x = list(range(1, len(y) + 1))
        return ax.plot(x, y, **kwargs)
    x = _arr(data[0]).flatten()
    y = _arr(data[1]).flatten()
    return ax.plot(x, y, **kwargs)


def _emit_kwargs(args: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    return _split_plot_args(args)


def scatter(*args: Any) -> Any:
    data, kwargs = _emit_kwargs(list(args))
    ax = _state.prepare_plot()
    x = _arr(data[0]).flatten()
    y = _arr(data[1]).flatten()
    if not kwargs:
        kwargs.setdefault("s", 20)
    return ax.scatter(x, y, **kwargs)


def bar(*args: Any) -> Any:
    data, kwargs = _emit_kwargs(list(args))
    ax = _state.prepare_plot()
    x = _arr(data[0]).flatten()
    if len(data) >= 2:
        y = _arr(data[1]).flatten()
    else:
        y = x
        x = list(range(1, len(y) + 1))
    return ax.bar(x, y, **kwargs)


def histogram(*args: Any) -> Any:
    data, kwargs = _emit_kwargs(list(args))
    ax = _state.prepare_plot()
    x = _arr(data[0]).flatten()
    return ax.hist(x, **kwargs)


def stem(*args: Any) -> Any:
    data, kwargs = _emit_kwargs(list(args))
    ax = _state.prepare_plot()
    y = _arr(data[0]).flatten()
    if len(data) >= 2:
        x = _arr(data[1]).flatten()
    else:
        x = list(range(1, len(y) + 1))
    return ax.stem(x, y, **kwargs)


def stairs(*args: Any) -> Any:
    data, kwargs = _emit_kwargs(list(args))
    ax = _state.prepare_plot()
    y = _arr(data[0]).flatten()
    if len(data) >= 2:
        x = _arr(data[1]).flatten()
    else:
        x = list(range(1, len(y) + 1))
    return ax.step(x, y, where="post", **kwargs)


def _scale_plot(func_name: str, *args: Any) -> Any:
    data, kwargs = _emit_kwargs(list(args))
    ax = _state.prepare_plot()
    if len(data) == 1:
        y = _arr(data[0]).flatten()
        x = list(range(1, len(y) + 1))
    else:
        x = _arr(data[0]).flatten()
        y = _arr(data[1]).flatten()
    getattr(ax, func_name)(x, y, **kwargs)
    return ax


def semilogy(*args: Any) -> Any:
    return _scale_plot("semilogy", *args)


def semilogx(*args: Any) -> Any:
    return _scale_plot("semilogx", *args)


def loglog(*args: Any) -> Any:
    return _scale_plot("loglog", *args)


def errorbar(*args: Any) -> Any:
    data, kwargs = _emit_kwargs(list(args))
    ax = _state.prepare_plot()
    x = _arr(data[0]).flatten()
    y = _arr(data[1]).flatten()
    err = _arr(data[2]).flatten()
    return ax.errorbar(x, y, yerr=err, **kwargs)


def fill(*args: Any) -> Any:
    data, kwargs = _emit_kwargs(list(args))
    ax = _state.prepare_plot()
    x = _arr(data[0]).flatten()
    y = _arr(data[1]).flatten()
    return ax.fill(x, y, **kwargs)


def subplot(m: Any, n: Any, p: Any) -> Any:
    m = int(float(as_array(m).reshape(-1)[0]))
    n = int(float(as_array(n).reshape(-1)[0]))
    p = int(float(as_array(p).reshape(-1)[0]))
    return plt.subplot(m, n, p)


def title(txt: Any) -> None:
    plt.title(str(txt))


def xlabel(txt: Any) -> None:
    plt.xlabel(str(txt))


def ylabel(txt: Any) -> None:
    plt.ylabel(str(txt))


def zlabel(txt: Any) -> None:
    ax = plt.gca()
    if hasattr(ax, "set_zlabel"):
        ax.set_zlabel(str(txt))


def legend(*args: Any) -> None:
    labels = [str(a) for a in args]
    ax = plt.gca()
    if labels:
        handles = list(ax.get_lines()) + list(ax.collections)
        ax.legend(handles[: len(labels)], labels)
    else:
        ax.legend()


def grid(mode: Any = None) -> None:
    m = str(mode).lower()
    if m in ("on", "yes"):
        plt.grid(True)
    elif m in ("off", "no"):
        plt.grid(False)
    else:
        plt.grid(True)


def xlim(*args: Any) -> None:
    if len(args) == 1:
        lims = _arr(args[0]).flatten()
        plt.xlim(float(lims[0]), float(lims[1]))
    else:
        plt.xlim(float(as_array(args[0]).reshape(-1)[0]), float(as_array(args[1]).reshape(-1)[0]))


def ylim(*args: Any) -> None:
    if len(args) == 1:
        lims = _arr(args[0]).flatten()
        plt.ylim(float(lims[0]), float(lims[1]))
    else:
        plt.ylim(float(as_array(args[0]).reshape(-1)[0]), float(as_array(args[1]).reshape(-1)[0]))


def zlim(*args: Any) -> None:
    ax = plt.gca()
    if not hasattr(ax, "set_zlim"):
        return
    if len(args) == 1:
        lims = _arr(args[0]).flatten()
        ax.set_zlim(float(lims[0]), float(lims[1]))
    else:
        ax.set_zlim(float(as_array(args[0]).reshape(-1)[0]), float(as_array(args[1]).reshape(-1)[0]))


def axis(mode: Any = None) -> None:
    m = str(mode).lower()
    if m == "tight":
        plt.axis("tight")
    elif m == "equal":
        plt.axis("equal")
    elif m == "square":
        plt.axis("square")
    elif m == "off":
        plt.axis("off")
    elif m == "on":
        plt.axis("on")
    else:
        plt.axis(m)


def _ensure_3d() -> Any:
    ax = plt.gca()
    if hasattr(ax, "plot_surface"):
        return ax
    fig = plt.gcf()
    # If the current axes is an empty auto-created 2D axes, replace it.
    if (
        len(ax.lines) == 0
        and len(ax.collections) == 0
        and len(ax.images) == 0
        and len(ax.patches) == 0
    ):
        ax.remove()
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    ax3 = fig.add_subplot(111, projection="3d")
    plt.sca(ax3)
    return ax3


def surf(X: Any, Y: Any, Z: Any) -> Any:
    ax = _ensure_3d()
    x = _arr(X)
    y = _arr(Y)
    z = _arr(Z)
    return ax.plot_surface(x, y, z)


def mesh(X: Any, Y: Any, Z: Any) -> Any:
    ax = _ensure_3d()
    return ax.plot_wireframe(_arr(X), _arr(Y), _arr(Z))


def view(az: Any, el: Any) -> None:
    ax = plt.gca()
    if hasattr(ax, "view_init"):
        ax.view_init(elev=float(as_array(el).reshape(-1)[0]), azim=float(as_array(az).reshape(-1)[0]))


def imagesc(A: Any, *args: Any) -> Any:
    ax = _state.prepare_plot()
    a = _arr(A)
    img = ax.imshow(a, aspect="auto", origin="upper")
    _state._last_mappable = img
    return img


def image(A: Any, *args: Any) -> Any:
    return imagesc(A, *args)


def colorbar(*args: Any) -> Any:
    ax = plt.gca()
    mappable = _state._last_mappable
    if mappable is None:
        # find the last image/collection in the axes
        if ax.images:
            mappable = ax.images[-1]
        elif ax.collections:
            mappable = ax.collections[-1]
    if mappable is None:
        raise RuntimeError_("colorbar: no image or surface to attach to")
    return plt.colorbar(mappable, ax=ax)


def contour(X: Any, Y: Any, Z: Any, *args: Any) -> Any:
    ax = _state.prepare_plot()
    return ax.contour(_arr(X), _arr(Y), _arr(Z))


def contourf(X: Any, Y: Any, Z: Any, *args: Any) -> Any:
    ax = _state.prepare_plot()
    return ax.contourf(_arr(X), _arr(Y), _arr(Z))


def drawnow() -> None:
    plt.draw()


def show() -> None:
    plt.show()


# Headless ("hardcopy") backends have no window to open; ``plt.show`` on them
# only emits a warning, so skip it entirely.
_NON_INTERACTIVE_BACKENDS = frozenset(
    {"agg", "cairo", "pdf", "pgf", "ps", "svg", "template"}
)


def show_if_any() -> None:
    """Display any open figures (a no-op under headless backends like ``Agg``)."""
    if not plt.get_fignums():
        return
    if matplotlib.get_backend().lower() in _NON_INTERACTIVE_BACKENDS:
        return
    plt.show()


# Accessors used by the graphics test suite.
def figure_count() -> int:
    return len(plt.get_fignums())


def current_figure() -> Any:
    return plt.gcf()


def all_figures() -> list[Any]:
    return [plt.figure(n) for n in plt.get_fignums()]
