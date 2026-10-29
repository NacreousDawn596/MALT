"""Source-level debugger (malt debug)."""

from __future__ import annotations

import builtins

from malt.compiler import compile_source
from malt.debugger import Debugger


def _drive(source: str, commands: list[str], monkeypatch, capsys):
    unit = compile_source(source, "t.m")
    dbg = Debugger(unit)
    cmds = iter(commands)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(cmds, "q"))
    ns = dbg.run()
    return ns, capsys.readouterr().out


def test_debugger_continue_runs_to_completion(monkeypatch, capsys):
    ns, _ = _drive("x = 1;\ny = x + 2;\n", ["c"], monkeypatch, capsys)
    assert ns["x"] == 1
    assert ns["y"] == 3


def test_debugger_next_and_print(monkeypatch, capsys):
    ns, out = _drive("x = 1;\ny = x + 2;\n", ["n", "p x"], monkeypatch, capsys)
    assert ns["x"] == 1
    assert "1" in out


def test_debugger_breakpoint_stops(monkeypatch, capsys):
    unit = compile_source("x = 1;\ny = x + 2;\nz = 3;\n", "t.m")
    dbg = Debugger(unit)
    dbg.breakpoints.add(3)
    cmds = iter(["c"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(cmds, "q"))
    dbg.run()
    assert "t.m:3" in capsys.readouterr().out


def test_debugger_quit_before_execution(monkeypatch, capsys):
    ns, _ = _drive("x = 1;\n", ["q"], monkeypatch, capsys)
    assert "x" not in ns


def test_debugger_prints_source_context(monkeypatch, capsys):
    _, out = _drive("x = 1;\n", ["q"], monkeypatch, capsys)
    assert "x = 1;" in out
    assert "t.m:1" in out
