"""Game history: every game summary saved as one JSON file, listed, deleted and exported from the window."""
import csv
import io
import json
import re
import shutil
import time
from pathlib import Path

import config

FIELDS = ("name", "ended_at", "seconds", "duration", "fps_avg", "fps_1low", "fps_max", "max", "fps_series")


def folder(cfg):
    custom = str((cfg.get("history") or {}).get("folder") or "").strip()
    return Path(custom) if custom else config.DATA / "games"


def _slug(name):
    return re.sub(r"[^A-Za-z0-9]+", "-", name or "game").strip("-")[:40] or "game"


def save(cfg, summary):
    """Writes one game. Returns the file id, or None when the history is off."""
    h = cfg.get("history") or {}
    if not h.get("save", True):
        return None
    d = folder(cfg)
    d.mkdir(parents=True, exist_ok=True)
    ended = summary.get("ended_at") or time.time()
    gid = time.strftime("%Y%m%d-%H%M%S", time.localtime(ended)) + "_" + _slug(summary.get("name"))
    data = {k: summary.get(k) for k in FIELDS}
    data["ended_at"] = ended
    (d / f"{gid}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    prune(cfg)
    return gid


def _files(cfg):
    d = folder(cfg)
    try:
        return sorted(d.glob("*.json"), key=lambda p: p.name, reverse=True)   # names start with the date
    except OSError:
        return []


def _read(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["id"] = path.stem
        return data
    except (OSError, ValueError):
        return None


def entries(cfg):
    """All games, newest first, without the FPS series (light for the list)."""
    out = []
    for p in _files(cfg):
        g = _read(p)
        if g:
            g.pop("fps_series", None)
            out.append(g)
    return out


def get(cfg, gid):
    p = folder(cfg) / f"{Path(gid).name}.json"
    return _read(p) if p.exists() else None


def delete(cfg, ids):
    n = 0
    for gid in ids:
        p = folder(cfg) / f"{Path(gid).name}.json"
        if p.exists():
            p.unlink()
            n += 1
    return n


def prune(cfg):
    keep = int((cfg.get("history") or {}).get("keep", 200) or 0)
    if keep <= 0:
        return 0
    old = _files(cfg)[keep:]
    for p in old:
        p.unlink(missing_ok=True)
    return len(old)


def move(cfg, new_folder):
    """Moves the saved games to another folder (the setting is changed by the caller)."""
    src, dst = folder(cfg), Path(new_folder)
    dst.mkdir(parents=True, exist_ok=True)
    if src.resolve() == dst.resolve():
        return 0
    n = 0
    for p in _files(cfg):
        shutil.move(str(p), str(dst / p.name))
        n += 1
    return n


def to_csv(cfg):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["date", "game", "minutes", "fps_avg", "fps_1low", "fps_max", "cpu_max", "gpu_max", "hotspot_max"])
    for g in entries(cfg):
        m = g.get("max") or {}

        def r(v):
            return "" if v is None else round(float(v), 1)
        w.writerow([time.strftime("%Y-%m-%d %H:%M", time.localtime(g.get("ended_at") or 0)), g.get("name"),
                    r((g.get("seconds") or 0) / 60), r(g.get("fps_avg")), r(g.get("fps_1low")), r(g.get("fps_max")),
                    r(m.get("cpu")), r(m.get("gpu")), r(m.get("hotspot"))])
    return out.getvalue()
