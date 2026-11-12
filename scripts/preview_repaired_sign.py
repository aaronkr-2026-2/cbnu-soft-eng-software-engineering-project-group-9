"""Render a contact sheet for local pose QA, not a runtime dependency."""
import argparse
from pathlib import Path
import cv2
import numpy as np
from mediapipe.python.solutions.face_mesh_connections import FACEMESH_CONTOURS
from cospeaklocal.schema import MotionClip
from cospeaklocal.render import HAND_EDGES

ap = argparse.ArgumentParser()
ap.add_argument('clip')
ap.add_argument('--out', default='data/processed/hand_repair/preview.png')
args = ap.parse_args()
x = MotionClip.load_npz(args.clip).poses
edges = [(11,12),(11,13),(13,15),(12,14),(14,16),(11,23),(12,24),(23,24)]
edges += [(a+33,b+33) for a,b in FACEMESH_CONTOURS]
edges += [(a+s,b+s) for s in (501,522) for a,b in HAND_EDGES]
ids = np.unique(edges)
points = x[:,ids,:2].reshape(-1,2)
points = points[np.isfinite(points).all(axis=1)]
lo, hi = points.min(axis=0), points.max(axis=0)
scale = min(320/max(hi[0]-lo[0],.01), 340/max(hi[1]-lo[1],.01))
canvas = np.full((400,1440,3), 32, dtype=np.uint8)
for column, frame in enumerate(np.linspace(0,len(x)-1,4).astype(int)):
    f = x[frame]
    for a,b in edges:
        if not np.isfinite(f[[a,b],:2]).all(): continue
        if b in (15,16):
            start = 501 if b == 15 else 522
            if np.isfinite(f[start:start+21]).all() and np.ptp(f[start:start+21,:2],axis=0).max() > 1e-6:
                b = start
        p,q = ((f[[a,b],:2]-lo)*scale + [column*360+20,40]).astype(int)
        cv2.line(canvas,tuple(p),tuple(q),(70,220,120) if a>=501 else (60,60,230),1,cv2.LINE_AA)
    cv2.putText(canvas,f'frame {frame}',(column*360+20,22),cv2.FONT_HERSHEY_SIMPLEX,.5,(240,240,240),1)
Path(args.out).parent.mkdir(parents=True,exist_ok=True)
cv2.imwrite(args.out, canvas)
