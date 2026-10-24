"""Screen layouts: blocks (groups) of widgets with coordinates relative to the block.

Each screen theme (themes.py) has a layout per orientation; layouts/<family>.yaml holds the screen size, the
sensors and the "full" theme. The layout editor saves the user's copy of the current theme in the data
folder (themes.edits_path); that one wins when it exists.
Moving a block changes its x/y; resizing changes w/h and every item scales with it.
"""
import copy
from pathlib import Path

import yaml

import config

FAMILIES = ("landscape", "portrait")
POSITION = ("x", "cx")
POSITION_Y = ("y", "cy")
SIZE_KEYS = ("size", "unit_size", "title_size", "artist_size", "radius", "thickness", "min_scale")
DEFAULT_SIZES = {"value": 14, "text": 12, "clock": 24, "gauge": 26, "media": 11}


def family(orientation):
    return "portrait" if str(orientation or "").startswith("portrait") else "landscape"


def default_path(fam):
    return config.HERE / "layouts" / f"{fam}.yaml"


def user_path(fam, theme=None):
    import themes
    return themes.edits_path(theme or themes.LEGACY, fam)


def theme_of(cfg):
    import themes
    return themes.current(cfg)


# default items that changed in a version: a user's copy that still has the old item untouched gets the new one
UPGRADES = {
    "landscape": [  # 1.4.6: weather next to the date
        ("top", {"type": "clock", "format": "{weekday} %d/%m", "x": 468, "y": 19, "align": "right", "size": 14,
                 "color": "secondary", "when": "no_media_in_game", "fade": True},
         {"type": "clock", "format": "{weekday} %d/%m{weather}", "x": 468, "y": 19, "align": "right", "size": 11,
          "color": "secondary", "when": "no_media_in_game", "fade": True}),
    ],
    "portrait": [
        ("top", {"type": "clock", "format": "{weekday} %d/%m", "x": 310, "y": 16, "align": "right", "size": 13,
                 "color": "secondary", "when": "no_media_in_game", "fade": True},
         {"type": "clock", "format": "{weekday} %d/%m{weather}", "x": 310, "y": 16, "align": "right", "size": 13,
          "color": "secondary", "when": "no_media_in_game", "fade": True}),  # 1.4.5: frame time under the media, bigger FPS (the FPS was squeezed)
        ("top", {"type": "value", "sensor": "fps", "x": 10, "y": 39, "size": 18, "bold": True, "unit": " FPS",
                 "unit_size": 9, "empty": ""},
         {"type": "value", "sensor": "fps", "x": 10, "y": 43, "size": 24, "bold": True, "unit": " FPS",
          "unit_size": 11, "empty": ""}),
        ("top", {"type": "frametime", "x": 10, "y": 49, "w": 150, "h": 8, "seconds": 2, "labels": "right",
                 "label_size": 8},
         {"type": "frametime", "x": 128, "y": 44, "w": 184, "h": 12, "seconds": 2, "label_size": 9}),
    ],
}


def upgrade(fam, groups):
    """Applies UPGRADES to a user's layout (only items still equal to the old default)."""
    changed = False
    for gid, old, new in UPGRADES.get(fam, []):
        for g in groups or []:
            if g.get("id") != gid:
                continue
            for i, it in enumerate(g.get("items") or []):
                extra = {k: v for k, v in it.items() if k == "enabled"}
                if {k: v for k, v in it.items() if k != "enabled"} == old:
                    g["items"][i] = dict(new, **extra)
                    changed = True
    return changed


