"""Convert compact TED Gesture-Type metadata CSV into a MediaPipe extraction manifest.

Run export_ted_gesture_type_metadata.py first. This script never unpickles data.
"""
from __future__ import annotations
import argparse, csv
from pathlib import Path
VIDEO_EXTS=(".mp4", ".mkv", ".webm", ".mov")

def resolve_video(root: Path, vid: str) -> Path | None:
    for ext in VIDEO_EXTS:
        p=root/f"{vid}{ext}"
        if p.exists(): return p
    matches=[p for p in root.glob(f"{vid}.*") if p.is_file()]
    return matches[0] if matches else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("metadata_csv")
    ap.add_argument("--video-root", required=True)
    ap.add_argument("--out", default="data/ted_gesture_type_manifest.csv")
    ap.add_argument("--limit", type=int, default=300)
    args=ap.parse_args()
    root=Path(args.video_root); out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    rows=[]
    with open(args.metadata_csv,encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f):
            vp=resolve_video(root,r['vid_id'])
            if vp is None: continue
            rows.append({"clip_id":f"tedgt_{r['gesture_id']}","video_path":str(vp.resolve()),"text":r['text'].strip(),"speaker":"","source":"ted-gesture-type","start_frame":int(r['start_frame_no']),"end_frame":int(r['end_frame_no']),"gesture_type":r['gesture_type']})
            if args.limit and len(rows)>=args.limit: break
    fields=["clip_id","video_path","text","speaker","source","start_frame","end_frame","gesture_type"]
    with out.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}")

if __name__=='__main__': main()
