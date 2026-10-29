"""Non-fatal semantic warnings (shadowing builtins / imaginary unit)."""

from __future__ import annotations

from malt.compiler import compile_source


def test_shadowing_builtin_warns():
    unit = compile_source("sin = 5;\n", "w.m")
    codes = [w.code for w in unit.warnings]
    assert "W1001" in codes
    assert any("sin" in w.message for w in unit.warnings)


def test_shadowing_imaginary_unit_warns():
    unit = compile_source("for i = 1:3\n x = i;\nend\n", "w.m")
    codes = [w.code for w in unit.warnings]
    assert "W1002" in codes


def test_loop_variable_jj_is_clean():
    unit = compile_source("for jj = 1:3\n x = jj;\nend\n", "w.m")
    assert not any(w.code == "W1002" for w in unit.warnings)


def test_normal_code_has_no_warnings():
    unit = compile_source("x = 1 + 2;\ny = sin(x);\n", "w.m")
    assert unit.warnings == []


def test_warning_has_location_and_hint():
    unit = compile_source("sin = 5;\n", "w.m")
    w = unit.warnings[0]
    assert w.location is not None
    assert w.location.line == 1
    assert w.hint is not None
