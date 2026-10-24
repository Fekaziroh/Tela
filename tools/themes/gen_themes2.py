"""1.5.0 themes, part 1: Aero, Arial, Aqua, Clear, Serial. Writes Tela/themes/<id>.yaml."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gen_themes import (CPU_ALERTS, DATE, FPS, GPU_ALERTS, ROOT, VRAM_G, bar, block, clock, gauge, line,  # noqa: E402
                        panel, text, themes, value)

LOGOS = {"type": "image", "files": "logos"}


def logos(x, y, w, h, **kw):
    return dict(LOGOS, x=x, y=y, w=w, h=h, **kw)


def media(x, y, w, h):
    return {"type": "media", "x": x, "y": y, "w": w, "h": h, "when": "media_any", "fade": True}


CK_GHZ = {"scale": 0.001, "format": "{:.2f}"}


# ================================================================ AERO (sky, glass, bubbles)
def glass(w, h, title="", sub="", **kw):
    d = panel(w, h, title, sub, border="#FFFFFF", opacity=0.5, gradient=["#FFFFFF", "#D6EEFF"], gloss=0.55,
              radius=14, shadow=2)
    d.update(kw)
    return d


def aero_card(gid, title, sub, temp, maxs, alerts, rws, x, y, w, h, gx, gy, r, rx0, ry0, step):
    items = [glass(w, h, title, sub),
             gauge(temp, gx, gy, r, 7, size=24, max_sensor=maxs, alerts=alerts, fill="#FFFFFF", gloss=0.6)]
    for i, (lab, s, u, kw) in enumerate(rws):
        yy = ry0 + i * step
        items += [text(lab, rx0, yy, 9, bold=True), value(s, w - 12, yy, 14, u, unit_size=8, **kw)]
        if i < len(rws) - 1:
            items.append(line(rx0, round(yy + step / 2), w - 12 - rx0, "#BFDDF2"))
    return block(gid, title, x, y, w, h, items)


AERO_CPU = [("#load", "cpu_load", " %", {}), ("#clock", "cpu_clock", " GHz", CK_GHZ), ("#power", "cpu_power", " W", {}),
            ("#fan", "cpu_fan", " RPM", {})]
AERO_GPU = [("#load", "gpu_load", " %", {}), ("#clock", "gpu_clock", " MHz", {}), ("#power", "gpu_power", " W", {}),
            ("#fan", "gpu_fan", " RPM", {})]


def aero_bubble(gid, title, sensor, unit, x, y, s, lo=0, hi=100, **kw):
    c = s / 2
    return block(gid, title, x, y, s, s, [
        gauge(sensor, c, c, c - 3, 6, lo=lo, hi=hi, size=round(s * 0.18), unit=unit, start_angle=-90, end_angle=270,
              fill="#F4FBFF", gloss=0.75, offset_y=-4, **kw),
        text(title, c, c + s * 0.2, 8.5, align="center", bold=True, over=True),
    ])


def aero_net(x, y, w, h):
    return block("network", "#network", x, y, w, h, [
        glass(w, h, "#network"),
        text("↓", 12, h * 0.48, 12, color="accent", bold=True), value("net_down", w - 12, h * 0.48, 14, " Mb/s",
                                                                       unit_size=8, format="{:.1f}"),
        text("↑", 12, h * 0.78, 12, color="secondary", bold=True), value("net_up", w - 12, h * 0.78, 14, " Mb/s",
                                                                          unit_size=8, format="{:.1f}"),
    ])


def aero_landscape():
    top = block("top", "#top", 0, 0, 480, 42, [
        glass(468, 34, x=6, y=4, radius=17, shadow=1),
        value("fps", 20, 21, 20, " FPS", align="left", unit_size=9, **FPS),
        logos(20, 13, 100, 16, when="no_fps"),
        clock("%H:%M", 240, 21, 22, bold=True),
        clock(DATE, 462, 21, 10, "right", color="secondary", when="no_media_any", fade=True),
        media(296, 6, 172, 30),
    ])
    cpu = aero_card("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_temp_max", CPU_ALERTS, AERO_CPU, 6, 48, 231, 146,
                    58, 88, 42, 112, 40, 27)
    gpu = aero_card("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_temp_max", GPU_ALERTS, AERO_GPU, 243, 48, 231, 146,
                    58, 88, 42, 112, 40, 27)
    return [top, cpu, gpu,
            aero_bubble("ram", "RAM", "ram_pct", "%", 10, 202, 108),
            aero_bubble("vram", "VRAM", "vram_mb", "GB", 126, 202, 108, 0, 12288, **VRAM_G),
            aero_bubble("disks", "{disks_title}", "disk1_act", "%", 242, 202, 108, ssd=True),
            aero_net(358, 206, 116, 100)]


def aero_portrait():
    top = block("top", "#top", 0, 0, 320, 62, [
        glass(308, 54, x=6, y=4, radius=16, shadow=1),
        value("fps", 18, 20, 18, " FPS", align="left", unit_size=9, **FPS),
        logos(18, 12, 80, 15, when="no_fps"),
        clock("%H:%M", 302, 20, 22, "right", bold=True),
        clock(DATE, 18, 44, 10, "left", color="secondary", when="no_media_any", fade=True),
        media(14, 32, 292, 24),
    ])
    cpu = aero_card("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_temp_max", CPU_ALERTS, AERO_CPU, 6, 68, 308, 128,
                    62, 78, 40, 128, 38, 24)
    gpu = aero_card("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_temp_max", GPU_ALERTS, AERO_GPU, 6, 202, 308, 128,
                    62, 78, 40, 128, 38, 24)
    return [top, cpu, gpu,
            aero_bubble("ram", "RAM", "ram_pct", "%", 8, 336, 96),
            aero_bubble("vram", "VRAM", "vram_mb", "GB", 112, 336, 96, 0, 12288, **VRAM_G),
            aero_bubble("disks", "{disks_title}", "disk1_act", "%", 216, 336, 96, ssd=True),
            aero_net(6, 436, 308, 40) | {"items": [
                glass(308, 40, ""),
                text("#network", 12, 20, 9, bold=True),
                text("↓", 110, 20, 12, color="accent", bold=True),
                value("net_down", 200, 20, 13, " Mb/s", unit_size=8, format="{:.1f}"),
                text("↑", 214, 20, 12, color="secondary", bold=True),
                value("net_up", 298, 20, 13, " Mb/s", unit_size=8, format="{:.1f}")]}]


# ================================================================ ARIAL (light, silver, sky)
A = {"font": "arial"}


def silver(w, h, title="", sub=""):
    return panel(w, h, title, sub, border="#C3CCD6", gradient=["#FFFFFF", "#E2E8EF"], opacity=0.92, radius=10,
                 shadow=1, font="arial")


def at(t, x, y, size=9, color="secondary", **kw):
    return text(t, x, y, size, color, **dict(A, **kw))


def av(s, x, y, size=16, unit="", **kw):
    return value(s, x, y, size, unit, **dict(A, **kw))


def arial_strip(gid, title, sub, temp, alerts, load, clk, power, clk_unit, ck, x, y, w, h, portrait=False):
    items = [silver(w, h, title, sub)]
    if not portrait:
        items += [av(temp, 16, 50, 32, "°C", align="left", unit_size=12, alerts=alerts),
                  at("#temp", 18, 70, 8.5, bold=True)]
        cols = [(150, "#load", load, " %", {}), (262, "#clock", clk, clk_unit, ck), (370, "#power", power, " W", {})]
        for cx, lab, s, u, kw in cols:
            items += [at(lab, cx, 34, 8.5, bold=True), av(s, cx, 52, 17, u, align="left", unit_size=9, **kw)]
        items.append(bar(load, 150, 66, w - 164, 3))
    else:
        items += [av(temp, 16, 54, 34, "°C", align="left", unit_size=12, alerts=alerts),
                  at("#temp", 18, 76, 8.5, bold=True),
                  bar(temp, 16, 92, 120, 3, 20, 95, alerts=alerts)]
        rws = [("#load", load, " %", {}), ("#clock", clk, clk_unit, ck), ("#power", power, " W", {})]
        for i, (lab, s, u, kw) in enumerate(rws):
            yy = 40 + i * 24
            items += [at(lab, 160, yy, 8.5, bold=True), av(s, w - 14, yy, 15, u, unit_size=8, **kw)]
        items.append(bar(load, 160, 100, w - 174, 3))
    return block(gid, title, x, y, w, h, items)


def arial_tile(gid, title, sub, s, unit, x, y, w, h, lo=0, hi=100, **kw):
    return block(gid, title, x, y, w, h, [
        silver(w, h, title, sub),
        av(s, 12, h - 26, 22, unit, align="left", unit_size=10, **kw),
        bar(s, 12, h - 12, w - 24, 3, lo, hi, ssd=kw.get("ssd", False)) if not kw.get("format") else
        bar(s, 12, h - 12, w - 24, 3, lo, hi),
    ])


def arial_net(x, y, w, h):
    return block("network", "#network", x, y, w, h, [
        silver(w, h, "#network"),
        at("↓", 12, h * 0.5, 12, "accent", bold=True), av("net_down", w - 12, h * 0.5, 15, " Mb/s", unit_size=8,
                                                           format="{:.1f}"),
        at("↑", 12, h * 0.78, 12, bold=True), av("net_up", w - 12, h * 0.78, 15, " Mb/s", unit_size=8, format="{:.1f}"),
    ])


def arial_landscape():
    top = block("top", "#top", 0, 0, 480, 66, [
        clock("%H:%M", 14, 28, 40, "left", **A),
        clock(DATE, 16, 56, 10.5, "left", color="secondary", **A),
        value("fps", 466, 28, 26, " FPS", align="right", unit_size=11, **dict(FPS, **A), when="no_media_any"),
        value("fps", 286, 28, 22, " FPS", align="right", unit_size=10, **dict(FPS, **A), when="media_any"),
        logos(350, 18, 114, 22, when=["no_fps", "no_media_any"], align="right"),
        media(296, 10, 172, 34),
    ])
    return [top,
            arial_strip("cpu", "CPU", "{cpu_name}", "cpu_temp", CPU_ALERTS, "cpu_load", "cpu_clock", "cpu_power",
                        " GHz", CK_GHZ, 6, 68, 468, 80),
            arial_strip("gpu", "GPU", "{gpu_name}", "gpu_temp", GPU_ALERTS, "gpu_load", "gpu_clock", "gpu_power",
                        " MHz", {}, 6, 152, 468, 80),
            arial_tile("ram", "RAM", "{ram_desc}", "ram_pct", " %", 6, 236, 152, 78),
            arial_tile("disks", "{disks_title}", "{disk1_name}", "disk1_act", " %", 164, 236, 152, 78, ssd=True),
            arial_net(322, 236, 152, 78)]


def arial_portrait():
    top = block("top", "#top", 0, 0, 320, 72, [
        clock("%H:%M", 12, 26, 36, "left", **A),
        clock(DATE, 14, 54, 10, "left", color="secondary", when="no_media_any", **A),
        value("fps", 308, 26, 22, " FPS", align="right", unit_size=10, **dict(FPS, **A)),
        logos(208, 16, 100, 18, when="no_fps", align="right"),
        media(10, 42, 300, 28),
    ])
    return [top,
            arial_strip("cpu", "CPU", "{cpu_name}", "cpu_temp", CPU_ALERTS, "cpu_load", "cpu_clock", "cpu_power",
                        " GHz", CK_GHZ, 6, 76, 308, 112, portrait=True),
            arial_strip("gpu", "GPU", "{gpu_name}", "gpu_temp", GPU_ALERTS, "gpu_load", "gpu_clock", "gpu_power",
                        " MHz", {}, 6, 194, 308, 112, portrait=True),
            arial_tile("ram", "RAM", "", "ram_pct", " %", 6, 312, 151, 78),
            arial_tile("disks", "{disks_title}", "", "disk1_act", " %", 163, 312, 151, 78, ssd=True),
            arial_tile("vram", "VRAM", "", "vram_mb", " GB", 6, 396, 151, 80, 0, 12288, **VRAM_G),
            arial_net(163, 396, 151, 80)]


# ================================================================ AQUA (gel capsules, pinstripes)
Q = {"font": "verdana"}


def window(w, h, title, sub=""):
    """A white window with a blue gel title bar."""
    return [panel(w, h, "", border="#AEB6BF", color="#FFFFFF", radius=9, shadow=2),
            panel(w, 22, "", border=None, gradient=["#8EC5FF", "#2A73D9"], gloss=0.55, radius=9),
            {"type": "rect", "x": 0, "y": 13, "w": w, "h": 9, "color": "#2A73D9"},
            text(title, 10, 11, 10, color="#FFFFFF", bold=True, **Q),
            text(sub, w - 10, 11, 9, color="#E6F0FF", align="right", **Q) if sub else None]


def capsule(s, x, y, w, lo=0, hi=100, **kw):
    return bar(s, x, y, w, 12, lo, hi, gloss=0.6, **kw)


def aqua_unit(gid, title, sub, temp, alerts, load, clk, power, clk_unit, ck, x, y, w, h):
    items = [i for i in window(w, h, title, sub) if i]
    items += [
        text("#temp", 12, 40, 9, color="secondary", bold=True, **Q),
        value(temp, w - 12, 40, 18, "°C", unit_size=9, bold=True, alerts=alerts, **Q),
        capsule(temp, 12, 52, w - 24, 20, 95, alerts=alerts),
        text("#load", 12, 80, 9, color="secondary", bold=True, **Q),
        value(load, w - 12, 80, 14, " %", unit_size=8, **Q),
        capsule(load, 12, 90, w - 24),
        text("#clock", 12, h - 18, 9, color="secondary", bold=True, **Q),
        value(clk, w / 2 - 6, h - 18, 12, clk_unit, unit_size=7, **dict(Q, **ck)),
        text("#power", w / 2 + 6, h - 18, 9, color="secondary", bold=True, **Q),
        value(power, w - 12, h - 18, 12, " W", unit_size=7, **Q),
    ]
    return block(gid, title, x, y, w, h, items)


def aqua_sys(x, y, w, h, two_cols=True):
    items = [i for i in window(w, h, "RAM · VRAM · {disks_title}") if i]
    rows_ = [("RAM", "ram_pct", " %", 0, 100, {}), ("VRAM", "vram_mb", " GB", 0, 12288, VRAM_G),
             ("{disks_title}", "disk1_act", " %", 0, 100, {"ssd": True}), ("#volume", "volume", " %", 0, 100, {})]
    if two_cols:
        cw = (w - 36) / 2
        for i, (lab, s, u, lo, hi, kw) in enumerate(rows_):
            cx = 12 + (i % 2) * (cw + 12)
            yy = 40 + (i // 2) * 34
            items += [text(lab, cx, yy, 9, color="secondary", bold=True, **Q),
                      value(s, cx + cw, yy, 12, u, unit_size=7, **dict(Q, **kw)),
                      capsule(s, cx, yy + 9, cw, lo, hi, ssd=kw.get("ssd", False))]
        items += [text("#network", 12, h - 14, 9, color="secondary", bold=True, **Q),
                  value("net_down", w / 2 + 40, h - 14, 12, " Mb/s ↓", unit_size=7, format="{:.1f}", **Q),
                  value("net_up", w - 12, h - 14, 12, " Mb/s ↑", unit_size=7, format="{:.1f}", **Q)]
    else:
        for i, (lab, s, u, lo, hi, kw) in enumerate(rows_[:3]):
            yy = 38 + i * 26
            items += [text(lab, 12, yy, 9, color="secondary", bold=True, **Q),
                      value(s, 120, yy, 12, u, unit_size=7, **dict(Q, **kw)),
                      capsule(s, 130, yy - 6, w - 142, lo, hi, ssd=kw.get("ssd", False))]
        items += [text("#network", 12, h - 14, 9, color="secondary", bold=True, **Q),
                  value("net_down", w / 2 + 40, h - 14, 12, " ↓", unit_size=7, format="{:.1f}", **Q),
                  value("net_up", w - 12, h - 14, 12, " ↑", unit_size=7, format="{:.1f}", **Q)]
    return block("sys", "SYS", x, y, w, h, items)


def aqua_landscape():
    top = block("top", "#top", 0, 0, 480, 38, [
        panel(468, 30, "", border="#AEB6BF", color="#FFFFFF", radius=15, shadow=1, x=6, y=4),
        value("fps", 20, 19, 18, " FPS", align="left", unit_size=9, **dict(FPS, **Q)),
        logos(20, 12, 90, 14, when="no_fps"),
        clock("%H:%M", 240, 19, 18, bold=True, **Q),
        clock(DATE, 462, 19, 9.5, "right", color="secondary", when="no_media_any", fade=True, **Q),
        media(300, 6, 168, 26),
    ])
    return [top,
            aqua_unit("cpu", "CPU", "{cpu_name}", "cpu_temp", CPU_ALERTS, "cpu_load", "cpu_clock", "cpu_power",
                      " GHz", CK_GHZ, 6, 44, 231, 140),
            aqua_unit("gpu", "GPU", "{gpu_name}", "gpu_temp", GPU_ALERTS, "gpu_load", "gpu_clock", "gpu_power",
                      " MHz", {}, 243, 44, 231, 140),
            aqua_sys(6, 190, 468, 124)]


def aqua_portrait():
    top = block("top", "#top", 0, 0, 320, 64, [
        panel(308, 56, "", border="#AEB6BF", color="#FFFFFF", radius=12, shadow=1, x=6, y=4),
        value("fps", 18, 20, 16, " FPS", align="left", unit_size=8, **dict(FPS, **Q)),
        logos(18, 13, 80, 14, when="no_fps"),
        clock("%H:%M", 302, 20, 18, "right", bold=True, **Q),
        clock(DATE, 18, 44, 9.5, "left", color="secondary", when="no_media_any", fade=True, **Q),
        media(14, 33, 292, 24),
    ])
    return [top,
            aqua_unit("cpu", "CPU", "{cpu_name}", "cpu_temp", CPU_ALERTS, "cpu_load", "cpu_clock", "cpu_power",
                      " GHz", CK_GHZ, 6, 70, 308, 132),
            aqua_unit("gpu", "GPU", "{gpu_name}", "gpu_temp", GPU_ALERTS, "gpu_load", "gpu_clock", "gpu_power",
                      " MHz", {}, 6, 208, 308, 132),
            aqua_sys(6, 346, 308, 130, two_cols=False)]


# ================================================================ CLEAR (gelatin, transparent, glossy)
C = {"font": "verdana"}
JELLY = {
    "cpu": {"panel": "#FF8FC0", "accent": "#E8196F", "track": "#FFFFFF"},
    "gpu": {"panel": "#7FE3C2", "accent": "#079E74", "track": "#FFFFFF"},
    "ram": {"panel": "#FFE07A", "accent": "#D19300", "track": "#FFFFFF"},
    "disks": {"panel": "#94C6FF", "accent": "#1F6FD6", "track": "#FFFFFF"},
    "network": {"panel": "#CDAFFF", "accent": "#6E3FF2", "track": "#FFFFFF"},
}


def jelly(w, h, title="", sub=""):
    return panel(w, h, title, sub, border="#FFFFFF", opacity=0.6, gloss=0.6, radius=18, shadow=2, font="verdana")


def jblock(gid, title, x, y, w, h, items):
    b = block(gid, title, x, y, w, h, items)
    b["colors"] = JELLY[gid]
    return b


def clear_chip(gid, title, sub, temp, maxs, alerts, rws, x, y, w, h, gx, gy, r, rx0, ry0, step):
    items = [jelly(w, h, title, sub),
             gauge(temp, gx, gy, r, 9, size=24, max_sensor=maxs, alerts=alerts, gloss=0.35, font="verdana")]
    for i, (lab, s, u, kw) in enumerate(rws):
        yy = ry0 + i * step
        items += [text(lab, rx0, yy, 9, bold=True, **C), value(s, w - 14, yy, 14, u, unit_size=8, **dict(C, **kw))]
    return jblock(gid, title, x, y, w, h, items)


def clear_tile(gid, title, sub, s, unit, x, y, w, h, lo=0, hi=100, **kw):
    return jblock(gid, title, x, y, w, h, [
        jelly(w, h, title, sub),
        value(s, w / 2, h * 0.58, 26 if h > 90 else 20, unit, align="center", unit_size=11, bold=True, **dict(C, **kw)),
        bar(s, 14, h - 18, w - 28, 8, lo, hi, gloss=0.5, ssd=kw.get("ssd", False)),
    ])


def clear_net(x, y, w, h):
    return jblock("network", "#network", x, y, w, h, [
        jelly(w, h, "#network"),
        text("↓", 14, h * 0.5, 13, color="accent", bold=True), value("net_down", w - 14, h * 0.5, 15, " Mb/s",
                                                                      unit_size=8, format="{:.1f}", **C),
        text("↑", 14, h * 0.78, 13, color="secondary", bold=True), value("net_up", w - 14, h * 0.78, 15, " Mb/s",
                                                                         unit_size=8, format="{:.1f}", **C),
    ])


def clear_landscape():
    top = block("top", "#top", 0, 0, 480, 40, [
        value("fps", 12, 20, 22, " FPS", align="left", unit_size=10, **dict(FPS, **C)),
        logos(12, 11, 100, 18, when="no_fps"),
        clock("%H:%M", 240, 20, 26, bold=True, **C),
        clock(DATE, 468, 20, 10, "right", color="secondary", when="no_media_any", fade=True, **C),
        media(298, 4, 172, 32),
    ])
    return [top,
            clear_chip("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_temp_max", CPU_ALERTS, AERO_CPU, 6, 42, 231, 146,
                       60, 90, 42, 116, 44, 26),
            clear_chip("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_temp_max", GPU_ALERTS, AERO_GPU, 243, 42, 231, 146,
                       60, 90, 42, 116, 44, 26),
            clear_tile("ram", "RAM", "{ram_desc}", "ram_pct", "%", 6, 194, 152, 120),
            clear_tile("disks", "{disks_title}", "", "disk1_act", "%", 164, 194, 152, 120, ssd=True),
            clear_net(322, 194, 152, 120)]


def clear_portrait():
    top = block("top", "#top", 0, 0, 320, 58, [
        value("fps", 10, 18, 20, " FPS", align="left", unit_size=9, **dict(FPS, **C)),
        logos(10, 10, 80, 15, when="no_fps"),
        clock("%H:%M", 310, 18, 24, "right", bold=True, **C),
        clock(DATE, 10, 44, 10, "left", color="secondary", when="no_media_any", fade=True, **C),
        media(10, 32, 300, 24),
    ])
    return [top,
            clear_chip("cpu", "CPU", "{cpu_name}", "cpu_temp", "cpu_temp_max", CPU_ALERTS, AERO_CPU, 6, 62, 308, 128,
                       64, 78, 40, 130, 40, 24),
            clear_chip("gpu", "GPU", "{gpu_name}", "gpu_temp", "gpu_temp_max", GPU_ALERTS, AERO_GPU, 6, 196, 308, 128,
                       64, 78, 40, 130, 40, 24),
            clear_tile("ram", "RAM", "", "ram_pct", "%", 6, 330, 151, 78),
            clear_tile("disks", "{disks_title}", "", "disk1_act", "%", 163, 330, 151, 78, ssd=True),
            jblock("network", "#network", 6, 414, 308, 62, [
                jelly(308, 62, "#network"),
                text("↓", 14, 42, 13, color="accent", bold=True),
                value("net_down", 150, 42, 15, " Mb/s", unit_size=8, format="{:.1f}", **C),
                text("↑", 166, 42, 13, color="secondary", bold=True),
                value("net_up", 294, 42, 15, " Mb/s", unit_size=8, format="{:.1f}", **C)])]


# ================================================================ SERIAL (code, ASCII bars)
M = {"font": "consolas"}


def code_panel(w, h, title, sub=""):
    return panel(w, h, title, sub, border="track", title_color="secondary", font="consolas", radius=4)


def kv(key, s, unit, x, y, vx, size=13, **kw):
    """key = value unit, like a line of code (key in the keyword color). vx: where "=" goes."""
    return [text(key, x, y, size - 1, color="accent", **M), text("=", vx, y, size - 1, color="track", **M),
            value(s, vx + 14, y, size, unit, align="left", unit_size=size - 3, **dict(M, **kw))]


def ascii_bar(s, x, y, cells, lo=0, hi=100, size=10, **kw):
    return dict(bar(s, x, y, cells * 6, 6, lo, hi, **kw), style="ascii", cells=cells, size=size, font="consolas",
                chars="#.")


def serial_unit(gid, name, sub, temp, alerts, load, clk, power, clk_unit, ck, x, y, w, h, portrait=False):
    p = name.lower()
    items = [code_panel(w, h, f"// {p}", sub)]
    if not portrait:
        items += kv(f"{p}.temp", temp, " °C", 14, 38, 104, alerts=alerts)
        items.append(ascii_bar(temp, 236, 38, 26, 20, 95, alerts=alerts))
        items += kv(f"{p}.load", load, " %", 14, 58, 104)
        items.append(ascii_bar(load, 236, 58, 26))
        items += kv(f"{p}.clock", clk, clk_unit, 14, 78, 104, **ck)
        items += kv(f"{p}.power", power, " W", 236, 78, 326)
    else:
        items += kv(f"{p}.temp", temp, " °C", 12, 36, 104, alerts=alerts)
        items.append(ascii_bar(temp, 12, 54, 38, 20, 95, alerts=alerts))
        items += kv(f"{p}.load", load, " %", 12, 74, 104)
        items.append(ascii_bar(load, 12, 92, 38))
        items += kv(f"{p}.clock", clk, clk_unit, 12, 112, 104, **ck)
        items += kv(f"{p}.power", power, " W", 12, 128, 104)
    return block(gid, name, x, y, w, h, items)


def serial_sys(x, y, w, h, portrait=False):
    items = [code_panel(w, h, "// sys")]
    if not portrait:
        items += kv("ram", "ram_pct", " %", 14, 38, 104) + [ascii_bar("ram_pct", 236, 38, 26)]
        items += kv("disk", "disk1_act", " %", 14, 58, 104, ssd=True) + [ascii_bar("disk1_act", 236, 58, 26, ssd=True)]
        items += kv("vram", "vram_mb", " GB", 14, 78, 104, **VRAM_G)
        items += kv("vol", "volume", " %", 236, 78, 326)
        items += [text("net", 330, 16, 12, color="accent", **M),
                  value("net_down", 368, 16, 12, "↓", align="left", unit_size=10, format="{:.1f}", **M),
                  value("net_up", 460, 16, 12, "↑", unit_size=10, format="{:.1f}", **M)]
    else:
        items += kv("ram", "ram_pct", " %", 12, 36, 104) + [ascii_bar("ram_pct", 12, 52, 38)]
        items += kv("disk", "disk1_act", " %", 12, 70, 104, ssd=True) + [ascii_bar("disk1_act", 12, 86, 38, ssd=True)]
        items += kv("vram", "vram_mb", " GB", 12, 102, 104, **VRAM_G)
        items += kv("net.down", "net_down", " Mb/s", 12, 118, 104, format="{:.1f}")
        items += kv("net.up", "net_up", " Mb/s", 12, 134, 104, format="{:.1f}")
    return block("sys", "SYS", x, y, w, h, items)


def serial_top(W):
    if W > 320:
        return block("top", "#top", 0, 0, W, 32, [
            text("$ tela --watch", 10, 16, 12, color="secondary", when="no_fps", **M),
            text("fps =", 10, 16, 12, color="accent", when="fps", **M),
            value("fps", 60, 16, 16, "", align="left", bold=True, empty="", **M),
            clock("%H:%M:%S", W - 10, 16, 16, "right", bold=True, **M),
            clock("{weekday} %d/%m{weather}", 180, 16, 10, "left", color="secondary", when="no_media_any", **M),
            media(170, 2, 200, 28),
        ])
    return block("top", "#top", 0, 0, W, 50, [
        text("$ tela --watch", 10, 14, 11, color="secondary", when="no_fps", **M),
        text("fps =", 10, 14, 11, color="accent", when="fps", **M),
        value("fps", 56, 14, 14, "", align="left", bold=True, empty="", **M),
        clock("%H:%M:%S", W - 10, 14, 15, "right", bold=True, **M),
        clock("{weekday} %d/%m{weather}", 10, 38, 10, "left", color="secondary", when="no_media_any", **M),
        media(10, 26, 300, 24),
    ])


def serial_landscape():
    return [serial_top(480),
            serial_unit("cpu", "CPU", "{cpu_name}", "cpu_temp", CPU_ALERTS, "cpu_load", "cpu_clock", "cpu_power",
                        " GHz", CK_GHZ, 6, 34, 468, 90),
            serial_unit("gpu", "GPU", "{gpu_name}", "gpu_temp", GPU_ALERTS, "gpu_load", "gpu_clock", "gpu_power",
                        " MHz", {}, 6, 128, 468, 90),
            serial_sys(6, 222, 468, 92)]


def serial_portrait():
    return [serial_top(320),
            serial_unit("cpu", "CPU", "{cpu_name}", "cpu_temp", CPU_ALERTS, "cpu_load", "cpu_clock", "cpu_power",
                        " GHz", CK_GHZ, 6, 52, 308, 138, portrait=True),
            serial_unit("gpu", "GPU", "{gpu_name}", "gpu_temp", GPU_ALERTS, "gpu_load", "gpu_clock", "gpu_power",
                        " MHz", {}, 6, 194, 308, 138, portrait=True),
            serial_sys(6, 336, 308, 140, portrait=True)]


THEMES = {
    "aero": {"order": 6, "name": {"pt": "Aero", "en": "Aero", "es": "Aero", "zh": "Aero"},
             "colors": {"background": "#4DB3F0", "panel": "#FFFFFF", "text": "#0B2E4F", "secondary": "#3D6B91",
                        "track": "#C7E0F2", "accent": "#2FA84F", "warn": "#F08A00", "crit": "#E53935"},
             "art": "aero", "landscape": aero_landscape, "portrait": aero_portrait},
    "arial": {"order": 7, "name": {"pt": "Arial", "en": "Arial", "es": "Arial", "zh": "Arial"},
              "colors": {"background": "#E9F0F6", "panel": "#F7F9FB", "text": "#1F2933", "secondary": "#66727F",
                         "track": "#D3DAE2", "accent": "#3D7CC9", "warn": "#E08A00", "crit": "#D93025"},
              "art": "arial", "landscape": arial_landscape, "portrait": arial_portrait},
    "aqua": {"order": 8, "name": {"pt": "Aqua", "en": "Aqua", "es": "Aqua", "zh": "Aqua"},
             "colors": {"background": "#ECECEC", "panel": "#FFFFFF", "text": "#1A1A1A", "secondary": "#5A6068",
                        "track": "#D8E0E9", "accent": "#2F7FE0", "warn": "#F5A623", "crit": "#E5383B"},
             "art": "aqua", "landscape": aqua_landscape, "portrait": aqua_portrait},
    "clear": {"order": 9, "name": {"pt": "Clear", "en": "Clear", "es": "Clear", "zh": "Clear"},
              "colors": {"background": "#F4F6FB", "panel": "#FFFFFF", "text": "#2B2140", "secondary": "#5E5672",
                         "track": "#FFFFFF", "accent": "#E8196F", "warn": "#F08A00", "crit": "#D7263D"},
              "art": "clear", "landscape": clear_landscape, "portrait": clear_portrait},
    "serial": {"order": 10, "name": {"pt": "Serial", "en": "Serial", "es": "Serial", "zh": "Serial"},
               "colors": {"background": "#0B0E13", "panel": "#0F131A", "text": "#D4D4D4", "secondary": "#6A9955",
                          "track": "#3C4452", "accent": "#4FC1FF", "warn": "#DCDCAA", "crit": "#F44747"},
               "art": "serial", "landscape": serial_landscape, "portrait": serial_portrait},
}


def clean(items):
    return [i for i in items if i]


def build(tid):
    t = THEMES[tid]
    data = {"name": t["name"], "order": t["order"], "tela": 1, "colors": t["colors"]}
    for fam, k in (("landscape", "l"), ("portrait", "p")):
        groups = t[fam]()
        for g in groups:
            g["items"] = clean(g["items"])
        data[fam] = {"art": f"{t['art']}_{k}.png", "groups": groups}
    return data


if __name__ == "__main__":
    for tid in (sys.argv[1:] or THEMES):
        (ROOT / "themes" / f"{tid}.yaml").write_text(themes.dump(build(tid)).replace(
            "# Tela! screen theme. Install it in the app: Appearance › Themes › Import.",
            "# Built-in Tela! screen theme (replaced by every update; your changes are kept apart)."), encoding="utf-8")
        print("wrote", tid)
