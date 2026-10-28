"""Lexer for MALT MATLAB-like source."""

from __future__ import annotations

from .errors import LexError, SourceLocation
from .tokens import Token, TokenType

# Tokens whose presence signals an operand (not a value) precedes a quote.
_OPERAND_PRECEDERS = frozenset(
    {
        TokenType.IDENT,
        TokenType.INTEGER,
        TokenType.FLOAT,
        TokenType.STRING,
        TokenType.RPAREN,
        TokenType.RBRACKET,
        TokenType.RBRACE,
        TokenType.TRANSPOSE,
        TokenType.DOT_TRANSPOSE,
    }
)

_TWO_CHAR_OPS = {
    ".*": TokenType.DOT_STAR,
    "./": TokenType.DOT_SLASH,
    ".\\": TokenType.DOT_BACKSLASH,
    ".^": TokenType.DOT_CARET,
    ".'": TokenType.DOT_TRANSPOSE,
    "==": TokenType.EQ_EQ,
    "~=": TokenType.NE,
    "<=": TokenType.LE,
    ">=": TokenType.GE,
    "&&": TokenType.AND_AND,
    "||": TokenType.OR_OR,
}

_THREE_CHAR_OPS = {
    ".*=": TokenType.DOT_STAR_EQ,
    "./=": TokenType.DOT_SLASH_EQ,
    ".\\=": TokenType.DOT_BACKSLASH_EQ,
    ".^=": TokenType.DOT_CARET_EQ,
}

_ONE_CHAR_OPS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "\\": TokenType.BACKSLASH,
    "^": TokenType.CARET,
    "'": TokenType.TRANSPOSE,
    "&": TokenType.AMP,
    "|": TokenType.PIPE,
    "~": TokenType.TILDE,
    ":": TokenType.COLON,
    "=": TokenType.EQ,
    "@": TokenType.AT,
    "<": TokenType.LT,
    ">": TokenType.GT,
}

_COMPOUND_OPS = {
    "+=": TokenType.PLUS_EQ,
    "-=": TokenType.MINUS_EQ,
    "*=": TokenType.STAR_EQ,
    "/=": TokenType.SLASH_EQ,
    "\\=": TokenType.BACKSLASH_EQ,
    "^=": TokenType.CARET_EQ,
}

_DELIMITERS = {
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    ",": TokenType.COMMA,
    ";": TokenType.SEMICOLON,
}

_IDENT_START = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
_IDENT_CONT = _IDENT_START | set("0123456789")
_DIGITS = set("0123456789")


