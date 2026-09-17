from __future__ import annotations
import numpy as np

LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12


def normalize_landmarks(frames: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """Center on shoulder midpoint and scale by shoulder width frame-by-frame.

    frames: [T,75,3]. Missing landmarks should be NaN. NaNs are preserved.
    """
    x = np.asarray(frames, dtype=np.float32).copy()
    if x.ndim != 3 or x.shape[1:] != (75, 3):
        raise ValueError(f"expected [T,75,3], got {x.shape}")
    for i in range(len(x)):
        ls = x[i, LEFT_SHOULDER]
        rs = x[i, RIGHT_SHOULDER]
        if np.isnan(ls).any() or np.isnan(rs).any():
            continue
        center = (ls + rs) / 2.0
        scale = float(np.linalg.norm(ls - rs))
        if scale < eps:
            continue
        valid = ~np.isnan(x[i]).any(axis=1)
        x[i, valid] = (x[i, valid] - center) / scale
    return x


def interpolate_missing(frames: np.ndarray) -> np.ndarray:
    """Linear interpolation per landmark/coordinate; edge gaps use nearest valid value."""
    x = np.asarray(frames, dtype=np.float32).copy()
    t = np.arange(len(x), dtype=np.float32)
    for j in range(x.shape[1]):
        for c in range(x.shape[2]):
            y = x[:, j, c]
            good = np.isfinite(y)
            if good.any():
                x[:, j, c] = np.interp(t, t[good], y[good])
            else:
                x[:, j, c] = 0.0
    return x
