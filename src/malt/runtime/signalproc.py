"""Signal processing (FFT, filtering, and spectral analysis) via SciPy."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import signal as _sig

from .arrays import as_array, scalar_value


def _fft_axis(a: np.ndarray) -> int:
    for i in range(a.ndim):
        if a.shape[i] != 1:
            return i
    return 0


def fft(x: Any, n: Any = None) -> np.ndarray:
    a = np.asarray(as_array(x))
    n = None if n is None else int(scalar_value(n))
    return np.fft.fft(a, n=n, axis=_fft_axis(a))


def ifft(x: Any, n: Any = None) -> np.ndarray:
    a = np.asarray(as_array(x))
    n = None if n is None else int(scalar_value(n))
    return np.fft.ifft(a, n=n, axis=_fft_axis(a))


def fft2(x: Any) -> np.ndarray:
    return np.fft.fft2(np.asarray(as_array(x)))


def ifft2(x: Any) -> np.ndarray:
    return np.fft.ifft2(np.asarray(as_array(x)))


def fftn(x: Any) -> np.ndarray:
    return np.fft.fftn(np.asarray(as_array(x)))


def ifftn(x: Any) -> np.ndarray:
    return np.fft.ifftn(np.asarray(as_array(x)))


def fftshift(x: Any) -> np.ndarray:
    return np.fft.fftshift(np.asarray(as_array(x)))


def ifftshift(x: Any) -> np.ndarray:
    return np.fft.ifftshift(np.asarray(as_array(x)))


def nextpow2(x: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return np.asarray([np.ceil(np.log2(v)) if v > 0 else 0 for v in a]).reshape(1, -1)


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def filter(b: Any, a: Any, x: Any) -> np.ndarray:  # noqa: A001 - MATLAB name
    b = np.asarray(as_array(b)).flatten()
    a = np.asarray(as_array(a)).flatten()
    x = np.asarray(as_array(x)).flatten()
    return np.asarray(_sig.lfilter(b, a, x))


def filtfilt(b: Any, a: Any, x: Any) -> np.ndarray:
    b = np.asarray(as_array(b)).flatten()
    a = np.asarray(as_array(a)).flatten()
    x = np.asarray(as_array(x)).flatten()
    return np.asarray(_sig.filtfilt(b, a, x))


def conv2(A: Any, B: Any) -> np.ndarray:
    from scipy.signal import convolve2d

    return np.asarray(convolve2d(np.asarray(as_array(A)), np.asarray(as_array(B))))


def medfilt1(x: Any, n: Any = 3) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return np.asarray(_sig.medfilt(a, int(scalar_value(n))))


def sgolayfilt(x: Any, order: Any, framelen: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return np.asarray(_sig.savgol_filter(a, int(scalar_value(framelen)), int(scalar_value(order))))


# ---------------------------------------------------------------------------
# Filter design
# ---------------------------------------------------------------------------


def butter(n: Any, wn: Any, btype: Any = "low") -> tuple[np.ndarray, np.ndarray]:
    from scipy.signal import butter as _b

    b, a = _b(int(scalar_value(n)), float(scalar_value(wn)), btype=str(btype).lower(), analog=False)
    return np.asarray(b).reshape(1, -1), np.asarray(a).reshape(1, -1)


def cheby1(n: Any, rp: Any, wn: Any, btype: Any = "low") -> tuple[np.ndarray, np.ndarray]:
    from scipy.signal import cheby1 as _c

    b, a = _c(int(scalar_value(n)), float(scalar_value(rp)), float(scalar_value(wn)), btype=str(btype).lower(), analog=False)
    return np.asarray(b).reshape(1, -1), np.asarray(a).reshape(1, -1)


def cheby2(n: Any, rs: Any, wn: Any, btype: Any = "low") -> tuple[np.ndarray, np.ndarray]:
    from scipy.signal import cheby2 as _c

    b, a = _c(int(scalar_value(n)), float(scalar_value(rs)), float(scalar_value(wn)), btype=str(btype).lower(), analog=False)
    return np.asarray(b).reshape(1, -1), np.asarray(a).reshape(1, -1)


def ellip(n: Any, rp: Any, rs: Any, wn: Any, btype: Any = "low") -> tuple[np.ndarray, np.ndarray]:
    from scipy.signal import ellip as _e

    b, a = _e(int(scalar_value(n)), float(scalar_value(rp)), float(scalar_value(rs)), float(scalar_value(wn)), btype=str(btype).lower(), analog=False)
    return np.asarray(b).reshape(1, -1), np.asarray(a).reshape(1, -1)


def fir1(n: Any, wn: Any) -> np.ndarray:
    from scipy.signal import firwin

    return np.asarray(firwin(int(scalar_value(n)) + 1, float(scalar_value(wn)))).reshape(1, -1)


def freqz(b: Any, a: Any = None) -> tuple[np.ndarray, np.ndarray]:
    b = np.asarray(as_array(b)).flatten()
    if a is None:
        a = [1.0]
    a = np.asarray(as_array(a)).flatten()
    w, h = _sig.freqz(b, a)
    return w.reshape(-1, 1), np.abs(h).reshape(-1, 1)


# ---------------------------------------------------------------------------
# Transforms and analysis
# ---------------------------------------------------------------------------


def hilbert(x: Any) -> np.ndarray:
    return np.asarray(_sig.hilbert(np.asarray(as_array(x)).flatten())).reshape(-1, 1)


def xcorr(a: Any, b: Any = None) -> np.ndarray:
    a = np.asarray(as_array(a)).flatten()
    if b is None:
        return np.asarray(np.correlate(a, a, mode="full")).reshape(-1, 1)
    b = np.asarray(as_array(b)).flatten()
    return np.asarray(np.correlate(a, b, mode="full")).reshape(-1, 1)


def findpeaks(x: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    peaks, _ = _sig.find_peaks(a)
    return np.asarray(peaks, dtype=float).reshape(-1, 1)


def resample(x: Any, p: Any, q: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return np.asarray(_sig.resample(a, int(np.round(len(a) * float(scalar_value(p)) / float(scalar_value(q)))))).reshape(-1, 1)


def decimate(x: Any, q: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return np.asarray(_sig.decimate(a, int(scalar_value(q))))


def upsample(x: Any, n: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    n = int(scalar_value(n))
    out = np.zeros(len(a) * n)
    out[::n] = a
    return out.reshape(1, -1)


def downsample(x: Any, n: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    return a[:: int(scalar_value(n))].reshape(1, -1)


def spectrogram(x: Any, *args: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    f, t, s = _sig.spectrogram(a)
    return np.asarray(np.abs(s))


def periodogram(x: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    f, pxx = _sig.periodogram(a)
    return np.asarray(pxx).reshape(1, -1)


def pwelch(x: Any) -> np.ndarray:
    a = np.asarray(as_array(x)).flatten()
    f, pxx = _sig.welch(a)
    return np.asarray(pxx).reshape(1, -1)
