"""Randomized, bounded differential tests: generated programs vs Octave."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from . import check_structured, octave_available

pytestmark = pytest.mark.skipif(not octave_available(), reason="Octave not installed")


def _lit(rows):
    return "[" + "; ".join(" ".join(str(v) for v in row) for row in rows) + "]"


@settings(max_examples=80, deadline=None)
@given(
    st.integers(min_value=1, max_value=3).flatmap(
        lambda n: st.tuples(
            st.lists(st.lists(st.integers(-5, 5), min_size=n, max_size=n), min_size=n, max_size=n),
            st.lists(st.lists(st.integers(-5, 5), min_size=n, max_size=n), min_size=n, max_size=n),
        )
    )
)
def test_random_matrix_ops_match_octave(ab):
    a_rows, b_rows = ab
    A = _lit(a_rows)
    B = _lit(b_rows)
    body = (
        f"A = {A};\nB = {B};\n"
        "emit(A + B);\nemit(A - B);\nemit(A .* B);\nemit(A * B);\n"
        "emit(A');\nemit(sum(A));\nemit(mean(A));\nemit(A * A');\n"
    )
    check_structured(body)


@settings(max_examples=60, deadline=None)
@given(st.lists(st.integers(-9, 9), min_size=1, max_size=12))
def test_random_vector_ops_match_octave(vals):
    v = "[" + " ".join(str(x) for x in vals) + "]"
    body = (
        f"v = {v};\n"
        "emit(v);\nemit(sum(v));\nemit(v .^ 2);\nemit(v * v');\nemit(v');\n"
    )
    check_structured(body)


@settings(max_examples=40, deadline=None)
@given(
    st.integers(min_value=-10, max_value=10),
    st.integers(min_value=-10, max_value=10).filter(lambda x: x != 0),
    st.integers(min_value=-10, max_value=10),
)
def test_random_colon_match_octave(start, step, end):
    body = f"emit({start}:{step}:{end});\nemit(sum({start}:{step}:{end}));\n"
    check_structured(body)


@settings(max_examples=40, deadline=None)
@given(
    st.lists(st.integers(-9, 9), min_size=1, max_size=6),
    st.integers(min_value=1, max_value=3),
    st.integers(min_value=1, max_value=3),
)
def test_random_reshape_match_octave(vals, m, n):
    if len(vals) != m * n:
        return
    v = "[" + " ".join(str(x) for x in vals) + "]"
    body = f"emit(reshape({v}, {m}, {n}));\n"
    check_structured(body)


@settings(max_examples=30, deadline=None)
@given(
    st.integers(min_value=1, max_value=50),
    st.integers(min_value=-20, max_value=20),
)
def test_random_loop_accumulation_match_octave(n, start):
    body = (
        f"total = 0;\nfor k = 1:{n}\n total = total + k * {start};\nend\nemit(total);\nemit(k);\n"
    )
    check_structured(body)
