# Benchmarks

A reproducible benchmark harness for MALT's compilation and execution
pipeline.

## Running

```bash
nix develop -c python benchmarks/run.py          # full suite
nix develop -c python benchmarks/run.py --quick  # reduced iteration counts
```

The harness measures compiler stages (lexing, parsing, semantic analysis, code
generation, full compilation — both uncached and cached), scalar/runtime
workloads, numerical workloads (matmul, element-wise, linear solve), and
end-to-end cold/warm/repeated execution. Every workload validates its result
before timing.

## Fixtures

`benchmarks/fixtures/*.m` are executed through the real compiler and runtime.
The runner asserts the expected numerical outputs (e.g. `scalar_loop` must
produce `5000050000`) and never times an unused or eliminated computation.

## Methodology

- `time.perf_counter_ns()` per sample; median/min/max and sample count are
  reported (see `common.py`).
- Warm-up iterations are discarded.
- `MPLBACKEND=Agg` is used so headless runs need no display.
- Results are machine-specific (CPU, BLAS, Python version); they are not
  universal performance guarantees. The runner prints Python version and core
  count for cross-run comparison.

## Baseline vs. optimized (this machine: i5-1145G7, OpenBLAS)

| workload | baseline | optimized | speedup |
| --- | --- | --- | --- |
| scalar loop 100k | ~644 ms | ~71 ms | ~9x |
| linear solve 2x2 | ~0.88 ms | ~0.14 ms | ~6x |
| full compile | ~0.55 ms | ~0.55 ms (uncached) | — |
| cached compile | — | ~1 us | ~500x |
| 200x200 matmul | ~4.0 ms | ~4.0 ms | BLAS-bound |
| repeated compile+execute | ~1.04 ms | ~0.21 ms | ~5x (cache) |
