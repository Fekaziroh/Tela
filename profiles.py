"""Profiles: named snapshots of the user's settings and layouts. Saved in DATA/profiles as JSON,
exported and imported as .tela-profile files (the same JSON)."""
import json
import re
import time
from pathlib import Path

import config
import layout

EXT = ".tela-profile"
FAMILIES = ("landscape", "portrait")
# things that belong to this PC, not to a profile
SKIP = {("display", "port"), ("history", "folder"), ("ui", "wizard_done"), ("ui", "language")}


def folder():
    return config.DATA / "profiles"


def _safe(name):
    name = re.sub(r'[\\/:*?"<>|]+', " ", str(name or "")).strip()[:60]
    return name or "Profile"


def snapshot(cfg, name, version=""):
    values, intervals = config.user_values(cfg)
    layouts = {}
    for fam in FAMILIES:
        p = layout.user_path(fam)
        if p.exists():
            layouts[fam] = p.read_text(encoding="utf-8")
    return {"tela_profile": 1, "name": _safe(name), "version": version, "created": time.time(),
            "settings": [[s, k, v] for s, k, v in values if (s, k) not in SKIP],
            "intervals": intervals, "layouts": layouts}


def validate(data):
    if not isinstance(data, dict) or data.get("tela_profile") != 1 or not isinstance(data.get("settings"), list):
        raise ValueError("not a Tela! profile")
    for row in data["settings"]:
        if not (isinstance(row, list) and len(row) == 3 and (row[0] is None or isinstance(row[0], str))
                and isinstance(row[1], str) and not isinstance(row[2], (list, dict))):
            raise ValueError("damaged profile")
        if row[0] is not None and row[0] not in config.USER_SECTIONS:
            raise ValueError(f"unknown section {row[0]}")
    for fam, txt in (data.get("layouts") or {}).items():
        if fam not in FAMILIES or not isinstance(txt, str):
            raise ValueError("damaged profile layout")
    return data


def _path(name):
    return folder() / f"{_safe(name)}.json"


def save(cfg, name, version=""):
    d = folder()
    d.mkdir(parents=True, exist_ok=True)
    data = snapshot(cfg, name, version)
    _path(name).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data["name"]


def entries():
    out = []
    for p in sorted(folder().glob("*.json")) if folder().exists() else []:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            out.append({"name": data.get("name") or p.stem, "created": data.get("created"),
                        "version": data.get("version"), "layouts": sorted((data.get("layouts") or {}).keys())})
        except (OSError, ValueError):
            continue
    return out


def read(name):
    return validate(json.loads(_path(name).read_text(encoding="utf-8")))


def delete(name):
    p = _path(name)
    if p.exists():
        p.unlink()
        return True
    return False


def apply(cfg_path, data):
    """Writes a profile over the current settings and layouts."""
    data = validate(data)
    s = config.Settings(cfg_path)
    s.set_many([(sec, k, v) for sec, k, v in data["settings"]])
    base = next((v for sec, k, v in data["settings"] if sec is None and k == "interval"), None)
    if base is not None:
        s.set_intervals(float(base), {k: float(v) for k, v in (data.get("intervals") or {}).items()})
    for fam in FAMILIES:
        txt = (data.get("layouts") or {}).get(fam)
        p = layout.user_path(fam)
        if txt:
            p.write_text(txt, encoding="utf-8")
        elif p.exists():
            p.unlink()          # the profile uses the default layout of this orientation


def export(name, path):
    Path(path).write_text(json.dumps(read(name), ensure_ascii=False, indent=1), encoding="utf-8")


def import_file(path):
    data = validate(json.loads(Path(path).read_text(encoding="utf-8-sig")))
    base = _safe(data.get("name") or Path(path).stem)
    name, n = base, 2
    while _path(name).exists():
        name, n = f"{base} ({n})", n + 1
    data["name"] = name
    folder().mkdir(parents=True, exist_ok=True)
    _path(name).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return name
