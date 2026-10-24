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


def kitty_face(d, cx, cy, r, fill, line):
    """A small original cat face: round head, two ears, eyes, nose and whiskers."""
    d.polygon([(cx - r * 0.9, cy - r * 0.35), (cx - r * 0.75, cy - r * 1.25), (cx - r * 0.2, cy - r * 0.85)], fill=fill)
    d.polygon([(cx + r * 0.9, cy - r * 0.35), (cx + r * 0.75, cy - r * 1.25), (cx + r * 0.2, cy - r * 0.85)], fill=fill)
    d.ellipse([cx - r, cy - r * 0.95, cx + r, cy + r * 0.8], fill=fill)
    e = r * 0.12
    for sx in (-0.38, 0.38):
        d.ellipse([cx + sx * r - e, cy - r * 0.12 - e * 1.3, cx + sx * r + e, cy - r * 0.12 + e * 1.3], fill=line)
    d.polygon([(cx - e, cy + r * 0.12), (cx + e, cy + r * 0.12), (cx, cy + r * 0.24)], fill="#F08AA8")
    for sy in (0.18, 0.3):
        d.line([(cx - r * 0.25, cy + r * sy), (cx - r * 1.05, cy + r * (sy - 0.08))], fill=line, width=max(1, int(r / 18)))
        d.line([(cx + r * 0.25, cy + r * sy), (cx + r * 1.05, cy + r * (sy - 0.08))], fill=line, width=max(1, int(r / 18)))


def paw(d, cx, cy, r, fill):
    d.ellipse([cx - r, cy - r * 0.7, cx + r, cy + r * 0.8], fill=fill)
    for dx, dy in ((-0.95, -1.05), (-0.35, -1.45), (0.35, -1.45), (0.95, -1.05)):
        d.ellipse([cx + dx * r - r * 0.33, cy + dy * r - r * 0.4, cx + dx * r + r * 0.33, cy + dy * r + r * 0.4], fill=fill)


def kitty(size):
    w, h = size
    img = vgrad(size, [(0, "#FFE4EE"), (1, "#E9DFFF")])
    d = ImageDraw.Draw(img)
    rnd = random.Random(5)
    for _ in range(26):
        paw(d, rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(8, 14) * w / 960, "#F7CFE0")
    # cats peeking from the bottom edge
    k = w / 960
    for i, (fx, col) in enumerate([(0.12, "#FFFFFF"), (0.5, "#FFD2A6"), (0.86, "#D9D2E9")]):
        kitty_face(d, fx * w, h - 22 * k, 70 * k, col, "#5B4A63")
    return img


def cyber(size):
    """Black with a red perspective grid and a glowing horizon."""
    w, h = size
    img = Image.new("RGB", size, "#07030A")
    hz = h * 0.58
    glow(img, [-w * 0.2, hz - h * 0.12, w * 1.2, hz + h * 0.06], "#FF1E3C", 90, h / 18)
    d = ImageDraw.Draw(img)
    for i in range(-14, 15):   # lines to the vanishing point
        d.line([(w / 2, hz), (w / 2 + i * w * 0.16, h)], fill="#5A0A16", width=2)
    y, step = hz, 6.0
    while y < h:
        d.line([(0, y), (w, y)], fill="#5A0A16", width=2)
        step *= 1.32
        y += step
    d.line([(0, hz), (w, hz)], fill="#FF2D4A", width=3)
    for i in range(0, w, 6):   # scanlines
        pass
    a = np.asarray(img).copy()
    a[::4] = (a[::4] * 0.82).astype(np.uint8)
    return Image.fromarray(a)


def phantom(size):
    """Dark green mist with faint ghost shapes."""
    w, h = size
    img = vgrad(size, [(0, "#020805"), (1, "#03140A")])
    rnd = random.Random(9)
    for _ in range(14):
        cx, cy = rnd.uniform(0, w), rnd.uniform(0.2, 1.0) * h
        r = rnd.uniform(0.12, 0.3) * max(w, h)
        glow(img, [cx - r, cy - r * 0.35, cx + r, cy + r * 0.35], "#1FBF5A", rnd.randint(25, 55), r / 3)
    for _ in range(5):   # little ghosts
        cx, cy, r = rnd.uniform(0.05, 0.95) * w, rnd.uniform(0.1, 0.8) * h, rnd.uniform(18, 32) * w / 960
        layer = Image.new("L", size, 0)
        dd = ImageDraw.Draw(layer)
        dd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=70)
        dd.rectangle([cx - r, cy, cx + r, cy + r * 1.3], fill=70)
        for k in range(3):
            dd.ellipse([cx - r + k * r * 2 / 3, cy + r * 1.05, cx - r + (k + 1) * r * 2 / 3, cy + r * 1.55], fill=0)
        layer = layer.filter(ImageFilter.GaussianBlur(r / 6))
        img.paste(Image.new("RGB", size, "#B8FFD0"), (0, 0), layer)
    return img


