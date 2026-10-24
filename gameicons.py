"""Game icons: the icon stored in the game's .exe, saved once as a small PNG (DATA/game_icons) for the game summary
on the screen and the game history in the window."""
import base64
import re
import sys
import threading
from pathlib import Path

import config

WINDOWS = sys.platform == "win32"
_busy = set()
_lock = threading.Lock()


def folder():
    return config.DATA / "game_icons"


def _slug(name):
    return re.sub(r"[^A-Za-z0-9]+", "-", name or "game").strip("-").lower()[:60] or "game"


def path_for(name):
    return folder() / f"{_slug(name)}.png"


def find(name):
    """Path of the saved icon for this game name, or None."""
    p = path_for(name)
    return p if p.exists() else None


def _extract(exe, out):
    """Windows only: the .exe's own icon (32x32) as a PNG, through .NET (already loaded for the sensors)."""
    import clr  # type: ignore
    clr.AddReference("System.Drawing")
    from System.Drawing import Icon  # type: ignore
    from System.Drawing.Imaging import ImageFormat  # type: ignore
    ico = Icon.ExtractAssociatedIcon(str(exe))
    if ico is None:
        return
    bmp = ico.ToBitmap()
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".tmp")
        bmp.Save(str(tmp), ImageFormat.Png)
        tmp.replace(out)
    finally:
        bmp.Dispose()
        ico.Dispose()


def ensure(exe, name, log=None):
    """Saves the game's icon in the background, once per game name."""
    if not WINDOWS or not exe:
        return
    out = path_for(name)
    with _lock:
        if out.exists() or out in _busy:
            return
        _busy.add(out)

    def run():
        try:
            _extract(Path(exe), out)
        except Exception as e:  # noqa: BLE001 — no icon is fine
            if log:
                log(f"Game icon of {name}: {e}")
        finally:
            with _lock:
                _busy.discard(out)
    threading.Thread(target=run, name="game-icon", daemon=True).start()


def data_url(name):
    """The icon as a data URL for the window ('' when there is none)."""
    p = find(name)
    if not p:
        return ""
    try:
        return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")
    except OSError:
        return ""
