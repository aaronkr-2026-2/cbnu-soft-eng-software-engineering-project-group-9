"""Regenerate the architecture PNGs: python docs/draw_diagrams.py (Pillow)."""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = Path("C:/Windows/Fonts/segoeui.ttf")
BOLD = Path("C:/Windows/Fonts/segoeuib.ttf")


def render(name, title, subtitle, boxes, arrows, footer):
    image = Image.new("RGB", (1500, 1100), "#0c1220")
    d = ImageDraw.Draw(image)
    def font(size, bold=False):
        path = BOLD if bold else FONT
        return ImageFont.truetype(str(path) if path.exists() else "DejaVuSans.ttf", size)
    d.text((65, 40), title, fill="#f4f7ff", font=font(40, True))
    d.text((65, 102), subtitle, fill="#abbad0", font=font(23))
    for rect, heading, lines, color in boxes:
        d.rounded_rectangle(rect, radius=20, fill=color, outline="#8196b5", width=2)
        x0, y0, x1, y1 = rect
        d.text(((x0+x1)/2, y0+20), heading, anchor="mt", fill="#13233a", font=font(27, True))
        for i, line in enumerate(lines):
            d.text(((x0+x1)/2, y0+64+i*32), line, anchor="mt", fill="#314962", font=font(22))
    for points, label, pos in arrows:
        d.line(points, fill="#c1d3ea", width=4)
        x, y = points[-1]
        px, py = points[-2]
        angle = math.atan2(y-py, x-px)
        d.polygon([(x,y),(x-16*math.cos(angle-.45),y-16*math.sin(angle-.45)),
                   (x-16*math.cos(angle+.45),y-16*math.sin(angle+.45))], fill="#c1d3ea")
        bounds = d.textbbox(pos, label, anchor="mm", font=font(20))
        d.rectangle((bounds[0]-7, bounds[1]-5, bounds[2]+7, bounds[3]+5), fill="#0c1220")
        d.text(pos, label, anchor="mm", fill="#c1d3ea", font=font(20))
    d.text((65,1045), footer, fill="#abbad0", font=font(21))
    pending = ROOT / (name + ".pending")
    image.save(pending, format="PNG")
    pending.replace(ROOT / name)


render("architecture.png", "CoSpeakLocal | System architecture",
       "English input → dictionary lookup → stitched pose sequence → browser animation",
       [
           ((70,185,920,335),"Presentation | HTML + JavaScript",
            ["Text / browser speech input • match feedback",
             "Animated body, face and hand preview"],"#dceaff"),
           ((70,440,920,640),"Application | FastAPI + NumPy",
            ["Validate input → match signs → load motion",
             "Join clips and smooth transitions",
             "Return pose data and match feedback"],"#d9f5e6"),
           ((70,760,920,955),"Data | Bundled JSON + NPZ",
            ["WLASL-derived sign dictionary",
             "Body, face and hand landmarks",
             "Prepared motion clips"],"#eee2ff"),
           ((1030,440,1430,640),"Offline preparation",
            ["WLASL videos + metadata",
             "pose-format / MediaPipe",
             "Normalize + coverage gate"],"#fff0d7"),
       ],
       [
           ([(320,335),(320,440)],"Form input",(200,385)),
           ([(700,440),(700,335)],"JSON poses",(810,385)),
           ([(320,640),(320,760)],"Read index / clips",(210,702)),
           ([(700,760),(700,640)],"Landmarks",(800,702)),
           ([(1230,640),(1230,850),(920,850)],"Derived assets",(1230,720)),
       ],
       "Runtime uses prepared files; video extraction runs separately before deployment.")

render("deployment.png", "CoSpeakLocal | Deployment architecture",
       "One Vercel application serves the browser interface and the FastAPI endpoints.",
       [
           ((70,185,760,355),"User's browser",
            ["HTML / CSS / JavaScript + Canvas",
             "Microphone → browser speech recognition"],"#dceaff"),
           ((70,485,760,695),"Vercel | FastAPI application",
            ["Web interface",
             "Text-to-pose API",
             "Same-origin HTTPS"],"#d9f5e6"),
           ((70,825,760,990),"Bundled motion assets",
            ["Sign dictionary",
             "Prepared pose sequences"],"#eee2ff"),
           ((960,185,1430,355),"Offline workstation",
            ["WLASL source videos",
             "Holistic extraction + normalization"],"#fff0d7"),
           ((960,485,1430,695),"GitHub",
            ["Application source",
             "Prepared dictionary + pose assets",
             "Deployment source"],"#e3e8f0"),
       ],
       [
           ([(300,355),(300,485)],"HTTPS requests",(210,415)),
           ([(590,485),(590,355)],"HTML / JSON",(690,415)),
           ([(410,695),(410,825)],"Local file reads",(550,760)),
           ([(1195,355),(1195,485)],"Commit prepared assets",(1195,415)),
           ([(960,590),(760,590)],"Deploy",(860,553)),
       ],
       "Public URL: co-speak-local.vercel.app • Raw source media stays on the preparation workstation.")
