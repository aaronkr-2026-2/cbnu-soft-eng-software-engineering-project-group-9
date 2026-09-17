import io
import pickle
import pytest
from cospeaklocal.safe_pickle import RestrictedNumpyUnpickler


def test_restricted_pickle_rejects_arbitrary_globals():
    payload=pickle.dumps(eval, protocol=3)
    with pytest.raises(pickle.UnpicklingError):
        RestrictedNumpyUnpickler(io.BytesIO(payload)).load()


def test_ted_annotation_clock_is_25fps():
    # Regression guard for conversion used by prepare_ted_gesture_type_subset.py.
    start_frame, end_frame = 8270, 8395
    assert start_frame / 25.0 == 330.8
    assert end_frame / 25.0 == 335.8
