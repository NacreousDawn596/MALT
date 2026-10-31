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
from .arrays import as_array, scalar_value
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


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def damp(sys: Any) -> np.ndarray:
    s = _lti(sys)
    p = np.roots(np.asarray(s.den).reshape(-1))
    wn = np.abs(p)
    z = -np.real(p) / np.where(wn == 0, 1.0, wn)
    return np.asarray([wn, z]).T


def evalfr(sys: Any, s: Any) -> np.ndarray:
    x = complex(np.asarray(as_array(s)).reshape(-1)[0])
    s_ = _lti(sys)
    num = np.asarray(s_.num).reshape(-1)
    den = np.asarray(s_.den).reshape(-1)
    val = np.polyval(num, x) / np.polyval(den, x)
    return np.array([[complex(val)]])


def isstable(sys: Any) -> np.ndarray:
    s = _lti(sys)
    p = np.roots(np.asarray(s.den).reshape(-1))
    stable = all(np.real(p) < 0)
    return np.array([[1.0 if stable else 0.0]])


def isproper(sys: Any) -> np.ndarray:
    if isinstance(sys, TransferFunction):
        proper = sys.num.size <= sys.den.size
        return np.array([[1.0 if proper else 0.0]])
    return np.array([[1.0]])


def bandwidth(sys: Any) -> np.ndarray:
    s = _lti(sys)
    w, mag, _ = _sig.bode(s)
    mag = np.asarray(mag)
    w = np.asarray(w)
    dc = mag[0]
    target = dc - 3.0
    idx = np.flatnonzero(mag <= target)
    if idx.size == 0:
        return np.array([[float(w[-1])]])
    return np.array([[float(w[idx[0]])]])


def dcgain2(sys: Any) -> np.ndarray:
    return dcgain(sys)


def tfdata(sys: Any, nout: int = 2) -> Any:
    num, den = _tf_arrays(sys)
    if nout >= 2:
        return num.reshape(1, -1), den.reshape(1, -1)
    return num.reshape(1, -1)


def ssdata(sys: Any, nout: int = 4) -> Any:
    s = _lti(sys)
    if isinstance(s, _sig.TransferFunction):
        s = s.to_ss()
    A = np.asarray(s.A)
    B = np.asarray(s.B)
    C = np.asarray(s.C)
    D = np.asarray(s.D)
    return A, B, C, D


def tf2ss(num: Any, den: Any) -> Any:
    A, B, C, D = _sig.tf2ss(np.asarray(as_array(num)).flatten(), np.asarray(as_array(den)).flatten())
    return A, B, C, D


def ss2tf(A: Any, B: Any, C: Any, D: Any) -> Any:
    num, den = _sig.ss2tf(np.asarray(as_array(A)), np.asarray(as_array(B)), np.asarray(as_array(C)), np.asarray(as_array(D)))
    return num.reshape(1, -1), den.reshape(1, -1)


def tf2zp(num: Any, den: Any) -> Any:
    z, p, k = _sig.tf2zpk(np.asarray(as_array(num)).flatten(), np.asarray(as_array(den)).flatten())
    return z.reshape(-1, 1), p.reshape(-1, 1), np.array([[k]])


def zp2tf(z: Any, p: Any, k: Any) -> Any:
    num, den = _sig.zpk2tf(np.asarray(as_array(z)).flatten(), np.asarray(as_array(p)).flatten(), float(scalar_value(k)))
    return num.reshape(1, -1), den.reshape(1, -1)


def ss2zp(A: Any, B: Any, C: Any, D: Any) -> Any:
    z, p, k = _sig.ss2zpk(np.asarray(as_array(A)), np.asarray(as_array(B)), np.asarray(as_array(C)), np.asarray(as_array(D)))
    return z.reshape(-1, 1), p.reshape(-1, 1), np.array([[k]])


def minreal(sys: Any) -> TransferFunction:
    num, den = _tf_arrays(sys)
    num, den = num.astype(float), den.astype(float)
    while len(num) > 1 and len(den) > 1:
        r = np.roots(den)
        changed = False
        for root in r:
            if abs(np.polyval(num, root)) < 1e-9:
                num = np.poly(np.delete(np.roots(num), np.argmin(np.abs(np.roots(num) - root))))
                den = np.poly(np.delete(np.roots(den), np.argmin(np.abs(np.roots(den) - root))))
                changed = True
                break
        if not changed:
            break
    return TransferFunction(np.trim_zeros(num, "f"), np.trim_zeros(den, "f"))


