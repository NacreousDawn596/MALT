"""Error-handling and diagnostics tests."""

from __future__ import annotations

import pytest

from malt.compiler import compile_source
from malt.errors import (
    DimensionError,
    IndexError_,
    LexError,
    MaltError,
    ParseError,
    SemanticError,
)
from malt.executor import execute


def _raises(src: str, exc: type[MaltError]):
    unit = compile_source(src, "err.m")
    with pytest.raises(exc):
        execute(unit)


def test_syntax_error_has_location():
    from malt.diagnostics import render_error

    try:
        compile_source("x = [1 2; 3 4", "test.m")
    except ParseError as e:
        rendered = render_error(e, source="x = [1 2; 3 4")
        assert "test.m:1" in rendered
    else:
        raise AssertionError("expected ParseError")


def test_undefined_variable_is_runtime_error():
    unit = compile_source("disp(y);", "u.m")
    with pytest.raises(MaltError):
        execute(unit)


def test_index_out_of_bounds():
    _raises("A = [1 2; 3 4];\ndisp(A(10, 1));", IndexError_)


def test_dimension_mismatch():
    _raises("A = [1 2; 3 4];\nB = [1 2 3];\nC = A * B;", DimensionError)


def test_break_outside_loop():
    with pytest.raises(SemanticError):
        compile_source("break;", "b.m")


def test_unterminated_string():
    with pytest.raises(LexError):
        compile_source("x = 'abc;", "s.m")


def test_error_diagnostic_excerpt():
    from malt.diagnostics import render_error

    src = "A = [1 2; 3 4];\ndisp(A(10,1));"
    unit = compile_source(src, "test.m")
    try:
        execute(unit)
    except IndexError_ as e:
        rendered = render_error(e, source=src)
        assert "test.m:2" in rendered
        assert "disp(A(10,1))" in rendered
    else:
        raise AssertionError("expected IndexError_")


def test_singular_solve_does_not_crash():
    # A singular system should fall back to least squares, not raise.
    unit = compile_source("A = [1 1; 1 1];\nb = [1; 1];\nx = A \\ b;", "s.m")
    ns = execute(unit)
    assert "x" in ns
