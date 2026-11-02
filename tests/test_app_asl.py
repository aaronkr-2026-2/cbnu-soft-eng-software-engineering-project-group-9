from pathlib import Path
import json
import numpy as np
import pytest
from cospeaklocal.schema import MotionClip
from cospeaklocal.sign_dictionary import SignDictionary


def test_sign_dictionary_clip_sequence(tmp_path):
    clips=tmp_path/'clips'; clips.mkdir()
    entries=[]
    for gloss in ('hello','thank you'):
        p=clips/(gloss.replace(' ','_')+'.npz')
        c=MotionClip(gloss.replace(' ','_'),gloss,np.zeros((4,75,3),np.float32),gesture_type='ASL')
        c.save_npz(p)
        entries.append({'gloss':gloss,'clip_id':c.clip_id,'path':f'clips/{p.name}','fps':25})
    idx=tmp_path/'dict.json'; idx.write_text(json.dumps({'entries':entries}))
    d=SignDictionary(idx)
    plan=d.plan('hello thanks')
    assert [m.gloss for m in plan] == ['hello','thank you']
    assert len(d.clips_for_plan(plan)) == 2
