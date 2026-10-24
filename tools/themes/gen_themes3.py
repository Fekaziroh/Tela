"""1.5.1 themes, part 2: Kitty, Cyber, Phantom, Tech, Rústico (Freijó, Mel, Imbuia), Xmas, Halloween.

    python tools/themes/gen_themes3.py [theme ...]

Writes themes/<id>.yaml. Art: tools/make_art.py. Rest screens: tools/themes/gen_clocks.py.
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gen_themes import (CPU_ALERTS, DATE, FPS, GPU_ALERTS, ROOT, VRAM_G, bar, block, clock, dial, gauge, graph,  # noqa: E402
                        line, mini, panel, retro_sys, retro_unit, text, themes, value)
from gen_themes2 import AERO_CPU, AERO_GPU, CK_GHZ, logos, media  # noqa: E402

HEADER = "# Built-in Tela! screen theme (replaced by every update; your changes are kept apart)."


def restyle(groups, panel_kw=None, bar_kw=None, item_fn=None):
    """Same layout, another look: extra keys on every panel / bar, or a function on every element."""
    groups = copy.deepcopy(groups)
    for g in groups:
        for it in g["items"]:
            if it["type"] == "panel" and panel_kw:
                it.update(panel_kw)
            if it["type"] == "bar" and bar_kw:
                it.update(bar_kw)
            if item_fn:
                item_fn(it)
    return groups


# ---------------------------------------------------------------- cards (Kitty, Xmas): gauge + rows, bubbles below
def card(gid, title, sub, temp, maxs, alerts, rws, x, y, w, h, gx, gy, r, rx0, ry0, step, skin, gauge_kw):
    items = [skin(w, h, title, sub), gauge(temp, gx, gy, r, 7, size=24, max_sensor=maxs, alerts=alerts, **gauge_kw)]
    for i, (lab, s, u, kw) in enumerate(rws):
        yy = ry0 + i * step
        items += [text(lab, rx0, yy, 9, bold=True), value(s, w - 12, yy, 14, u, unit_size=8, **kw)]
        if i < len(rws) - 1:
            items.append(line(rx0, round(yy + step / 2), w - 12 - rx0))
    return block(gid, title, x, y, w, h, items)


def ball(gid, title, sensor, unit, x, y, s, gauge_kw, lo=0, hi=100, **kw):
    c = s / 2
    return block(gid, title, x, y, s, s, [
        gauge(sensor, c, c, c - 3, 6, lo=lo, hi=hi, size=round(s * 0.2), unit=unit, start_angle=-90, end_angle=270,
              offset_y=-4, **gauge_kw, **kw),
        text(title, c, c + s * 0.22, 8.5, align="center", bold=True, over=True),
    ])


def net_card(x, y, w, h, skin, one_row=False):
    if one_row:
        return block("network", "#network", x, y, w, h, [
            skin(w, h, ""), text("#network", 12, h / 2, 9, bold=True),
            text("↓", w * 0.34, h / 2, 12, color="accent", bold=True),
            value("net_down", w * 0.62, h / 2, 13, " Mb/s", unit_size=8, format="{:.1f}"),
            text("↑", w * 0.66, h / 2, 12, color="secondary", bold=True),
            value("net_up", w - 12, h / 2, 13, " Mb/s", unit_size=8, format="{:.1f}")])
    return block("network", "#network", x, y, w, h, [
        skin(w, h, "#network"),
        text("↓", 12, h * 0.5, 12, color="accent", bold=True),
        value("net_down", w - 12, h * 0.5, 14, " Mb/s", unit_size=8, format="{:.1f}"),
        text("↑", 12, h * 0.8, 12, color="secondary", bold=True),
        value("net_up", w - 12, h * 0.8, 14, " Mb/s", unit_size=8, format="{:.1f}")])


def cards_landscape(skin, gauge_kw, ball_kw, top_y=0, top_h=40, y0=44, card_h=140, by=None, bs=98, font=None):
    by = by if by is not None else y0 + card_h + 6
    top = block("top", "#top", 0, top_y, 480, top_h, [
        value("fps", 12, top_h / 2, 20, " FPS", align="left", unit_size=9, **FPS),
        logos(12, top_h / 2 - 8, 100, 16, when="no_fps"),
        clock("%H:%M", 240, top_h / 2, 24, bold=True),
        clock(DATE, 468, top_h / 2, 10, "right", color="secondary", when="no_media_any", fade=True),
        media(296, top_h / 2 - 15, 172, 30)])
    gs = [top,
          card("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_temp_max", CPU_ALERTS, AERO_CPU, 6, y0, 231, card_h,
               58, card_h * 0.6, 40, 112, 38, (card_h - 46) / 3.4, skin, gauge_kw),
          card("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_temp_max", GPU_ALERTS, AERO_GPU, 243, y0, 231, card_h,
               58, card_h * 0.6, 40, 112, 38, (card_h - 46) / 3.4, skin, gauge_kw),
          ball("ram", "RAM", "ram_pct", "%", 12, by, bs, ball_kw),
          ball("vram", "VRAM", "vram_mb", "GB", 12 + bs + 14, by, bs, ball_kw, 0, 12288, **VRAM_G),
          ball("disks", "{disks_title}", "disk1_act", "%", 12 + 2 * (bs + 14), by, bs, ball_kw, ssd=True),
          net_card(12 + 3 * (bs + 14), by + 4, 474 - (12 + 3 * (bs + 14)), bs - 8, skin)]
    return _font(gs, font)


def cards_portrait(skin, gauge_kw, ball_kw, top_y=0, top_h=58, y0=62, card_h=120, bs=88, font=None, bottom=476):
    top = block("top", "#top", 0, top_y, 320, top_h, [
        value("fps", 10, 18, 18, " FPS", align="left", unit_size=9, **FPS),
        logos(10, 10, 80, 15, when="no_fps"),
        clock("%H:%M", 310, 18, 22, "right", bold=True),
        clock(DATE, 10, top_h - 14, 10, "left", color="secondary", when="no_media_any", fade=True),
        media(10, top_h - 28, 300, 24)])
    y1 = y0 + card_h + 6
    by = y1 + card_h + 6
    gap = (308 - 3 * bs) / 2
    net_y = by + bs + 4
    gs = [top,
          card("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_temp_max", CPU_ALERTS, AERO_CPU, 6, y0, 308, card_h,
               62, card_h * 0.58, 38, 128, 36, (card_h - 44) / 3.3, skin, gauge_kw),
          card("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_temp_max", GPU_ALERTS, AERO_GPU, 6, y1, 308, card_h,
               62, card_h * 0.58, 38, 128, 36, (card_h - 44) / 3.3, skin, gauge_kw),
          ball("ram", "RAM", "ram_pct", "%", 6, by, bs, ball_kw),
          ball("vram", "VRAM", "vram_mb", "GB", 6 + bs + gap, by, bs, ball_kw, 0, 12288, **VRAM_G),
          ball("disks", "{disks_title}", "disk1_act", "%", 6 + 2 * (bs + gap), by, bs, ball_kw, ssd=True)]
    if bottom - net_y >= 30:
        gs.append(net_card(6, net_y, 308, min(40, bottom - net_y), skin, one_row=True))
    return _font(gs, font)


def _font(groups, font):
    if not font:
        return groups
    for g in groups:
        for it in g["items"]:
            if it["type"] in ("text", "value", "clock", "gauge", "panel"):
                it.setdefault("font", font)
    return groups


# ---------------------------------------------------------------- KITTY
def kitty_skin(w, h, title="", sub=""):
    return panel(w, h, title, sub, border="#F5C6DA", color="#FFFFFF", opacity=0.92, radius=20, shadow=1)


KITTY_GAUGE = {"fill": "#FFF6FA", "track_color": "#F7D9E7"}
KITTY_BALL = {"fill": "#FFFFFF", "gloss": 0.35, "track_color": "#F7D9E7"}


def kitty_landscape():
    return cards_landscape(kitty_skin, KITTY_GAUGE, KITTY_BALL, y0=42, card_h=136, by=182, bs=80, font="verdana")


def kitty_portrait():
    return cards_portrait(kitty_skin, KITTY_GAUGE, KITTY_BALL, y0=60, card_h=116, bs=84, font="verdana", bottom=436)


# ---------------------------------------------------------------- XMAS
def xmas_skin(w, h, title="", sub=""):
    return panel(w, h, title, sub, border="#FFD34E", color="#6A0F1C", opacity=0.9, radius=14, shadow=2,
                 gradient=["#8A1424", "#5A0B16"], gloss=0.18)


XMAS_GAUGE = {"track_color": "#3D0910"}
XMAS_BALL = {"fill": "#F4F9FF", "gloss": 0.6, "track_color": "#DDE8F3", "text_color": "#5A0B16"}


def xmas_landscape():
    return cards_landscape(xmas_skin, XMAS_GAUGE, XMAS_BALL, top_y=22, top_h=34, y0=58, card_h=132, by=196, bs=96)


def xmas_portrait():
    return cards_portrait(xmas_skin, XMAS_GAUGE, XMAS_BALL, top_y=20, top_h=54, y0=78, card_h=114, bs=86, bottom=460)


# ---------------------------------------------------------------- CYBER (sharp red HUD)
def hud_skin(w, h, title="", sub=""):
    return panel(w, h, title, sub, border="accent", radius=0, opacity=0.86, title_color="accent")


SEG = {"style": "segments", "gap": 2}


def hud_unit(gid, title, sub, temp, alerts, load, clk, power, clk_unit, ck, x, y, w, h):
    items = [hud_skin(w, h, f"{title} //", sub),
             value(temp, 12, 52, 34, "°C", align="left", bold=True, unit_size=12, alerts=alerts),
             dict(bar(temp, 12, 70, w - 24, 8, 20, 95, alerts=alerts), cells=24, **SEG),
             text("#load", 12, 92, 8.5, bold=True), value(load, w / 2 - 8, 92, 13, " %", unit_size=8),
             dict(bar(load, 12, 102, w / 2 - 20, 5), cells=12, **SEG),
             text("#power", w / 2 + 8, 92, 8.5, bold=True), value(power, w - 12, 92, 13, " W", unit_size=8),
             dict(bar(power, w / 2 + 8, 102, w / 2 - 20, 5, 0, 300), cells=12, **SEG),
             text("#clock", 12, h - 12, 8.5, bold=True), value(clk, w - 12, h - 12, 12, clk_unit, unit_size=7, **ck)]
    return block(gid, title, x, y, w, h, items)


def hud_sys(x, y, w, h, cols=3):
    items = [hud_skin(w, h, "SYS //")]
    entries = [("RAM", "ram_pct", " %", 0, 100, {}), ("VRAM", "vram_mb", " GB", 0, 12288, VRAM_G),
               ("{disks_title}", "disk1_act", " %", 0, 100, {"ssd": True})]
    cw = (w - 24 - (cols - 1) * 12) / cols
    for i, (lab, s, u, lo, hi, kw) in enumerate(entries):
        cx, yy = 12 + (i % cols) * (cw + 12), 40 + (i // cols) * 34
        items += [text(lab, cx, yy, 8.5, bold=True), value(s, cx + cw, yy, 13, u, unit_size=8, **kw),
                  dict(bar(s, cx, yy + 10, cw, 5, lo, hi, ssd=kw.get("ssd", False)), cells=14, **SEG)]
    gy = 40 + ((len(entries) - 1) // cols + 1) * 34
    items += [text("#network", 12, gy + 4, 8.5, bold=True),
              value("net_down", w - 90, gy + 4, 12, " ↓", unit_size=8, format="{:.1f}"),
              value("net_up", w - 12, gy + 4, 12, " ↑", unit_size=8, format="{:.1f}"),
              graph("net_down", 12, gy + 12, w - 24, h - gy - 18, 0, 500, fill_color="accent@14")]
    return block("sys", "SYS", x, y, w, h, items)


def hud_top(W, portrait=False):
    if not portrait:
        return block("top", "#top", 0, 0, W, 34, [
            text("◢ TELA!", 10, 17, 13, color="accent", bold=True, when="no_fps"),
            value("fps", 10, 17, 18, " FPS", align="left", unit_size=9, **FPS),
            clock("%H:%M:%S", W - 10, 17, 18, "right", bold=True),
            clock(DATE, 150, 17, 10, "left", color="secondary", when="no_media_any"),
            media(140, 3, 190, 28)])
    return block("top", "#top", 0, 0, W, 54, [
        text("◢ TELA!", 10, 16, 12, color="accent", bold=True, when="no_fps"),
        value("fps", 10, 16, 16, " FPS", align="left", unit_size=8, **FPS),
        clock("%H:%M:%S", W - 10, 16, 16, "right", bold=True),
        clock(DATE, 10, 42, 10, "left", color="secondary", when="no_media_any"),
        media(10, 28, 300, 24)])


def cyber_landscape():
    return [hud_top(480),
            hud_unit("cpu", "CPU", "{cpu_name}", "cpu_temp", CPU_ALERTS, "cpu_load", "cpu_clock", "cpu_power", " GHz",
                     CK_GHZ, 6, 38, 231, 142),
            hud_unit("gpu", "GPU", "{gpu_name}", "gpu_temp", GPU_ALERTS, "gpu_load", "gpu_clock", "gpu_power", " MHz",
                     {}, 243, 38, 231, 142),
            hud_sys(6, 186, 468, 128)]


def cyber_portrait():
    return [hud_top(320, True),
            hud_unit("cpu", "CPU", "{cpu_name}", "cpu_temp", CPU_ALERTS, "cpu_load", "cpu_clock", "cpu_power", " GHz",
                     CK_GHZ, 6, 58, 308, 136),
            hud_unit("gpu", "GPU", "{gpu_name}", "gpu_temp", GPU_ALERTS, "gpu_load", "gpu_clock", "gpu_power", " MHz",
                     {}, 6, 198, 308, 136),
            hud_sys(6, 338, 308, 138, cols=3)]


# ---------------------------------------------------------------- PHANTOM (ghostly dials)
def ghostly(it):
    if it["type"] == "panel":
        it.update(opacity=0.55, radius=16, border="accent@30")


def phantom_landscape():
    cpu = dial("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_temp_max", CPU_ALERTS, "cpu_load", "cpu_power", 4, 38, 234, 182)
    gpu = dial("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_temp_max", GPU_ALERTS, "gpu_load", "gpu_power", 242, 38, 234, 182)
    gs = [hud_top(480), cpu, gpu,
          mini("ram", "RAM", "ram_pct", "%", 4, 224, 115, 92),
          mini("vram", "VRAM", "vram_mb", "GB", 123, 224, 115, 92, 0, 12288, **VRAM_G),
          mini("disks", "{disks_title}", "disk1_act", "%", 242, 224, 115, 92, ssd=True),
          mini("volume", "#volume", "volume", "%", 361, 224, 115, 92)]
    gs[0]["items"][0]["text"] = "☾ TELA!"
    return restyle(gs, item_fn=ghostly)


def phantom_portrait():
    cpu = dial("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_temp_max", CPU_ALERTS, "cpu_load", "cpu_power", 4, 58, 312, 152)
    gpu = dial("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_temp_max", GPU_ALERTS, "gpu_load", "gpu_power", 4, 214, 312, 152)
    gs = [hud_top(320, True), cpu, gpu,
          mini("ram", "RAM", "ram_pct", "%", 4, 370, 75, 106),
          mini("vram", "VRAM", "vram_mb", "GB", 83, 370, 75, 106, 0, 12288, **VRAM_G),
          mini("disks", "{disks_title}", "disk1_act", "%", 162, 370, 75, 106, ssd=True),
          mini("volume", "#volume", "volume", "%", 241, 370, 75, 106)]
    gs[0]["items"][0]["text"] = "☾ TELA!"
    return restyle(gs, item_fn=ghostly)


# ---------------------------------------------------------------- TECH (military, stencil, segments)
def tech_look(it):
    if it["type"] == "panel":
        it.update(opacity=0.88, radius=2, border="accent@45")
    if it["type"] == "bar":
        it.update(style="segments", gap=2, cells=16)


def tech_landscape():
    from gen_themes import retro_top
    gs = [retro_top(480),
          retro_unit("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_load", "cpu_clock", "cpu_power", 4, 38, 234, True),
          retro_unit("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_load", "gpu_clock", "gpu_power", 242, 38, 234, False),
          retro_sys(4, 202, 472, 114)]
    gs[0]["items"][0]["text"] = "TELA! //"
    return restyle(gs, item_fn=tech_look)


def tech_portrait():
    from gen_themes import retro_top
    top = retro_top(320)
    top["h"] = 62
    top["items"][0]["text"] = "TELA! //"
    cpu = retro_unit("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_load", "cpu_clock", "cpu_power", 4, 64, 312, True)
    gpu = retro_unit("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_load", "gpu_clock", "gpu_power", 4, 228, 312, False)
    return restyle([top, cpu, gpu, retro_sys(4, 392, 312, 84, bars=False)], item_fn=tech_look)


# ---------------------------------------------------------------- RÚSTICO (the Clean layout over wood)
def wood_look(it):
    if it["type"] == "panel":
        it.update(opacity=0.84, radius=10, shadow=2)


def with_top_panel(groups, **kw):
    """The Clean top bar has no panel: over a picture it needs one to stay readable."""
    for g in groups:
        if g["id"] == "top":
            g["items"].insert(0, dict(panel(g["w"] - 8, g["h"] - 4, "", border=None, x=4, y=2), **kw))
    return groups


def rustico(fam):
    return with_top_panel(restyle(themes.groups("clean", fam), item_fn=wood_look), opacity=0.84, radius=10, shadow=2)


# ---------------------------------------------------------------- HALLOWEEN (Clean layout, purple and orange)
def spooky(it):
    if it["type"] == "panel":
        it.update(opacity=0.94, radius=14, border="accent@40", gradient=["#2A0E3A", "#160622"])
    if it["type"] == "gauge":
        it.update(thickness=8)


def halloween(fam):
    return with_top_panel(restyle(themes.groups("clean", fam), item_fn=spooky), opacity=0.94, radius=14,
                          border="accent@40", gradient=["#2A0E3A", "#160622"])


THEMES = {
    "kitty": {"order": 11, "name": {"pt": "Kitty", "en": "Kitty", "es": "Kitty", "zh": "Kitty"}, "art": "kitty",
              "colors": {"background": "#FBE7F0", "panel": "#FFFFFF", "text": "#4A3550", "secondary": "#8E6F9B",
                         "track": "#F7D9E7", "accent": "#FF5E9C", "warn": "#FF9A3D", "crit": "#E5484D"},
              "landscape": kitty_landscape, "portrait": kitty_portrait},
    "cyber": {"order": 12, "name": {"pt": "Cyber", "en": "Cyber", "es": "Cyber", "zh": "Cyber"}, "art": "cyber",
              "colors": {"background": "#07030A", "panel": "#0E0508", "text": "#FFE9EC", "secondary": "#B9707D",
                         "track": "#3A0D16", "accent": "#FF2D4A", "warn": "#FFC14D", "crit": "#FFFFFF"},
              "landscape": cyber_landscape, "portrait": cyber_portrait},
    "phantom": {"order": 13, "name": {"pt": "Phantom", "en": "Phantom", "es": "Phantom", "zh": "Phantom"},
                "art": "phantom",
                "colors": {"background": "#020805", "panel": "#06140C", "text": "#C8FFD9", "secondary": "#5FA37A",
                           "track": "#0F2A1A", "accent": "#3DFF8A", "warn": "#E6FF5C", "crit": "#FF5A5A"},
                "landscape": phantom_landscape, "portrait": phantom_portrait},
    "tech": {"order": 14, "name": {"pt": "Tech", "en": "Tech", "es": "Tech", "zh": "Tech"}, "art": "tech",
             "colors": {"background": "#20241F", "panel": "#151813", "text": "#D9E0CF", "secondary": "#8C9A7E",
                        "track": "#2F362B", "accent": "#9BC53D", "warn": "#E0B000", "crit": "#E5484D"},
             "landscape": tech_landscape, "portrait": tech_portrait},
    "rustico-freijo": {"order": 15, "art": "rustico-freijo", "ext": "jpg",
                       "name": {"pt": "Rústico Freijó", "en": "Rustic Freijó", "es": "Rústico Freijó", "zh": "原木 · 浅"},
                       "colors": {"background": "#2A1C12", "panel": "#120C07", "text": "#F4E6D2", "secondary": "#C9A882",
                                  "track": "#3A2A1C", "accent": "#E0B06A", "warn": "#FF9F43", "crit": "#FF5A4F"},
                       "landscape": lambda: rustico("landscape"), "portrait": lambda: rustico("portrait")},
    "rustico-mel": {"order": 16, "art": "rustico-mel", "ext": "jpg",
                    "name": {"pt": "Rústico Mel", "en": "Rustic Honey", "es": "Rústico Miel", "zh": "原木 · 蜂蜜"},
                    "colors": {"background": "#2A1C12", "panel": "#140C04", "text": "#FFF0D6", "secondary": "#D6A65C",
                               "track": "#3D2A12", "accent": "#F2B33D", "warn": "#FF9F43", "crit": "#FF5A4F"},
                    "landscape": lambda: rustico("landscape"), "portrait": lambda: rustico("portrait")},
    "rustico-imbuia": {"order": 17, "art": "rustico-imbuia", "ext": "jpg",
                       "name": {"pt": "Rústico Imbuia", "en": "Rustic Imbuia", "es": "Rústico Imbuia", "zh": "原木 · 深"},
                       "colors": {"background": "#1A0F08", "panel": "#0D0805", "text": "#F1E2CF", "secondary": "#B89470",
                                  "track": "#2E2016", "accent": "#D9A46B", "warn": "#FF9F43", "crit": "#FF5A4F"},
                       "landscape": lambda: rustico("landscape"), "portrait": lambda: rustico("portrait")},
    "xmas": {"order": 18, "name": {"pt": "Natal", "en": "Christmas", "es": "Navidad", "zh": "圣诞"}, "art": "xmas",
             "colors": {"background": "#0B2A1A", "panel": "#5E0B16", "text": "#FFF4E6", "secondary": "#F2C6A0",
                        "track": "#3D0910", "accent": "#FFD34E", "warn": "#FF9F43", "crit": "#FFFFFF"},
             "landscape": xmas_landscape, "portrait": xmas_portrait},
    "halloween": {"order": 19, "name": {"pt": "Halloween", "en": "Halloween", "es": "Halloween", "zh": "万圣节"},
                  "art": "halloween",
                  "colors": {"background": "#14061F", "panel": "#1E0A2C", "text": "#FFE9D1", "secondary": "#C9A0E0",
                             "track": "#3A1550", "accent": "#FF7A1A", "warn": "#FFD34E", "crit": "#FF3B3B"},
                  "landscape": lambda: halloween("landscape"), "portrait": lambda: halloween("portrait")},
}


def build(tid):
    t = THEMES[tid]
    data = {"name": t["name"], "order": t["order"], "tela": 1, "colors": t["colors"]}
    for fam, k in (("landscape", "l"), ("portrait", "p")):
        groups = t[fam]()
        for g in groups:
            g["items"] = [i for i in g["items"] if i]
        data[fam] = {"art": f"{t['art']}_{k}.{t.get('ext', 'png')}", "groups": groups}
    old = ROOT / "themes" / f"{tid}.yaml"
    if old.exists():   # keep a Rest screen written before
        import yaml
        prev = yaml.safe_load(old.read_text(encoding="utf-8")) or {}
        if prev.get("clock"):
            data["clock"] = prev["clock"]
    return data


if __name__ == "__main__":
    for tid in (sys.argv[1:] or THEMES):
        (ROOT / "themes" / f"{tid}.yaml").write_text(themes.dump(build(tid)).replace(
            "# Tela! screen theme. Install it in the app: Appearance › Themes › Import.", HEADER), encoding="utf-8")
        print("wrote", tid)
