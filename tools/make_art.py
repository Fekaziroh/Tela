"""Draws the pictures behind the built-in themes (themes/art/*.png). Original art, made only from code.

    python tools/make_art.py

Each theme gets a landscape (960x640) and a portrait (640x960) picture: twice the screen size, so the renderer's
supersampling stays sharp.
"""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent.parent / "themes" / "art"
SIZES = {"l": (960, 640), "p": (640, 960)}


def vgrad(size, stops):
    """Vertical gradient. stops: [(0..1, '#RRGGBB'), ...]."""
    w, h = size
    ys = np.linspace(0, 1, h)
    pos = [p for p, _ in stops]
    cols = np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for _, c in stops], dtype=float)
    rgb = np.stack([np.interp(ys, pos, cols[:, k]) for k in range(3)], axis=1)
    return Image.fromarray(np.repeat(rgb[:, None, :], w, axis=1).astype(np.uint8), "RGB")


def glow(img, box, color, alpha, blur):
    layer = Image.new("L", img.size, 0)
    ImageDraw.Draw(layer).ellipse(box, fill=alpha)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.paste(Image.new("RGB", img.size, color), (0, 0), layer)


def bubble(img, cx, cy, r, alpha=1.0):
    """A soap bubble: faint body, white rim, a bright spot up-left."""
    s = int(r * 2 + 8)
    body = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(body)
    d.ellipse([4, 4, s - 4, s - 4], fill=int(28 * alpha))
    d.ellipse([4, 4, s - 4, s - 4], outline=int(150 * alpha), width=max(1, int(r / 14)))
    body = body.filter(ImageFilter.GaussianBlur(max(0.6, r / 40)))
    img.paste(Image.new("RGB", (s, s), "#FFFFFF"), (int(cx - s / 2), int(cy - s / 2)), body)
    spot = Image.new("L", (s, s), 0)
    ImageDraw.Draw(spot).ellipse([s * 0.24, s * 0.18, s * 0.46, s * 0.34], fill=int(210 * alpha))
    spot = spot.filter(ImageFilter.GaussianBlur(max(1, r / 10)))
    img.paste(Image.new("RGB", (s, s), "#FFFFFF"), (int(cx - s / 2), int(cy - s / 2)), spot)


def aero(size):
    w, h = size
    img = vgrad(size, [(0, "#0E5FB8"), (0.45, "#4DB3F0"), (0.78, "#BFE9FF"), (1, "#E9FBFF")])
    # light rays from the upper left
    rays = Image.new("L", size, 0)
    d = ImageDraw.Draw(rays)
    ox, oy = -w * 0.1, -h * 0.15
    for i in range(9):
        a = math.radians(18 + i * 7.5)
        spread = math.radians(2.2)
        far = max(w, h) * 1.6
        pts = [(ox, oy), (ox + far * math.cos(a - spread), oy + far * math.sin(a - spread)),
               (ox + far * math.cos(a + spread), oy + far * math.sin(a + spread))]
        d.polygon(pts, fill=34 if i % 2 else 22)
    rays = rays.filter(ImageFilter.GaussianBlur(w / 60))
    img.paste(Image.new("RGB", size, "#FFFFFF"), (0, 0), rays)
    glow(img, [-w * 0.25, -h * 0.35, w * 0.35, h * 0.25], "#FFFFFF", 150, w / 14)
    # two green hills at the bottom
    for k, (top, c1, c2) in enumerate([(0.80, "#9BE15D", "#4CAF50"), (0.88, "#6CC24A", "#2E7D32")]):
        hill = Image.new("L", size, 0)
        dd = ImageDraw.Draw(hill)
        pts = [(x, h * top + math.sin(x / w * math.pi * (1.2 + k * 0.5) + k) * h * 0.035) for x in range(0, w + 8, 8)]
        dd.polygon(pts + [(w, h), (0, h)], fill=255)
        hill = hill.filter(ImageFilter.GaussianBlur(1.5))
        img.paste(vgrad(size, [(0, c1), (top, c1), (1, c2)]), (0, 0), hill)
    # a soft shine line over the hills
    glow(img, [w * 0.15, h * 0.79, w * 0.85, h * 0.83], "#F4FFE8", 90, w / 60)
    rnd = random.Random(7)
    for _ in range(16 if w > h else 18):
        r = rnd.uniform(8, 34) * w / 960
        bubble(img, rnd.uniform(0, w), rnd.uniform(h * 0.05, h * 0.78), r, rnd.uniform(0.5, 1.0))
    return img


def arial(size):
    w, h = size
    img = vgrad(size, [(0, "#C9D9EA"), (0.55, "#E9F0F6"), (1, "#F8FAFC")])
    rnd = random.Random(3)
    for _ in range(9):   # thin high clouds
        cx, cy = rnd.uniform(-0.1, 1.1) * w, rnd.uniform(0.05, 0.6) * h
        cw, ch = rnd.uniform(0.25, 0.55) * w, rnd.uniform(0.03, 0.07) * h
        glow(img, [cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2], "#FFFFFF", rnd.randint(110, 190), h / 40)
    # a silver horizon
    glow(img, [-w * 0.2, h * 0.70, w * 1.2, h * 0.76], "#FFFFFF", 120, h / 50)
    return img


def aqua(size):
    """Pinstripes (thin grey lines), like the windows of the early 2000s."""
    w, h = size
    a = np.full((h, w, 3), 236, dtype=np.uint8)
    a[::4] = 246
    a[1::4] = 246
    img = Image.fromarray(a, "RGB")
    glow(img, [-w * 0.3, -h * 0.4, w * 1.3, h * 0.35], "#FFFFFF", 90, h / 10)
    return img


def clear(size):
    """Light background with big soft color blobs: colored gelatin looks best over it."""
    w, h = size
    img = vgrad(size, [(0, "#FBFCFF"), (1, "#EEF1F8")])
    for (fx, fy, fr, c) in [(0.15, 0.2, 0.32, "#FFC3DA"), (0.85, 0.25, 0.30, "#BDF2DD"), (0.55, 0.85, 0.36, "#FFF1B0"),
                            (0.05, 0.9, 0.25, "#C9DDFF"), (0.95, 0.85, 0.22, "#E2CCFF")]:
        r = fr * max(w, h)
        glow(img, [fx * w - r, fy * h - r, fx * w + r, fy * h + r], c, 200, r / 2.4)
    return img


def serial(size):
    """Dark editor background with faint hex code in the back."""
    w, h = size
    img = Image.new("RGB", size, "#0B0E13")
    d = ImageDraw.Draw(img)
    try:
        ft = ImageFont.truetype("DejaVuSansMono.ttf", 18)
    except OSError:
        ft = ImageFont.load_default()
    rnd = random.Random(11)
    for y in range(6, h, 26):
        line = " ".join(f"{rnd.randrange(256):02X}" for _ in range(w // 34))
        d.text((8, y), line, font=ft, fill="#121821")
    return img


THEMES = {"aero": aero, "arial": arial, "aqua": aqua, "clear": clear, "serial": serial}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in THEMES.items():
        for k, size in SIZES.items():
            path = OUT / f"{name}_{k}.png"
            fn(size).save(path, optimize=True)
            print(path.name, path.stat().st_size // 1024, "KB")
