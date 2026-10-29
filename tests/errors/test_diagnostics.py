"""Structured (JSON) and colored diagnostics."""

from __future__ import annotations

import json

from malt.compiler import compile_source
from malt.diagnostics import color_enabled, render_error
from malt.errors import IndexError_, UndefinedVariableError
from malt.executor import execute


def _run(src: str, exc: type[Exception]) -> Exception:
    unit = compile_source(src, "t.m")
    try:
        execute(unit)
    except exc as e:
        return e
    raise AssertionError(f"expected {exc.__name__}")


def test_error_code_in_text_render():
    e = _run("A = [1 2];\ndisp(A(5));", IndexError_)
    rendered = render_error(e, source="A = [1 2];\ndisp(A(5));", color=False)
    assert "[E2001]" in rendered


def test_json_render_has_code_and_location():
    e = _run("disp(undefined_var);", UndefinedVariableError)
    data = json.loads(render_error(e, source="disp(undefined_var);", style="json"))
    assert data["severity"] == "error"
    assert data["code"] == "E2003"
    assert data["category"] == "undefined variable"
    assert data["location"]["filename"] == "t.m"
    assert data["location"]["line"] == 1


def test_hint_rendered_on_help_line():
    e = _run("disp(undefined_var);", UndefinedVariableError)
    rendered = render_error(e, source="disp(undefined_var);", color=False)
    assert "help:" in rendered
    assert "case-sensitive" in rendered


def test_colored_render_has_ansi_codes():
    e = _run("disp(undefined_var);", UndefinedVariableError)
    colored = render_error(e, source="disp(undefined_var);", color=True)
    plain = render_error(e, source="disp(undefined_var);", color=False)
    assert "\x1b[" in colored
    assert "\x1b[" not in plain


def test_color_enabled_override():
    assert color_enabled(override=True) is True
    assert color_enabled(override=False) is False


def test_color_env_vars(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setenv("NO_COLOR", "1")
    assert color_enabled(override=None) is False
    monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert color_enabled(override=None) is True


def test_non_malt_error_json_fallback():
    out = json.loads(render_error(RuntimeError("boom"), style="json"))
    assert out["severity"] == "error"
    assert "boom" in out["message"]
