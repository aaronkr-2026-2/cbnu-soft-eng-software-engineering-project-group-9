from __future__ import annotations
import numpy as np
from .schema import to_holistic_layout


def _smoothstep(x: np.ndarray) -> np.ndarray:
    return x * x * (3.0 - 2.0 * x)


def smooth_sequence(sequence: np.ndarray) -> np.ndarray:
    """Remove frame-scale detector jitter without slowing or warping a sign.

    A centred five-frame binomial filter has no playback lag and preserves a
    constant-speed movement.  It is applied only within contiguous tracked
    landmark runs; missing pose-format components (all-zero or NaN rows) are
    left untouched so an absent hand cannot smear into a visible one.
    """
    x = np.asarray(sequence, dtype=np.float32).copy()
    if len(x) < 3:
        return x
    kernel = np.asarray([1, 4, 6, 4, 1], dtype=np.float32) / 16.0
    for landmark in range(x.shape[1]):
        tracked = np.isfinite(x[:, landmark]).all(axis=1)
        tracked &= np.any(np.abs(x[:, landmark]) > 1e-8, axis=1)
        starts = np.flatnonzero(tracked & np.r_[True, ~tracked[:-1]])
        ends = np.flatnonzero(tracked & np.r_[~tracked[1:], True]) + 1
        for start, end in zip(starts, ends):
            if end - start < 3:
                continue
            run = x[start:end, landmark]
            padded = np.pad(run, ((2, 2), (0, 0)), mode="edge")
            x[start:end, landmark] = np.stack(
                [np.convolve(padded[:, axis], kernel, mode="valid") for axis in range(3)],
                axis=1,
            )
    return x


def _boundary_pair(previous: np.ndarray, following: np.ndarray, window: int) -> tuple[int, int]:
    """Choose the most compatible frames near an isolated-sign boundary.

    Isolated signs often include lead-in and follow-through. Joining literal
    endpoints makes a hand teleport; blending a long run of every landmark
    makes the signer appear to move in slow motion. This retains the sign
    motion and discards only a few incompatible boundary frames.
    """
    # A dense, nearly static face would drown out the hand and arm signal.
    landmark_ids = np.r_[11:17, 501:543]
    start = max(0, len(previous) - window)
    stop = min(window, len(following))
    best_i, best_j = len(previous) - 1, 0
    best_score = np.inf
    # Start at the literal endpoints so ties preserve the complete clips.
    for i in range(len(previous) - 1, start - 1, -1):
        a = previous[i, landmark_ids]
        for j in range(stop):
            b = following[j, landmark_ids]
            valid = np.isfinite(a).all(axis=1) & np.isfinite(b).all(axis=1)
            if not np.any(valid):
                continue
            score = float(np.mean((a[valid] - b[valid]) ** 2))
            if score < best_score:
                best_score, best_i, best_j = score, i, j
    return best_i, best_j


def stitch_sequences(sequences: list[np.ndarray], transition_frames: int = 3) -> np.ndarray:
    """Join isolated signs with a short, boundary-aware eased transition."""
    seqs = [to_holistic_layout(s) for s in sequences if len(s)]
    if not seqs:
        return np.empty((0, 543, 3), dtype=np.float32)
    out = seqs[0].copy()
    for nxt in seqs[1:]:
        n = max(0, int(transition_frames))
        if n:
            last, first = _boundary_pair(out, nxt, window=max(1, n * 2))
            out = out[: last + 1]
            nxt = nxt[first:]
            a = out[-1]
            b = nxt[0]
            alpha = _smoothstep(np.linspace(0.0, 1.0, n + 2, dtype=np.float32)[1:-1])[:, None, None]
            bridge = (1.0 - alpha) * a[None] + alpha * b[None]
            out = np.concatenate([out, bridge, nxt], axis=0)
        else:
            out = np.concatenate([out, nxt], axis=0)
    return out