def load(fam, user=True, theme=None):
    """{"size", "sensors", "groups", "custom", "theme"} of a theme (default: "full", the program's own layout).
    The user's copy gets sensors added in newer versions."""
    import themes
    theme = theme or themes.LEGACY
    base = yaml.safe_load(default_path(fam).read_text(encoding="utf-8")) or {}
    sensors = dict(base.get("sensors") or {})
    sensors.update(themes.sensors(theme))
    try:
        groups = copy.deepcopy(themes.groups(theme, fam))
    except (KeyError, ValueError, OSError, yaml.YAMLError):   # a theme that is gone or damaged: the program's layout
        theme, groups = themes.LEGACY, base.get("groups") or []
    out = {"size": base.get("size"), "sensors": sensors, "groups": groups, "custom": False, "theme": theme,
           "art": themes.art(theme, fam), "rest": themes.clock_screen(theme, fam)}
    path = user_path(fam, theme)
    if user and path.exists():
        try:
            mine = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if mine.get("groups"):
                sensors.update(mine.get("sensors") or {})
                if theme == themes.LEGACY:
                    upgrade(fam, mine["groups"])
                return dict(out, groups=mine["groups"], custom=True)
        except Exception:  # noqa: BLE001 — a damaged copy falls back to the theme
            pass
    return out


def _flow(v):
    out = yaml.safe_dump(v, default_flow_style=True, width=10000, allow_unicode=True, sort_keys=False).strip()
    return out[:-4].rstrip() if out.endswith("\n...") else out   # plain scalars get a document end marker


def dump(data):
    """YAML text with one line per item (readable and diff-friendly)."""
    out = ["# Your Tela! layout, saved by the layout editor. Delete this file to go back to the default.", ""]
    out.append(f"size: {_flow(data.get('size') or [480, 320])}")
    out.append("")
    out.append("sensors:")
    for k, v in (data.get("sensors") or {}).items():
        out.append(f"  {k}: {_flow(v)}")
    out.append("")
    out.append("groups:")
    for g in data.get("groups") or []:
        head = {k: v for k, v in g.items() if k != "items"}
        out.append("  - " + "\n    ".join(f"{k}: {_flow(v)}" for k, v in head.items()))
        out.append("    items:")
        for it in g.get("items") or []:
            out.append(f"      - {_flow(it)}")
    return "\n".join(out) + "\n"


def save(fam, data, theme=None):
    data = {k: v for k, v in data.items() if k in ("size", "sensors", "groups")}
    user_path(fam, theme).write_text(dump(data), encoding="utf-8")


def reset(fam, theme=None):
    user_path(fam, theme).unlink(missing_ok=True)


def base_size(g):
    b = g.get("base")
    return (float(b[0]), float(b[1])) if b else (float(g["w"]), float(g["h"]))


def flatten(groups):
    """Absolute widget list for the renderer. Every widget gets 'group' and its scale 'k'."""
    out = []
    for g in groups or []:
        if g.get("enabled") is False:
            continue
        bw, bh = base_size(g)
        sx, sy = float(g["w"]) / bw, float(g["h"]) / bh
        k = min(sx, sy)
        gx, gy = float(g["x"]), float(g["y"])
        for it in g.get("items") or []:
            if it.get("enabled") is False:
                continue
            w = copy.deepcopy(it)
            w["group"] = g["id"]
            if isinstance(g.get("colors"), dict) and g["colors"]:   # the block's own colors (Layout editor)
                w["palette"] = g["colors"]
            for key in POSITION:
                if key in w:
                    w[key] = gx + float(w[key]) * sx
            for key in POSITION_Y:
                if key in w:
                    w[key] = gy + float(w[key]) * sy
            if "w" in w:
                w["w"] = float(w["w"]) * sx
            if "h" in w:
                w["h"] = float(w["h"]) * sy
            if abs(k - 1) > 1e-6:
                w["k"] = k
                if "size" not in w and w.get("type") in DEFAULT_SIZES:
                    w["size"] = DEFAULT_SIZES[w["type"]]
                for key in SIZE_KEYS:
                    if isinstance(w.get(key), (int, float)):
                        w[key] = float(w[key]) * k
                if w.get("type") == "gauge" and "thickness" not in w:
                    w["thickness"] = 7 * k
            out.append(w)
    return out


