import sys, random, math, os, tempfile
os.environ["TELA_DATA"] = tempfile.mkdtemp()
sys.path.insert(0, "/home/claude/Tela")
import config, layout, render, sensors, hardware, themes
from PIL import Image
from pathlib import Path
ROOT = "/home/claude/Tela"
OUT = sys.argv[1]
only = sys.argv[2:] or [t["id"] for t in themes.entries()]
render.FONT_FAMILIES["arial"] = (["/usr/share/fonts/truetype/freefont/FreeSans.ttf"], ["/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"])
render.FONT_FAMILIES["verdana"] = (["DejaVuSans.ttf"], ["DejaVuSans-Bold.ttf"])
render.FONT_FAMILIES["consolas"] = (["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
                                   ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"])
fields = hardware.fields(hardware.build(hardware.DEMO_RAW))
random.seed(4)

def shot(tid, fam, game, media):
    cfg = config.load(Path(ROOT) / config.DEFAULT)
    cfg["theme"] = {"name": tid}
    if fam == "portrait":
        cfg["display"]["orientation"] = "portrait"
    layout.apply(cfg)
    cfg["colors"] = themes.colors(tid)
    W, H = (480, 320) if fam == "landscape" else (320, 480)
    col = sensors.Collector(cfg, demo=True, base=ROOT, fields=fields, demo_game=game, demo_media=media)
    col.update()
    r = render.Renderer(cfg, W, H, base=ROOT, fields=fields)
    r.draw(col)
    for _ in range(120):
        col.update()
    if "net_down" in col._hist:
        col._hist["net_down"].extend(220 + 120 * math.sin(i / 9) + random.uniform(-40, 40) for i in range(120))
    img = None
    for _ in range(3):
        img = r.draw(col)
    return img

for tid in only:
    tiles = [shot(tid, fam, g, m) for fam in ("landscape", "portrait") for g, m in ((False, True), (True, True))]
    pad = 16
    out = Image.new("RGB", (sum(t.width for t in tiles) + pad * (len(tiles) + 1), 480 + 2 * pad), "#1c1c1e")
    x = pad
    for t in tiles:
        out.paste(t.convert("RGB"), (x, pad)); x += t.width + pad
    out.save(f"{OUT}/{tid}.png")
    print("ok", tid)
