from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np

POSE_LANDMARKS = 33
FACE_LANDMARKS = 468
HAND_LANDMARKS = 21
LEGACY_LANDMARK_COUNT = POSE_LANDMARKS + 2 * HAND_LANDMARKS
LANDMARK_COUNT = POSE_LANDMARKS + FACE_LANDMARKS + 2 * HAND_LANDMARKS


def to_holistic_layout(poses: np.ndarray) -> np.ndarray:
    """Upgrade legacy body+hands clips by inserting an empty face component."""
    x = np.asarray(poses, dtype=np.float32)
    if x.ndim != 3 or x.shape[2] != 3:
        raise ValueError(f"poses must be [T,N,3], got {x.shape}")
    if x.shape[1] == LANDMARK_COUNT:
        return x
    if x.shape[1] != LEGACY_LANDMARK_COUNT:
        raise ValueError(f"expected {LEGACY_LANDMARK_COUNT} or {LANDMARK_COUNT} landmarks, got {x.shape}")
    out = np.full((len(x), LANDMARK_COUNT, 3), np.nan, dtype=np.float32)
    out[:, :POSE_LANDMARKS] = x[:, :POSE_LANDMARKS]
    out[:, POSE_LANDMARKS + FACE_LANDMARKS:] = x[:, POSE_LANDMARKS:]
    return out

@dataclass
class MotionClip:
    clip_id: str
    text: str
    poses: np.ndarray  # [T,75,3] legacy or [T,543,3] pose-format Holistic
    fps: float = 25.0
    audio_path: str | None = None
    speaker: str | None = None
    source: str | None = None
    gesture_type: str | None = None
    quality: dict | None = None

    def validate(self) -> None:
        if self.poses.ndim != 3 or self.poses.shape[2] != 3 or self.poses.shape[1] not in {LEGACY_LANDMARK_COUNT, LANDMARK_COUNT}:
            raise ValueError(f"poses must be [T,{LEGACY_LANDMARK_COUNT}|{LANDMARK_COUNT},3], got {self.poses.shape}")
        if len(self.poses) == 0:
            raise ValueError("motion clip must contain at least one frame")
        if self.fps <= 0:
            raise ValueError("fps must be positive")

    def save_npz(self, path: str | Path) -> None:
        self.validate()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = {
            "clip_id": self.clip_id,
            "text": self.text,
            "fps": self.fps,
            "audio_path": self.audio_path,
            "speaker": self.speaker,
            "source": self.source,
            "gesture_type": self.gesture_type,
            "quality": self.quality,
        }
        np.savez_compressed(path, poses=self.poses.astype(np.float32), meta=json.dumps(meta))

    @classmethod
    def load_npz(cls, path: str | Path) -> "MotionClip":
        data = np.load(path, allow_pickle=False)
        meta = json.loads(str(data["meta"]))
        clip = cls(poses=data["poses"].astype(np.float32), **meta)
        clip.validate()
        return clip
