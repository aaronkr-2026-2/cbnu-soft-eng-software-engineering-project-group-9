"""Restricted pickle loader for the official TED Gesture-Type artifact.

Pickle is code-capable. This loader intentionally permits only NumPy primitives
observed in the official artifact's opcode scan; any other GLOBAL is rejected.
"""
from __future__ import annotations
import io
import pickle

_ALLOWED = {
    ("numpy.core.multiarray", "_reconstruct"),
    ("numpy", "ndarray"),
    ("numpy", "dtype"),
}

class RestrictedNumpyUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str):
        if (module, name) not in _ALLOWED:
            raise pickle.UnpicklingError(f"forbidden pickle global: {module}.{name}")
        mod = __import__(module, fromlist=[name])
        return getattr(mod, name)

def restricted_numpy_load(file_obj):
    return RestrictedNumpyUnpickler(file_obj).load()

def restricted_numpy_load_path(path):
    with open(path, "rb") as f:
        return restricted_numpy_load(f)
