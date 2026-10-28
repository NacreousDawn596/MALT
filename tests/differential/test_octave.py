"""Differential tests: run the same ``.m`` source through MALT and GNU Octave.

Skipped automatically when Octave is not installed. Numeric output is emitted
with ``fprintf('%g ', ...)`` so both runtimes produce identical canonical text
(Octave's ``disp`` wraps wide matrices into "Column" headers and formats complex
numbers differently, which are display-only differences). This compares
language *semantics*: values and their order.
"""

from __future__ import annotations

import re

import numpy as np
import pytest

from . import octave_available, run_malt, run_octave

pytestmark = pytest.mark.skipif(
    not octave_available(), reason="GNU Octave (octave-cli) not installed"
)


def _floats(text: str) -> list[float]:
    return [float(m) for m in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)]


def _assert_same(src: str, atol: float = 1e-9):
    malt_out, _ = run_malt(src)
    oct_out, oct_err, oct_rc = run_octave(src)
    assert oct_rc == 0, f"Octave failed:\n{oct_err}"
    m = _floats(malt_out)
    o = _floats(oct_out)
    assert len(m) == len(o), f"value count differs:\nMALT={malt_out}\nOCT={oct_out}"
    np.testing.assert_allclose(m, o, atol=atol, err_msg=f"MALT={malt_out}\nOCT={oct_out}")


def _fmt(*values) -> str:
    return "".join(f"fprintf('%g ', {v});" for v in values)


# ---------------------------------------------------------------------------
# Arithmetic and precedence
# ---------------------------------------------------------------------------


def test_scalar_arithmetic_precedence():
    _assert_same(
        "fprintf('%g ', 2 + 3 * 4);\nfprintf('%g ', (2 + 3) * 4);\nfprintf('%g ', 2 ^ 3);\n"
        "fprintf('%g ', 10 / 4);\nfprintf('%g ', 10 \\ 4);\n"
    )


def test_elementwise_vs_matrix():
    _assert_same(
        "A = [1 2; 3 4];\nB = [5 6; 7 8];\n"
        "fprintf('%g ', A * B);\nfprintf('%g ', A .* B);\nfprintf('%g ', A + B);\nfprintf('%g ', A ./ B);\n"
    )


def test_power():
    _assert_same("fprintf('%g ', 2 ^ 10);\nfprintf('%g ', 2 .^ 10);\nfprintf('%g ', [1 2; 3 4] ^ 2);\n")


def test_transpose():
    _assert_same(
        "A = [1+2i 3+4i; 5+6i 7+8i];\n"
        "fprintf('%g ', real(A'));\nfprintf('%g ', imag(A'));\n"
        "fprintf('%g ', real(A.'));\nfprintf('%g ', imag(A.'));\n"
    )


def test_comparisons_and_logic():
    _assert_same(
        "fprintf('%g ', 1 < 2);\nfprintf('%g ', 2 <= 2);\nfprintf('%g ', 3 > 4);\n"
        "fprintf('%g ', 1 & 0);\nfprintf('%g ', 1 | 0);\nfprintf('%g ', ~1);\nfprintf('%g ', 1 && 0);\nfprintf('%g ', 0 || 3);\n"
    )


# ---------------------------------------------------------------------------
# Arrays, shapes, indexing
# ---------------------------------------------------------------------------


def test_matrix_construction_and_size():
    _assert_same(
        "A = [1 2; 3 4];\nfprintf('%g ', A);\nfprintf('%g ', size(A));\nfprintf('%g ', numel(A));\nfprintf('%g ', ndims(A));\nfprintf('%g ', length(A));\n"
    )


def test_row_and_column_vectors():
    _assert_same("r = [1 2 3];\nc = [1; 2; 3];\nfprintf('%g ', size(r));\nfprintf('%g ', size(c));\n")


def test_one_based_indexing():
    _assert_same(
        "A = [10 20 30; 40 50 60];\nfprintf('%g ', A(1,2));\nfprintf('%g ', A(2,1));\n"
        "fprintf('%g ', A(:,2));\nfprintf('%g ', A(2,:));\nfprintf('%g ', A(end));\n"
    )


def test_linear_indexing_column_major():
    _assert_same(
        "A = [1 2 3; 4 5 6];\nfprintf('%g ', A(3));\nfprintf('%g ', A(6));\nfprintf('%g ', A([1 3 5]));\nfprintf('%g ', A(:));\n"
    )


