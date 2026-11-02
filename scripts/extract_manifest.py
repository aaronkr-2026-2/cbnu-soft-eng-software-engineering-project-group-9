from __future__ import annotations
import argparse, csv
from pathlib import Path
from cospeaklocal.mediapipe_extract import extract_video


def main():
    p = argparse.ArgumentParser(description="Extract English co-speech video clips with MediaPipe")
    p.add_argument("manifest", help="CSV: clip_id,video_path,text[,speaker,source]")
    p.add_argument("--out", default="data/processed")
    p.add_argument("--fps", type=float, default=25.0)
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    with open(args.manifest, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if args.limit is not None and i >= args.limit:
                break
            extract_video(
                row["video_path"], row["text"], row["clip_id"], out / f'{row["clip_id"]}.npz',
                speaker=row.get("speaker") or None, source=row.get("source") or None, target_fps=args.fps,
                start_frame=int(row["start_frame"]) if row.get("start_frame") else None,
                end_frame=int(row["end_frame"]) if row.get("end_frame") else None,
            )
            print("extracted", row["clip_id"], flush=True)

if __name__ == "__main__": main()
