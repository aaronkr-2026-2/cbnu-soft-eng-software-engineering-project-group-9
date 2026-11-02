from __future__ import annotations
from pathlib import Path
import hashlib
import json
import math
import re
from .library import features
from .schema import MotionClip

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_CLAUSE_SPLIT = re.compile(r"\s+(?:and\s+then|and|but|so|because|then)\s+", flags=re.I)
_WORD_RE = re.compile(r"[a-z]+(?:['’][a-z]+)?", flags=re.I)

# Explicit common-conversation intent layer. This is reported as intent routing,
# never disguised as a semantic retrieval hit.
_INTENT_PATTERNS = {
    "greeting": re.compile(r"^(?:(?:hi|hello|hey|hiya)(?:\s+(?:there|everyone|everybody))?|welcome|good\s+(?:morning|afternoon|evening)|nice\s+to\s+meet\s+you|how\s+are\s+you|how['’]?s\s+it\s+going|what['’]?s\s+up)$", re.I),
    "farewell": re.compile(r"^(?:bye|goodbye|see\s+you|see\s+ya|take\s+care|have\s+a\s+good\s+(?:day|night))$", re.I),
    "thanks": re.compile(r"^(?:thanks|thank\s+you|thanks\s+a\s+lot|many\s+thanks|appreciate\s+it)$", re.I),
    "agreement": re.compile(r"^(?:yes|yeah|yep|yup|agreed|exactly|correct|absolutely|okay|ok|sure|of\s+course|sounds\s+good)$", re.I),
    "response": re.compile(r"^(?:no|nope|not\s+really|maybe|perhaps|i\s+don['’]?t\s+know)$", re.I),
    "request": re.compile(r"^(?:please\s+)?(?:continue|go\s+on|keep\s+going|tell\s+me(?:\s+more)?|show\s+me(?:\s+.+)?|explain(?:\s+this|\s+that|\s+it)?)$", re.I),
}
_INTENT_CLIPS = {
    "greeting": "0iIh5YYDR2o_30_0",
    "farewell": "0iIh5YYDR2o_30_0",
    "thanks": "0iIh5YYDR2o_30_0",
    "agreement": "AFRmGkdXkxA_23_4",
    "response": "0iIh5YYDR2o_30_0",
    "question": "GB4s5b9NL3I_25_3",
    "request": "0iIh5YYDR2o_30_0",
}


class Retriever:
    def __init__(self, index_path: str | Path, lexical_threshold: float = 0.08):
        self.index_path = Path(index_path).resolve()
        obj = json.loads(self.index_path.read_text(encoding="utf-8"))
        self.idf: dict[str, float] = obj["idf"]
        self.vectors: list[dict[str, float]] = obj["vectors"]
        self.meta: list[dict] = obj["meta"]
        # Portable indexes store clip paths relative to the index directory.
        for meta in self.meta:
            clip_path = Path(meta["path"])
            if not clip_path.is_absolute():
                meta["path"] = str((self.index_path.parent / clip_path).resolve())
        self.lexical_threshold = float(lexical_threshold)

    @staticmethod
    def chunks(text: str) -> list[str]:
        chunks: list[str] = []
        for sent in _SENTENCE_SPLIT.split(text.strip()):
            sent = sent.strip()
            if not sent:
                continue
            parts = [p.strip() for p in _CLAUSE_SPLIT.split(sent) if p.strip()]
            chunks.extend(parts or [sent])
        return chunks or ([text.strip()] if text.strip() else [])

    def _query_vector(self, text: str) -> dict[str, float]:
        counts = features(text)
        v = {term: float((1.0 + math.log(count)) * self.idf[term])
             for term, count in counts.items() if term in self.idf}
        norm = math.sqrt(sum(x*x for x in v.values())) or 1.0
        return {k: x / norm for k, x in v.items()}

    def search(self, text: str, k: int = 3) -> list[tuple[float, dict]]:
        q = self._query_vector(text)
        scored = []
        for i, d in enumerate(self.vectors):
            score = sum(weight * d.get(term, 0.0) for term, weight in q.items())
            scored.append((float(score), self.meta[i]))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:max(1, min(k, len(scored)))]

    def _intent_for(self, chunk: str) -> str | None:
        cleaned = " ".join(_WORD_RE.findall(chunk.lower()))
        for name, pattern in _INTENT_PATTERNS.items():
            if pattern.fullmatch(cleaned):
                return name
        words = cleaned.split()
        question_leads = {"who", "what", "when", "where", "why", "how", "can", "could", "would", "should", "do", "does", "is", "are"}
        if words and len(words) <= 8 and (chunk.strip().endswith("?") or words[0] in question_leads):
            return "question"
        return None

    def _intent_meta(self, intent: str) -> dict:
        wanted = _INTENT_CLIPS.get(intent)
        if wanted:
            for meta in self.meta:
                if meta.get("clip_id") == wanted:
                    return meta
        return self._fallback_meta(intent)

    def _fallback_meta(self, chunk: str) -> dict:
        beats = [m for m in self.meta if str(m.get("gesture_type") or "").lower() == "beat"]
        candidates = beats or self.meta
        if not candidates:
            raise RuntimeError("empty motion index")
        digest = hashlib.sha256(chunk.lower().encode("utf-8")).digest()
        idx = int.from_bytes(digest[:8], "big") % len(candidates)
        return candidates[idx]

    def plan_for_text(self, text: str) -> list[dict]:
        plan=[]
        for chunk in self.chunks(text):
            intent = self._intent_for(chunk)
            if intent is not None:
                meta = self._intent_meta(intent)
                score = 1.0
                mode = "intent"
            else:
                hits=self.search(chunk,k=1)
                score,meta=hits[0]
                if score >= self.lexical_threshold:
                    mode="lexical"
                else:
                    meta=self._fallback_meta(chunk)
                    score=0.0
                    mode="beat_fallback" if str(meta.get("gesture_type") or "").lower()=="beat" else "library_fallback"
            plan.append({"chunk":chunk,"score":float(score),"mode":mode,"intent":intent,"meta":meta})
        return plan

    def motion_for_text(self, text: str) -> list[MotionClip]:
        return [MotionClip.load_npz(step["meta"]["path"]) for step in self.plan_for_text(text)]
