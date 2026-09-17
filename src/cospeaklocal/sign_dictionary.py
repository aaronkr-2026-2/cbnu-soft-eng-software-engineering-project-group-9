from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import re
from .schema import MotionClip

_WORD_RE = re.compile(r"[a-z]+(?:['’][a-z]+)?", re.I)

# Small transparent aliases only; no semantic model is pretending to translate.
SKIP_WORDS = {"a","an","the","am","are","is","was","were","be","been","being","of","to","for","and"}

ALIASES = {
    "hi": "hello",
    "hey": "hello",
    "thanks": "thank you",
    "thanks a lot": "thank you",
    "yeah": "yes",
    "yep": "yes",
    "nope": "no",
    "okay": "yes",
    "ok": "yes",
}


def normalize_words(text: str) -> list[str]:
    return [w.replace("’", "'").lower() for w in _WORD_RE.findall(text)]


@dataclass(frozen=True)
class SignMatch:
    surface: str
    gloss: str | None
    meta: dict | None
    mode: str  # isolated_sign | unknown


class SignDictionary:
    """Portable word/gloss -> isolated sign motion dictionary.

    This mirrors ViSTAR's generation-side dictionary pattern but uses a compact
    JSON index instead of Elasticsearch. It performs longest exact gloss match;
    it is intentionally not a sign recognizer or a learned translation model.
    """

    def __init__(self, index_path: str | Path):
        self.index_path = Path(index_path).resolve()
        obj = json.loads(self.index_path.read_text(encoding="utf-8"))
        self.meta = obj.get("entries", [])
        self.by_gloss: dict[str, dict] = {}
        for m in self.meta:
            gloss = str(m["gloss"]).strip().lower()
            p = Path(m["path"])
            if not p.is_absolute():
                m["path"] = str((self.index_path.parent / p).resolve())
            self.by_gloss.setdefault(gloss, m)
        self.max_gloss_words = max((len(g.split()) for g in self.by_gloss), default=1)

    def plan(self, text: str) -> list[SignMatch]:
        words = normalize_words(text)
        if not words:
            return []
        plan: list[SignMatch] = []
        i = 0
        while i < len(words):
            matched = None
            max_n = min(self.max_gloss_words, len(words) - i)
            # First try literal longest match.
            for n in range(max_n, 0, -1):
                surface = " ".join(words[i:i+n])
                gloss = ALIASES.get(surface, surface)
                if gloss in self.by_gloss:
                    matched = (n, surface, gloss, self.by_gloss[gloss])
                    break
            if matched is not None:
                n, surface, gloss, meta = matched
                plan.append(SignMatch(surface, gloss, meta, "isolated_sign"))
                i += n
                continue
            surface = words[i]
            if surface in SKIP_WORDS:
                plan.append(SignMatch(surface, None, None, "function_word"))
                i += 1
                continue
            # One-word alias may expand to a multiword gloss, e.g. thanks -> thank you.
            gloss = ALIASES.get(surface)
            if gloss and gloss in self.by_gloss:
                plan.append(SignMatch(surface, gloss, self.by_gloss[gloss], "isolated_sign"))
            else:
                plan.append(SignMatch(surface, None, None, "unknown"))
            i += 1
        return plan

    def clips_for_plan(self, plan: list[SignMatch]) -> list[MotionClip]:
        return [MotionClip.load_npz(m.meta["path"]) for m in plan if m.meta is not None]
