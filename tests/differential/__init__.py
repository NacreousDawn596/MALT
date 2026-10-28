"""Shared helpers for differential tests against GNU Octave."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

import numpy as np

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


# ---------------------------------------------------------------------------
# Structured comparison: serialize shape and real/imaginary parts separately,
# then compare the reconstructed values. This catches shape, precision, and
# complex differences that comparing `fprintf('%g ', …)` text would hide.
# ---------------------------------------------------------------------------

# A ``.m`` function both runtimes implement identically. It emits, per value:
#   S <dims...>          (shape)
#   R <real parts...>    (column-major)
#   I <imag parts...>    (column-major)
_EMIT_FN = """
function emit(v)
    s = size(v);
    fprintf('S');
    for d = 1:length(s)
        fprintf(' %d', s(d));
    end
    fprintf('\\n');
    fprintf('R');
    fprintf(' %.17g', real(v));
    fprintf('\\n');
    fprintf('I');
    fprintf(' %.17g', imag(v));
    fprintf('\\n');
end
""".strip()


@dataclass
class StructuredValue:
    shape: tuple[int, ...]
    array: np.ndarray  # complex


def _structured_source(body: str) -> str:
    return _EMIT_FN + "\n" + body


def _parse_structured(text: str) -> list[StructuredValue]:
    values: list[StructuredValue] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("S"):
            dims = tuple(int(x) for x in line[1:].split())
            reals = [float(x) for x in lines[i + 1][1:].split()]
            imags = [float(x) for x in lines[i + 2][1:].split()]
            assert len(reals) == len(imags)
            arr = np.array(reals, dtype=float) + 1j * np.array(imags, dtype=float)
            arr = arr.reshape(dims, order="F") if dims and arr.size else arr
            values.append(StructuredValue(dims, arr))
            i += 3
        else:
            i += 1
    return values


def run_structured_malt(body: str, optimization_level: int = 1) -> list[StructuredValue]:
    out, _ = run_malt(_structured_source(body), optimization_level=optimization_level)
    return _parse_structured(out)


def run_structured_octave(body: str) -> list[StructuredValue]:
    out, err, rc = run_octave(_structured_source(body))
    assert rc == 0, f"Octave failed:\n{err}\n{out}"
    return _parse_structured(out)


def compare_structured(
    malt: list[StructuredValue],
    octave: list[StructuredValue],
    rtol: float = 1e-9,
    atol: float = 1e-9,
) -> None:
    """Compare structured values: shape, then real/imag with NaN/Inf handling."""
    assert len(malt) == len(octave), f"value count: {len(malt)} vs {len(octave)}"
    for m, o in zip(malt, octave, strict=False):
        assert m.shape == o.shape, f"shape {m.shape} vs {o.shape}"
        np.testing.assert_allclose(m.array, o.array, rtol=rtol, atol=atol, equal_nan=True)


def check_structured(body: str, rtol: float = 1e-9, atol: float = 1e-9) -> None:
    """Run ``body`` (which must call ``emit(expr)`` for each value) through both
    runtimes and compare the structured (shape + real/imag) values."""
    malt = run_structured_malt(body)
    octave = run_structured_octave(body)
    compare_structured(malt, octave, rtol=rtol, atol=atol)