def apply(cfg):
    """Puts the layout for the configured orientation into cfg ('sensors', 'widgets', 'layout')."""
    fam = family((cfg.get("display") or {}).get("orientation"))
    lay = load(fam, theme=theme_of(cfg))
    cfg["sensors"] = lay.get("sensors") or {}
    cfg["widgets"] = flatten(lay.get("groups"))
    cfg["layout"] = {"family": fam, "size": lay.get("size"), "custom": lay.get("custom", False),
                     "overlap": overlapping(lay.get("groups")), "theme": lay.get("theme"), "art": lay.get("art") or "",
                     "rest": lay.get("rest") or []}
    return cfg


def overlapping(groups):
    """True if two visible blocks overlap (then the renderer draws everything in order, without the cache)."""
    rects = [(float(g["x"]), float(g["y"]), float(g["x"]) + float(g["w"]), float(g["y"]) + float(g["h"]))
             for g in groups or [] if g.get("enabled") is not False]
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            if a[0] < b[2] - 0.5 and b[0] < a[2] - 0.5 and a[1] < b[3] - 0.5 and b[1] < a[3] - 0.5:
                return True
    return False


# ---------------------------------------------------------------- blocks the editor can add
def new_block(kind, x=10, y=10, sensor=None, label=None):
    """A new block for the editor. Sizes are a good default; the user resizes after."""
    s = sensor or "cpu_temp"
    t = label or "#new"
    if kind == "value":
        items = [{"type": "panel", "x": 0, "y": 0, "w": 115, "h": 56, "title": t},
                 {"type": "value", "sensor": s, "x": 105, "y": 34, "align": "right", "size": 20, "bold": True},
                 {"type": "bar", "sensor": s, "x": 10, "y": 46, "w": 95, "h": 4, "min": 0, "max": 100}]
        w, h = 115, 56
    elif kind == "gauge":
        items = [{"type": "panel", "x": 0, "y": 0, "w": 115, "h": 116, "title": t},
                 {"type": "gauge", "sensor": s, "cx": 57.5, "cy": 68, "radius": 38, "thickness": 6, "min": 0, "max": 100, "size": 22}]
        w, h = 115, 116
    elif kind == "graph":
        items = [{"type": "panel", "x": 0, "y": 0, "w": 234, "h": 76, "title": t},
                 {"type": "value", "sensor": s, "x": 224, "y": 14, "align": "right", "size": 12, "bold": True},
                 {"type": "graph", "sensor": s, "x": 10, "y": 26, "w": 214, "h": 42, "points": 60}]
        w, h = 234, 76
    elif kind == "text":
        items = [{"type": "text", "text": label or "Tela!", "x": 0, "y": 12, "size": 16, "bold": True}]
        w, h = 120, 24
    elif kind == "media":
        items = [{"type": "media", "x": 0, "y": 0, "w": 200, "h": 30, "when": "media", "progress": "bottom", "show_time": False}]
        w, h = 200, 30
    elif kind == "usage":
        items = [{"type": "panel", "x": 0, "y": 0, "w": 115, "h": 56, "title": "Tela!"},
                 {"type": "value", "sensor": "app_cpu", "x": 10, "y": 34, "size": 15, "bold": True, "format": "{:.1f}", "unit": "%", "unit_size": 9},
                 {"type": "value", "sensor": "app_ram", "x": 105, "y": 34, "align": "right", "size": 15, "unit": " MB", "unit_size": 9}]
        w, h = 115, 56
    elif kind == "clock":
        items = [{"type": "clock", "format": "%H:%M", "x": 0, "y": 16, "size": 28, "bold": True}]
        w, h = 90, 32
    else:
        raise ValueError(f"unknown block: {kind}")
    return {"id": f"{kind}_{abs(hash((kind, x, y, s))) % 100000}", "name": t if kind != "media" else "#media",
            "x": x, "y": y, "w": w, "h": h, "items": items}


BLOCK_KINDS = ("value", "gauge", "graph", "media", "clock", "text", "usage")


def exists(fam):
    return Path(default_path(fam)).exists()
