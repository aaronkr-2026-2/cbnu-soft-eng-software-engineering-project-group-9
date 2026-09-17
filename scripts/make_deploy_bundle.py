"""Create the portable isolated-ASL motion bundle used by the hosted demo."""
from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--index',default='data/index/asl_dictionary.json')
    ap.add_argument('--out',default='demo_data')
    args=ap.parse_args()
    index_path=Path(args.index).resolve()
    obj=json.loads(index_path.read_text(encoding='utf-8'))
    out=Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    clips_out=out/'asl_clips'; clips_out.mkdir(parents=True,exist_ok=True)
    entries=[]; total_bytes=0; total_frames=0
    from cospeaklocal.schema import MotionClip
    for src_meta in obj.get('entries',[]):
        meta=dict(src_meta)
        src=Path(meta['path'])
        if not src.is_absolute(): src=(index_path.parent/src).resolve()
        if not src.exists(): raise FileNotFoundError(src)
        # Derivatives only: compact landmark NPZ, never source video/audio.
        dst=clips_out/src.name
        shutil.copy2(src,dst)
        clip=MotionClip.load_npz(dst)
        total_frames += len(clip.poses)
        total_bytes += dst.stat().st_size
        # Do not ship source URL or local path; only minimal provenance IDs.
        meta['path']=f'asl_clips/{dst.name}'
        entries.append(meta)
    bundle={'format':'cospeak-asl-dictionary-v1','entries':entries}
    (out/'asl_dictionary.json').write_text(json.dumps(bundle,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    manifest={
        'signs':len(entries),
        'landmark_frames':total_frames,
        'motion_bytes':total_bytes,
        'landmarks_per_frame':75,
        'source_dataset':'WLASL',
        'raw_video_included':False,
        'raw_audio_included':False,
        'recognition_model_included':False,
    }
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (out/'README.md').write_text(
        '# Hosted isolated-ASL motion bundle\n\n'
        'Contains only MediaPipe landmark derivatives used by the hackathon/research demo. '
        'No WLASL source video or audio is included. The upstream WLASL project states that '
        'the dataset is for academic/computational use and not commercial use; review upstream '
        'terms before any non-research deployment.\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
