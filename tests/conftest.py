"""Shared test fixtures and harness helpers."""

from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
os.environ.setdefault("MPLBACKEND", "Agg")

import malt.runtime.graphics as mg  # noqa: E402
from malt.compiler import compile_source  # noqa: E402
from malt.executor import execute  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_graphics():
    mg._state.reset()
    yield
    mg._state.reset()


def run_source(source: str, filename: str = "<test>"):
    """Compile and execute MATLAB source, returning (namespace, stdout)."""
    import contextlib
    import io

    unit = compile_source(source, filename=filename)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ns = execute(unit)
    return ns, buf.getvalue()


def run_file(path: str):
    with open(path, encoding="utf-8") as f:
        source = f.read()
    return run_source(source, filename=path)


def scalar(ns, name: str) -> float | complex:
    v = ns[name]
    if isinstance(v, np.ndarray):
        return v.reshape(-1)[0].item()
    return v


def arr(ns, name: str) -> np.ndarray:
    return np.asarray(ns[name])


def norm_out(text: str) -> str:
    """Normalize printed output for loose string comparison."""
    import re

    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)