class Lexer:
    def __init__(self, source: str, filename: str = "<malt>") -> None:
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []
        self._prev_significant: TokenType | None = None
        self._pending_space = False

    def _loc(self) -> SourceLocation:
        return SourceLocation(self.filename, self.line, self.col)

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return ""

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _emit(self, type: TokenType, value: object, raw: str, loc: SourceLocation) -> None:
        self.tokens.append(Token(type, value, loc, raw, spaced=self._pending_space))
        self._pending_space = False
        self._prev_significant = type

    def _error(self, message: str) -> None:
        raise LexError(message, self._loc())

    def tokenize(self) -> list[Token]:
        while self.pos < len(self.source):
            ch = self._peek()

            if ch == "\n":
                loc = self._loc()
                self._advance()
                self._emit(TokenType.NEWLINE, "\n", "\n", loc)
                continue

            if ch in " \t\r\f\v":
                self._advance()
                self._pending_space = True
                continue

            if ch == "%":
                self._skip_comment()
                continue

            if ch in _DIGITS or (ch == "." and self._peek(1) in _DIGITS):
                self._read_number()
                continue

            if ch in _IDENT_START:
                self._read_ident()
                continue

            if ch == "'":
                if self._prev_significant in _OPERAND_PRECEDERS:
                    self._emit(TokenType.TRANSPOSE, "'", "'", self._loc())
                    self._advance()
                    continue
                self._read_string()
                continue

            # Three-character operators
            three = self.source[self.pos : self.pos + 3]
            if three in _THREE_CHAR_OPS:
                loc = self._loc()
                for _ in range(3):
                    self._advance()
                self._emit(_THREE_CHAR_OPS[three], three, three, loc)
                continue

            two = self.source[self.pos : self.pos + 2]
            if two in _TWO_CHAR_OPS:
                loc = self._loc()
                for _ in range(2):
                    self._advance()
                self._emit(_TWO_CHAR_OPS[two], two, two, loc)
                continue

            if two in _COMPOUND_OPS:
                loc = self._loc()
                for _ in range(2):
                    self._advance()
                self._emit(_COMPOUND_OPS[two], two, two, loc)
                continue

            if ch in _ONE_CHAR_OPS:
                loc = self._loc()
                self._emit(_ONE_CHAR_OPS[ch], ch, ch, loc)
                self._advance()
                continue

            if ch in _DELIMITERS:
                loc = self._loc()
                self._emit(_DELIMITERS[ch], ch, ch, loc)
                self._advance()
                continue

            self._error(f"unexpected character {ch!r}")

        self._emit(TokenType.EOF, None, "", self._loc())
        return self.tokens

    def _skip_comment(self) -> None:
        while self.pos < len(self.source) and self._peek() != "\n":
            self._advance()

    def _read_ident(self) -> None:
        start = self.pos
        loc = self._loc()
        while self.pos < len(self.source) and self._peek() in _IDENT_CONT:
            self._advance()
        text = self.source[start : self.pos]
        self._emit(TokenType.IDENT, text, text, loc)

    def _read_number(self) -> None:
        start = self.pos
        loc = self._loc()
        is_float = False

        # integer or leading-dot fraction
        if self._peek() in _DIGITS:
            while self.pos < len(self.source) and self._peek() in _DIGITS:
                self._advance()
            if self._peek() == "." and self._peek(1) != "'":
                # `.` followed by `.` would be `..` — treat single dot as fraction
                if self._peek(1) in _DIGITS or self._peek(1) not in ".\\^*/":
                    is_float = True
                    self._advance()  # consume '.'
                    while self.pos < len(self.source) and self._peek() in _DIGITS:
                        self._advance()
        elif self._peek() == ".":
            is_float = True
            self._advance()
            while self.pos < len(self.source) and self._peek() in _DIGITS:
                self._advance()

        # exponent
        if self._peek() in "eE":
            nxt = self._peek(1)
            if nxt in _DIGITS or (nxt in "+-" and self._peek(2) in _DIGITS):
                is_float = True
                self._advance()
                if self._peek() in "+-":
                    self._advance()
                while self.pos < len(self.source) and self._peek() in _DIGITS:
                    self._advance()

        # imaginary suffix
        imag = False
        if self._peek() in "ij":
            nxt = self._peek(1)
            if nxt not in _IDENT_CONT:
                imag = True
                self._advance()

        raw = self.source[start : self.pos]
        if imag:
            # value becomes a pure imaginary complex
            if is_float or ("." in raw or "e" in raw.lower()):
                value = complex(0.0, float(raw[:-1]))
            else:
                value = complex(0.0, float(raw[:-1]))
            self._emit(TokenType.FLOAT, value, raw, loc)
            return

        if is_float:
            value = float(raw)
            self._emit(TokenType.FLOAT, value, raw, loc)
        else:
            value = int(raw)
            self._emit(TokenType.INTEGER, value, raw, loc)

    def _read_string(self) -> None:
        loc = self._loc()
        self._advance()  # opening quote
        chars: list[str] = []
        while True:
            if self.pos >= len(self.source):
                self._error("unterminated string literal")
            ch = self._peek()
            if ch == "'":
                if self._peek(1) == "'":
                    chars.append("'")
                    self._advance()
                    self._advance()
                    continue
                self._advance()
                break
            if ch == "\n":
                self._error("newline in string literal (use a char vector without newline)")
            chars.append(ch)
            self._advance()
        self._emit(TokenType.STRING, "".join(chars), "'" + "".join(chars) + "'", loc)
