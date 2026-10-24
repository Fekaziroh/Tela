"""Writes each built-in theme's Rest screen ("clock:" in themes/<id>.yaml, landscape and portrait).

    python tools/themes/gen_clocks.py [theme ...]

Widgets are absolute (screen pixels). "{weekday} %d/%m" is the date, "{weather_only}" the weather alone.
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import themes  # noqa: E402

DATE = "{weekday} %d/%m"
WX = "{weather_only}"
HEADER = "# Built-in Tela! screen theme (replaced by every update; your changes are kept apart)."


def clk(fmt, x, y, size, align="center", **kw):
    return dict({"type": "clock", "format": fmt, "x": x, "y": y, "size": size, "align": align}, **kw)


def txt(t, x, y, size, align="left", **kw):
    return dict({"type": "text", "text": t, "x": x, "y": y, "size": size, "align": align}, **kw)


def temps(W, y, **kw):
    return [dict({"type": "value", "sensor": "cpu_temp", "x": W / 2 - 12, "y": y, "align": "right", "size": 13,
                  "unit": "°", "prefix": "CPU ", "color": "secondary"}, **kw),
            dict({"type": "value", "sensor": "gpu_temp", "x": W / 2 + 12, "y": y, "align": "left", "size": 13,
                  "unit": "°", "prefix": "GPU ", "color": "secondary"}, **kw)]


def ring(cx, cy, r, th, **kw):
    """A decorative ring (a gauge with no sensor draws only its track)."""
    return dict({"type": "gauge", "cx": cx, "cy": cy, "radius": r, "thickness": th, "start_angle": -90,
                 "end_angle": 270, "size": 0, "unit": ""}, **kw)


def panel(x, y, w, h, **kw):
    return dict({"type": "panel", "x": x, "y": y, "w": w, "h": h}, **kw)


# ---------------------------------------------------------------- one function per theme: (W, H) -> widgets
def clean(W, H):
    land = W > H
    big, cy = (104, H * 0.40) if land else (84, H * 0.38)
    return [clk("%H:%M", W / 2, cy, big, bold=True, spacing=2),
            {"type": "rect", "x": W / 2 - 40, "y": cy + big * 0.62, "w": 80, "h": 2, "color": "accent"},
            clk(DATE, W / 2, cy + big * 0.86, 20 if land else 18, color="secondary"),
            clk(WX, W / 2, cy + big * 0.86 + 30, 16, color="text"),
            *temps(W, H - 18)]


def full(W, H):
    land = W > H
    big, cy = (96, H * 0.42) if land else (72, H * 0.38)
    return [clk("%H:%M", W / 2 - (22 if land else 18), cy, big, bold=True),
            clk("%S", W / 2 + (128 if land else 96), cy + big * 0.18, 28 if land else 22, "left", color="secondary"),
            clk(DATE + "{weather}", W / 2, cy + big * 0.72, 18 if land else 15, color="secondary"),
            *temps(W, H - 18)]


def cockpit(W, H):
    r = min(W, H) * 0.42
    cx, cy = W / 2, H / 2 - (0 if W > H else 30)
    return [ring(cx, cy, r, 10, track_color="accent@35"),
            ring(cx, cy, r - 18, 3, track_color="secondary@40"),
            clk("%H:%M", cx, cy - 6, 62 if W > H else 58, bold=True),
            clk(DATE, cx, cy + 38, 15, color="accent", bold=True),
            clk(WX, cx, cy + 60, 12, color="secondary"),
            *temps(W, H - 16)]


def lines(W, H):
    land = W > H
    return [clk("%H:%M", 24, H * (0.30 if land else 0.20), 92 if land else 80, "left", bold=True),
            clk(DATE, 28, H * (0.30 if land else 0.20) + 62, 18, "left", color="secondary"),
            clk(WX, 28, H * (0.30 if land else 0.20) + 88, 15, "left", color="accent"),
            {"type": "graph", "sensor": "cpu_temp", "x": 24, "y": H * (0.62 if land else 0.56), "w": W - 48,
             "h": H * (0.24 if land else 0.26), "min": 20, "max": 95, "points": 90, "fill_color": "accent@18"},
            txt("CPU °C", 24, H - 12, 10, color="secondary", bold=True)]


def retro(W, H):
    F = {"font": "consolas"}
    land = W > H
    size, cy = (64, H * 0.42) if land else (46, H * 0.38)
    return [panel(8, 8, W - 16, H - 16, title="[ CLOCK ]", border="accent", **F),
            clk("88:88:88", W / 2, cy, size, bold=True, color="track", **F),   # the LCD's unlit segments
            {"type": "text", "text": "", "x": 0, "y": 0, "size": 1},
            clk("%H:%M:%S", W / 2, cy, size, bold=True, color="accent", over=True, **F),
            clk(DATE, W / 2, cy + size * 0.95, 16, color="secondary", **F),
            clk(WX, W / 2, cy + size * 0.95 + 26, 14, color="accent", **F),
            *temps(W, H - 28, **F)]


def aero(W, H):
    land = W > H
    r = min(W, H) * (0.40 if land else 0.36)
    cx, cy = W / 2, H * (0.44 if land else 0.38)
    return [ring(cx, cy, r, 6, fill="#F4FBFF", gloss=0.75, track_color="accent"),
            clk("%H:%M", cx, cy - 6, 50 if land else 46, bold=True, over=True),
            clk(DATE, cx, cy + 30, 14, color="secondary", over=True),
            panel(W / 2 - 120, H - 50, 240, 36, border="#FFFFFF", opacity=0.5, gradient=["#FFFFFF", "#D6EEFF"],
                  gloss=0.55, radius=18),
            clk(WX, W / 2, H - 32, 14, over=True)]


def arial(W, H):
    A = {"font": "arial"}
    land = W > H
    return [clk("%H:%M", 26, H * (0.36 if land else 0.24), 110 if land else 92, "left", **A),
            clk(DATE, 30, H * (0.36 if land else 0.24) + 72, 20, "left", color="secondary", **A),
            {"type": "rect", "x": 30, "y": H * (0.36 if land else 0.24) + 92, "w": W - 60, "h": 1, "color": "track"},
            clk(WX, 30, H * (0.36 if land else 0.24) + 116, 18, "left", color="accent", **A),
            *temps(W, H - 18, **A)]


def aqua(W, H):
    Q = {"font": "verdana"}
    x, y, w, h = 20, 30, W - 40, H - 60
    return [panel(x, y, w, h, title="", border="#AEB6BF", color="#FFFFFF", radius=9, shadow=2),
            panel(x, y, w, 24, title="", gradient=["#8EC5FF", "#2A73D9"], gloss=0.55, radius=9),
            {"type": "rect", "x": x, "y": y + 14, "w": w, "h": 10, "color": "#2A73D9"},
            txt("Tela!", x + 12, y + 12, 10, color="#FFFFFF", bold=True, **Q),
            clk("%H:%M", W / 2, y + h * 0.44, 70 if W > H else 60, bold=True, **Q),
            clk(DATE, W / 2, y + h * 0.44 + 50, 15, color="secondary", **Q),
            clk(WX, W / 2, y + h * 0.44 + 74, 13, color="accent", **Q)]


def clear(W, H):
    C = {"font": "verdana"}
    land = W > H
    w, h = (360, 200) if land else (280, 230)
    x, y = (W - w) / 2, (H - h) / 2 - 10
    pal = {"panel": "#FF8FC0", "accent": "#E8196F"}
    return [panel(x, y, w, h, border="#FFFFFF", opacity=0.6, gloss=0.6, radius=24, shadow=2, palette=pal),
            clk("%H:%M", W / 2, y + h * 0.42, 68 if land else 60, bold=True, **C),
            clk(DATE, W / 2, y + h * 0.42 + 48, 15, color="secondary", **C),
            clk(WX, W / 2, y + h * 0.42 + 72, 13, **C),
            *temps(W, H - 18, **C)]


def serial(W, H):
    M = {"font": "consolas"}
    x, y0, step = 18, 40, 30 if W > H else 34
    return [txt("$ date +%H:%M", x, y0, 14, color="secondary", **M),
            clk("%H:%M", x, y0 + step + 30, 72 if W > H else 64, "left", bold=True, **M),
            txt("$ date +%a\\ %d/%m", x, y0 + step * 3 + 30, 14, color="secondary", **M),
            clk(DATE, x, y0 + step * 4 + 30, 16, "left", **M),
            txt("$ weather", x, y0 + step * 5 + 30, 14, color="secondary", **M),
            clk(WX, x, y0 + step * 6 + 30, 16, "left", color="accent", **M),
            txt("$ _", x, y0 + step * 7 + 30, 14, color="accent", **M)]


def boxed(W, H, w, h, y=None, **panel_kw):
    """Clock, date and weather inside a panel (themes whose picture should show around it)."""
    x = (W - w) / 2
    y = (H - h) / 2 if y is None else y
    font = {k: panel_kw.pop(k) for k in ("font",) if k in panel_kw}
    return [panel(x, y, w, h, **panel_kw),
            clk("%H:%M", W / 2, y + h * 0.42, 64 if W > H else 56, bold=True, **font),
            clk(DATE, W / 2, y + h * 0.42 + 46, 15, color="secondary", **font),
            clk(WX, W / 2, y + h * 0.42 + 70, 13, color="accent", **font)]


def kitty(W, H):
    land = W > H
    return boxed(W, H, 300 if land else 270, 170 if land else 190, y=24 if land else 80, border="#F5C6DA",
                 color="#FFFFFF", opacity=0.92, radius=24, shadow=1, font="verdana")


def cyber(W, H):
    land = W > H
    cy = H * (0.30 if land else 0.28)
    return [txt("◢ TELA!", 16, 22, 13, color="accent", bold=True),
            clk("%H:%M", W / 2, cy, 92 if land else 70, bold=True),
            clk(":%S", W / 2 + (140 if land else 108), cy + 18, 22, "left", color="accent", bold=True),
            clk(DATE, W / 2, cy + (64 if land else 56), 16, color="secondary"),
            clk(WX, W / 2, cy + (88 if land else 80), 14, color="accent")]


def phantom(W, H):
    return cockpit(W, H)


def tech(W, H):
    F = {"font": "consolas"}
    land = W > H
    cy = H * (0.42 if land else 0.38)
    return [panel(8, 8, W - 16, H - 16, title="[ TIME ]", border="accent@45", opacity=0.88, radius=2, **F),
            clk("%H:%M:%S", W / 2, cy, 64 if land else 46, bold=True, color="accent", **F),
            clk(DATE, W / 2, cy + 50, 16, color="secondary", **F),
            clk(WX, W / 2, cy + 76, 14, **F),
            *temps(W, H - 28, **F)]


def rustico(W, H):
    land = W > H
    return boxed(W, H, 320 if land else 280, 180 if land else 200, opacity=0.84, radius=12, shadow=2)


def xmas(W, H):
    land = W > H
    return boxed(W, H, 300 if land else 270, 170 if land else 190, y=58 if land else 110, border="#FFD34E",
                 gradient=["#8A1424", "#5A0B16"], gloss=0.18, opacity=0.92, radius=16, shadow=2)


def halloween(W, H):
    land = W > H
    cy = H * (0.42 if land else 0.52)
    return [clk("%H:%M", 24 if land else W / 2, cy, 88 if land else 76, "left" if land else "center", bold=True,
                color="accent"),
            clk(DATE, 28 if land else W / 2, cy + 56, 16, "left" if land else "center", color="secondary"),
            clk(WX, 28 if land else W / 2, cy + 80, 14, "left" if land else "center")]


DESIGNS = {"clean": clean, "full": full, "cockpit": cockpit, "lines": lines, "retro": retro, "aero": aero,
           "arial": arial, "aqua": aqua, "clear": clear, "serial": serial, "kitty": kitty, "cyber": cyber,
           "phantom": phantom, "tech": tech, "rustico-freijo": rustico, "rustico-mel": rustico,
           "rustico-imbuia": rustico, "xmas": xmas, "halloween": halloween}


def write(tid):
    p = ROOT / "themes" / f"{tid}.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    data["clock"] = {fam: [w for w in DESIGNS[tid](*size) if w.get("type") != "text" or w.get("text")]
                     for fam, size in (("landscape", (480, 320)), ("portrait", (320, 480)))}
    p.write_text(themes.dump(data).replace(
        "# Tela! screen theme. Install it in the app: Appearance › Themes › Import.", HEADER), encoding="utf-8")
    print("clock written:", tid)


if __name__ == "__main__":
    for t in sys.argv[1:] or DESIGNS:
        write(t)
