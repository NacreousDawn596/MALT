"""Token definitions for the MALT lexer."""

from __future__ import annotations

import enum

from .errors import SourceLocation


class TokenType(enum.Enum):
    # Literals
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    IDENT = "identifier"

    # Operators
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    BACKSLASH = "\\"
    CARET = "^"
    DOT_STAR = ".*"
    DOT_SLASH = "./"
    DOT_BACKSLASH = ".\\"
    DOT_CARET = ".^"
    TRANSPOSE = "'"
    DOT_TRANSPOSE = ".'"
    DOT = "."
    EQ_EQ = "=="
    NE = "~="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    AND_AND = "&&"
    OR_OR = "||"
    AMP = "&"
    PIPE = "|"
    TILDE = "~"
    COLON = ":"
    EQ = "="
    PLUS_EQ = "+="
    MINUS_EQ = "-="
    STAR_EQ = "*="
    DOT_STAR_EQ = ".*="
    SLASH_EQ = "/="
    DOT_SLASH_EQ = "./="
    BACKSLASH_EQ = "\\="
    DOT_BACKSLASH_EQ = ".\\="
    CARET_EQ = "^="
    DOT_CARET_EQ = ".^="
    AT = "@"

    # Delimiters
    LPAREN = "("
    RPAREN = ")"
    LBRACKET = "["
    RBRACKET = "]"
    LBRACE = "{"
    RBRACE = "}"
    COMMA = ","
    SEMICOLON = ";"

    # Special
    NEWLINE = "newline"
    EOF = "eof"


class Token:
    __slots__ = ("type", "value", "location", "raw", "spaced")

    def __init__(
        self,
        type: TokenType,
        value: object,
        location: SourceLocation,
        raw: str,
        spaced: bool = False,
    ) -> None:
        self.type = type
        self.value = value
        self.location = location
        self.raw = raw
        self.spaced = spaced

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Token({self.type.name}, {self.value!r})"

    @property
    def end_location(self) -> SourceLocation:
        """The inclusive end position of this token (from its raw text)."""
        loc = self.location
        parts = self.raw.split("\n")
        if len(parts) == 1:
            return SourceLocation(
                loc.filename,
                loc.line,
                loc.column + len(self.raw),
                loc.line,
                loc.column + len(self.raw),
            )
        end_line = loc.line + len(parts) - 1
        end_col = loc.column + len(parts[-1])
        return SourceLocation(loc.filename, end_line, end_col, end_line, end_col)
