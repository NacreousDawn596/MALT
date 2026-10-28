"""Shared benchmarking helpers: timing, statistics, and result validation."""

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field


@dataclass
class Measurement:
    label: str
    samples_s: list[float] = field(default_factory=list)

    @property
    def median(self) -> float:
        return statistics.median(self.samples_s)

    @property
    def min(self) -> float:
        return min(self.samples_s)

    @property
    def max(self) -> float:
        return max(self.samples_s)

    def summarize(self, unit: str = "ms") -> str:
        scale = {"s": 1.0, "ms": 1e3, "us": 1e6}[unit]
        med = self.median * scale
        lo = self.min * scale
        hi = self.max * scale
        try:
            q1 = statistics.quantiles(self.samples_s, n=4)[0] * scale
            q3 = statistics.quantiles(self.samples_s, n=4)[2] * scale
            spread = f"iqr=[{q1:.3f}, {q3:.3f}]"
        except statistics.StatisticsError:
            spread = "iqr=n/a"
        return (
            f"{self.label:<42} median={med:10.3f} {unit}  "
            f"min={lo:10.3f} max={hi:10.3f}  {spread}  n={len(self.samples_s)}"
        )


def timeit(fn, number: int = 1, warmup: int = 0) -> list[float]:
    """Run ``fn`` ``number`` times and return per-call seconds.

    ``warmup`` iterations are executed first and discarded.
    """
    for _ in range(warmup):
        fn()
    samples: list[float] = []
    for _ in range(number):
        start = time.perf_counter_ns()
        fn()
        samples.append((time.perf_counter_ns() - start) / 1e9)
    return samples


def measure(fn, number: int, warmup: int, label: str) -> Measurement:
    return Measurement(label, timeit(fn, number=number, warmup=warmup))
