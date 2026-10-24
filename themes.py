"""Screen themes: a theme is a set of screen colors plus a layout for landscape and one for portrait.

Built-in themes ship in themes/<id>.yaml (replaced by updates). The user's own themes (saved from the window
or imported from a .tela-theme file) live in DATA/user_themes/<id>.yaml.

Changes made in the layout editor are kept per theme and per orientation in the data folder, so switching
themes never loses them and "Restore" just deletes them:
    layout_<family>.yaml            edits of the "full" theme (the layout of Tela! up to 1.4.5)
    layout_<family>_<id>.yaml       edits of any other theme
Color changes are kept per theme in DATA/theme_colors.json when the user switches to another theme.
"""
import copy
import json
import re
import time
from pathlib import Path

import yaml

import config

EXT = ".tela-theme"
FAMILIES = ("landscape", "portrait")
DEFAULT = "clean"          # new installs
LEGACY = "full"            # people updating from 1.4.5 or older keep this one
LANGS = ("pt", "en", "es", "zh")


def builtin_dir():
    return config.HERE / "themes"


def user_dir():
    return config.DATA / "user_themes"   # not "themes": from source or portable, DATA is the program folder


def _slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", str(name or "").lower()).strip("-")[:40]
    return s or "theme"


def _read(path):
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig")) or {}
    if not isinstance(data, dict):
        raise ValueError("not a Tela! theme")
    return data


def _files():
    """{id: (path, builtin)}; a user theme never hides a built-in one."""
    out = {}
    for p in sorted(user_dir().glob("*.yaml")) if user_dir().exists() else []:
        out[p.stem] = (p, False)
    for p in sorted(builtin_dir().glob("*.yaml")) if builtin_dir().exists() else []:
        out[p.stem] = (p, True)
    return out


def exists(tid):
    return tid in _files()


def current(cfg):
    """Theme in use (falls back to the default when the chosen one is gone)."""
    tid = str(((cfg or {}).get("theme") or {}).get("name") or DEFAULT)
    if exists(tid):
        return tid
    return DEFAULT if exists(DEFAULT) else LEGACY


def load(tid):
    """The theme as stored, with 'id' and 'builtin'. Raises KeyError when it does not exist."""
    files = _files()
    if tid not in files:
        raise KeyError(tid)
    path, builtin = files[tid]
    data = _read(path)
    data["id"], data["builtin"] = tid, builtin
    return data


def name(data, lang="en"):
    n = data.get("name")
    if isinstance(n, dict):
        return str(n.get(lang) or n.get("en") or next(iter(n.values()), "") or data.get("id"))
    return str(n or data.get("id"))


def base_layout(fam):
    """layouts/<family>.yaml: screen size, the sensors every theme can use, and the "full" theme's blocks."""
    return yaml.safe_load((config.HERE / "layouts" / f"{fam}.yaml").read_text(encoding="utf-8")) or {}


def groups(tid, fam):
    """The theme's own blocks for an orientation (without the user's edits)."""
    data = load(tid)
    part = data.get(fam)
    if part == "default" or part is None and tid == LEGACY:
        return base_layout(fam).get("groups") or []
    if not isinstance(part, dict) or not part.get("groups"):
        other = data.get("landscape" if fam == "portrait" else "portrait")
        if isinstance(other, dict) and other.get("groups"):   # one orientation only: the other uses "full"
            return base_layout(fam).get("groups") or []
        raise ValueError(f"theme {tid} has no layout")
    return part["groups"]


def art(tid, fam):
    """Picture a theme draws behind its blocks ("art: <file>" in its landscape/portrait part), or ''.
    Looked up in the program's themes/art folder, then in the user's themes/art folder."""
    try:
        part = load(tid).get(fam)
    except (KeyError, ValueError, OSError):
        return ""
    name = part.get("art") if isinstance(part, dict) else None
    if not name or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}", str(name)):
        return ""
    for d in (builtin_dir() / "art", user_dir() / "art"):
        if (d / name).is_file():
            return str(d / name)
    return ""


