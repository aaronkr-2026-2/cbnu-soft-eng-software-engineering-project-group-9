from __future__ import annotations
import numpy as np
from .schema import LANDMARK_COUNT, LEGACY_LANDMARK_COUNT, FACE_LANDMARKS

# Sign-language display is intentionally upper-body + hands only.
POSE_EDGES = [(11,12),(11,13),(13,15),(12,14),(14,16)]
HAND_EDGES = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(17,18),(18,19),(19,20),(0,17)]

LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_ELBOW, RIGHT_ELBOW = 13, 14
LEFT_WRIST, RIGHT_WRIST = 15, 16
LEFT_HAND_START, RIGHT_HAND_START = 33 + FACE_LANDMARKS, 33 + FACE_LANDMARKS + 21


def _unit(v: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if not np.isfinite(n) or n < 1e-6:
        return fallback.astype(np.float32)
    return (v / n).astype(np.float32)


def canonicalize_upper_body(
    frames: np.ndarray,
    upper_arm: float = 0.62,
    forearm: float = 0.52,
    palm: float = 0.18,
) -> np.ndarray:
    """Retarget 2-D pose geometry to one stable avatar skeleton.

    The source MediaPipe clips come from different signers/cameras, so body
    proportions vary even after shoulder normalization. For display we preserve
    arm/hand *directions* but impose conservative, human-scale arm and palm
    lengths. Earlier lengths made a single arm 1.52 times the shoulder width,
    which reads as distorted in a 2-D signing preview. Z is left untouched
    because the browser renderer is 2-D.
    """
    x = np.asarray(frames, dtype=np.float32).copy()
    if x.ndim != 3 or x.shape[2] != 3 or x.shape[1] not in {LEGACY_LANDMARK_COUNT, LANDMARK_COUNT}:
        raise ValueError(f"expected [T,{LEGACY_LANDMARK_COUNT}|{LANDMARK_COUNT},3], got {x.shape}")

    for f in x:
        old_ls, old_rs = f[LEFT_SHOULDER, :2].copy(), f[RIGHT_SHOULDER, :2].copy()
        center = (old_ls + old_rs) * 0.5
        shoulder_dir = _unit(old_rs - old_ls, np.array([1.0, 0.0], dtype=np.float32))
        new_ls = -0.5 * shoulder_dir
        new_rs = 0.5 * shoulder_dir
        f[:, :2] -= center
        f[LEFT_SHOULDER, :2] = new_ls
        f[RIGHT_SHOULDER, :2] = new_rs

        hand_offset = FACE_LANDMARKS if f.shape[0] == LANDMARK_COUNT else 0
        for shoulder_i, elbow_i, wrist_i, hand_start, shoulder_xy in (
            (LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST, 33 + hand_offset, new_ls),
            (RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST, 54 + hand_offset, new_rs),
        ):
            old_elbow = f[elbow_i, :2].copy()
            old_wrist = f[wrist_i, :2].copy()
            upper_dir = _unit(old_elbow - f[shoulder_i, :2], np.array([0.0, 1.0], dtype=np.float32))
            fore_dir = _unit(old_wrist - old_elbow, upper_dir)
            new_elbow = shoulder_xy + upper_dir * upper_arm
            new_wrist = new_elbow + fore_dir * forearm
            f[elbow_i, :2] = new_elbow
            f[wrist_i, :2] = new_wrist

            hs = slice(hand_start, hand_start + 21)
            hand = f[hs, :2].copy()
            old_hand_wrist = hand[0].copy()
            palm_vec = hand[9] - old_hand_wrist
            palm_len = float(np.linalg.norm(palm_vec))
            if np.isfinite(palm_len) and palm_len > 1e-5:
                scale = float(palm / palm_len)
                f[hs, :2] = new_wrist + (hand - old_hand_wrist) * scale
            else:
                f[hs, :2] = new_wrist

    return x


def pose_to_jsonable(frames: np.ndarray, max_frames: int | None = None) -> list:
    # Preserve the extracted geometry, including face/hand contact and palm
    # foreshortening. Independently resizing palms amplifies tracking noise.
    x = np.asarray(frames, dtype=np.float32)
    if max_frames is not None and len(x) > max_frames:
        ids = np.linspace(0, len(x) - 1, max_frames).round().astype(int)
        x = x[ids]
    values = x.astype(object)
    values[~np.isfinite(x)] = None
    return values.tolist()
