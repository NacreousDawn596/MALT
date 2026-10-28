"""Optimization-coverage measurement.

Usage:
    nix develop -c python benchmarks/coverage.py

Reports, per example program, how many ``for`` loops qualified for level-2 JIT
specialization and why the others fell back, then times a fully-specialized
loop against an equivalent loop that is forced to fall back.
"""

from __future__ import annotations

import os
import sys
from contextlib import redirect_stdout
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from common import measure  # noqa: E402

from malt.compiler import compile_source  # noqa: E402
from malt.executor import execute  # noqa: E402

CORPUS = {
    "scalar_loop (specializes)": "n = 100000;\ntotal = 0;\nfor k = 1:n\n total = total + k;\nend\n",
    "multi_accum (specializes)": "s = 0;\np = 1;\nfor k = 1:1000\n s = s + k;\n p = p * k;\nend\n",
    "nested (inner refs outer: falls back)": "s = 0;\nfor i = 1:100\n for j = 1:100\n  s = s + i*j;\n end\nend\n",
    "indexed_assign (falls back)": "v = zeros(1, 1000);\nfor k = 1:1000\n v(k) = k;\nend\n",
    "free_variable (falls back)": "c = 3;\ns = 0;\nfor k = 1:1000\n s = s + c * k;\nend\n",
    "function_call (falls back)": "s = 0;\nfor k = 1:1000\n s = s + sin(k);\nend\n",
    "float_step (specialized; colon at runtime)": "s = 0;\nfor k = 0:0.5:10\n s = s + k;\nend\n",
    "multi_statement (falls back)": "s = 0;\nfor k = 1:1000\n s = s + k;\n t = k * 2;\nend\n",
}


def _run(src: str, lvl: int):
    unit = compile_source(src, "cov.m", optimization_level=lvl)
    with redirect_stdout(StringIO()):
        execute(unit)
    return unit


def main() -> int:
    print("== JIT optimization coverage (level 2) ==")
    for name, src in CORPUS.items():
        unit = _run(src, 2)
        jitted = sum(1 for d in unit.diagnostics if d["jit"])
        total = len(unit.diagnostics)
        reasons = ", ".join(
            f"L{d['line']}: {d['reason']}" for d in unit.diagnostics if not d["jit"]
        )
        print(f"{name:<32} {jitted}/{total} specialized" + (f"  [{reasons}]" if reasons else ""))

    print("\n== time: specialized vs. equivalent general loop ==")
    specialized = "n = 100000;\ns = 0;\nfor k = 1:n\n s = s + k;\nend\n"
    # Force a fallback by making the RHS depend on a free (non-loop) variable.
    general = "n = 100000;\nc = 1;\ns = 0;\nfor k = 1:n\n s = s + c * k;\nend\n"

    for label, src in (("specialized (JIT, level 2)", specialized), ("general (fallback)", general)):
        lvl = 2
        unit = _run(src, lvl)
        m = measure(lambda unit=unit, src=src, lvl=lvl: _run(src, lvl), 5, 2, label)
        print(f"  {label:<28} {m.median * 1e3:8.2f} ms")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
