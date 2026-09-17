"""Attach gesture type metadata to already-extracted TED .npz clips without re-running MediaPipe."""
from __future__ import annotations
import argparse, csv
from pathlib import Path
from cospeaklocal.schema import MotionClip

ap=argparse.ArgumentParser(); ap.add_argument('metadata_csv'); ap.add_argument('--clips',default='data/processed/ted'); args=ap.parse_args()
rows={r['gesture_id']:r for r in csv.DictReader(open(args.metadata_csv,encoding='utf-8',newline=''))}
updated=0
for p in Path(args.clips).glob('*.npz'):
    c=MotionClip.load_npz(p); r=rows.get(c.clip_id)
    if r and c.gesture_type != r['gesture_type']:
        c.gesture_type=r['gesture_type']; c.save_npz(p); updated+=1
print(f'updated {updated} clips')
