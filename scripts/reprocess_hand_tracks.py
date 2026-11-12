"""Repair bundled hand tracks; optionally re-extract named local source clips.

Writes staged output and a report under data/processed, never replaces the
deployed bundle until --apply is passed. Existing confidence masks cannot be
recovered from old NPZ files, so cleanup is conservative, not full recovery.
"""
import argparse
import json
import shutil
from pathlib import Path
import numpy as np
from cospeaklocal.normalize import repair_hand_tracks
from cospeaklocal.schema import MotionClip


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--index', default='demo_data/asl_dictionary.json')
    ap.add_argument('--stage', default='data/processed/hand_repair')
    ap.add_argument('--reextract', default='')
    ap.add_argument('--videos', default='D:/pythonProject/WLASL_Complete')
    ap.add_argument('--metadata', default='D:/pythonProject/WLASL_repo/start_kit/WLASL_v0.3.json')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    index = Path(args.index)
    stage = Path(args.stage)
    stage.mkdir(parents=True, exist_ok=True)
    entries = json.loads(index.read_text(encoding='utf-8'))['entries']
    selected = set(filter(None, args.reextract.split(',')))
    videos = {p.stem: p for p in Path(args.videos).rglob('*.mp4')} if selected else {}
    metadata = json.loads(Path(args.metadata).read_text(encoding='utf-8')) if selected else []
    report = []
    for entry in entries:
        path = index.parent / entry['path']
        original = MotionClip.load_npz(path)
        original_poses = original.poses.copy()
        clip = original
        if entry['gloss'] in selected:
            from cospeaklocal.mediapipe_extract import extract_video
            row = next(r for r in metadata if r['gloss'] == entry['gloss'])
            video_id = path.stem.rsplit('__', 1)[-1]
            inst = next(i for i in row['instances'] if str(i['video_id']) == video_id)
            fps = float(inst.get('fps') or 25)
            start = (max(1, int(inst.get('frame_start') or 1)) - 1) / fps
            end_frame = int(inst.get('frame_end') or -1)
            clip = extract_video(videos[video_id], original.text, original.clip_id,
                                 stage / path.name, speaker=original.speaker,
                                 source=original.source, gesture_type=original.gesture_type,
                                 start_time=start,
                                 end_time=None if end_frame < 0 else (end_frame - 1) / fps)
        clip.poses = repair_hand_tracks(clip.poses)
        # Keep old absent-component zero encoding where no hand was ever seen.
        for start in (501, 522):
            if np.all(original_poses[:, start:start+21] == 0):
                clip.poses[:, start:start+21] = 0
        changed = not np.array_equal(original_poses, clip.poses, equal_nan=True)
        if changed:
            clip.save_npz(stage / path.name)
            if args.apply:
                backup = stage / 'originals' / path.name
                backup.parent.mkdir(exist_ok=True)
                if not backup.exists():
                    shutil.copy2(path, backup)
                shutil.copy2(stage / path.name, path)
        visible = np.isfinite(clip.poses[:, [501, 522]]).all(axis=2)
        visible &= np.stack([np.any(clip.poses[:, s:s+21] != 0, axis=(1,2)) for s in (501,522)],axis=1)
        report.append({'gloss': entry['gloss'], 'changed': changed,
                       'reextracted': entry['gloss'] in selected,
                       'hand_wrist_finite_rate': visible.mean(axis=0).tolist()})
        if entry['gloss'] in selected:
            print(report[-1], flush=True)
    (stage / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'{sum(r["changed"] for r in report)}/{len(report)} clips changed; apply={args.apply}', flush=True)


if __name__ == '__main__':
    main()
