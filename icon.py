"""Tela! icons: the app icon (a small screen with a gauge arc) and the tray temperature icon."""
from PIL import Image, ImageDraw, ImageFont

DARK = "#18181B"
EDGE = "#4A4A52"


def app_icon(size=256, accent="#FFFFFF"):
    """The TelaV3 icon: a small dark screen with a gauge arc."""
    S = 4
    n = size * S
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = n / 64
    d.rounded_rectangle([2 * u, 6 * u, 62 * u, 58 * u], radius=12 * u, fill=DARK, outline=EDGE, width=round(3 * u))
    box = [15 * u, 15 * u, 49 * u, 49 * u]
    d.arc(box, 135, 405, fill=EDGE, width=round(6 * u))
    d.arc(box, 135, 320, fill=accent, width=round(6 * u))
    return im.resize((size, size), Image.LANCZOS)


def save_ico(path):
    app_icon(256).save(path, sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), (64, 64), (256, 256)])


def _font(px):
    for name in ("bahnschrift.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"):
        try:
            f = ImageFont.truetype(name, px)
            if name == "bahnschrift.ttf":
                try:
                    f.set_variation_by_name("Bold")
                except Exception:  # noqa: BLE001
                    pass
            return f
        except OSError:
            continue
    return ImageFont.load_default(px)


def temp_icon(value, warn=False, crit=False, size=64):
    """Tray icon showing a temperature number ('62')."""
    S = 4
    n = size * S
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    color = "#FF453A" if crit else ("#FF9F0A" if warn else "#FFFFFF")
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=n * 0.18, fill=DARK)
    d.rectangle([n * 0.1, n * 0.86, n * 0.9, n * 0.94], fill=color)
    txt = "--" if value is None else f"{min(199, max(0, round(value)))}"
    f = _font(int(n * (0.74 if len(txt) <= 2 else 0.56)))
    d.text((n / 2, n * 0.44), txt, font=f, fill=color, anchor="mm")
    return im.resize((size, size), Image.LANCZOS)