def clock_screen(tid, fam):
    """The theme's own Rest screen ("clock: {landscape: [...], portrait: [...]}"): absolute widgets, or []."""
    try:
        items = (load(tid).get("clock") or {}).get(fam)
    except (KeyError, ValueError, OSError, AttributeError):
        return []
    return [dict(w) for w in items if isinstance(w, dict) and isinstance(w.get("type"), str)] if isinstance(items, list) else []


def sensors(tid):
    """Extra sensors a theme brings (added with "more sensors" in the editor)."""
    try:
        return dict(load(tid).get("sensors") or {})
    except (KeyError, ValueError, OSError):
        return {}


def colors(tid):
    from render import DEFAULT_COLORS
    try:
        c = load(tid).get("colors") or {}
    except (KeyError, ValueError, OSError):
        c = {}
    return {**DEFAULT_COLORS, **{k: v for k, v in c.items() if k in DEFAULT_COLORS and _hex(v)}}


def _hex(v):
    return bool(re.fullmatch(r"#[0-9a-fA-F]{6}", str(v)))


def edits_path(tid, fam):
    return config.DATA / (f"layout_{fam}.yaml" if tid == LEGACY else f"layout_{fam}_{tid}.yaml")


def edited(tid):
    return any(edits_path(tid, f).exists() for f in FAMILIES)


def reset(tid, fam=None):
    for f in FAMILIES if fam is None else (fam,):
        edits_path(tid, f).unlink(missing_ok=True)


# ---------------------------------------------------------------- colors kept per theme
def _colors_file():
    return config.DATA / "theme_colors.json"


def saved_colors(tid):
    try:
        data = json.loads(_colors_file().read_text(encoding="utf-8"))
        c = data.get(tid)
        return {k: v for k, v in c.items() if _hex(v)} if isinstance(c, dict) else None
    except (OSError, ValueError, AttributeError):
        return None


def keep_colors(tid, colors_now):
    """Remembers the colors the user had on a theme (only when they differ from the theme's own)."""
    try:
        data = json.loads(_colors_file().read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}
    clean = {k: v for k, v in (colors_now or {}).items() if _hex(v)}
    if not clean or clean == colors(tid):
        data.pop(tid, None)
    else:
        data[tid] = clean
    _colors_file().write_text(json.dumps(data, indent=1), encoding="utf-8")


def colors_for(tid):
    """Colors to put on the screen when switching to a theme: the user's own for it, else the theme's."""
    return {**colors(tid), **(saved_colors(tid) or {})}


# ---------------------------------------------------------------- listing
def entries(lang="en"):
    out = []
    for tid, (path, builtin) in _files().items():
        try:
            data = _read(path)
        except (OSError, ValueError):
            continue
        data["id"] = tid
        out.append({"id": tid, "name": name(data, lang), "builtin": builtin, "edited": edited(tid),
                    "order": int(data.get("order", 50 if builtin else 100)),
                    "colors": colors(tid), "author": str(data.get("author") or "")})
    out.sort(key=lambda e: (e["order"], e["name"].lower()))
    return out


# ---------------------------------------------------------------- the theme as a file
def _flow(v):
    out = yaml.safe_dump(v, default_flow_style=True, width=10000, allow_unicode=True, sort_keys=False).strip()
    return out[:-4].rstrip() if out.endswith("\n...") else out