def test_colon_semantics():
    _assert_same(
        "fprintf('%g ', 1:5);\nfprintf('%g ', 1:2:10);\nfprintf('%g ', 10:-1:1);\nfprintf('%g ', 10:-2:1);\nfprintf('%g ', 0:0.5:2);\nfprintf('%g ', 3:3);\n"
    )


def test_colon_empty():
    _assert_same("fprintf('%g ', size(1:0));\nfprintf('%g ', size(10:1));\nfprintf('%g ', size(10:-1:20));\n")


def test_column_major_reshape():
    _assert_same("fprintf('%g ', reshape([1 2 3 4 5 6], 2, 3));\n")


# ---------------------------------------------------------------------------
# Loops and control flow
# ---------------------------------------------------------------------------


def test_loop_accumulation():
    _assert_same("total = 0;\nfor k = 1:100\n total = total + k;\nend\nfprintf('%g ', total);\n")


def test_loop_variable_persists():
    _assert_same("for k = 1:7\nend\nfprintf('%g ', k);\n")


def test_loop_descending():
    _assert_same("s = 0;\nfor k = 10:-1:1\n s = s + k;\nend\nfprintf('%g ', s);\n")


def test_nested_loops():
    _assert_same(
        "s = 0;\nfor i = 1:10\n for j = 1:10\n  s = s + i*j;\n end\nend\nfprintf('%g ', s);\n"
    )


def test_while_loop():
    _assert_same("x = 0;\nwhile x < 10\n x = x + 3;\nend\nfprintf('%g ', x);\n")


def test_conditionals():
    _assert_same(
        "x = -5;\nif x > 0\n r = 1;\nelseif x < 0\n r = -1;\nelse\n r = 0;\nend\nfprintf('%g ', r);\n"
    )


def test_break_continue():
    _assert_same(
        "s = 0;\nfor k = 1:10\n if k == 5\n  continue;\n end\n if k == 8\n  break;\n end\n s = s + k;\nend\nfprintf('%g ', s);\n"
    )


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def test_multi_output_function():
    _assert_same(
        "function [s, p] = stats(a, b)\n s = a + b;\n p = a * b;\nend\n[x, y] = stats(3, 4);\nfprintf('%g ', x);\nfprintf('%g ', y);\n"
    )


def test_single_output_function():
    _assert_same("function y = sq(x)\n y = x * x;\nend\nfprintf('%g ', sq(9));\n")


def test_anonymous_function():
    _assert_same("f = @(x) x .^ 2 + 1;\nfprintf('%g ', f(3));\nfprintf('%g ', f(10));\n")


# ---------------------------------------------------------------------------
# Complex and numerical
# ---------------------------------------------------------------------------


def test_complex_arithmetic():
    _assert_same(
        "z = 3 + 4i;\nfprintf('%g ', abs(z));\nfprintf('%g ', real(z));\nfprintf('%g ', imag(z));\n"
        "fprintf('%g ', real(conj(z)));\nfprintf('%g ', imag(conj(z)));\nfprintf('%g ', angle(z));\n"
    )


def test_reductions():
    _assert_same(
        "A = [1 2 3; 4 5 6];\nfprintf('%g ', sum(A));\nfprintf('%g ', sum(A, 2));\nfprintf('%g ', mean(A));\n"
        "fprintf('%g ', max(A));\nfprintf('%g ', min(A));\nfprintf('%g ', prod(A));\n"
    )


def test_cumulative_and_sort():
    _assert_same(
        "A = [1 3 2; 6 5 4];\nfprintf('%g ', cumsum(A));\nfprintf('%g ', sort(A));\n"
    )


def test_linear_solve():
    _assert_same("A = [4 1; 1 3];\nb = [1; 2];\nfprintf('%g ', A \\ b);\n")


def test_eig():
    _assert_same("fprintf('%g ', eig([2 1; 1 2]));\n")


def test_math_functions():
    _assert_same(
        "fprintf('%g ', sin(0));\nfprintf('%g ', cos(0));\nfprintf('%g ', sqrt(9));\nfprintf('%g ', exp(0));\nfprintf('%g ', log(1));\n"
        "fprintf('%g ', floor(2.7));\nfprintf('%g ', ceil(2.1));\nfprintf('%g ', round(2.5));\nfprintf('%g ', round(-2.5));\nfprintf('%g ', abs(-5));\n"
    )
