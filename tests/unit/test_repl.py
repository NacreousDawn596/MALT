"""REPL: completeness detection and command handling."""

from __future__ import annotations

from malt.repl.session import Repl, _is_incomplete


def test_is_incomplete_blocks():
    assert _is_incomplete("if x > 1") is True
    assert _is_incomplete("for i = 1:3") is True
    assert _is_incomplete("while true") is True
    assert _is_incomplete("if x > 1\n  disp(x)\nend") is False


def test_is_incomplete_brackets():
    assert _is_incomplete("A = [1 2;") is True
    assert _is_incomplete("A = [1 2; 3 4];") is False
    assert _is_incomplete("f = @(x) x.^2") is False


def test_is_incomplete_line_continuation():
    assert _is_incomplete("x = 1 + ...") is True
    assert _is_incomplete("x = 1;") is False


def test_is_incomplete_end_as_index():
    assert _is_incomplete("x = A(end);") is False


def test_repl_handle_expression(capsys):
    r = Repl()
    r._handle("x = 2 + 3;")
    assert r.namespace["x"] == 5


def test_repl_handle_whos(capsys):
    r = Repl()
    r._handle("A = [1 2; 3 4];")
    r._handle("whos")
    out = capsys.readouterr().out
    assert "A" in out
    assert "2x2" in out


def test_repl_handle_clear(capsys):
    r = Repl()
    r._handle("x = 1;")
    r._handle("clear")
    assert "x" not in r.namespace


def test_repl_handle_exit():
    r = Repl()
    assert r._handle("exit") == "quit"
    assert r._handle("quit") == "quit"
