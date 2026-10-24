"""Community gallery: screen themes shared by people, kept on the repository's "gallery" branch.

Themes are posted in GitHub Discussions (file + picture); the approved ones go to the branch with a picture and a
line in index.json. Tela! reads that list (no account, no GitHub API limits: plain files) and imports a theme with
one click. Only the theme file and its picture are downloaded; nothing about the PC is sent.
"""
import base64
import json
import os
import re
import tempfile
import time
import urllib.request
from pathlib import Path

REPO = "Fekaziroh/Tela"
BASE = os.environ.get("TELA_GALLERY_URL") or f"https://raw.githubusercontent.com/{REPO}/gallery/"   # env: tests
SHARE_URL = f"https://github.com/{REPO}/discussions/categories/show-and-tell"
MAX_BYTES = 512 * 1024
_cache = {"at": 0.0, "items": None}
_pictures = {}


def _get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Tela-gallery"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 — fixed https URLs on GitHub
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("file too big")
    return data


def _safe(name):
    """Only plain file names inside the gallery (no folders, no other sites)."""
    name = str(name or "")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}", name) or ".." in name:
        raise ValueError(f"bad file name: {name!r}")
    return name


def parse(raw):
    """index.json → the entries Tela! can show (anything malformed is skipped)."""
    data = json.loads(raw)
    items = data.get("themes") if isinstance(data, dict) else data
    out = []
    for it in items or []:
        try:
            out.append({"id": _safe(it["file"]).rsplit(".", 1)[0], "file": _safe(it["file"]),
                        "picture": _safe(it["picture"]) if it.get("picture") else "",
                        "name": str(it.get("name") or it["file"])[:40], "author": str(it.get("author") or "")[:40],
                        "link": str(it.get("link") or "") if str(it.get("link") or "").startswith("https://github.com/") else "",
                        "added": str(it.get("added") or "")[:10]})
        except (KeyError, TypeError, ValueError):
            continue
    return out


def items(force=False):
    """The gallery's themes (kept for 10 minutes)."""
    if not force and _cache["items"] is not None and time.monotonic() - _cache["at"] < 600:
        return _cache["items"]
    _cache["items"] = parse(_get(BASE + "index.json"))
    _cache["at"] = time.monotonic()
    return _cache["items"]


def picture(it):
    """The theme's picture as a data URL ('' when there is none)."""
    if not it.get("picture"):
        return ""
    key = it["picture"]
    if key not in _pictures:
        try:
            raw = _get(BASE + "pictures/" + key)
            kind = "png" if raw[:8] == b"\x89PNG\r\n\x1a\n" else "jpeg" if raw[:2] == b"\xff\xd8" else None
            _pictures[key] = f"data:image/{kind};base64," + base64.b64encode(raw).decode("ascii") if kind else ""
        except (OSError, ValueError):
            return ""
    return _pictures[key]


def download(it):
    """Downloads the theme file to a temporary file and returns its path (the caller imports and deletes it)."""
    raw = _get(BASE + "themes/" + _safe(it["file"]))
    tmp = Path(tempfile.mkdtemp(prefix="tela-gallery-")) / _safe(it["file"])
    tmp.write_bytes(raw)
    return tmp
