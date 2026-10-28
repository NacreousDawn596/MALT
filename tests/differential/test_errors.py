"""Error-compatibility tests: MALT and Octave should agree on what errors."""

from __future__ import annotations

import pytest

from malt.errors import MaltError

from . import octave_available, run_malt, run_octave

pytestmark = pytest.mark.skipif(not octave_available(), reason="Octave not installed")


def _malt_errors(src: str) -> bool:
    try:
        run_malt(src)
        return False
    except MaltError:
        return True


def _octave_errors(src: str) -> bool:
    _, err, rc = run_octave(src)
    return rc != 0 or "error" in err.lower()


def _assert_both_error(src: str):
    assert _malt_errors(src), f"MALT did not error:\n{src}"
    assert _octave_errors(src), f"Octave did not error:\n{src}"


def test_index_out_of_bounds_errors():
    _assert_both_error("A = [1 2; 3 4];\nx = A(10);\n")


def test_index_non_integer_errors():
    _assert_both_error("A = [1 2; 3 4];\nx = A(1.5);\n")


def test_dimension_mismatch_errors():
    _assert_both_error("A = [1 2; 3 4];\nB = [1 2 3];\nC = A * B;\n")


def test_matrix_addition_dimension_mismatch():
    _assert_both_error("A = [1 2];\nB = [1 2 3];\nC = A + B;\n")


def test_string_arithmetic_intentional_difference():
    # MATLAB performs char arithmetic on 'char' + number; MALT rejects it.
    # This is an intentional difference (char arrays are not implemented).
    assert _malt_errors("x = 'hello' + 1;\n")
    assert not _octave_errors("x = 'hello' + 1;\n")


def test_undefined_function_errors():
    _assert_both_error("x = no_such_function(1);\n")


def test_undefined_variable_errors():
    _assert_both_error("x = some_undefined_name;\n")


def test_too_many_outputs_errors():
    _assert_both_error("function y = f()\n y = 1;\nend\n[a, b] = f();\n")


def test_missing_end_errors():
    _assert_both_error("if 1 > 0\n x = 1;\n")


def test_singular_solve_does_not_error_malt():
    # MALT falls back to least squares (MATLAB-like); Octave warns but returns.
    # This is an intentional difference: MALT must not crash the REPL.
    try:
        run_malt("A = [1 1; 1 1];\nb = [1; 1];\nx = A \\ b;\n")
    except MaltError:
        pytest.fail("singular solve should not raise in MALT")
