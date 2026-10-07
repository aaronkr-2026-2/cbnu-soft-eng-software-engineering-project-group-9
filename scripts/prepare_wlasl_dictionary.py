"""Build an English isolated-ASL landmark dictionary from WLASL metadata.

This follows ViSTAR's generation-side pattern: one gloss -> one isolated motion
sequence. Raw source videos are temporary and are never committed.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.request import urlopen
import cv2
from cospeaklocal.mediapipe_extract import extract_video

METADATA_URL = 'https://raw.githubusercontent.com/dxli94/WLASL/master/start_kit/WLASL_v0.3.json'
DEFAULT_GLOSSES = [
    'hello','thank you','yes','no','please','sorry','help','good','bad','love',
    'you','i','we','what','where','how','name','friend','work','school','home',
    'want','need','like','understand','again','morning','night','today','tomorrow',
    'who','when','why','can','go','come','stop','start','more','big','small','happy','sad',
]


def ensure_metadata(path: Path) -> list[dict]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(urlopen(METADATA_URL, timeout=60).read())
    return json.loads(path.read_text(encoding='utf-8'))


def source_key(url: str) -> str:
    m = re.search(r'(?:v=|youtu\.be/)([A-Za-z0-9_-]{6,})', url)
    if m:
        return m.group(1)
    return hashlib.sha1(url.encode()).hexdigest()[:16]


def find_source(cache: Path, key: str) -> Path | None:
    for p in cache.glob(f'{key}.*'):
        if p.suffix.lower() in {'.mp4','.webm','.mkv','.mov'}:
            return p
    return None


def local_source_map(root: Path) -> dict[str, Path]:
    """Index a pre-downloaded WLASL corpus by the dataset video id."""
    if not root.is_dir():
        raise FileNotFoundError(f'local WLASL video root does not exist: {root}')
    videos: dict[str, Path] = {}
    for suffix in ('*.mp4', '*.webm', '*.mkv', '*.mov'):
        for path in root.rglob(suffix):
            videos.setdefault(path.stem, path)
    if not videos:
        raise RuntimeError(f'no videos found below {root}')
    return videos


def download_source(yt_dlp: Path, cache: Path, url: str) -> Path:
    key = source_key(url)
    existing = find_source(cache, key)
    if existing:
        return existing
    cache.mkdir(parents=True, exist_ok=True)
    selector = (
        'bestvideo[vcodec^=avc1][ext=mp4][height<=360]/'
        'bestvideo[vcodec^=avc1][ext=mp4][height<=480]/best[ext=mp4]'
    )
    # Force a deterministic local name rather than the upstream video id.
    out = cache / f'{key}.%(ext)s'
    subprocess.run([str(yt_dlp), '--no-playlist', '--no-warnings', '-f', selector,
                    '-o', str(out), url], check=True)
    p = find_source(cache, key)
    if p is None:
        raise FileNotFoundError(f'download succeeded but no source file found for {url}')
    return p


def source_info(path: Path) -> tuple[float,int]:
    cap=cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f'cannot open {path}')
    fps=float(cap.get(cv2.CAP_PROP_FPS) or 0)
    n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release(); return fps,n


def candidate_rows(metadata: list[dict], glosses: list[str]) -> dict[str,list[dict]]:
    by={str(r['gloss']).lower(): r for r in metadata}
    result={}
    for gloss in glosses:
        row=by.get(gloss.lower())
        if not row:
            continue
        inst=list(row.get('instances',[]))
        # Prefer the common signer/source used heavily in WLASL, then train/val/test.
        inst.sort(key=lambda x: (x.get('signer_id') != 9, x.get('source') != 'asl5200', x.get('instance_id',0)))
        result[gloss.lower()]=inst
    return result


def existing_glosses(index: Path) -> list[str]:
    if not index.exists():
        return []
    try:
        obj = json.loads(index.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return []
    return [str(entry.get('gloss', '')).strip().lower() for entry in obj.get('entries', []) if entry.get('gloss')]


def top_local_glosses(metadata: list[dict], video_paths: dict[str, Path]) -> list[str]:
    """Rank glosses by the number of usable local WLASL instances."""
    ranked: list[tuple[int, str]] = []
    for row in metadata:
        gloss = str(row.get('gloss', '')).strip().lower()
        count = sum(str(inst.get('video_id')) in video_paths for inst in row.get('instances', []))
        if gloss and count:
            ranked.append((count, gloss))
    return [gloss for _, gloss in sorted(ranked, key=lambda item: (-item[0], item[1]))]


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--metadata', default='data/vendor/wlasl/WLASL_v0.3.json')
    ap.add_argument('--out', default='data/processed/wlasl')
    ap.add_argument('--index', default='data/index/asl_dictionary.json')
    ap.add_argument('--cache', default='data/raw/wlasl_cache')
    ap.add_argument('--yt-dlp', default=('tools/yt-dlp.exe' if sys.platform.startswith('win') else 'tools/yt-dlp'))
    ap.add_argument('--glosses', default=','.join(DEFAULT_GLOSSES))
    ap.add_argument('--local-video-root', help='pre-downloaded WLASL corpus; skips yt-dlp downloads')
    ap.add_argument('--target-count', type=int, help='expand the requested/current dictionary to this many locally covered glosses')
    ap.add_argument('--portable-index-paths', action='store_true', help='store clip paths relative to the index for deployment')
    ap.add_argument('--max-attempts-per-gloss', type=int, default=4)
    ap.add_argument('--force', action='store_true', help='re-extract existing clips with the active pose pipeline')
    ap.add_argument('--keep-source', action='store_true')
    args=ap.parse_args()
    metadata=ensure_metadata(Path(args.metadata))
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    cache=Path(args.cache); ytdlp=Path(args.yt_dlp).resolve()
    local_videos = local_source_map(Path(args.local_video_root)) if args.local_video_root else None
    requested=[g.strip().lower() for g in args.glosses.split(',') if g.strip()]
    if args.target_count is not None:
        if args.target_count < 1:
            raise ValueError('--target-count must be positive')
        if local_videos is None:
            raise ValueError('--target-count requires --local-video-root for reproducible coverage selection')
        seeds = existing_glosses(Path(args.index)) + requested
        ranked = top_local_glosses(metadata, local_videos)
        glosses = list(dict.fromkeys(seeds + ranked))[:args.target_count]
    else:
        glosses = list(dict.fromkeys(requested))
    candidates=candidate_rows(metadata, glosses)
    entries=[]; report=[]

    def index_clip_path(path: Path) -> str:
        return f'asl_clips/{path.name}' if args.portable_index_paths else str(path.resolve())

    # Existing outputs are reusable.
    for gloss in glosses:
        safe=re.sub(r'[^a-z0-9]+','_',gloss).strip('_')
        existing=sorted(out.glob(f'{safe}__*.npz'))
        if existing and not args.force:
            from cospeaklocal.schema import MotionClip
            clip=MotionClip.load_npz(existing[0])
            entries.append({'gloss':gloss,'clip_id':clip.clip_id,'path':index_clip_path(existing[0]),
                            'fps':clip.fps,'source':clip.source,'quality':clip.quality})
            continue
        insts=candidates.get(gloss,[])
        ok=False
        for inst in insts[:args.max_attempts_per_gloss]:
            url=inst.get('url')
            if not url: continue
            rec={'gloss':gloss,'video_id':inst.get('video_id'),'url':url,'instance_id':inst.get('instance_id')}
            pending=None
            try:
                src = local_videos.get(str(inst.get('video_id'))) if local_videos is not None else download_source(ytdlp,cache,url)
                if src is None:
                    raise FileNotFoundError(f'local WLASL video is unavailable for {inst.get("video_id")}')
                sfps,nframes=source_info(src)
                ann_fps=float(inst.get('fps') or 25.0)
                fs=max(1,int(inst.get('frame_start') or 1))
                fe=int(inst.get('frame_end') or -1)
                start=(fs-1)/ann_fps
                end=None if fe < 0 else (fe-1)/ann_fps
                cid=f'wlasl_{safe}_{inst.get("video_id")}'
                path=out/f'{safe}__{inst.get("video_id")}.npz'
                pending=path.with_suffix('.pending.npz')
                pending.unlink(missing_ok=True)
                clip=extract_video(src,gloss,cid,pending,speaker=str(inst.get('signer_id')),
                                   source='wlasl',target_fps=25.0,start_time=start,end_time=end,
                                   gesture_type='ASL')
                q=clip.quality or {}
                active=max(q.get('left_hand_detect_rate',0.0),q.get('right_hand_detect_rate',0.0))
                # Sign generation needs a visible body and at least one tracked hand.
                if q.get('pose_detect_rate',0.0) < 0.75 or active < 0.45:
                    raise RuntimeError(f'poor landmark coverage {q}')
                pending.replace(path)
                entries.append({'gloss':gloss,'clip_id':clip.clip_id,'path':index_clip_path(path),
                                'fps':clip.fps,'source':'wlasl','signer_id':inst.get('signer_id'),
                                'video_id':inst.get('video_id'),'quality':q})
                rec.update(status='ok',frames=len(clip.poses),quality=q,source_fps=sfps,source_frames=nframes)
                report.append(rec); ok=True
                print(f'{gloss}: OK {cid} {len(clip.poses)}f {q}',flush=True)
                break
            except Exception as e:
                if pending is not None:
                    pending.unlink(missing_ok=True)
                rec.update(status='failed',error=repr(e)); report.append(rec)
                print(f'{gloss}: retry after {e!r}',flush=True)
            finally:
                if local_videos is None and not args.keep_source and url:
                    p=find_source(cache,source_key(url))
                    if p: p.unlink(missing_ok=True)
        if not ok:
            print(f'{gloss}: UNAVAILABLE',flush=True)

    idx=Path(args.index); idx.parent.mkdir(parents=True,exist_ok=True)
    idx.write_text(json.dumps({'format':'cospeak-asl-dictionary-v1','entries':entries},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    rp=idx.with_name(idx.stem+'_report.json')
    rp.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'built {len(entries)}/{len(glosses)} signs -> {idx}')
    return 0 if entries else 2

if __name__=='__main__':
    raise SystemExit(main())
