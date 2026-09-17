from __future__ import annotations
import json
from pathlib import Path
import pytest
from fastapi import HTTPException
from cospeaklocal.app import generate
from cospeaklocal.sign_dictionary import SignDictionary


def test_deploy_bundle_is_portable_and_complete():
    root=Path(__file__).resolve().parents[1]
    index=root/'demo_data/asl_dictionary.json'
    obj=json.loads(index.read_text(encoding='utf-8'))
    assert len(obj['entries']) == 20
    assert all(not Path(m['path']).is_absolute() for m in obj['entries'])
    assert {m['gloss'] for m in obj['entries']} >= {'hello','thank you','yes','no','help','what','how','you'}
    d=SignDictionary(index)
    assert all(Path(m['path']).is_absolute() and Path(m['path']).exists() for m in d.meta)


def test_hosted_input_guards():
    with pytest.raises(HTTPException) as exc:
        generate('x'*601)
    assert exc.value.status_code == 413
    with pytest.raises(HTTPException) as exc:
        generate(' '.join(['hello']*25))
    assert exc.value.status_code == 413


def test_real_hello_uses_isolated_sign_not_fallback():
    r=generate('hello')
    assert r['mode']=='isolated_asl_dictionary'
    assert r['signs']==1 and not r['unknown']
    assert r['matches'][0]['mode']=='isolated_sign'
    assert r['matches'][0]['gloss']=='hello'
    assert r['matches'][0]['clip_id'].startswith('wlasl_hello_')
    assert len(r['frames']) > 0


def test_phrase_and_unknown_behavior_are_explicit():
    r=generate('hello thank you quantum')
    assert r['signs']==2
    assert r['unknown']==['quantum']
    assert [m['mode'] for m in r['matches']] == ['isolated_sign','isolated_sign','unknown']


def test_function_words_are_skipped_not_faked():
    r=generate('how are you')
    assert r['signs']==2
    assert r['unknown']==[]
    assert [(m['surface'],m['mode']) for m in r['matches']] == [
        ('how','isolated_sign'),('are','function_word'),('you','isolated_sign')
    ]
