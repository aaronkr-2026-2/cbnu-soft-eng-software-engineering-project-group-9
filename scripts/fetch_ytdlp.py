"""Install the standalone yt-dlp executable into ./tools without Python dependencies."""
from __future__ import annotations
import argparse, os, platform, urllib.request
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--dir',default='tools'); args=ap.parse_args()
    system=platform.system().lower()
    if system=='windows': asset='yt-dlp.exe'
    elif system=='linux': asset='yt-dlp'
    elif system=='darwin': asset='yt-dlp_macos'
    else: raise RuntimeError(f'unsupported platform: {system}')
    out=Path(args.dir)/asset; out.parent.mkdir(parents=True,exist_ok=True)
    url=f'https://github.com/yt-dlp/yt-dlp/releases/latest/download/{asset}'
    req=urllib.request.Request(url,headers={'User-Agent':'CoSpeakLocal/0.1'})
    with urllib.request.urlopen(req,timeout=60) as r, out.open('wb') as f:
        while True:
            b=r.read(1024*1024)
            if not b: break
            f.write(b)
    if system!='windows': os.chmod(out,0o755)
    print(out.resolve())
if __name__=='__main__': main()
