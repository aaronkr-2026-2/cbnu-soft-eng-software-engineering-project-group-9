"""Download and hash-verify the official TED Gesture-Type metadata artifact."""
from __future__ import annotations
import argparse, hashlib, os, urllib.request
from pathlib import Path

FILE_ID='1QwXCnCPIC0TiVDY_K3Gq0iGVeYXkhvwl'
URL=f'https://drive.usercontent.google.com/download?id={FILE_ID}&export=download&confirm=t'
EXPECTED_SHA256='753fb598910333e5f243adc0fcb7699abe8af19b5f437de4ff0e8ff3a1ef60f6'

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='data/source/TED_gesture-type_dataset.pickle'); args=ap.parse_args()
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists() and sha256(out)==EXPECTED_SHA256:
        print(f'already verified: {out}'); return
    part=Path(str(out)+'.part')
    req=urllib.request.Request(URL,headers={'User-Agent':'CoSpeakLocal/0.1'})
    with urllib.request.urlopen(req,timeout=60) as r, part.open('wb') as f:
        while True:
            b=r.read(1024*1024)
            if not b: break
            f.write(b)
    got=sha256(part)
    if got != EXPECTED_SHA256:
        part.unlink(missing_ok=True)
        raise RuntimeError(f'SHA-256 mismatch: expected {EXPECTED_SHA256}, got {got}')
    os.replace(part,out)
    print(f'verified {out} sha256={got}')
if __name__=='__main__': main()
