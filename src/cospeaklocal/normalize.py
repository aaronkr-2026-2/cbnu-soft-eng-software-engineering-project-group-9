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


def repair_hand_tracks(frames: np.ndarray, max_gap: int = 3,
                       max_wrist_distance: float = 0.25) -> np.ndarray:
    """Reject detached hands; fill only short internal gaps relative to the wrist.

    Distance is measured in shoulder widths in XY (hand/body Z have different
    origins in MediaPipe). Never extrapolate hand shapes into unobserved edges
    or long occlusions. Missing hands remain NaN, not a fabricated gesture.
    Body, face and accepted hand observations are preserved exactly.
    """
    x = np.asarray(frames, dtype=np.float32).copy()
    if x.ndim != 3 or x.shape[1] not in (75, 543) or x.shape[2] != 3:
        raise ValueError('expected [T,75|543,3]')
    if not len(x):
        return x
    width = np.linalg.norm(x[:, 11, :2] - x[:, 12, :2], axis=1)
    offset = 501 if x.shape[1] == 543 else 33
    for start, wrist in ((offset, 15), (offset + 21, 16)):
        hand = x[:, start:start + 21].copy()
        anchors = x[:, wrist]
        valid = np.isfinite(hand).all(axis=(1, 2))
        valid &= np.isfinite(anchors).all(axis=1) & np.isfinite(width) & (width > 1e-6)
        valid &= np.max(np.linalg.norm(hand[:, :, :2] - hand[:, :1, :2], axis=2), axis=1) > 1e-6
        valid &= np.linalg.norm(hand[:, 0, :2] - anchors[:, :2], axis=1) <= width * max_wrist_distance
        hand[~valid] = np.nan
        good = np.flatnonzero(valid)
        for left, right in zip(good[:-1], good[1:]):
            gap = right - left - 1
            if not 0 < gap <= max_gap or not np.isfinite(anchors[left:right + 1]).all():
                continue
            for t in range(left + 1, right):
                alpha = (t - left) / (right - left)
                # Interpolate local hand geometry, not stale screen positions.
                hand[t] = ((1 - alpha) * (hand[left] - anchors[left])
                           + alpha * (hand[right] - anchors[right]) + anchors[t])
                if np.linalg.norm(hand[t, 0, :2] - anchors[t, :2]) > width[t] * max_wrist_distance:
                    hand[t] = np.nan
        x[:, start:start + 21] = hand
    return x