def dump(data):
    """YAML text of a theme, one line per element (readable and diff-friendly)."""
    out = ["# Tela! screen theme. Install it in the app: Appearance › Themes › Import.", ""]
    for key in ("name", "author", "description", "order", "tela"):
        if data.get(key) not in (None, ""):
            out.append(f"{key}: {_flow(data[key])}")
    out.append("")
    out.append("colors:")
    for k, v in (data.get("colors") or {}).items():
        out.append(f"  {k}: {_flow(v)}")
    if data.get("sensors"):
        out.append("")
        out.append("sensors:")
        for k, v in data["sensors"].items():
            out.append(f"  {k}: {_flow(v)}")
    for fam in FAMILIES:
        part = data.get(fam)
        if part is None:
            continue
        out.append("")
        if part == "default":
            out.append(f"{fam}: default")
            continue
        out.append(f"{fam}:")
        if part.get("art"):
            out.append(f"  art: {_flow(part['art'])}")
        out.append("  groups:")
        for g in part.get("groups") or []:
            head = {k: v for k, v in g.items() if k != "items"}
            out.append("    - " + "\n      ".join(f"{k}: {_flow(v)}" for k, v in head.items()))
            out.append("      items:")
            for it in g.get("items") or []:
                out.append(f"        - {_flow(it)}")
    clock = data.get("clock")
    if isinstance(clock, dict) and any(clock.get(f) for f in FAMILIES):
        out.append("")
        out.append("clock:   # the Rest screen (absolute positions)")
        for fam in FAMILIES:
            if clock.get(fam):
                out.append(f"  {fam}:")
                for it in clock[fam]:
                    out.append(f"    - {_flow(it)}")
    return "\n".join(out) + "\n"


def validate(data):
    """Checks a theme read from a file someone shared. Raises ValueError when it is not usable."""
    if not isinstance(data, dict):
        raise ValueError("not a Tela! theme")
    found = False
    for fam in FAMILIES:
        part = data.get(fam)
        if part is None or part == "default":
            continue
        if not isinstance(part, dict) or not isinstance(part.get("groups"), list):
            raise ValueError("damaged theme layout")
        for g in part["groups"]:
            if not isinstance(g, dict) or not isinstance(g.get("items"), list):
                raise ValueError("damaged theme block")
            for k in ("x", "y", "w", "h"):
                if not isinstance(g.get(k), (int, float)):
                    raise ValueError("damaged theme block")
            if "colors" in g:   # the block's own colors: only #RRGGBB values
                pal = g["colors"] if isinstance(g["colors"], dict) else {}
                g["colors"] = {k: v for k, v in pal.items() if isinstance(k, str) and _hex(v)}
            for it in g["items"]:
                if not isinstance(it, dict) or not isinstance(it.get("type"), str):
                    raise ValueError("damaged theme element")
                if it["type"] == "image" and it.get("file"):   # pictures stay on the PC that made the theme
                    it.pop("file")
        found = True
    if not found:
        raise ValueError("the theme has no layout")
    if "clock" in data:   # the Rest screen: plain elements only, no pictures from the other PC
        clock = data["clock"] if isinstance(data["clock"], dict) else {}
        data["clock"] = {f: [it for it in clock.get(f) or [] if isinstance(it, dict) and isinstance(it.get("type"), str)
                             and it["type"] != "image"] for f in FAMILIES if isinstance(clock.get(f), list)}
    if not isinstance(data.get("colors") or {}, dict):
        raise ValueError("damaged theme colors")
    for k, v in (data.get("sensors") or {}).items():
        if not isinstance(k, str) or not isinstance(v, (str, list)):
            raise ValueError("damaged theme sensors")
    return data


def snapshot(tid, colors_now=None, lang="en", new_name=None):
    """The theme as it is now on this PC (the user's edits and colors included), ready to be saved or shared."""
    data = load(tid)
    out = {"name": new_name or name(data, lang), "author": data.get("author") or "", "tela": 1,
           "colors": {k: v for k, v in (colors_now or colors_for(tid)).items() if _hex(v)}}
    extra = dict(data.get("sensors") or {})
    for fam in FAMILIES:
        path = edits_path(tid, fam)
        gs = None
        if path.exists():
            try:
                mine = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                gs = mine.get("groups")
                base = base_layout(fam).get("sensors") or {}
                extra.update({k: v for k, v in (mine.get("sensors") or {}).items() if k not in base})
            except (OSError, ValueError, yaml.YAMLError):
                gs = None
        out[fam] = {"groups": copy.deepcopy(gs or groups(tid, fam))}
        part = data.get(fam)
        if isinstance(part, dict) and part.get("art"):   # the picture stays a file name (found in themes/art)
            out[fam]["art"] = part["art"]
    if extra:
        out["sensors"] = extra
    if isinstance(data.get("clock"), dict):   # the theme's Rest screen
        out["clock"] = copy.deepcopy(data["clock"])
    return out


