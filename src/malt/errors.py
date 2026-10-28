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


class MaltError(Exception):
    """Base class for all MALT-reported errors."""

    category = "error"

    def __init__(
        self,
        message: str,
        location: SourceLocation | None = None,
        excerpt: str | None = None,
        caret: str | None = None,
        note: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.location = location
        self.excerpt = excerpt
        self.caret = caret
        self.note = note

    def render(self) -> str:
        parts: list[str] = []
        if self.location is not None:
            parts.append(f"{self.location}: {self.category}: {self.message}")
        else:
            parts.append(f"{self.category}: {self.message}")
        if self.excerpt is not None:
            parts.append("")
            parts.append(self.excerpt)
            if self.caret is not None:
                parts.append(self.caret)
        if self.note is not None:
            parts.append(self.note)
        return "\n".join(parts)


class LexError(MaltError):
    category = "lex error"


class ParseError(MaltError):
    category = "parse error"


class SemanticError(MaltError):
    category = "semantic error"


class CodegenError(MaltError):
    category = "code generation error"


class RuntimeError_(MaltError):
    """Runtime error, distinct from the builtin ``RuntimeError``."""

    category = "runtime error"


class IndexError_(RuntimeError_):
    category = "index exceeds array dimensions"


class DimensionError(RuntimeError_):
    category = "dimension mismatch"


class UndefinedVariableError(RuntimeError_):
    category = "undefined variable"


class UnsupportedFeatureError(MaltError):
    category = "unsupported feature"


class ReturnSignal(Exception):
    """Internal control-flow signal used to implement top-level ``return``."""

    def __init__(self) -> None:
        super().__init__("malt return signal")
