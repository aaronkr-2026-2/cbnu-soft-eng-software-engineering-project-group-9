"""Safely export a compact English metadata subset from TED Gesture-Type.

The official pickle includes large Kinect skeleton arrays that CoSpeakLocal does
not use. We load with a restricted NumPy-only unpickler, then write JSONL/CSV
containing only metadata required to re-extract MediaPipe landmarks from video.
"""
from __future__ import annotations
import argparse, csv, json, random
from collections import Counter, defaultdict
from pathlib import Path
from cospeaklocal.safe_pickle import restricted_numpy_load_path

FIELDS = ["vid_id", "gesture_id", "gesture_type", "start_frame_no", "end_frame_no", "text", "remark", "word_timestamp"]

def scalar(x):
    if hasattr(x, "item"):
        try: return x.item()
        except Exception: pass
    return x

def normalize_row(data, i):
    row={k: scalar(data[k][i]) for k in FIELDS if k in data}
    row["vid_id"] = str(row.get("vid_id", "")).strip()
    row["gesture_id"] = str(row.get("gesture_id", i)).strip()
    row["gesture_type"] = str(row.get("gesture_type", "")).strip()
    row["text"] = str(row.get("text", "")).strip()
    row["remark"] = str(row.get("remark", "")).strip()
    row["start_frame_no"] = int(row.get("start_frame_no", 0))
    row["end_frame_no"] = int(row.get("end_frame_no", 0))
    ts=row.get("word_timestamp")
    if hasattr(ts, "tolist"): ts=ts.tolist()
    row["word_timestamp"] = ts
    return row

def choose(rows, limit, per_video, seed):
    rng=random.Random(seed)
    by_type=defaultdict(list)
    for r in rows: by_type[r["gesture_type"].lower()].append(r)
    # Shuffle then round-robin types while capping repeats from one video.
    for xs in by_type.values(): rng.shuffle(xs)
    order=[k for k in ("beat","imagistic") if k in by_type] + [k for k in by_type if k not in ("beat","imagistic")]
    ptr={k:0 for k in order}; used=Counter(); out=[]
    while len(out)<limit and order:
        progressed=False
        for k in list(order):
            xs=by_type[k]
            while ptr[k]<len(xs):
                r=xs[ptr[k]]; ptr[k]+=1
                if used[r["vid_id"]] >= per_video: continue
                out.append(r); used[r["vid_id"]]+=1; progressed=True; break
            if len(out)>=limit: break
        if not progressed: break
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("pickle")
    ap.add_argument("--out-prefix", default="data/metadata/ted_gesture_type_small")
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--per-video", type=int, default=4)
    ap.add_argument("--types", default="Beat,Imagistic")
    ap.add_argument("--seed", type=int, default=42)
    args=ap.parse_args()
    data=restricted_numpy_load_path(args.pickle)
    required=set(FIELDS)|{"skeletons"}
    missing=required-set(data)
    if missing: raise KeyError(f"official artifact missing fields: {sorted(missing)}")
    n=len(data["vid_id"])
    keep={x.strip().lower() for x in args.types.split(',') if x.strip()}
    rows=[]
    for i in range(n):
        r=normalize_row(data,i)
        if keep and r["gesture_type"].lower() not in keep: continue
        if not r["vid_id"] or not r["text"] or r["end_frame_no"]<=r["start_frame_no"]: continue
        rows.append(r)
    selected=choose(rows,args.limit,args.per_video,args.seed)
    prefix=Path(args.out_prefix); prefix.parent.mkdir(parents=True,exist_ok=True)
    jsonl=prefix.with_suffix('.jsonl'); csvp=prefix.with_suffix('.csv')
    with jsonl.open('w',encoding='utf-8') as f:
        for r in selected: f.write(json.dumps(r,ensure_ascii=False,default=str)+'\n')
    csv_fields=["vid_id","gesture_id","gesture_type","start_frame_no","end_frame_no","text","remark"]
    with csvp.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=csv_fields); w.writeheader()
        for r in selected: w.writerow({k:r.get(k,'') for k in csv_fields})
    print('official_rows',n)
    print('eligible_rows',len(rows))
    print('selected_rows',len(selected))
    print('selected_types',dict(Counter(r['gesture_type'] for r in selected)))
    print('unique_videos',len(set(r['vid_id'] for r in selected)))
    print('jsonl',jsonl)
    print('csv',csvp)

if __name__=='__main__': main()
