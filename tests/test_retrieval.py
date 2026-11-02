import numpy as np
from cospeaklocal.library import MotionLibrary
from cospeaklocal.retrieval import Retriever
from cospeaklocal.schema import MotionClip


def test_local_tfidf_retrieval(tmp_path):
    clips = tmp_path / "clips"; clips.mkdir()
    for cid, text in [("big", "This is a much bigger idea."), ("count", "There are several things to consider.")]:
        MotionClip(cid, text, np.zeros((2,75,3), dtype=np.float32)).save_npz(clips/f"{cid}.npz")
    idx=tmp_path/"idx.json"
    lib=MotionLibrary(clips).load(); lib.build_index(); lib.save_index(idx)
    r=Retriever(idx)
    assert r.search("a bigger idea",1)[0][1]["clip_id"] == "big"


def test_common_greeting_uses_intent_not_fallback(tmp_path):
    clips = tmp_path / "clips"; clips.mkdir()
    MotionClip("0iIh5YYDR2o_30_0", "generic beat", np.zeros((2,75,3), dtype=np.float32), gesture_type="Beat").save_npz(clips/"0iIh5YYDR2o_30_0.npz")
    MotionClip("other", "unrelated words", np.ones((2,75,3), dtype=np.float32), gesture_type="Beat").save_npz(clips/"other.npz")
    idx=tmp_path/"idx.json"
    lib=MotionLibrary(clips).load(); lib.build_index(); lib.save_index(idx)
    step=Retriever(idx).plan_for_text("Hello!")[0]
    assert step["mode"] == "intent"
    assert step["intent"] == "greeting"
    assert step["meta"]["clip_id"] == "0iIh5YYDR2o_30_0"


def test_short_question_uses_question_intent(tmp_path):
    clips = tmp_path / "clips"; clips.mkdir()
    MotionClip("GB4s5b9NL3I_25_3", "what would it take", np.zeros((2,75,3), dtype=np.float32), gesture_type="Beat").save_npz(clips/"GB4s5b9NL3I_25_3.npz")
    MotionClip("other", "unrelated words", np.ones((2,75,3), dtype=np.float32), gesture_type="Beat").save_npz(clips/"other.npz")
    idx=tmp_path/"idx.json"
    lib=MotionLibrary(clips).load(); lib.build_index(); lib.save_index(idx)
    step=Retriever(idx).plan_for_text("How does this work?")[0]
    assert step["mode"] == "intent"
    assert step["intent"] == "question"
    assert step["meta"]["clip_id"] == "GB4s5b9NL3I_25_3"