def _free_id(base):
    tid, n = base, 2
    while exists(tid):
        tid, n = f"{base}-{n}", n + 1
    return tid


def save_as(tid, new_name, colors_now=None, lang="en"):
    """Saves the current theme (with the user's edits and colors) as a new theme of the user's. Returns its id."""
    new_name = str(new_name or "").strip()[:40] or "Tema"
    data = snapshot(tid, colors_now, lang, new_name)
    data["created"] = time.time()
    new = _free_id(_slug(new_name))
    user_dir().mkdir(parents=True, exist_ok=True)
    (user_dir() / f"{new}.yaml").write_text(dump(data), encoding="utf-8")
    return new


def blank_groups(fam):
    """A new theme from scratch starts with just the clock and the date; the rest is added in the editor."""
    W = 480 if fam == "landscape" else 320
    return [{"id": "top", "name": "#top", "x": 0, "y": 0, "w": W, "h": 56, "items": [
        {"type": "clock", "format": "%H:%M", "x": W / 2, "y": 22, "align": "center", "size": 30, "bold": True},
        {"type": "clock", "format": "{weekday} %d/%m{weather}", "x": W / 2, "y": 46, "align": "center", "size": 11,
         "color": "secondary"}]}]


def new_theme(new_name, colors_now=None):
    """An empty theme of the user's. Returns its id."""
    from render import DEFAULT_COLORS
    new_name = str(new_name or "").strip()[:40] or "Tema"
    data = {"name": new_name, "tela": 1, "created": time.time(),
            "colors": {k: v for k, v in {**DEFAULT_COLORS, **(colors_now or {})}.items() if _hex(v)}}
    for fam in FAMILIES:
        data[fam] = {"groups": blank_groups(fam)}
    new = _free_id(_slug(new_name))
    user_dir().mkdir(parents=True, exist_ok=True)
    (user_dir() / f"{new}.yaml").write_text(dump(data), encoding="utf-8")
    return new


def rename(tid, new_name):
    data = load(tid)
    if data["builtin"]:
        return False
    data["name"] = str(new_name or "").strip()[:40] or data["name"]
    (user_dir() / f"{tid}.yaml").write_text(dump({k: v for k, v in data.items() if k not in ("id", "builtin")}),
                                            encoding="utf-8")
    return True


def delete(tid):
    """Deletes a theme of the user's (built-in themes stay) and its edits."""
    files = _files()
    if tid not in files or files[tid][1]:
        return False
    files[tid][0].unlink(missing_ok=True)
    reset(tid)
    return True


def export(tid, path, colors_now=None, lang="en"):
    Path(path).write_text(dump(snapshot(tid, colors_now, lang)), encoding="utf-8")
    return str(path)


def import_file(path):
    """Copies a .tela-theme into the user's themes. Returns the new id."""
    data = validate(_read(path))
    nm = data.get("name")
    if isinstance(nm, dict):
        nm = nm.get("en") or next(iter(nm.values()), "")
    nm = str(nm or Path(path).stem).strip()[:40] or "Tema"
    data["name"] = nm
    data.pop("order", None)
    new = _free_id(_slug(nm))
    user_dir().mkdir(parents=True, exist_ok=True)
    (user_dir() / f"{new}.yaml").write_text(dump(data), encoding="utf-8")
    return new
