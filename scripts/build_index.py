from __future__ import annotations
import argparse
from cospeaklocal.library import MotionLibrary

p = argparse.ArgumentParser(description="Build the tiny local English TF-IDF motion index")
p.add_argument("--clips", default="data/processed")
p.add_argument("--out", default="data/index/library.json")
a = p.parse_args()
lib = MotionLibrary(a.clips).load(); lib.build_index(); lib.save_index(a.out)
print(f"indexed {len(lib.clips)} clips -> {a.out}")
