"""Older theme builder (1.4.6): helpers used by gen_themes2.py. The built-in themes are now edited directly in themes/*.yaml."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import themes  # noqa: E402

DATE = "{weekday} %d/%m{weather}"
CPU_ALERTS = [{"above": 75, "color": "warn"}, {"above": 85, "color": "crit"}]
GPU_ALERTS = [{"above": 70, "color": "warn"}, {"above": 80, "color": "crit"}]


# ---------------------------------------------------------------- small builders (coordinates relative to the block)
def panel(w, h, title="", sub="", border="track", **kw):
    d = {"type": "panel", "x": 0, "y": 0, "w": w, "h": h, "title": title}
    if sub:
        d["subtitle"] = sub
    if border:
        d["border"] = border
    return dict(d, **kw)


def text(t, x, y, size=10, color="secondary", **kw):
    return dict({"type": "text", "text": t, "x": x, "y": y, "size": size, "color": color}, **kw)


def value(sensor, x, y, size=14, unit="", align="right", **kw):
    d = {"type": "value", "sensor": sensor, "x": x, "y": y, "size": size}
    if unit:
        d["unit"] = unit
    if align != "left":
        d["align"] = align
    return dict(d, **kw)


def line(x, y, w, color="track"):
    return {"type": "rect", "x": x, "y": y, "w": w, "h": 1, "color": color}


def bar(sensor, x, y, w, h=4, lo=0, hi=100, **kw):
    return dict({"type": "bar", "sensor": sensor, "x": x, "y": y, "w": w, "h": h, "min": lo, "max": hi}, **kw)


def gauge(sensor, cx, cy, r, th=6, lo=20, hi=95, size=24, unit="°C", **kw):
    return dict({"type": "gauge", "sensor": sensor, "cx": cx, "cy": cy, "radius": r, "thickness": th, "min": lo,
                 "max": hi, "unit": unit, "size": size}, **kw)


def graph(sensor, x, y, w, h, lo=0, hi=100, **kw):
    return dict({"type": "graph", "sensor": sensor, "x": x, "y": y, "w": w, "h": h, "min": lo, "max": hi,
                 "points": 90}, **kw)


def clock(fmt, x, y, size, align="center", **kw):
    return dict({"type": "clock", "format": fmt, "x": x, "y": y, "align": align, "size": size}, **kw)


def block(gid, name, x, y, w, h, items):
    return {"id": gid, "name": name, "x": x, "y": y, "w": w, "h": h, "items": items}


def rows(x0, x1, y0, step, entries, size=15, label=9.5, sep=True):
    """Label on the left, value on the right, a thin line between rows (the 'Clean' look)."""
    out = []
    for i, (lab, sensor, unit, extra) in enumerate(entries):
        y = y0 + i * step
        out.append(text(lab, x0, y, label, bold=True))
        out.append(value(sensor, x1, y, size, unit, unit_size=round(size * 0.6), **extra))
        if sep and i < len(entries) - 1:
            out.append(line(x0, round(y + step / 2), x1 - x0))
    return out


CPU_ROWS = [("#load", "cpu_load", " %", {}), ("#clock", "cpu_clock", " GHz", {"scale": 0.001, "format": "{:.2f}"}),
            ("#power", "cpu_power", " W", {}), ("#fan", "cpu_fan", " RPM", {})]
GPU_ROWS = [("#load", "gpu_load", " %", {}), ("#clock", "gpu_clock", " MHz", {}),
            ("#power", "gpu_power", " W", {}), ("#fan", "gpu_fan", " RPM", {})]
FPS = {"bold": True, "empty": ""}


def top_simple(W, logo_w=90):
    """FPS or logos on the left, clock in the middle, the media or the date on the right (never both)."""
    return block("top", "#top", 0, 0, W, 34, [
        value("fps", 12, 18, 22, " FPS", align="left", unit_size=10, **FPS),
        {"type": "image", "files": "logos", "when": "no_fps", "x": 12, "y": 9, "w": logo_w, "h": 16},
        clock("%H:%M", W / 2, 18, 24, bold=True),
        clock(DATE, W - 12, 18, 11, "right", color="secondary", when="no_media_any", fade=True),
        {"type": "media", "x": W - 182, "y": 3, "w": 172, "h": 28, "when": "media_any", "fade": True},
    ])


def top_simple_portrait():
    """Row 1: FPS or logos, clock. Row 2: the media, or the date."""
    return block("top", "#top", 0, 0, 320, 56, [
        value("fps", 10, 16, 20, " FPS", align="left", unit_size=9, **FPS),
        {"type": "image", "files": "logos", "when": "no_fps", "x": 10, "y": 9, "w": 80, "h": 15},
        clock("%H:%M", 310, 16, 22, "right", bold=True),
        clock(DATE, 10, 42, 10, "left", color="secondary", when="no_media_any", fade=True),
        {"type": "media", "x": 10, "y": 30, "w": 300, "h": 24, "when": "media_any", "fade": True},
    ])


# ---------------------------------------------------------------- Clean (new default, the owner's first-version look)
def clean_landscape():
    top = block("top", "#top", 0, 0, 480, 52, [
        {"type": "image", "files": "logos", "pick": 0, "when": "no_fps", "x": 12, "y": 13, "w": 120, "h": 22},
        value("fps", 12, 26, 26, " FPS", align="left", unit_size=12, **FPS),
        clock("%H:%M", 240, 22, 28, bold=True),
        clock(DATE, 240, 44, 9.5, color="secondary"),
        {"type": "image", "files": "logos", "pick": 1, "when": "no_media_any", "align": "right", "x": 348, "y": 13,
         "w": 120, "h": 22},
        {"type": "media", "x": 322, "y": 10, "w": 150, "h": 32, "when": "media_any", "fade": True},
    ])

    def chip(gid, title, sub, sensor, maxs, alerts, rws, x):
        return block(gid, title, x, 56, 234, 150, [
            panel(234, 150, title, sub),
            gauge(sensor, 60, 90, 42, 5, size=26, max_sensor=maxs, alerts=alerts),
            *rows(118, 224, 36, 30, rws),
        ])
    cpu = chip("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_temp_max", CPU_ALERTS, CPU_ROWS, 4)
    gpu = chip("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_temp_max", GPU_ALERTS, GPU_ROWS, 242)
    ram = block("ram", "RAM", 4, 210, 150, 106, [
        panel(150, 106, "RAM", "{ram_desc}"),
        *rows(10, 140, 44, 32, [("#load", "ram_pct", " %", {}), ("#used", "ram_used_gb", " GB", {"format": "{:.1f}"})],
              size=16)])
    ssd = block("disks", "{disks_title}", 158, 210, 150, 106, [
        panel(150, 106, "{disks_title}", "{disk1_name}"),
        *rows(10, 140, 44, 32, [("#load", "disk1_act", " %", {"ssd": True}), ("#temp", "ssd1_temp", " °C", {})],
              size=16)])
    netvol = block("netvol", "#network", 312, 210, 164, 106, [
        panel(164, 106, "#network"),
        *rows(10, 154, 36, 22, [("DOWN", "net_down", " Mb/s", {"format": "{:.1f}"}),
                                ("UP", "net_up", " Mb/s", {"format": "{:.1f}"})], size=13, sep=False),
        line(10, 70, 144),
        text("#volume", 10, 88, 9.5, bold=True),
        bar("volume", 66, 86, 54, 4),
        value("volume", 154, 88, 13, " %", unit_size=8),
    ])
    return [top, cpu, gpu, ram, ssd, netvol]


def clean_portrait():
    top = block("top", "#top", 0, 0, 320, 66, [
        {"type": "image", "files": "logos", "pick": 0, "when": "no_fps", "x": 10, "y": 12, "w": 80, "h": 16},
        value("fps", 10, 20, 20, " FPS", align="left", unit_size=10, **FPS),
        clock("%H:%M", 160, 22, 26, bold=True),
        clock(DATE, 160, 46, 10, color="secondary", when="no_media_any"),
        {"type": "image", "files": "logos", "pick": 1, "when": "no_media_any", "align": "right", "x": 230, "y": 12,
         "w": 80, "h": 16},
        {"type": "media", "x": 10, "y": 38, "w": 300, "h": 26, "when": "media_any", "fade": True},
    ])

    def chip(gid, title, sub, sensor, maxs, alerts, rws, y):
        return block(gid, title, 4, y, 312, 124, [
            panel(312, 124, title, sub),
            gauge(sensor, 62, 74, 40, 5, size=26, max_sensor=maxs, alerts=alerts),
            *rows(126, 302, 36, 24, rws, size=15),
        ])
    cpu = chip("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_temp_max", CPU_ALERTS, CPU_ROWS, 70)
    gpu = chip("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_temp_max", GPU_ALERTS, GPU_ROWS, 198)
    ram = block("ram", "RAM", 4, 326, 154, 74, [
        panel(154, 74, "RAM", "{ram_desc}"),
        *rows(10, 144, 36, 24, [("#load", "ram_pct", " %", {}), ("#used", "ram_used_gb", " GB", {"format": "{:.1f}"})],
              size=14)])
    ssd = block("disks", "{disks_title}", 162, 326, 154, 74, [
        panel(154, 74, "{disks_title}", "{disk1_name}"),
        *rows(10, 144, 36, 24, [("#load", "disk1_act", " %", {"ssd": True}), ("#temp", "ssd1_temp", " °C", {})],
              size=14)])
    netvol = block("netvol", "#network", 4, 404, 312, 72, [
        panel(312, 72, "#network"),
        *rows(10, 150, 36, 22, [("DOWN", "net_down", " Mb/s", {"format": "{:.1f}"}),
                                ("UP", "net_up", " Mb/s", {"format": "{:.1f}"})], size=13, sep=False),
        text("#volume", 170, 36, 9.5, bold=True),
        value("volume", 302, 36, 13, " %", unit_size=8),
        bar("volume", 170, 54, 132, 4),
    ])
    return [top, cpu, gpu, ram, ssd, netvol]


# ---------------------------------------------------------------- Cockpit (big arcs, like a dashboard)
def dial(gid, title, sub, temp, maxs, alerts, load, power, x, y, w, h):
    cx, cy, r = w / 2, h * 0.6, min(w * 0.32, h * 0.41)
    return block(gid, title, x, y, w, h, [
        panel(w, h, title, sub, border=None),
        gauge(temp, cx, cy, r, 10, size=34, max_sensor=maxs, alerts=alerts, start_angle=150, end_angle=390),
        gauge(load, cx, cy, r - 14, 3, lo=0, hi=100, size=0, unit="", start_angle=150, end_angle=390,
              color="secondary"),
        text("#load", cx - r * 0.45, h - 14, 9, align="center", bold=True),
        value(load, cx - r * 0.45, h - 28, 15, "%", align="center", unit_size=9),
        text("#power", cx + r * 0.45, h - 14, 9, align="center", bold=True),
        value(power, cx + r * 0.45, h - 28, 15, "W", align="center", unit_size=9),
    ])


def mini(gid, title, sensor, unit, x, y, w, h, lo=0, hi=100, **v):
    r = min(w * 0.36, h * 0.38)
    return block(gid, title, x, y, w, h, [
        panel(w, h, title, border=None),
        gauge(sensor, w / 2, h - 22, r, 5, lo=lo, hi=hi, size=14, unit=unit, start_angle=180, end_angle=360, **v),
    ])


VRAM_G = {"scale": 0.001, "format": "{:.1f}"}


def cockpit_landscape():
    cpu = dial("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_temp_max", CPU_ALERTS, "cpu_load", "cpu_power", 4, 38, 234, 182)
    gpu = dial("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_temp_max", GPU_ALERTS, "gpu_load", "gpu_power", 242, 38, 234, 182)
    return [top_simple(480), cpu, gpu,
            mini("ram", "RAM", "ram_pct", "%", 4, 224, 115, 92),
            mini("vram", "VRAM", "vram_mb", "GB", 123, 224, 115, 92, 0, 12288, **VRAM_G),
            mini("disks", "{disks_title}", "disk1_act", "%", 242, 224, 115, 92, ssd=True),
            mini("volume", "#volume", "volume", "%", 361, 224, 115, 92)]


def cockpit_portrait():
    cpu = dial("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_temp_max", CPU_ALERTS, "cpu_load", "cpu_power", 4, 60, 312, 150)
    gpu = dial("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_temp_max", GPU_ALERTS, "gpu_load", "gpu_power", 4, 214, 312, 150)
    return [top_simple_portrait(), cpu, gpu,
            mini("ram", "RAM", "ram_pct", "%", 4, 368, 75, 108),
            mini("vram", "VRAM", "vram_mb", "GB", 83, 368, 75, 108, 0, 12288, **VRAM_G),
            mini("disks", "{disks_title}", "disk1_act", "%", 162, 368, 75, 108, ssd=True),
            mini("volume", "#volume", "volume", "%", 241, 368, 75, 108)]


# ---------------------------------------------------------------- Linhas (graphs over time)
def trend(gid, title, sub, temp, load, x, y, w, h):
    g1 = round(h * 0.4)
    return block(gid, title, x, y, w, h, [
        panel(w, h, title, sub),
        value(temp, w - 10, 14, 13, "°C", bold=True, unit_size=8),
        graph(temp, 10, 30, w - 20, g1, 20, 95, fill_color="accent@18"),
        text("#load", 10, 38 + g1, 8.5, bold=True),
        value(load, w - 10, 38 + g1, 10, "%", unit_size=7),
        graph(load, 10, 46 + g1, w - 20, h - 56 - g1, 0, 100, color="secondary", fill_color="secondary@14"),
    ])


def spark(gid, title, sub, sensor, unit, x, y, w, h, lo=0, hi=100, **v):
    return block(gid, title, x, y, w, h, [
        panel(w, h, title, sub),
        value(sensor, w - 10, 14, 13, unit, bold=True, unit_size=8, **v),
        graph(sensor, 10, 28, w - 20, h - 36, lo, hi, fill_color="accent@12"),
    ])


def lines_landscape():
    return [top_simple(480),
            trend("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_load", 4, 38, 234, 136),
            trend("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_load", 242, 38, 234, 136),
            spark("ram", "RAM", "{ram_desc}", "ram_pct", "%", 4, 178, 234, 66),
            spark("network", "#network", "", "net_down", " Mb/s ↓", 242, 178, 234, 66, 0, 500, format="{:.1f}"),
            spark("vram", "VRAM", "{vram_desc}", "vram_mb", " GB", 4, 248, 234, 68, 0, 12288, **VRAM_G),
            spark("disks", "{disks_title}", "{disk1_name}", "disk1_act", "%", 242, 248, 234, 68, ssd=True)]


def lines_portrait():
    return [top_simple_portrait(),
            trend("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_load", 4, 60, 312, 118),
            trend("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_load", 4, 182, 312, 118),
            spark("ram", "RAM", "", "ram_pct", "%", 4, 304, 154, 84),
            spark("network", "#network", "", "net_down", " ↓", 162, 304, 154, 84, 0, 500, format="{:.0f}"),
            spark("vram", "VRAM", "", "vram_mb", " GB", 4, 392, 154, 84, 0, 12288, **VRAM_G),
            spark("disks", "{disks_title}", "", "disk1_act", "%", 162, 392, 154, 84, ssd=True)]


# ---------------------------------------------------------------- Retrô (amber terminal / LCD)
F = {"font": "consolas"}


def rt(s, x, y, size=11, color="secondary", **kw):
    return text(s, x, y, size, color, **dict(F, **kw))


def rv(sensor, x, y, size=16, unit="", **kw):
    return value(sensor, x, y, size, unit, **dict(F, **kw))


def retro_top(W):
    return block("top", "#top", 0, 0, W, 34, [
        rt("TELA! >", 10, 18, 12, "accent", bold=True),
        rv("fps", 90 if W > 320 else 76, 18, 18, " FPS", align="left", bold=True, unit_size=10, empty=""),
        clock("%H:%M:%S", W - 12, 18, 18, "right", bold=True, **F),
        {"type": "media", "x": 170 if W > 320 else 10, "y": 3 if W > 320 else 36, "w": 180 if W > 320 else 300,
         "h": 28 if W > 320 else 24, "when": "media_any", "fade": True},
    ])


def retro_unit(gid, title, sub, temp, load, clk, power, x, y, w, ghz):
    ck = {"scale": 0.001, "format": "{:.2f}"} if ghz else {}
    r = w - 12
    return block(gid, title, x, y, w, 160, [
        panel(w, 160, f"[ {title} ]", sub, border="accent", **F),
        rt("TEMP", 12, 44), rv(temp, r, 44, 26, "°C", bold=True, unit_size=12),
        bar(temp, 12, 62, w - 24, 6, 20, 95, color="accent"),
        rt("LOAD", 12, 84), rv(load, r, 84, 15, " %"),
        bar(load, 12, 96, w - 24, 6),
        rt("CLOCK", 12, 118), rv(clk, r, 118, 15, " GHZ" if ghz else " MHZ", **ck),
        rt("POWER", 12, 140), rv(power, r, 140, 15, " W"),
    ])


def retro_sys(x, y, w, h, bars=True):
    c2 = w / 2 + 14
    v1 = 120 if bars else c2 - 18
    ys = (38, 58, 78, 98) if bars else (34, 52, 70)
    left = [("RAM", "ram_pct", " %", {}), ("VRAM", "vram_mb", " GB", {"scale": 0.001, "format": "{:.1f}"}),
            ("DISK", "disk1_act", " %", {"ssd": True}), ("VOL", "volume", " %", {})]
    right = [("NET DOWN" if bars else "DOWN", "net_down", " MB/S", {"format": "{:.1f}"}),
             ("NET UP" if bars else "UP", "net_up", " MB/S", {"format": "{:.1f}"}),
             ("SSD TEMP" if bars else "SSD", "ssd1_temp", " °C", {}), ("HOTSPOT", "gpu_hotspot", " °C", {})]
    out = [panel(w, h, "[ SYS ]", border="accent", **F)]
    for yy, (lab, s, u, kw) in zip(ys, left):
        out += [rt(lab, 12, yy), rv(s, v1, yy, 15 if bars else 13, u, **kw)]
    for yy, (lab, s, u, kw) in zip(ys, right):
        out += [rt(lab, c2, yy), rv(s, w - 12, yy, 15 if bars else 13, u, **kw)]
    if bars:
        out += [bar("ram_pct", 130, 35, 100, 6), bar("disk1_act", 130, 75, 100, 6), bar("volume", 130, 95, 100, 6)]
    return block("sys", "SYS", x, y, w, h, out)


def retro_landscape():
    return [retro_top(480),
            retro_unit("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_load", "cpu_clock", "cpu_power", 4, 38, 234, True),
            retro_unit("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_load", "gpu_clock", "gpu_power", 242, 38, 234, False),
            retro_sys(4, 202, 472, 114)]


def retro_portrait():
    top = retro_top(320)
    top["h"] = 62
    cpu = retro_unit("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_load", "cpu_clock", "cpu_power", 4, 64, 312, True)
    gpu = retro_unit("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_load", "gpu_clock", "gpu_power", 4, 228, 312, False)
    cpu["h"] = gpu["h"] = 160
    return [top, cpu, gpu, retro_sys(4, 392, 312, 84 + 0, bars=False)]


THEMES = {
    "clean": {"order": 1, "name": {"pt": "Clean", "en": "Clean", "es": "Clean", "zh": "Clean"},
              "colors": {"background": "#000000", "panel": "#08080A", "text": "#F2F2F2", "secondary": "#8C8C8C",
                         "track": "#26262A", "accent": "#FFFFFF", "warn": "#FF9F0A", "crit": "#FF453A"},
              "landscape": clean_landscape, "portrait": clean_portrait},
    "full": {"order": 2, "name": {"pt": "Completo", "en": "Full", "es": "Completo", "zh": "完整"},
             "colors": {"background": "#000000", "panel": "#141414", "text": "#FFFFFF", "secondary": "#8C8C8C",
                        "track": "#333333", "accent": "#FFFFFF", "warn": "#FF9F0A", "crit": "#FF453A"},
             "landscape": "default", "portrait": "default"},
    "cockpit": {"order": 3, "name": {"pt": "Cilindro", "en": "Cylinder", "es": "Cilindro", "zh": "圆柱"},
                "colors": {"background": "#05070A", "panel": "#0B1016", "text": "#EAF2FA", "secondary": "#6F7D8C",
                           "track": "#1B2430", "accent": "#FF7A1A", "warn": "#FFB020", "crit": "#FF3B30"},
                "landscape": cockpit_landscape, "portrait": cockpit_portrait},
    "lines": {"order": 4, "name": {"pt": "Linhas", "en": "Lines", "es": "Líneas", "zh": "曲线"},
              "colors": {"background": "#06090C", "panel": "#0C1117", "text": "#E6F4F1", "secondary": "#7A8C89",
                         "track": "#1A232B", "accent": "#3DD9C1", "warn": "#FFB340", "crit": "#FF5A52"},
              "landscape": lines_landscape, "portrait": lines_portrait},
    "retro": {"order": 5, "name": {"pt": "Retrô", "en": "Retro", "es": "Retro", "zh": "复古"},
              "colors": {"background": "#0B0802", "panel": "#120D03", "text": "#FFB000", "secondary": "#A87400",
                         "track": "#3A2906", "accent": "#FFB000", "warn": "#FFD54A", "crit": "#FF5A1F"},
              "landscape": retro_landscape, "portrait": retro_portrait},
}


def build(tid):
    t = THEMES[tid]
    data = {"name": t["name"], "order": t["order"], "tela": 1, "colors": t["colors"]}
    for fam in ("landscape", "portrait"):
        part = t[fam]
        data[fam] = part if part == "default" else {"groups": part()}
    return data


if __name__ == "__main__":
    out = ROOT / "themes"
    out.mkdir(exist_ok=True)
    for tid in THEMES:
        (out / f"{tid}.yaml").write_text(themes.dump(build(tid)).replace(
            "# Tela! screen theme. Install it in the app: Appearance › Themes › Import.",
            "# Built-in Tela! screen theme (replaced by every update; your changes are kept apart)."), encoding="utf-8")
        print("wrote", tid)
