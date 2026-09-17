import numpy as np
from cospeaklocal.normalize import normalize_landmarks, interpolate_missing
from cospeaklocal.stitch import smooth_sequence, stitch_sequences
from cospeaklocal.render import canonicalize_upper_body
from cospeaklocal.schema import MotionClip


def test_normalize_shoulders():
    x=np.zeros((2,75,3),dtype=np.float32)
    x[:,11]=[-1,0,0]; x[:,12]=[1,0,0]; x[:,15]=[-2,1,0]
    y=normalize_landmarks(x)
    assert np.allclose(y[:,11,0],-.5)
    assert np.allclose(y[:,12,0],.5)


def test_playback_preserves_geometry_and_serializes_missing_face():
    from cospeaklocal.render import pose_to_jsonable
    import json
    x = np.random.default_rng(7).normal(size=(3,543,3)).astype(np.float32)
    x[1,33:501] = np.nan
    result = pose_to_jsonable(x)
    json.dumps(result, allow_nan=False)
    assert result[1][33] == [None, None, None]
    # Palm foreshortening and face contact must survive serialization unchanged.
    assert np.allclose(np.asarray(result[0]), x[0])


def test_interpolate_missing():
    x=np.zeros((3,75,3),dtype=np.float32); x[1,0,0]=np.nan; x[2,0,0]=2
    y=interpolate_missing(x)
    assert np.isfinite(y).all(); assert y[1,0,0]==1


def test_stitch_shape():
    a=np.zeros((3,75,3),dtype=np.float32); b=np.ones((4,75,3),dtype=np.float32)
    y=stitch_sequences([a,b],transition_frames=2)
    # Legacy 75-point clips are upgraded with an empty face component before
    # stitching so every browser response uses full pose-format Holistic data.
    assert y.shape==(9,543,3)
    assert np.isnan(y[:,33:501]).all()


def test_stitch_trims_to_a_compatible_boundary_before_bridging():
    a = np.zeros((4, 543, 3), dtype=np.float32)
    b = np.zeros((3, 543, 3), dtype=np.float32)
    a[-1, 501:, 0] = 8.0
    b[0, 501:, 0] = 1.0
    b[1, 501:, 0] = 20.0
    y = stitch_sequences([a, b], transition_frames=1)
    # The incompatible final frame of a is trimmed before the short bridge.
    assert len(y) == 7
    assert np.allclose(y[2], a[2])
    assert np.allclose(y[4], b[0])


def test_temporal_smoothing_removes_single_frame_jitter_without_lag():
    x = np.zeros((7, 543, 3), dtype=np.float32)
    x[:, 501, 0] = np.arange(7, dtype=np.float32)
    x[:, 502, 0] = np.arange(7, dtype=np.float32)
    x[3, 501, 0] += 4.0  # A single-frame detector spike.
    y = smooth_sequence(x)
    # The spike is reduced, while a normal linear movement stays aligned.
    assert y[3, 501, 0] < x[3, 501, 0]
    assert np.isclose(y[3, 502, 0], 3.0)


def test_motionclip_roundtrip(tmp_path):
    p=tmp_path/'x.npz'; c=MotionClip('x','hello',np.zeros((2,75,3),dtype=np.float32)); c.save_npz(p)
    d=MotionClip.load_npz(p); assert d.clip_id=='x' and d.poses.shape==(2,75,3)


def test_retriever_prefers_matching_phrase(tmp_path):
    from cospeaklocal.library import MotionLibrary
    from cospeaklocal.retrieval import Retriever
    a=MotionClip('a','a vaccine delivered with a needle',np.zeros((2,75,3),dtype=np.float32))
    b=MotionClip('b','mainstream fashion component',np.ones((2,75,3),dtype=np.float32))
    root=tmp_path/'clips'; root.mkdir(); a.save_npz(root/'a.npz'); b.save_npz(root/'b.npz')
    lib=MotionLibrary(root).load(); lib.build_index(); idx=tmp_path/'index.json'; lib.save_index(idx)
    hits=Retriever(idx).search('needle vaccine',2)
    assert hits[0][1]['clip_id']=='a'
    assert hits[0][0] > hits[1][0]


def test_retriever_chunking_is_english_clause_based():
    from cospeaklocal.retrieval import Retriever
    assert Retriever.chunks('I agree on quality, and then we change the plan.') == [
        'I agree on quality,', 'we change the plan.'
    ]


def test_fallback_prefers_beat_and_is_deterministic(tmp_path):
    from cospeaklocal.library import MotionLibrary
    from cospeaklocal.retrieval import Retriever
    root=tmp_path/'clips'; root.mkdir()
    MotionClip('beat','rhythmic emphasis',np.zeros((2,75,3),dtype=np.float32),gesture_type='Beat').save_npz(root/'beat.npz')
    MotionClip('image','describes a tall tower',np.ones((2,75,3),dtype=np.float32),gesture_type='Imagistic').save_npz(root/'image.npz')
    lib=MotionLibrary(root).load(); lib.build_index(); idx=tmp_path/'index.json'; lib.save_index(idx)
    r=Retriever(idx)
    p1=r.plan_for_text('quantum bananas dance sideways')[0]
    p2=r.plan_for_text('quantum bananas dance sideways')[0]
    assert p1['mode']=='beat_fallback'
    assert p1['meta']['clip_id']=='beat'
    assert p1['meta']['clip_id']==p2['meta']['clip_id']


def test_canonicalize_upper_body_has_fixed_bone_lengths():
    x=np.zeros((3,75,3),dtype=np.float32)
    x[:,11,:2]=[-.2,0]; x[:,12,:2]=[.2,0]
    x[:,13,:2]=[-1,1]; x[:,15,:2]=[-3,1.5]
    x[:,14,:2]=[.5,2]; x[:,16,:2]=[1.0,4]
    x[:,33,:2]=x[:,15,:2]; x[:,42,:2]=x[:,15,:2]+[0,.8]
    x[:,54,:2]=x[:,16,:2]; x[:,63,:2]=x[:,16,:2]+[0,.05]
    y=canonicalize_upper_body(x)
    assert np.allclose(np.linalg.norm(y[:,11,:2]-y[:,12,:2],axis=1),1.0,atol=1e-5)
    assert np.allclose(np.linalg.norm(y[:,11,:2]-y[:,13,:2],axis=1),.62,atol=1e-5)
    assert np.allclose(np.linalg.norm(y[:,13,:2]-y[:,15,:2],axis=1),.52,atol=1e-5)
    assert np.allclose(np.linalg.norm(y[:,33,:2]-y[:,42,:2],axis=1),.18,atol=1e-4)
