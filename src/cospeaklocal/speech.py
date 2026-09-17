from __future__ import annotations
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=2)
def _whisper_model(model_size: str):
    """Load an English Whisper model once per process and reuse it."""
    from faster_whisper import WhisperModel
    return WhisperModel(model_size, device="cpu", compute_type="int8")


def transcribe_local(audio_path: str | Path, model_size: str = "tiny.en") -> str:
    """Offline English ASR. The model downloads once, then runs from local cache."""
    model = _whisper_model(model_size)
    segments, _ = model.transcribe(str(audio_path), language="en", vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments if seg.text.strip()).strip()