def tech(size):
    """Military camouflage in dark greys and greens, with a faint grid."""
    w, h = size
    img = Image.new("RGB", size, "#20241F")
    rnd = random.Random(13)
    for col in ("#2C3328", "#171A16", "#353B31", "#262B24"):
        layer = Image.new("L", size, 0)
        d = ImageDraw.Draw(layer)
        for _ in range(int(55 * w * h / (960 * 640))):
            cx, cy = rnd.uniform(-0.05, 1.05) * w, rnd.uniform(-0.05, 1.05) * h
            pts = [(cx + math.cos(a) * rnd.uniform(25, 70) * w / 960, cy + math.sin(a) * rnd.uniform(15, 45) * w / 960)
                   for a in [k * math.pi / 4 for k in range(8)]]
            d.polygon(pts, fill=255)
        layer = layer.filter(ImageFilter.GaussianBlur(4))
        layer = layer.point(lambda p: 255 if p > 120 else 0)
        img.paste(Image.new("RGB", size, col), (0, 0), layer)
    d = ImageDraw.Draw(img)
    for x in range(0, w, 32):
        d.line([(x, 0), (x, h)], fill="#272C25")
    for y in range(0, h, 32):
        d.line([(0, y), (w, y)], fill="#272C25")
    return img


def wood(size, base, dark, light):
    """Wood planks: grain from stretched noise, a darker line between boards."""
    w, h = size
    rnd = np.random.default_rng(4)
    noise = rnd.random((h // 3 + 1, 5))   # few columns: stretched long and thin, like grain
    grain = np.array(Image.fromarray((noise * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255.0
    fine = rnd.random((h, w // 40 + 1))
    fine = np.array(Image.fromarray((fine * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)) / 255.0
    ys = np.arange(h)[:, None]
    rings = (np.sin(ys * 0.22 + grain * 5) + 1) / 2
    t = np.clip(0.5 * rings + 0.3 * grain + 0.2 * fine, 0, 1)[..., None]
    c0 = np.array([int(dark[i:i + 2], 16) for i in (1, 3, 5)], float)
    c1 = np.array([int(base[i:i + 2], 16) for i in (1, 3, 5)], float)
    c2 = np.array([int(light[i:i + 2], 16) for i in (1, 3, 5)], float)
    rgb = np.where(t < 0.5, c0 + (c1 - c0) * (t / 0.5), c1 + (c2 - c1) * ((t - 0.5) / 0.5))
    img = Image.fromarray(rgb.astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img)
    plank = h // 5 if w > h else h // 8
    for y in range(plank, h, plank):
        d.line([(0, y), (w, y)], fill=dark, width=3)
    return img


def rustico_freijo(size):
    return wood(size, "#B08A5B", "#6E5133", "#CDA977")


def rustico_mel(size):
    return wood(size, "#C98A2E", "#7A4E12", "#E6B05A")


def rustico_imbuia(size):
    return wood(size, "#5A3C26", "#2E1D12", "#7A5538")


def xmas(size):
    """Deep green with falling snow and a string of colored lights along the top."""
    w, h = size
    img = vgrad(size, [(0, "#0B2A1A"), (1, "#06170E")])
    rnd = random.Random(21)
    snow = Image.new("L", size, 0)
    d = ImageDraw.Draw(snow)
    for _ in range(int(160 * w * h / (960 * 640))):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(1.5, 4.5) * w / 960
        d.ellipse([x - r, y - r, x + r, y + r], fill=rnd.randint(120, 230))
    img.paste(Image.new("RGB", size, "#FFFFFF"), (0, 0), snow.filter(ImageFilter.GaussianBlur(0.8)))
    d = ImageDraw.Draw(img)
    pts = [(x, 18 * w / 960 + math.sin(x / w * math.pi * 6) * 10 * w / 960) for x in range(0, w + 1, 6)]
    d.line(pts, fill="#2E3B2E", width=max(2, int(3 * w / 960)))
    cols = ["#FF3B3B", "#FFD34E", "#3BC7FF", "#7CFF6B", "#FF7AD9"]
    for i, x in enumerate(range(20, w, int(54 * w / 960))):
        y = 18 * w / 960 + math.sin(x / w * math.pi * 6) * 10 * w / 960 + 10 * w / 960
        r = 7 * w / 960
        glow(img, [x - r * 2.4, y - r * 2.4, x + r * 2.4, y + r * 2.4], cols[i % 5], 110, r)
        ImageDraw.Draw(img).ellipse([x - r, y - r * 1.3, x + r, y + r * 1.3], fill=cols[i % 5])
    # snow bank at the bottom
    bank = Image.new("L", size, 0)
    ImageDraw.Draw(bank).polygon([(x, h * 0.93 + math.sin(x / w * 7) * h * 0.02) for x in range(0, w + 8, 8)] +
                                 [(w, h), (0, h)], fill=255)
    img.paste(Image.new("RGB", size, "#EAF4FF"), (0, 0), bank.filter(ImageFilter.GaussianBlur(2)))
    return img


def halloween(size):
    """Purple night, a big moon, bats and pumpkins on the ground."""
    w, h = size
    img = vgrad(size, [(0, "#14061F"), (0.7, "#2A0E3A"), (1, "#120618")])
    k = w / 960
    mx, my, mr = w * 0.78, h * 0.22, 70 * k
    glow(img, [mx - mr * 2.2, my - mr * 2.2, mx + mr * 2.2, my + mr * 2.2], "#FFB347", 70, mr)
    d = ImageDraw.Draw(img)
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill="#FFE2A8")
    rnd = random.Random(31)
    for _ in range(7):   # bats
        bx, by, s = rnd.uniform(0.05, 0.95) * w, rnd.uniform(0.08, 0.5) * h, rnd.uniform(10, 18) * k
        d.polygon([(bx, by), (bx - s * 1.6, by - s * 0.6), (bx - s * 1.1, by + s * 0.1), (bx - s * 0.6, by - s * 0.15),
                   (bx, by + s * 0.35), (bx + s * 0.6, by - s * 0.15), (bx + s * 1.1, by + s * 0.1),
                   (bx + s * 1.6, by - s * 0.6)], fill="#0A0310")
    ground = h * 0.9
    d.rectangle([0, ground, w, h], fill="#0E0614")
    for fx in (0.08, 0.22, 0.9):   # pumpkins (original, simple)
        px, pr = fx * w, 34 * k
        for dx in (-0.45, 0.45, 0):
            d.ellipse([px + dx * pr - pr * 0.7, ground - pr * 1.5, px + dx * pr + pr * 0.7, ground], fill="#E8741A")
        d.rectangle([px - pr * 0.08, ground - pr * 1.75, px + pr * 0.08, ground - pr * 1.4], fill="#3C6E1E")
        d.polygon([(px - pr * 0.5, ground - pr * 0.95), (px - pr * 0.25, ground - pr * 1.15), (px - pr * 0.1, ground - pr * 0.9)], fill="#FFD34E")
        d.polygon([(px + pr * 0.5, ground - pr * 0.95), (px + pr * 0.25, ground - pr * 1.15), (px + pr * 0.1, ground - pr * 0.9)], fill="#FFD34E")
    return img


THEMES = {"aero": aero, "arial": arial, "aqua": aqua, "clear": clear, "serial": serial,
          "kitty": kitty, "cyber": cyber, "phantom": phantom, "tech": tech, "rustico-freijo": rustico_freijo,
          "rustico-mel": rustico_mel, "rustico-imbuia": rustico_imbuia, "xmas": xmas, "halloween": halloween}

if __name__ == "__main__":
    import sys
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in THEMES.items():
        if sys.argv[1:] and name not in sys.argv[1:]:
            continue
        for k, size in SIZES.items():
            img = fn(size)
            if name.startswith("rustico"):   # photo-like wood: much smaller as JPEG
                path = OUT / f"{name}_{k}.jpg"
                img.save(path, quality=86, optimize=True)
            else:
                path = OUT / f"{name}_{k}.png"
                img.save(path, optimize=True)
            print(path.name, path.stat().st_size // 1024, "KB")
