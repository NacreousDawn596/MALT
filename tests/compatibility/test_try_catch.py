"""try/catch semantics (see docs/specs/try-catch.md)."""

from __future__ import annotations

from conftest import run_source, scalar


def test_catch_runtime_error():
    ns, _ = run_source(
        "x = 1;\ntry\n x = x + 1;\n y = A(10);\n z = 99;\ncatch\n x = x + 100;\nend\n"
    )
    assert scalar(ns, "x") == 102
    assert "z" not in ns  # statements after the error did not run


def test_catch_var_message():
    ns, _ = run_source(
        "try\n y = A(10);\ncatch err\n msg = err.message;\n ident = err.identifier;\nend\n"
    )
    assert isinstance(ns["msg"], str) and ns["msg"]
    assert isinstance(ns["ident"], str) and ns["ident"]


def test_catch_identifier_is_category():
    ns, _ = run_source(
        "A = [1 2];\ntry\n x = A(5);\ncatch err\n ident = err.identifier;\nend\n"
    )
    # IndexError_ category
    assert "index" in ns["ident"]


def test_skip_catch_on_success():
    ns, _ = run_source(
        "x = 1;\ntry\n x = x + 10;\ncatch\n x = 999;\nend\n"
    )
    assert scalar(ns, "x") == 11


def test_workspace_before_error_persists():
    ns, _ = run_source(
        "a = 5;\ntry\n b = 10;\n c = undefined_thing(1);\nd = 20;\ncatch\nend\n"
    )
    assert scalar(ns, "a") == 5
    assert scalar(ns, "b") == 10
    assert "d" not in ns  # after the error


def test_catch_var_persists_after_block():
    ns, _ = run_source(
        "A = [1 2];\ntry\n x = A(5);\ncatch err\nend\nafter = err.message;\n"
    )
    assert isinstance(ns["after"], str)


def test_nested_try_catch():
    ns, _ = run_source(
        "r = 0;\ntry\n try\n  x = undefined_var(1);\n catch\n  r = r + 1;\n end\ncatch\n r = r + 100;\nend\n"
    )
    assert scalar(ns, "r") == 1  # inner catch handled it


def test_break_inside_catch():
    ns, _ = run_source(
        "s = 0;\nfor k = 1:10\n try\n  if k == 3\n   x = undefined_thing(1);\n  end\n  s = s + k;\n catch\n  continue;\n end\nend\n"
    )
    # k=1,2 added; k=3 errors and continues; k=4..10 added
    assert scalar(ns, "s") == 55 - 3
