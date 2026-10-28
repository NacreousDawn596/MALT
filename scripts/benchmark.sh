#!/usr/bin/env bash
# Micro-benchmarks for MALT's compilation and execution pipeline.
set -euo pipefail

cd "$(dirname "$0")/.."

export MPLBACKEND=Agg

nix develop -c python - <<'PY'
import time

from malt.compiler import compile_source
from malt.executor import execute


def bench(label, fn, n=1):
    start = time.perf_counter()
    for _ in range(n):
        fn()
    dt = (time.perf_counter() - start) / n
    print(f"{label:<40} {dt * 1e3:10.3f} ms")


src_arith = "s = 0;\nfor k = 1:100000\n s = s + k * k;\nend\n"
src_matmul = (
    "A = rand(100, 100);\nB = rand(100, 100);\nC = A * B;\n"
)
src_linalg = "A = rand(100, 100);\nb = rand(100, 1);\nx = A \\ b;\n"

unit_arith = compile_source(src_arith, "bench_arith.m")
unit_matmul = compile_source(src_matmul, "bench_matmul.m")
unit_linalg = compile_source(src_linalg, "bench_linalg.m")

bench("parse + codegen + compile (arith)", lambda: compile_source(src_arith, "b.m"))
bench("execute: scalar loop 100k", lambda: execute(unit_arith), 3)
bench("execute: 100x100 matmul", lambda: execute(unit_matmul), 10)
bench("execute: 100x100 linear solve", lambda: execute(unit_linalg), 10)

import numpy as np
def py_matmul():
    a = np.random.rand(100, 100); b = np.random.rand(100, 100); a @ b
bench("native NumPy: 100x100 matmul", py_matmul, 100)
PY
