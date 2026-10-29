"""Diagnostic helpers: source excerpts, caret indicators, and rendering.

Rendering supports two output styles:

- ``text`` — the human-readable, optionally colorized form (the default).
- ``json`` — a structured, machine-readable form for editors and tooling
  (e.g. an LSP client), via :func:`render_error_json`.

Color is enabled by default only when the output stream is a TTY. It honors
the conventional ``NO_COLOR``/``FORCE_COLOR`` environment variables and can be
forced on/off with the ``color`` argument.
"""

from __future__ import annotations

import json
import os
import sys

from .errors import MaltError, SourceLocation

# ---------------------------------------------------------------------------
# ANSI color helpers
# ---------------------------------------------------------------------------

_ANSI = {
    "bold": "\x1b[1m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "cyan": "\x1b[36m",
    "reset": "\x1b[0m",
}


def color_enabled(stream: object | None = None, override: bool | None = None) -> bool:
    """Decide whether ANSI color should be emitted.

    Precedence: explicit ``override`` > ``NO_COLOR``/``FORCE_COLOR`` env vars >
    whether ``stream`` is a TTY.
    """
    if override is not None:
        return override
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    stream = stream if stream is not None else sys.stderr
    isatty = getattr(stream, "isatty", lambda: False)
    try:
        return bool(isatty())
    except Exception:
        return False


def _wrap(text: str, *styles: str, enabled: bool) -> str:
    if not enabled:
        return text
    prefix = "".join(_ANSI[s] for s in styles)
    return f"{prefix}{text}{_ANSI['reset']}"


# ---------------------------------------------------------------------------
# Source excerpts
# ---------------------------------------------------------------------------


def source_excerpt(
    source: str, location: SourceLocation, caret_span: int = 1
) -> tuple[str, str] | tuple[None, None]:
    """Return a ``(excerpt, caret)`` pair for a source location, or ``(None, None)``."""
    lines = source.splitlines()
    idx = location.line - 1
    if idx < 0 or idx >= len(lines):
        return None, None
    text = lines[idx]
    line_no = str(location.line)
    gutter = " " * (len(line_no) + 2)
    excerpt = f"{line_no} | {text}"
    col = max(0, location.column - 1)
    caret = f"{gutter}| {' ' * col}{'^' * max(1, caret_span)}"
    return excerpt, caret


def _populate(error: MaltError, source: str | None) -> None:
    """Fill excerpt/caret from ``source`` if not already present."""
    if error.excerpt is None and error.location is not None and source is not None:
        excerpt, caret = source_excerpt(source, error.location)
        if excerpt is not None:
            error.excerpt = excerpt
            error.caret = caret


# ---------------------------------------------------------------------------
# Text rendering
# ---------------------------------------------------------------------------


def _render_text(error: MaltError, enabled: bool) -> str:
    parts: list[str] = []
    if error.location is not None:
        loc = _wrap(str(error.location), "bold", enabled=enabled)
        cat = _wrap(error.category, "red", "bold", enabled=enabled)
        code = _wrap(f"[{error.code}]", "cyan", enabled=enabled)
        msg = _wrap(error.message, "bold", enabled=enabled)
        parts.append(f"{loc}: {cat} {code}: {msg}")
    else:
        cat = _wrap(error.category, "red", "bold", enabled=enabled)
        code = _wrap(f"[{error.code}]", "cyan", enabled=enabled)
        parts.append(f"{cat} {code}: {error.message}")
    if error.excerpt is not None:
        parts.append("")
        parts.append(error.excerpt)
        if error.caret is not None:
            parts.append(_wrap(error.caret, "red", enabled=enabled))
    if error.note is not None:
        label = _wrap("note", "blue", "bold", enabled=enabled)
        parts.append(f"{label}: {error.note}")
    if error.hint is not None:
        label = _wrap("help", "cyan", "bold", enabled=enabled)
        parts.append(f"{label}: {error.hint}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def render_error(
    error: BaseException,
    source: str | None = None,
    *,
    color: bool | None = None,
    style: str = "text",
) -> str:
    """Render a MALT error to a string.

    ``style`` is ``"text"`` (default) or ``"json"``. ``color`` overrides the
    automatic TTY/``NO_COLOR`` detection when not ``None``.
    """
    if isinstance(error, MaltError):
        _populate(error, source)
        if style == "json":
            return json.dumps(error.to_dict(), indent=2)
        return _render_text(error, color_enabled(override=color))
    if style == "json":
        return json.dumps({"severity": "error", "message": str(error)})
    return f"error: {error}"


def render_error_json(error: BaseException, source: str | None = None) -> str:
    """Render a MALT error as an indented JSON string."""
    return render_error(error, source, style="json")