def append(*systems: Any) -> TransferFunction:
    # Append SISO systems on the diagonal of a block-diagonal state-space model.
    from scipy.linalg import block_diag

    As, Bs, Cs, Ds = [], [], [], []
    for s in systems:
        ss = _lti(s)
        if isinstance(ss, _sig.TransferFunction):
            ss = ss.to_ss()
        As.append(np.asarray(ss.A))
        Bs.append(np.asarray(ss.B))
        Cs.append(np.asarray(ss.C))
        Ds.append(np.asarray(ss.D))
    A = block_diag(*As)
    B = block_diag(*Bs)
    C = block_diag(*Cs)
    D = block_diag(*Ds)
    num, den = _sig.ss2tf(A, B, C, D)
    return TransferFunction(num, den)


# ---------------------------------------------------------------------------
# Conversions and discretization
# ---------------------------------------------------------------------------


def c2d(sys: Any, Ts: Any, method: Any = "zoh") -> TransferFunction:
    num, den = _tf_arrays(sys)
    Ts = float(scalar_value(Ts))
    method_map = {"zoh": "zoh", "foh": "foh", "tustin": "bilinear", "bilinear": "bilinear", "matched": "matched"}
    m = method_map.get(str(method).lower(), "zoh")
    num_d, den_d, _ = _sig.cont2discrete((num, den), Ts, method=m)
    return TransferFunction(np.asarray(num_d).flatten(), np.asarray(den_d).flatten())


def _bilinear_subst(poly: np.ndarray, Ts: float) -> np.ndarray:
    """Substitute ``z = (2 + s*Ts) / (2 - s*Ts)`` into a polynomial in ``z``."""
    n = len(poly) - 1
    result = np.zeros(n + 1)
    for k, coef in enumerate(poly):
        a = np.poly1d([Ts, 2.0]) ** k
        b = np.poly1d([-Ts, 2.0]) ** (n - k)
        result = np.polyadd(result, coef * np.polymul(a, b))
    return result


def d2c(sys: Any, Ts: Any = 1.0) -> TransferFunction:
    """Discrete-to-continuous via the inverse bilinear (Tustin) transform."""
    num, den = _tf_arrays(sys)
    Ts = float(scalar_value(Ts))
    num_c = _bilinear_subst(num, Ts)
    den_c = _bilinear_subst(den, Ts)
    return TransferFunction(num_c, den_c)


def pid(Kp: Any, Ki: Any = 0, Kd: Any = 0) -> TransferFunction:
    Kp = float(scalar_value(Kp))
    Ki = float(scalar_value(Ki))
    Kd = float(scalar_value(Kd))
    return TransferFunction([Kd, Kp, Ki], [1.0, 0.0])


# ---------------------------------------------------------------------------
# State-space analysis and design
# ---------------------------------------------------------------------------


def ctrb(A: Any, B: Any) -> np.ndarray:
    from scipy.signal import ctrb as _ctrb

    return _ctrb(np.asarray(as_array(A)), np.asarray(as_array(B)))


def obsv(A: Any, C: Any) -> np.ndarray:
    from scipy.signal import obsv as _obsv

    return _obsv(np.asarray(as_array(A)), np.asarray(as_array(C)))


def lqr(A: Any, B: Any, Q: Any, R: Any) -> np.ndarray:
    from scipy.signal import lqr as _lqr

    K, _, _ = _lqr(np.asarray(as_array(A)), np.asarray(as_array(B)), np.asarray(as_array(Q)), np.asarray(as_array(R)))
    return K


def dlqr(A: Any, B: Any, Q: Any, R: Any) -> np.ndarray:
    from scipy.linalg import solve, solve_discrete_are

    A = np.asarray(as_array(A))
    B = np.asarray(as_array(B))
    Q = np.asarray(as_array(Q))
    R = np.asarray(as_array(R))
    P = solve_discrete_are(A, B, Q, R)
    K = solve(R + B.T @ P @ B, B.T @ P @ A)
    return K


