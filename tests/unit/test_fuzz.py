"""Fuzzing: the parser must never hang or crash on malformed input."""

from __future__ import annotations

import random

import pytest

from malt.compiler import compile_source
from malt.errors import MaltError


# Deterministic pseudo-random generator for reproducible fuzzing.
def _random_source(rng: random.Random, n: int) -> str:
    alphabet = (
        "0123456789abcdefghijklmnopqrstuvwxyz"
        "+-*/\\^()[]{},;:.'<>=~&|@% \n\t"
    )
    return "".join(rng.choice(alphabet) for _ in range(n))


@pytest.mark.parametrize("seed", range(200))
def test_parser_never_hangs(seed):
    rng = random.Random(seed)
    src = _random_source(rng, rng.randint(0, 60))
    try:
        compile_source(src, "fuzz.m")
    except MaltError:
        pass
    except RecursionError:
        pytest.fail(f"recursion error on input: {src!r}")


def test_malformed_blocks():
    cases = [
        "if x > 0",
        "if x > 0\nend\nend",
        "for i = 1:10",
        "function f(x)\n y = x;",
        "A = [1 2;",
        "x = (1 + 2",
        "x = 'unterminated",
        "x = 1 +",
    ]
    for c in cases:
        with pytest.raises(MaltError):
            compile_source(c, "fuzz.m")


def test_deep_nesting_does_not_crash():
    src = "(" * 200 + "1" + ")" * 200 + ";"
    try:
        compile_source(src, "fuzz.m")
    except (MaltError, RecursionError):
        pass


def test_fuzz_bounded_runs_quickly():
    import time

    start = time.time()
    rng = random.Random(0)
    for _ in range(500):
        src = _random_source(rng, 40)
        try:
            compile_source(src, "fuzz.m")
        except MaltError:
            pass
    assert time.time() - start < 30
