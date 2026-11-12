"""Inspect/re-extract already-trimmed local WLASL samples into a staging folder."""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from cospeaklocal.mediapipe_extract import extract_video


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--extract', action='store_true')
    ap.add_argument('--glosses', default='coffee,book,drink')
    ap.add_argument('--candidate', type=int, default=0)
    args = ap.parse_args()
    root = Path('D:/pythonProject/WLASL_Complete')
    videos = {p.stem: p for p in root.rglob('*.mp4')}
    metadata = json.loads(Path('D:/pythonProject/WLASL_repo/start_kit/WLASL_v0.3.json').read_text())
    stage = Path('data/processed/hand_repair/sources')
    stage.mkdir(parents=True, exist_ok=True)
    for gloss in args.glosses.split(','):
        inst = next(r for r in metadata if r['gloss'] == gloss)['instances'][args.candidate]
        source = videos[str(inst['video_id'])]
        cap = cv2.VideoCapture(str(source))
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, count // 2)
        ok, frame = cap.read()
        cap.release()
        if ok:
            cv2.imwrite(str(stage / f'{gloss}.png'), frame)
        print(gloss, source, 'local frames', count, 'annotation', inst['frame_start'], inst['frame_end'], flush=True)
        if args.extract:
            clip = extract_video(source, gloss, f'wlasl_{gloss}_{inst["video_id"]}',
                                 stage / f'{gloss}__{inst["video_id"]}.npz',
                                 speaker=str(inst['signer_id']), source='wlasl', gesture_type='ASL')
            print(gloss, clip.quality, 'visible hands',
                  np.isfinite(clip.poses[:, [501, 522]]).all(axis=2).mean(axis=0), flush=True)


if __name__ == '__main__':
    main()
