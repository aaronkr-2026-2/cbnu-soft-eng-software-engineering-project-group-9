from pathlib import Path
import json
import numpy as np
from cospeaklocal.schema import MotionClip
from cospeaklocal.sign_dictionary import SignDictionary


def _dict(tmp_path):
    clips=tmp_path/'clips'; clips.mkdir()
    entries=[]
    for gloss in ['hello','thank you','yes','you','work']:
        cid=gloss.replace(' ','_')
        p=clips/f'{cid}.npz'
        MotionClip(cid,gloss,np.zeros((3,75,3),np.float32),gesture_type='ASL').save_npz(p)
        entries.append({'gloss':gloss,'clip_id':cid,'path':f'clips/{p.name}','fps':25})
    idx=tmp_path/'dict.json'; idx.write_text(json.dumps({'entries':entries}))
    return SignDictionary(idx)


def test_longest_gloss_and_alias(tmp_path):
    d=_dict(tmp_path)
    p=d.plan('Hi, thank you!')
    assert [(x.mode,x.gloss) for x in p] == [('isolated_sign','hello'),('isolated_sign','thank you')]


def test_unknown_is_explicit(tmp_path):
    d=_dict(tmp_path)
    p=d.plan('you quantum work')
    assert [x.mode for x in p] == ['isolated_sign','unknown','isolated_sign']
    assert p[1].surface == 'quantum'


def test_function_word_is_skipped_explicitly(tmp_path):
    d=_dict(tmp_path)
    p=d.plan('how are you')
    # how is unknown in this tiny test fixture; are is deliberately skipped.
    assert [(x.surface,x.mode) for x in p] == [('how','unknown'),('are','function_word'),('you','isolated_sign')]
