"""Create a tiny procedural NON-DATASET smoke-test library. Replace it with real extracted English clips for demos."""
from pathlib import Path
import numpy as np
from cospeaklocal.schema import MotionClip

out = Path("data/processed"); out.mkdir(parents=True, exist_ok=True)
T=50
base=np.zeros((T,75,3),dtype=np.float32)
# simple normalized torso/arms only, enough to test rendering and retrieval plumbing
for t in range(T):
    p=t/(T-1)
    base[t,11]=[-.5,0,0]; base[t,12]=[.5,0,0]
    base[t,13]=[-.75,.35,0]; base[t,14]=[.75,.35,0]
    base[t,15]=[-.75+.15*np.sin(2*np.pi*p),.75+.15*np.cos(2*np.pi*p),0]
    base[t,16]=[.75-.15*np.sin(2*np.pi*p),.75+.15*np.cos(2*np.pi*p),0]
    base[t,23]=[-.35,1.0,0]; base[t,24]=[.35,1.0,0]
texts=[("beat","Let me explain the next point."),("wide","This is a much bigger idea."),("count","There are several things to consider.")]
for i,(cid,text) in enumerate(texts):
    x=base.copy(); x[:,15,0]-=.12*i; x[:,16,0]+=.12*i
    MotionClip(cid,text,x,25.0,source="procedural-dev-only").save_npz(out/f"{cid}.npz")
print("created",len(texts),"development-only clips")
