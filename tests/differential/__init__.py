"""Shared helpers for differential tests against GNU Octave."""

from __future__ import annotations

import shutil
import subprocess

from malt.compiler import compile_source
from malt.executor import execute


def octave_available() -> bool:
    return shutil.which("octave-cli") is not None


def run_octave(source: str) -> tuple[str, str, int]:
    """Run MATLAB/Octave source through GNU Octave, returning (stdout, stderr, rc).

    ``format long g`` is prepended so Octave prints full precision, matching
    MALT's full-precision display (Octave's default ``format short`` rounds to
    five significant digits, which would mask real differences).
    """
    proc = subprocess.run(
        ["octave-cli", "--quiet", "--no-window-system", "--eval", "format long g;" + source],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return proc.stdout, proc.stderr, proc.returncode


def run_malt(source: str, optimization_level: int = 1) -> tuple[str, dict]:
    """Run MATLAB source through MALT, returning (stdout, workspace)."""
    import contextlib
    import io

    unit = compile_source(source, "<differential>", optimization_level=optimization_level)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ns = execute(unit)
    return buf.getvalue(), ns


def normalize_floats(text: str) -> str:
    """Collapse whitespace and round floats to a canonical form for comparison.

    Octave and MALT format doubles differently (e.g. '2.5000' vs '2.5'), so we
    parse every number and re-emit it with a fixed precision before comparing.
    """
    import re

    out = []
    for tok in re.split(r"(\s+)", text):
        if not tok.strip():
            out.append(" ")
            continue
        try:
            f = float(tok)
            if abs(f) < 1e-12:
                f = 0.0
            out.append(f"{f:.6g}")
        except ValueError:
            out.append(tok)
    return "".join(out).strip()
