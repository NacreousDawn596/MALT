"""Control systems: transfer functions, step/impulse responses, and analysis.

A MATLAB-compatible subset built on SciPy's signal module. Exposes ``tf``,
``ss``, ``dcgain``, ``step``, ``impulse``, ``lsim``, ``stepinfo``,
``feedback``, ``series``, ``parallel``, ``pole``, and ``zero``.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import signal as _sig

from ..errors import RuntimeError_
from . import graphics as _graphics
from .arrays import as_array
from .cells import Struct


def _poly(x: Any) -> np.ndarray:
    a = as_array(x)
    if isinstance(a, str):
        raise RuntimeError_("transfer function coefficients must be numeric")
    a = np.asarray(a, dtype=float).reshape(-1)
    if a.size == 0:
        raise RuntimeError_("transfer function coefficients cannot be empty")
    return a


class TransferFunction:
    """A continuous-time SISO transfer function ``num(s) / den(s)``."""

    __slots__ = ("num", "den")

    def __init__(self, num: Any, den: Any) -> None:
        self.num = _poly(num)
        self.den = _poly(den)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"tf(num={np.array2string(self.num, precision=6)}, "
            f"den={np.array2string(self.den, precision=6)})"
        )

    def _scipy(self) -> _sig.TransferFunction:
        return _sig.TransferFunction(self.num, self.den)


class StateSpace:
    """A continuous-time state-space model ``dx = A x + B u; y = C x + D u``."""

    __slots__ = ("A", "B", "C", "D")

    def __init__(self, A: Any, B: Any, C: Any, D: Any) -> None:
        self.A = np.atleast_2d(np.asarray(A, dtype=float))
        self.B = np.atleast_2d(np.asarray(B, dtype=float))
        self.C = np.atleast_2d(np.asarray(C, dtype=float))
        self.D = np.atleast_2d(np.asarray(D, dtype=float))

    def _scipy(self) -> _sig.StateSpace:
        return _sig.StateSpace(self.A, self.B, self.C, self.D)


def _lti(sys: Any) -> _sig.lti:
    if isinstance(sys, (TransferFunction, StateSpace)):
        return sys._scipy()
    if isinstance(sys, _sig.lti):
        return sys
    raise RuntimeError_("expected a transfer function or state-space model")


def tf(num: Any, den: Any = None) -> TransferFunction:
    if isinstance(num, TransferFunction):
        if den is not None:
            raise RuntimeError_("tf(sys) does not accept a denominator")
        return num
    if den is None:
        den = [1.0]
    return TransferFunction(num, den)


def ss(A: Any, B: Any, C: Any, D: Any) -> StateSpace:
    return StateSpace(A, B, C, D)


def _dcgain_tf(num: np.ndarray, den: np.ndarray) -> float:
    if den[-1] == 0.0:
        return np.inf  # a pure integrator has infinite DC gain
    return float(num[-1] / den[-1])


def dcgain(sys: Any) -> np.ndarray:
    s = _lti(sys)
    if isinstance(s, _sig.StateSpace):
        A = np.asarray(s.A)
        B = np.asarray(s.B)
        C = np.asarray(s.C)
        D = np.asarray(s.D)
        try:
            gain = D - C @ np.linalg.solve(A, B)
        except np.linalg.LinAlgError:
            gain = D  # A singular: no well-defined DC gain
        return np.array([[float(np.asarray(gain).reshape(-1)[0])]])
    return np.array([[_dcgain_tf(np.asarray(s.num).reshape(-1), np.asarray(s.den).reshape(-1))]])


def _response(sys: Any, method: str) -> tuple[np.ndarray, np.ndarray]:
    s = _lti(sys)
    if method == "step":
        T, y = _sig.step(s)
    else:
        T, y = _sig.impulse(s)
    return np.asarray(T).reshape(-1), np.asarray(y).reshape(-1)


def step(sys: Any, *args: Any) -> np.ndarray:
    """Plot the unit step response and return the output vector."""
    T, y = _response(sys, "step")
    _graphics.plot(T, y)
    _graphics.xlabel("Time (seconds)")
    _graphics.ylabel("Amplitude")
    _graphics.title("Step Response")
    return y.reshape(-1, 1)


def impulse(sys: Any, *args: Any) -> np.ndarray:
    """Plot the unit impulse response and return the output vector."""
    T, y = _response(sys, "impulse")
    _graphics.plot(T, y)
    _graphics.xlabel("Time (seconds)")
    _graphics.ylabel("Amplitude")
    _graphics.title("Impulse Response")
    return y.reshape(-1, 1)


def lsim(sys: Any, u: Any, t: Any) -> np.ndarray:
    """Plot the response to input ``u`` over times ``t`` and return the output."""
    s = _lti(sys)
    u_arr = np.asarray(as_array(u), dtype=float).reshape(-1)
    t_arr = np.asarray(as_array(t), dtype=float).reshape(-1)
    T, y, _ = _sig.lsim(s, U=u_arr, T=t_arr)
    _graphics.plot(T, y)
    return np.asarray(y).reshape(-1, 1)


def _first_cross(t: np.ndarray, y: np.ndarray, level: float) -> float | None:
    """First time (via linear interpolation) the signal crosses ``level``."""
    for i in range(len(t) - 1):
        if (y[i] - level) * (y[i + 1] - level) <= 0:
            if y[i + 1] == y[i]:
                return float(t[i])
            frac = (level - y[i]) / (y[i + 1] - y[i])
            return float(t[i] + frac * (t[i + 1] - t[i]))
    return None


def _settling_time(t: np.ndarray, y: np.ndarray, band: float) -> float:
    """Last time the normalized response leaves the ``±band`` band."""
    above = np.abs(y - 1.0) > band
    idx = np.flatnonzero(above)
    if idx.size == 0:
        return float(t[0])
    return float(t[idx[-1]])


def stepinfo(sys: Any) -> Struct:
    """Step-response characteristics (rise time, settling time, overshoot…)."""
    T, y = _response(sys, "step")
    yf = float(y[-1])
    peak = float(np.max(y))
    peak_idx = int(np.argmax(y))
    if abs(yf) < 1e-15:
        rise = settling = np.nan
        overshoot = 0.0
    else:
        yn = y / yf
        t10 = _first_cross(T, yn, 0.1)
        t90 = _first_cross(T, yn, 0.9)
        rise = (t90 - t10) if (t10 is not None and t90 is not None) else np.nan
        settling = _settling_time(T, yn, 0.02)
        overshoot = (peak - yf) / yf * 100.0
    return Struct(
        {
            "RiseTime": float(rise),
            "SettlingTime": float(settling),
            "Overshoot": float(overshoot),
            "Peak": peak,
            "PeakTime": float(T[peak_idx]),
            "SteadyState": yf,
        }
    )


def _as_tf(sys: Any) -> _sig.TransferFunction:
    s = _lti(sys)
    if isinstance(s, _sig.StateSpace):
        s = s.to_tf()
    if not isinstance(s, _sig.TransferFunction):
        raise RuntimeError_("expected a transfer function")
    return s


def _tf_arrays(sys: Any) -> tuple[np.ndarray, np.ndarray]:
    s = _as_tf(sys)
    return np.asarray(s.num).reshape(-1), np.asarray(s.den).reshape(-1)


def feedback(sys1: Any, sys2: Any, sign: Any = -1) -> TransferFunction:
    """Feedback interconnection (``sign=-1`` negative by default, ``+1`` positive)."""
    n1, d1 = _tf_arrays(sys1)
    n2, d2 = _tf_arrays(sys2)
    s = float(np.asarray(sign).reshape(-1)[0])
    # negative feedback (s=-1) adds n1*n2; positive feedback (s=+1) subtracts it.
    num = np.polymul(n1, d2)
    den = np.polyadd(np.polymul(d1, d2), -s * np.polymul(n1, n2))
    return TransferFunction(num, den)


def series(sys1: Any, sys2: Any) -> TransferFunction:
    """Series interconnection ``sys1 * sys2``."""
    n1, d1 = _tf_arrays(sys1)
    n2, d2 = _tf_arrays(sys2)
    return TransferFunction(np.polymul(n1, n2), np.polymul(d1, d2))


def parallel(sys1: Any, sys2: Any) -> TransferFunction:
    """Parallel interconnection ``sys1 + sys2``."""
    n1, d1 = _tf_arrays(sys1)
    n2, d2 = _tf_arrays(sys2)
    num = np.polyadd(np.polymul(n1, d2), np.polymul(n2, d1))
    den = np.polymul(d1, d2)
    return TransferFunction(num, den)


def pole(sys: Any) -> np.ndarray:
    """Poles of a transfer function or state-space model."""
    s = _lti(sys)
    return np.roots(np.asarray(s.den).reshape(-1)).reshape(-1, 1)


def zero(sys: Any) -> np.ndarray:
    """Zeros of a transfer function (state-space models return their zeros)."""
    if isinstance(sys, TransferFunction):
        return np.roots(np.asarray(sys.num).reshape(-1)).reshape(-1, 1)
    s = _lti(sys)
    z, _, _ = _sig.ss2zpk(np.asarray(s.A), np.asarray(s.B), np.asarray(s.C), np.asarray(s.D))
    return np.asarray(z, dtype=float).reshape(-1, 1)
