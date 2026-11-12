"""Promote reviewed staged clips, preserving originals outside the bundle."""
import argparse
import json
import shutil
from pathlib import Path
from cospeaklocal.schema import MotionClip

ap = argparse.ArgumentParser()
ap.add_argument('clips', nargs='+')
args = ap.parse_args()
root = Path('demo_data')
index_path = root / 'asl_dictionary.json'
index = json.loads(index_path.read_text(encoding='utf-8'))
backup = Path('data/processed/hand_repair/replaced')
backup.mkdir(parents=True, exist_ok=True)
for candidate in args.clips:
    source = Path(candidate)
    clip = MotionClip.load_npz(source)
    entry = next(e for e in index['entries'] if e['gloss'] == clip.text)
    old = root / entry['path']
    shutil.copy2(old, backup / old.name)
    target = root / 'asl_clips' / source.name
    shutil.copy2(source, target)
    entry.update(clip_id=clip.clip_id, path=f'asl_clips/{target.name}',
                 fps=clip.fps, quality=clip.quality, source=clip.source,
                 signer_id=clip.speaker, video_id=source.stem.rsplit('__',1)[-1])
    print(f'{clip.text}: {old.name} -> {target.name}')
index_path.write_text(json.dumps(index,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
