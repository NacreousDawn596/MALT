"""Source locations and the MALT exception hierarchy."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceLocation:
    """A position within a source file."""

    filename: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.filename}:{self.line}:{self.column}"


@dataclass
class Diagnostic:
    """A non-fatal diagnostic (warning or note) attached to a source location.

    Unlike :class:`MaltError`, a ``Diagnostic`` is collected rather than
    raised, so a single compilation can report many of them.
    """

    severity: str  # "warning" | "note"
    code: str
    message: str
    location: SourceLocation | None = None
    hint: str | None = None

    def to_dict(self) -> dict[str, object]:
        loc = self.location
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "location": (
                {
                    "filename": loc.filename,
                    "line": loc.line,
                    "column": loc.column,
                }
                if loc is not None
                else None
            ),
            "hint": self.hint,
        }


class MaltError(Exception):
    """Base class for all MALT-reported errors.

    ``code`` is a stable, tool-friendly identifier (e.g. ``E2001``) useful for
    editors, LSP clients, and documentation. ``hint`` is optional guidance
    rendered on a separate ``help:`` line.
    """

    category = "error"
    code = "E0000"

    def __init__(
        self,
        message: str,
        location: SourceLocation | None = None,
        excerpt: str | None = None,
        caret: str | None = None,
        note: str | None = None,
        hint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.location = location
        self.excerpt = excerpt
        self.caret = caret
        self.note = note
        self.hint = hint

    def render(self) -> str:
        parts: list[str] = []
        if self.location is not None:
            parts.append(
                f"{self.location}: {self.category} [{self.code}]: {self.message}"
            )
        else:
            parts.append(f"{self.category} [{self.code}]: {self.message}")
        if self.excerpt is not None:
            parts.append("")
            parts.append(self.excerpt)
            if self.caret is not None:
                parts.append(self.caret)
        if self.note is not None:
            parts.append(f"note: {self.note}")
        if self.hint is not None:
            parts.append(f"help: {self.hint}")
        return "\n".join(parts)

    def to_dict(self) -> dict[str, object]:
        """A structured, JSON-serializable view of this error."""
        loc = self.location
        return {
            "severity": "error",
            "code": self.code,
            "category": self.category,
            "message": self.message,
            "location": (
                {
                    "filename": loc.filename,
                    "line": loc.line,
                    "column": loc.column,
                }
                if loc is not None
                else None
            ),
            "excerpt": self.excerpt,
            "note": self.note,
            "hint": self.hint,
        }


class LexError(MaltError):
    category = "lex error"
    code = "E1001"


class ParseError(MaltError):
    category = "parse error"
    code = "E1002"


class SemanticError(MaltError):
    category = "semantic error"
    code = "E1003"


class CodegenError(MaltError):
    category = "code generation error"
    code = "E1004"


class RuntimeError_(MaltError):
    """Runtime error, distinct from the builtin ``RuntimeError``."""

    category = "runtime error"
    code = "E2000"


class IndexError_(RuntimeError_):
    category = "index exceeds array dimensions"
    code = "E2001"


class DimensionError(RuntimeError_):
    category = "dimension mismatch"
    code = "E2002"


class UndefinedVariableError(RuntimeError_):
    category = "undefined variable"
    code = "E2003"


class UnsupportedFeatureError(MaltError):
    category = "unsupported feature"
    code = "E3000"


class ReturnSignal(Exception):
    """Internal control-flow signal used to implement top-level ``return``."""

    def __init__(self) -> None:
        super().__init__("malt return signal")
