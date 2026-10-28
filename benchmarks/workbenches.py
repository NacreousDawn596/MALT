"""Targeted workbenches for the reported optimizations.

Usage:
    nix develop -c python benchmarks/workbenches.py

Each workbench validates its result and reports median timings with the sample
count. "Before" figures for the indexed-assignment path are recorded baselines
(they cannot be re-measured after the code change); "after" figures are live.
"""

from __future__ import annotations

import os
import sys
from contextlib import redirect_stdout
from io import StringIO

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from common import measure  # noqa: E402

from malt.compiler import cache_clear, compile_source  # noqa: E402
from malt.executor import execute  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


def qexec(unit):
    with redirect_stdout(StringIO()):
        return execute(unit)


def workbench_scalar_loop():
    print("== Workbench 1: scalar loop (100k) — level 0 vs 1 vs 2 ==")
    src = load("scalar_loop.m")
    for lvl in (0, 1, 2):
        unit = compile_source(src, "s.m", optimization_level=lvl)
        qexec(unit)  # validate + warm
        ns = qexec(unit)
        assert float(np.asarray(ns["total"]).reshape(-1)[0]) == 5000050000.0
        m = measure(lambda unit=unit: qexec(unit), 10, 2, f"level {lvl}")
        print(f"  level {lvl}: {m.median * 1e3:8.2f} ms  "
              f"({m.median * 1e6 / 100000:.2f} us/iter)")


def workbench_indexed_assignment():
    print("\n== Workbench 2: indexed assignment (100k) — before vs after ==")
    src = load("array_loop.m")
    unit = compile_source(src, "a.m")
    qexec(unit)  # validate + warm
    ns = qexec(unit)
    assert float(np.asarray(ns["total"]).reshape(-1)[0]) == 5000050000.0
    m = measure(lambda: qexec(unit), 5, 1, "after (scalar-index fast path)")
    print("  before (baseline):   5470.00 ms   (recorded)")
    print(f"  after:               {m.median * 1e3:8.2f} ms")


def workbench_compile_cache():
    print("\n== Workbench 3: repeated compilation — cache disabled vs hit ==")
    src = load("repeated_execution.m")

    def uncached():
        cache_clear()
        compile_source(src, "r.m")

    def cached():
        compile_source(src, "r.m")

    m1 = measure(uncached, 200, 10, "cache disabled (full compile)")
    m2 = measure(cached, 2000, 10, "cache hit (memoized)")
    print(f"  cache disabled: {m1.median * 1e3:8.3f} ms")
    print(f"  cache hit:      {m2.median * 1e3:8.4f} ms")


def workbench_matmul():
    print("\n== Workbench 4: 200x200 matrix multiply — MALT vs NumPy ==")
    src = "rng(42);\nA = rand(200, 200);\nB = rand(200, 200);\nC = A * B;\n"
    unit = compile_source(src, "m.m")
    ns = qexec(unit)
    C = np.asarray(ns["C"])
    # reference
    np.random.seed(42)
    a = np.random.rand(200, 200)
    b = np.random.rand(200, 200)
    np.testing.assert_allclose(C, a @ b, atol=1e-9)
    m_malt = measure(lambda: qexec(unit), 10, 2, "MALT")
    m_np = measure(lambda: a @ b, 100, 5, "NumPy")
    print(f"  MALT:   {m_malt.median * 1e3:8.2f} ms")
    print(f"  NumPy:  {m_np.median * 1e3:8.2f} ms")


def workbench_linear_solve():
    print("\n== Workbench 5: 2x2 linear solve — MALT vs NumPy/SciPy ==")
    src = "A = [4 1; 1 3];\nb = [1; 2];\nx = A \\ b;\n"
    unit = compile_source(src, "l.m")
    ns = qexec(unit)
    x = np.asarray(ns["x"])
    a = np.array([[4, 1], [1, 3]], dtype=float)
    b = np.array([[1], [2]], dtype=float)
    np.testing.assert_allclose(x, np.linalg.solve(a, b), atol=1e-12)
    m_malt = measure(lambda: qexec(unit), 500, 20, "MALT")
    m_np = measure(lambda: np.linalg.solve(a, b), 2000, 50, "NumPy solve")
    print(f"  MALT:        {m_malt.median * 1e3:8.3f} ms")
    print(f"  NumPy solve: {m_np.median * 1e3:8.3f} ms")


def main() -> int:
    print(f"MALT workbenches — python {sys.version.split()[0]}, {os.cpu_count()} cores")
    workbench_scalar_loop()
    workbench_indexed_assignment()
    workbench_compile_cache()
    workbench_matmul()
    workbench_linear_solve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
