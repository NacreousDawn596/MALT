"""Control systems toolbox (tf, step, dcgain, stepinfo, interconnections)."""

from __future__ import annotations

import numpy as np
import pytest
from conftest import run_source

from malt.runtime.controlsys import (
    dcgain,
    feedback,
    parallel,
    pole,
    series,
    stepinfo,
    tf,
    zero,
)


def test_tf_dcgain_first_order():
    sys = tf(2, [1, 3])
    assert dcgain(sys).reshape(-1)[0] == pytest.approx(2 / 3)


def test_tf_dcgain_integrator_is_inf():
    sys = tf(1, [1, 0])
    assert np.isinf(dcgain(sys).reshape(-1)[0])


def test_step_response_returns_output():
    ns, _ = run_source("sys = tf(1, [1 1]);\ny = step(sys);\n")
    y = np.asarray(ns["y"]).reshape(-1)
    assert y.size > 1
    assert y[-1] == pytest.approx(1.0, rel=1e-3)  # DC gain of 1/(s+1) is 1


def test_stepinfo_struct_fields():
    sys = tf(1, [1, 1])  # first-order: no overshoot
    info = stepinfo(sys)
    assert "Overshoot" in info._fields
    assert "SettlingTime" in info._fields
    assert info._fields["Overshoot"] == pytest.approx(0.0, abs=1e-6)


def test_series_multiplies():
    g = series(tf(1, [1, 1]), tf(1, [1, 2]))
    assert np.allclose(g.den, np.polymul([1, 1], [1, 2]))
    assert np.allclose(g.num, [1])


def test_parallel_adds():
    g = parallel(tf(1, [1, 1]), tf(1, [1, 1]))
    assert np.allclose(g.num, [2, 2])
    assert np.allclose(g.den, [1, 2, 1])


def test_feedback_negative():
    # 1/s with unity feedback -> 1/(s+1)
    cl = feedback(tf(1, [1, 0]), tf(1))
    assert np.allclose(cl.num, [1])
    assert np.allclose(cl.den, [1, 1])


def test_pole_and_zero():
    sys = tf([1, 1], [1, 3, 2])  # zero at -1, poles at -2, -1
    assert np.allclose(np.sort(pole(sys).reshape(-1)), [-2, -1])
    assert np.allclose(zero(sys).reshape(-1), [-1])
