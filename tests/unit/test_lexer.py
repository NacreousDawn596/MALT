"""Lexer unit tests."""

from __future__ import annotations

import pytest

from malt.errors import LexError
from malt.lexer import Lexer
from malt.tokens import TokenType


def _types(src: str):
    return [t.type for t in Lexer(src).tokenize()]


def test_numbers():
    toks = Lexer("1 3.14 1e5 2.5e-3 .5 4i 3+4i").tokenize()
    vals = [t.value for t in toks if t.type in (TokenType.INTEGER, TokenType.FLOAT)]
    assert vals[0] == 1
    assert vals[1] == 3.14
    assert vals[2] == 1e5
    assert vals[3] == 2.5e-3
    assert vals[4] == 0.5
    assert vals[5] == 4j
    # `3+4i` tokenizes as INTEGER(3), PLUS, FLOAT(4j)
    assert vals[6] == 3
    assert vals[7] == 4j


def test_operators():
    src = "+ - * / \\ ^ .* ./ .\\ .^ == ~= < <= > >= && || & | ~ : = += -="
    types = _types(src)
    for expected in (
        TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
        TokenType.BACKSLASH, TokenType.CARET, TokenType.DOT_STAR,
        TokenType.DOT_SLASH, TokenType.DOT_BACKSLASH, TokenType.DOT_CARET,
        TokenType.EQ_EQ, TokenType.NE, TokenType.LT, TokenType.LE,
        TokenType.GT, TokenType.GE, TokenType.AND_AND, TokenType.OR_OR,
        TokenType.AMP, TokenType.PIPE, TokenType.TILDE, TokenType.COLON,
        TokenType.EQ, TokenType.PLUS_EQ, TokenType.MINUS_EQ,
    ):
        assert expected in types


def test_transpose_vs_string():
    # after a value, ' is transpose; after an operator, ' starts a string
    toks = Lexer("x' 'hello'").tokenize()
    assert toks[0].type == TokenType.IDENT
    assert toks[1].type == TokenType.TRANSPOSE
    assert toks[2].type == TokenType.STRING
    assert toks[2].value == "hello"


def test_string_escape():
    toks = Lexer("'it''s'").tokenize()
    assert toks[0].value == "it's"


def test_comments():
    toks = Lexer("x = 1 % comment\ny = 2").tokenize()
    idents = [t.value for t in toks if t.type == TokenType.IDENT]
    assert idents == ["x", "y"]


def test_unterminated_string():
    with pytest.raises(LexError):
        Lexer("'abc").tokenize()


def test_unexpected_character():
    with pytest.raises(LexError):
        Lexer("x = $").tokenize()


def test_matrix_unary_minus_spacing():
    # [1 -2 3] -> 1, -2, 3  (three elements)
    toks = Lexer("[1 -2 3]").tokenize()
    minus_spaced = [t.spaced for t in toks if t.type == TokenType.MINUS]
    assert minus_spaced == [True]
