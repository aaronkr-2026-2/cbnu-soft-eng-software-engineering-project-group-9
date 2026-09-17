from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .normalize import interpolate_missing
from .schema import MotionClip


def _extract_with_pose_format(
    frames: list[np.ndarray], fps: float, width: int, height: int
) -> tuple[np.ndarray, np.ndarray]:
    """Run pose-format Holistic and retain the runtime's 75 landmarks.

    pose-format owns MediaPipe extraction, confidence tracking and whole-sequence
    shoulder normalization.  The full 33 body + 468 face + 21 left-hand + 21
    right-hand layout is retained for the web API.
    """
    try:
        from pose_format.utils.holistic import load_holistic
    except ImportError as exc:
        raise RuntimeError(
            "Pose extraction needs pose-format; install requirements-extract.txt."
        ) from exc

    pose = load_holistic(
        frames,
        fps=fps,
        width=width,
        height=height,
        additional_holistic_config={
            "model_complexity": 2,
            "smooth_landmarks": True,
            "refine_face_landmarks": False,
            "min_detection_confidence": 0.5,
            "min_tracking_confidence": 0.5,
        },
    )
    # This is deliberately sequence-level normalization. Per-frame shoulder
    # scaling turns normal camera/tracker variation into visible limb warping.
    pose.normalize(scale_factor=1.0)
    compact = pose.get_components(
        ["POSE_LANDMARKS", "FACE_LANDMARKS", "LEFT_HAND_LANDMARKS", "RIGHT_HAND_LANDMARKS"]
    )
    data = np.ma.filled(compact.body.data[:, 0], np.nan).astype(np.float32)
    confidence = np.asarray(compact.body.confidence[:, 0], dtype=np.float32)
    data[confidence <= 0.0] = np.nan
    return data, confidence


def extract_video(
    video_path: str | Path,
    text: str,
    clip_id: str,
    out_path: str | Path,
    speaker: str | None = None,
    source: str | None = None,
    target_fps: float = 25.0,
    start_frame: int | None = None,
    end_frame: int | None = None,
    start_time: float | None = None,
    end_time: float | None = None,
    gesture_type: str | None = None,
) -> MotionClip:
    """Extract, globally normalize, and save a pose-format ``[T,75,3]`` clip."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"cannot open video: {video_path}")
    src_fps = float(cap.get(cv2.CAP_PROP_FPS) or target_fps)
    if start_time is not None:
        start_frame = int(round(float(start_time) * src_fps))
    if end_time is not None:
        end_frame = int(round(float(end_time) * src_fps))
    start_frame = max(0, int(start_frame or 0))
    if end_frame is not None and int(end_frame) < start_frame:
        cap.release()
        raise ValueError("end must not precede start")

    stride = max(1, round(src_fps / target_fps))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames: list[np.ndarray] = []
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    idx, local_idx = start_frame, 0
    while True:
        if end_frame is not None and idx > int(end_frame):
            break
        ok, frame = cap.read()
        if not ok:
            break
        if local_idx % stride == 0:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        idx += 1
        local_idx += 1
    cap.release()
    if not frames:
        raise RuntimeError(f"no frames extracted from {video_path}")

    fps = float(min(target_fps, src_fps))
    arr, confidence = _extract_with_pose_format(frames, fps=fps, width=width, height=height)
    pose_seen = np.any(confidence[:, :33] > 0.0, axis=1)
    left_seen = np.any(confidence[:, 501:522] > 0.0, axis=1)
    right_seen = np.any(confidence[:, 522:543] > 0.0, axis=1)
    arr = interpolate_missing(arr)
    clip = MotionClip(
        clip_id=clip_id,
        text=text.strip(),
        poses=arr,
        fps=fps,
        speaker=speaker,
        source=source,
        gesture_type=gesture_type,
        quality={
            "pose_detect_rate": float(np.mean(pose_seen)),
            "left_hand_detect_rate": float(np.mean(left_seen)),
            "right_hand_detect_rate": float(np.mean(right_seen)),
        },
    )
    clip.save_npz(out_path)
    return clip
