"""Report hand/body wrist disagreement in the bundled dictionary."""
import json
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[1] / 'demo_data'
entries = json.loads((root / 'asl_dictionary.json').read_text())['entries']
for entry in entries:
    a = np.load(root / entry['path'])['poses']
    gaps = np.linalg.norm(a[:, [15, 16], :2] - a[:, [501, 522], :2], axis=2)
    if entry['gloss'] in ('coffee', 'hello', 'book', 'drink', 'thank you'):
        print(entry['gloss'], entry.get('quality'), a.shape)
        print(a[len(a)//2, [11, 12, 13, 14, 15, 16, 501, 522], :2])
        print('median/max wrist gaps', np.median(gaps, axis=0), gaps.max(axis=0))
        print('worst frames', gaps.argmax(axis=0))
        print('first/last hand wrists', a[[0, -1]][:, [501, 522], :2])
