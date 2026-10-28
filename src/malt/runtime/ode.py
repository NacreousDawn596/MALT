"""ODE solvers (adaptive explicit Runge-Kutta via SciPy)."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

from ..errors import RuntimeError_
from .arrays import as_array, scalar_value


def ode45(odefun: Any, tspan: Any, y0: Any, nout: int = 2, options: Any = None) -> Any:
    if not callable(odefun):
        raise RuntimeError_("ode45 requires a function handle as its first argument")

    ts = as_array(tspan).flatten()
    if ts.size < 2:
        raise RuntimeError_("tspan must contain at least two elements")
    t0 = float(ts[0])
    t1 = float(ts[-1])
    y0a = as_array(y0).flatten().astype(float)

    def rhs(t: float, y: np.ndarray) -> np.ndarray:
        r = odefun(np.array([[t]]), y.reshape(-1, 1))
        return np.asarray(as_array(r)).flatten().astype(float)

    sol = solve_ivp(rhs, (t0, t1), y0a, method="RK45", rtol=1e-8, atol=1e-10)

    t = sol.t.reshape(-1, 1)
    y = sol.y.T.reshape(sol.y.shape[1], sol.y.shape[0])
    if y.shape[1] == 1:
        y = y.reshape(-1, 1)

    if nout >= 2:
        return t, y
    return t
