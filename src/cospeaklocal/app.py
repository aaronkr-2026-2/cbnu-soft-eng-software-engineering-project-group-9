from __future__ import annotations
import importlib.util
import os
from pathlib import Path
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from .sign_dictionary import SignDictionary, normalize_words
from .speech import transcribe_local
from .stitch import smooth_sequence, stitch_sequences
from .render import pose_to_jsonable

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
DEPLOY_SIGN_INDEX = ROOT / "demo_data/asl_dictionary.json"
LOCAL_SIGN_INDEX = ROOT / "data/index/asl_dictionary.json"
DEFAULT_SIGN_INDEX = Path(
    os.getenv("COSPEAK_SIGN_INDEX", DEPLOY_SIGN_INDEX if DEPLOY_SIGN_INDEX.exists() else LOCAL_SIGN_INDEX)
)
IS_VERCEL = bool(os.getenv("VERCEL"))
MAX_RESPONSE_FRAMES = int(os.getenv("COSPEAK_MAX_FRAMES", "360" if IS_VERCEL else "500"))
MAX_TEXT_CHARS = int(os.getenv("COSPEAK_MAX_TEXT_CHARS", "600"))
MAX_TEXT_WORDS = int(os.getenv("COSPEAK_MAX_TEXT_WORDS", "24"))

app = FastAPI(title="CoSpeakLocal", docs_url="/api/docs", redoc_url=None)
_sign_dictionary: SignDictionary | None = None


def sign_dictionary() -> SignDictionary:
    global _sign_dictionary
    if _sign_dictionary is None:
        if not DEFAULT_SIGN_INDEX.exists():
            raise HTTPException(503, f"ASL dictionary not built: {DEFAULT_SIGN_INDEX}")
        _sign_dictionary = SignDictionary(DEFAULT_SIGN_INDEX)
    return _sign_dictionary


def generate(text: str) -> dict:
    text = text.strip()
    if not text:
        raise HTTPException(400, "English text is required")
    if len(text) > MAX_TEXT_CHARS:
        raise HTTPException(413, f"Text is limited to {MAX_TEXT_CHARS} characters in the demo")
    words = normalize_words(text)
    if len(words) > MAX_TEXT_WORDS:
        raise HTTPException(413, f"Text is limited to {MAX_TEXT_WORDS} words in the demo")

    planner = sign_dictionary()
    plan = planner.plan(text)
    clips = planner.clips_for_plan(plan)
    seq = smooth_sequence(stitch_sequences([c.poses for c in clips], transition_frames=3))
    matches = []
    unknown = []
    for m in plan:
        if m.meta is None:
            if m.mode == "unknown":
                unknown.append(m.surface)
            matches.append({
                "chunk": m.surface, "surface": m.surface, "mode": m.mode,
                "gloss": None, "score": 0.0, "clip_id": None,
                "gesture_type": "Function word" if m.mode == "function_word" else "Unknown",
            })
        else:
            matches.append({
                "chunk": m.surface, "surface": m.surface, "mode": "isolated_sign",
                "gloss": m.gloss, "score": 1.0, "clip_id": m.meta.get("clip_id"),
                "gesture_type": "ASL", "quality": m.meta.get("quality"),
            })
    return {
        "text": text,
        "mode": "isolated_asl_dictionary",
        "fps": clips[0].fps if clips else 25.0,
        "frames": pose_to_jsonable(seq, max_frames=MAX_RESPONSE_FRAMES) if len(seq) else [],
        "clips": [c.clip_id for c in clips],
        "matches": matches,
        "unknown": unknown,
        "signs": len(clips),
    }


@app.get("/api/health")
def health() -> dict:
    d = sign_dictionary()
    return {
        "ok": True,
        "runtime": "vercel" if IS_VERCEL else "local",
        "mode": "isolated_asl_dictionary",
        "dictionary": DEFAULT_SIGN_INDEX.name,
        "signs": len(d.meta),
        "speech_backend": importlib.util.find_spec("faster_whisper") is not None,
        "recognition": False,
    }


@app.post("/api/text-to-pose")
def text_to_pose(text: str = Form(...)):
    return generate(text)


@app.post("/api/speech-to-pose")
async def speech_to_pose(file: UploadFile = File(...)):
    if importlib.util.find_spec("faster_whisper") is None:
        raise HTTPException(
            503,
            "Server-side speech recognition is disabled in the hosted demo. "
            "Use the browser microphone button or run requirements-speech.txt locally.",
        )
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(await file.read())
        temp = f.name
    try:
        text = transcribe_local(temp)
        result = generate(text)
        result["transcript"] = text
        return result
    finally:
        Path(temp).unlink(missing_ok=True)


app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
