"""Build a small real TED Gesture-Type -> MediaPipe motion library.

The official annotations use a 25 FPS frame clock. We convert annotation frame
numbers to seconds before seeking so YouTube re-encodes at a different FPS do
not silently shift the gesture window.

``--max-clips N`` means N *usable output clips*, not merely the first N metadata
rows. If a source video has become private/unavailable, the builder keeps
scanning later metadata rows until N clips are available or the metadata is
exhausted.
"""
from __future__ import annotations
import argparse, csv, json, subprocess, sys
from collections import defaultdict
from pathlib import Path
import cv2
from cospeaklocal.mediapipe_extract import extract_video

ANNOTATION_FPS = 25.0


def find_video(cache: Path, vid: str) -> Path | None:
    for ext in ('.mp4', '.webm', '.mkv', '.mov'):
        p = cache / f'{vid}{ext}'
        if p.exists():
            return p
    return None


def download_video(yt_dlp: Path, cache: Path, vid: str) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    existing = find_video(cache, vid)
    if existing:
        cap = cv2.VideoCapture(str(existing)); ok, _ = cap.read(); cap.release()
        if ok:
            return existing
        try:
            existing.unlink()
        except OSError:
            pass
    # AV1 MP4 is not decodable by every local OpenCV build. Prefer AVC/H.264.
    selector = (
        'bestvideo[vcodec^=avc1][ext=mp4][height<=360][fps=25]/'
        'bestvideo[vcodec^=avc1][ext=mp4][height<=480][fps=25]/'
        'bestvideo[vcodec^=avc1][ext=mp4]'
    )
    cmd = [
        str(yt_dlp), '--no-playlist', '--no-warnings', '-f', selector,
        '-o', str(cache / '%(id)s.%(ext)s'),
        f'https://www.youtube.com/watch?v={vid}',
    ]
    subprocess.run(cmd, check=True)
    p = find_video(cache, vid)
    if p is None:
        raise FileNotFoundError(f'yt-dlp completed but source not found for {vid}')
    return p


def source_info(path: Path) -> tuple[float, int]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f'cannot open downloaded source {path}')
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()
    return fps, frames


def group_rows(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r['vid_id']].append(r)
    return list(groups.items())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('metadata_csv')
    ap.add_argument('--out', default='data/processed/ted')
    ap.add_argument('--cache', default='data/raw/source_cache')
    ap.add_argument('--yt-dlp', default=('tools/yt-dlp.exe' if sys.platform.startswith('win') else 'tools/yt-dlp'))
    ap.add_argument('--max-clips', type=int, default=None,
                    help='target number of usable clips; unavailable rows are replaced by later candidates')
    ap.add_argument('--max-videos', type=int, default=None,
                    help='optional debug cap on distinct attempted source videos')
    ap.add_argument('--keep-source', action='store_true')
    ap.add_argument('--report', default='data/metadata/ted_build_report.json')
    args = ap.parse_args()

    all_rows = list(csv.DictReader(open(args.metadata_csv, encoding='utf-8', newline='')))
    target = args.max_clips if args.max_clips is not None else len(all_rows)
    if target <= 0:
        raise ValueError('--max-clips must be positive')

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    cache = Path(args.cache); ytdlp = Path(args.yt_dlp).resolve()
    report: list[dict] = []
    success = 0
    cursor = 0
    attempted_videos = 0
    round_no = 0

    # Process the smallest candidate prefix likely to satisfy the requested
    # target. If any candidates fail, extend only by the deficit.
    while success < target and cursor < len(all_rows):
        round_no += 1
        need = target - success
        batch = all_rows[cursor: min(len(all_rows), cursor + need)]
        cursor += len(batch)
        if not batch:
            break

        for vid, vrows in group_rows(batch):
            if success >= target:
                break
            pending: list[dict] = []
            for r in vrows:
                if success >= target:
                    break
                clip_path = out / f"{r['gesture_id']}.npz"
                if clip_path.exists():
                    success += 1
                    report.append({
                        'vid_id': vid, 'gesture_id': r['gesture_id'],
                        'gesture_type': r['gesture_type'], 'text': r['text'],
                        'status': 'existing',
                    })
                else:
                    pending.append(r)
            if not pending or success >= target:
                continue

            attempted_videos += 1
            if args.max_videos is not None and attempted_videos > args.max_videos:
                cursor = len(all_rows)
                break

            try:
                src = download_video(ytdlp, cache, vid)
                actual_fps, total_frames = source_info(src)
                for r in pending:
                    if success >= target:
                        break
                    rec = {
                        'vid_id': vid, 'gesture_id': r['gesture_id'],
                        'gesture_type': r['gesture_type'], 'text': r['text'],
                        'source_fps': actual_fps, 'source_frames': total_frames,
                    }
                    try:
                        start_s = int(r['start_frame_no']) / ANNOTATION_FPS
                        end_s = int(r['end_frame_no']) / ANNOTATION_FPS
                        clip = extract_video(
                            src, r['text'], r['gesture_id'], out / f"{r['gesture_id']}.npz",
                            source='ted-gesture-type', target_fps=25.0,
                            start_time=start_s, end_time=end_s,
                            gesture_type=r['gesture_type'],
                        )
                        rec.update(status='ok', frames=int(clip.poses.shape[0]),
                                   start_s=start_s, end_s=end_s)
                        success += 1
                    except Exception as e:
                        rec.update(status='extract_error', error=repr(e))
                    report.append(rec)
            except Exception as e:
                for r in pending:
                    report.append({
                        'vid_id': vid, 'gesture_id': r['gesture_id'],
                        'gesture_type': r['gesture_type'], 'text': r['text'],
                        'status': 'download_error', 'error': repr(e),
                    })
            finally:
                if not args.keep_source:
                    p = find_video(cache, vid)
                    if p is not None:
                        try:
                            p.unlink()
                        except OSError:
                            pass
            print(
                f'round {round_no} source {vid}: usable={success}/{target} '
                f'candidates_scanned={cursor}', flush=True,
            )

    report_path = Path(args.report); report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    failed = sum(r.get('status') in {'download_error', 'extract_error'} for r in report)
    print(
        f'finished: usable={success}/{target} failed_attempts={failed} '
        f'candidates_scanned={cursor} out={out} report={report_path}'
    )
    return 0 if success >= target else 2


if __name__ == '__main__':
    raise SystemExit(main())
