import numpy as np
from cospeaklocal.normalize import repair_hand_tracks


def sample(n=9):
    x = np.zeros((n, 543, 3), dtype=np.float32)
    x[:, 11, 0] = -.5
    x[:, 12, 0] = .5
    x[:, 15, 0] = np.arange(n) * .1
    x[:, 501:522] = x[:, 15:16]
    x[:, 502:522, 1] = np.linspace(.01, .2, 20)
    return x


def test_good_hand_and_body_face_are_unchanged():
    x = sample()
    y = repair_hand_tracks(x)
    np.testing.assert_array_equal(x[:, :522], y[:, :522])
    assert np.isnan(y[:, 522:]).all()  # absent hand stays absent


def test_short_gap_follows_moving_wrist():
    x = sample()
    x[3:5, 501:522] = np.nan
    y = repair_hand_tracks(x)
    np.testing.assert_allclose(y[3:5, 501], x[3:5, 15])
    assert np.isfinite(y[:, 501:522]).all()


def test_long_gaps_edges_and_outliers_are_not_fabricated():
    x = sample()
    x[:2, 501:522] = np.nan
    x[3:7, 501:522] += 5
    x[-1, 501:522] = np.nan
    y = repair_hand_tracks(x)
    assert np.isnan(y[:2, 501:522]).all()
    assert np.isnan(y[3:7, 501:522]).all()
    assert np.isnan(y[-1, 501:522]).all()
    np.testing.assert_array_equal(y[2, 501:522], x[2, 501:522])


def test_all_bundled_hands_respect_wrist_distance():
    import json
    from pathlib import Path
    from cospeaklocal.schema import MotionClip
    root = Path(__file__).resolve().parents[1] / 'demo_data'
    for entry in json.loads((root / 'asl_dictionary.json').read_text())['entries']:
        x = MotionClip.load_npz(root / entry['path']).poses
        width = np.linalg.norm(x[:, 11, :2] - x[:, 12, :2], axis=1)
        for start, wrist in ((501, 15), (522, 16)):
            hand = x[:, start:start+21]
            valid = np.isfinite(hand).all(axis=(1,2)) & np.any(hand != 0, axis=(1,2))
            distance = np.linalg.norm(hand[:,0,:2] - x[:,wrist,:2],axis=1)
            assert np.all(distance[valid] <= width[valid] * .25 + 1e-6), entry['gloss']


def test_reextracted_coffee_has_both_hands_and_json_safe_transitions():
    import json
    from cospeaklocal.app import generate
    coffee = generate('coffee')
    frames = np.asarray(coffee['frames'], dtype=float)
    assert np.isfinite(frames[:, 501:543]).all()
    assert coffee['clips'] == ['wlasl_coffee_11552']
    mixed = generate('hello coffee thank you')
    assert mixed['signs'] == 3
    json.dumps(mixed, allow_nan=False)
