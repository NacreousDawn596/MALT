"""Diagnostic helpers: source excerpts and caret indicators."""

from __future__ import annotations

from .errors import SourceLocation


def source_excerpt(source: str, location: SourceLocation, caret_span: int = 1) -> tuple[str, str] | tuple[None, None]:
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


def render_error(error: BaseException, source: str | None = None) -> str:
    """Render a MALT error with excerpt/caret if not already populated."""
    from .errors import MaltError

    if isinstance(error, MaltError):
        if error.excerpt is None and error.location is not None and source is not None:
            excerpt, caret = source_excerpt(source, error.location)
            if excerpt is not None:
                error.excerpt = excerpt
                error.caret = caret
        return error.render()
    return f"error: {error}"