def place(A: Any, B: Any, p: Any) -> np.ndarray:
    from scipy.signal import place_poles

    res = place_poles(np.asarray(as_array(A)), np.asarray(as_array(B)), np.asarray(as_array(p)).flatten())
    return res.gain_matrix


def acker(A: Any, B: Any, p: Any) -> np.ndarray:
    return place(A, B, p)


def lyap(A: Any, Q: Any) -> np.ndarray:
    from scipy.linalg import solve_continuous_lyapunov

    return solve_continuous_lyapunov(np.asarray(as_array(A)), np.asarray(as_array(Q)))


def care(A: Any, B: Any, Q: Any, R: Any) -> np.ndarray:
    from scipy.linalg import solve_continuous_are

    return solve_continuous_are(np.asarray(as_array(A)), np.asarray(as_array(B)), np.asarray(as_array(Q)), np.asarray(as_array(R)))


def dare(A: Any, B: Any, Q: Any, R: Any) -> np.ndarray:
    from scipy.linalg import solve_discrete_are

    return solve_discrete_are(np.asarray(as_array(A)), np.asarray(as_array(B)), np.asarray(as_array(Q)), np.asarray(as_array(R)))


# ---------------------------------------------------------------------------
# Frequency response
# ---------------------------------------------------------------------------


def bode(sys: Any, w: Any = None) -> tuple[np.ndarray, np.ndarray]:
    s = _lti(sys)
    if w is None:
        w, mag, phase = _sig.bode(s)
    else:
        w = np.asarray(as_array(w)).flatten()
        w, mag, phase = _sig.bode(s, w=w)
    return np.asarray(mag).reshape(-1, 1), np.asarray(phase).reshape(-1, 1)


def freqresp(sys: Any, w: Any) -> np.ndarray:
    s = _lti(sys)
    w = np.asarray(as_array(w)).flatten()
    _, h = _sig.freqresp(s, w)
    return np.asarray(h).reshape(-1, 1)


def margin(sys: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    s = _lti(sys)
    w, mag, phase = _sig.bode(s)
    w = np.asarray(w)
    mag = np.asarray(mag)
    phase = np.asarray(phase)
    gm = np.inf
    pm = np.inf
    wcg = np.nan
    wcp = np.nan
    for i in range(len(w) - 1):
        if phase[i] <= -180 <= phase[i + 1] or phase[i + 1] <= -180 <= phase[i]:
            wcg = w[i]
            gm = -mag[i]
            break
    for i in range(len(w)):
        if mag[i] <= 0:
            pm = 180 + phase[i]
            wcp = w[i]
            break
    return np.array([[gm]]), np.array([[pm]]), np.array([[wcg]]), np.array([[wcp]])


def nyquist(sys: Any) -> tuple[np.ndarray, np.ndarray]:
    s = _lti(sys)
    w, h = _sig.freqresp(s)
    return np.asarray(h.real).reshape(-1, 1), np.asarray(h.imag).reshape(-1, 1)


def gensig(kind: Any, tau: Any, tfinal: Any, Ts: Any = None) -> tuple[np.ndarray, np.ndarray]:
    k = str(kind).lower()
    tfinal = float(scalar_value(tfinal))
    Ts = float(scalar_value(Ts)) if Ts is not None else tfinal / 1000.0
    t = np.arange(0, tfinal + Ts, Ts)
    tau = float(scalar_value(tau))
    if k in ("sin", "sine"):
        u = np.sin(2 * np.pi * t / tau)
    elif k in ("square",):
        u = _sig.square(2 * np.pi * t / tau)
    elif k in ("pulse",):
        u = _sig.square(2 * np.pi * t / tau, duty=0.5)
    else:
        u = np.zeros_like(t)
    return u.reshape(-1, 1), t.reshape(-1, 1)


def initial(sys: Any, x0: Any) -> np.ndarray:
    s = _lti(sys)
    x0 = np.asarray(as_array(x0)).flatten()
    _, y, _ = _sig.lsim(s, U=np.zeros(100), T=np.linspace(0, 1, 100), X0=x0)
    return np.asarray(y).reshape(-1, 1)
