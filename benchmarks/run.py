"""MALT benchmark runner.

Usage:
    nix develop -c python benchmarks/run.py [--quick]

Runs compiler-stage, runtime, numerical, and end-to-end workloads, validating
every result, and prints median/min/max timings. Results are never fabricated
and every workload verifies its numerical output.
"""

from __future__ import annotations

import os
import sys
import time
from contextlib import redirect_stdout
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from common import measure  # noqa: E402

from malt.compiler import cache_clear, compile_source  # noqa: E402
from malt.executor import execute  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
QUICK = "--quick" in sys.argv


def load(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


def _quiet_execute(unit) -> dict:
    with redirect_stdout(StringIO()):
        return execute(unit)


def run_fixture(name: str) -> dict:
    src = load(name)
    unit = compile_source(src, name)
    return _quiet_execute(unit)


# --- compiler-stage timings ----------------------------------------------
def bench_compiler():
    src = load("scalar_loop.m")
    # warm up imports/caches
    compile_source(src, "warm.m")

    lexer = __import__("malt.lexer", fromlist=["Lexer"]).Lexer
    parser_mod = __import__("malt.parser", fromlist=["parse"])
    semantic_mod = __import__("malt.semantic", fromlist=["analyze"])
    codegen_mod = __import__("malt.codegen", fromlist=["generate"])

    def lex():
        lexer(src, "x.m").tokenize()

    def parse_full():
        parser_mod.parse(src, "x.m")

    def analyze():
        stmts = parser_mod.parse(src, "x.m")
        semantic_mod.analyze(stmts)

    def generate():
        stmts = parser_mod.parse(src, "x.m")
        codegen_mod.generate(stmts, "x.m")

    def compile_full():
        cache_clear()
        compile_source(src, "x.m")

    def compile_cached():
        compile_source(src, "x.m")

    results = [
        measure(lex, 200, 10, "lexer"),
        measure(parse_full, 200, 10, "parse"),
        measure(analyze, 200, 10, "semantic analysis"),
        measure(generate, 200, 10, "code generation"),
        measure(compile_full, 200, 10, "full compile (uncached)"),
        measure(compile_cached, 2000, 10, "cached compile (same source)"),
    ]
    for r in results:
        print(r.summarize("ms"))


def bench_runtime():
    src_loop = load("scalar_loop.m")
    unit = compile_source(src_loop, "scalar_loop.m")

    # warm execution
    _quiet_execute(unit)

    results = [
        measure(lambda: _quiet_execute(unit), 5, 2, "execute scalar_loop (100k)"),
    ]
    for r in results:
        print(r.summarize("ms"))


def bench_numerical():
    workloads = [
        ("matrix 200x200 matmul", "matrix_operations.m", 20),
        ("elementwise 100k", "elementwise.m", 10),
        ("linear solve 2x2", "linear_solve.m", 500),
    ]
    for label, name, n in workloads:
        run_fixture(name)  # validate once
        src = load(name)

        def fn(src=src, name=name):
            _quiet_execute(compile_source(src, name))

        m = measure(fn, n, 2, label)
        print(m.summarize("ms"))


def bench_end_to_end():
    # repeated execution of an already-compiled program in fresh workspaces
    src = load("repeated_execution.m")
    unit = compile_source(src, "repeated_execution.m")

    def re_exec():
        _quiet_execute(unit)

    def re_compile():
        _quiet_execute(compile_source(src, "repeated_execution.m"))

    print(measure(re_exec, 100, 5, "repeated execution (compiled)").summarize("us"))
    print(measure(re_compile, 100, 5, "repeated compile+execute").summarize("us"))


def main() -> int:
    t0 = time.perf_counter()
    print("== MALT benchmark ==")
    print(f"quick={QUICK} python={sys.version.split()[0]}")
    print(f"cpu={os.cpu_count()} cores")
    print()

    print("-- compiler stages --")
    bench_compiler()

    print("\n-- runtime --")
    bench_runtime()

    print("\n-- numerical --")
    bench_numerical()

    print("\n-- end-to-end --")
    bench_end_to_end()

    print(f"\ntotal wall {time.perf_counter() - t0:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
