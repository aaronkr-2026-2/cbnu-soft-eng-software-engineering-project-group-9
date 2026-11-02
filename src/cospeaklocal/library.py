from __future__ import annotations
from collections import Counter
from pathlib import Path
import json
import math
import re
from .schema import MotionClip

TOKEN_RE = re.compile(r"[a-z0-9']+")
STOPWORDS = {
    "a","an","and","are","as","at","be","but","by","for","from","had","has","have","he","her","hers","him","his",
    "i","if","in","is","it","its","me","my","of","on","or","our","ours","she","so","that","the","their","theirs",
    "them","then","there","they","this","to","us","was","we","were","what","when","where","which","who","will","with","you","your"
}


def features(text: str) -> Counter[str]:
    """English content-word unigrams plus local bigrams for tiny TF-IDF retrieval."""
    words = TOKEN_RE.findall(text.lower())
    toks = [w for w in words if w not in STOPWORDS]
    # Preserve phrase evidence even when a stopword occurs inside a short phrase.
    toks.extend(f"{a}::{b}" for a, b in zip(words, words[1:]) if a not in STOPWORDS or b not in STOPWORDS)
    return Counter(toks)


class MotionLibrary:
    """Tiny local TF-IDF index implemented with the Python stdlib."""
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.clips: list[MotionClip] = []
        self.index: dict | None = None

    def load(self) -> "MotionLibrary":
        self.clips = [MotionClip.load_npz(p) for p in sorted(self.root.glob("*.npz"))]
        return self

    def build_index(self) -> None:
        if not self.clips:
            self.load()
        if not self.clips:
            raise RuntimeError(f"no .npz motion clips in {self.root}")
        docs = [features(c.text) for c in self.clips]
        df = Counter()
        for d in docs:
            df.update(d.keys())
        n = len(docs)
        idf = {term: math.log((1 + n) / (1 + freq)) + 1.0 for term, freq in df.items()}
        vectors = []
        for d in docs:
            v = {term: float((1.0 + math.log(count)) * idf[term]) for term, count in d.items()}
            norm = math.sqrt(sum(x*x for x in v.values())) or 1.0
            vectors.append({k: x / norm for k, x in v.items()})
        meta = [{
            "clip_id": c.clip_id,
            "text": c.text,
            "path": str((self.root / f"{c.clip_id}.npz").resolve()),
            "fps": c.fps,
            "speaker": c.speaker,
            "source": c.source,
            "gesture_type": c.gesture_type,
        } for c in self.clips]
        self.index = {"idf": idf, "vectors": vectors, "meta": meta}

    def save_index(self, path: str | Path) -> None:
        if self.index is None:
            raise RuntimeError("build_index() first")
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
