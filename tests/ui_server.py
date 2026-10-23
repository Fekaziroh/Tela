"""Development server: the real window UI in a browser, wired to the engine in demo mode.

    python tests/ui_server.py [--port 8765]
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from api import Api  # noqa: E402
from bridge import Bridge  # noqa: E402
from engine import HERE, Engine, Log  # noqa: E402


class FakeUpdater:
    """Same interface as updater.Updater, offline. --update X.Y.Z pretends a release exists."""

    def __init__(self, version=None):
        from updater import PAGE
        self.state, self.version, self.progress, self.error, self.checked_at = "idle", version, 0.0, None, None
        self.info = {"version": version, "page": PAGE} if version else None

    def snapshot(self):
        return {"state": self.state, "version": self.version, "progress": self.progress, "error": self.error,
                "page": "", "checked_at": self.checked_at}

    def check(self):
        self.checked_at = time.time()
        self.state = "available" if self.version else "idle"
        return self.snapshot()

    def install(self, quit_app):
        import threading

        def run():
            self.state = "downloading"
            for i in range(11):
                self.progress = i / 10
                time.sleep(0.25)
            self.state = "installing"
        threading.Thread(target=run, daemon=True).start()
        return True


class DevApp:
    window_kind = "browser (dev)"

    def __init__(self, game=True, media=True):
        self.cfg_path = HERE / config.CONFIG
        if not self.cfg_path.exists():
            config.prepare(search_old=False)
        self.log = Log(echo=False)
        self.engine = Engine(self.cfg_path, self.log, demo=True, simulate="memory", demo_game=game, demo_media=media)
        self.engine.start()
        self.quit_called = False
        self.updater = FakeUpdater()

    def settings_changed(self, *a):
        pass

    def set_tray_accent(self, color):
        pass

    def pick_images(self):
        return []

    def pick_save_path(self, name, label="CSV", ext="csv"):
        import tempfile
        return str(Path(tempfile.gettempdir()) / name)

    def pick_open_path(self, label, ext):
        import tempfile
        p = Path(tempfile.gettempdir()) / f"import.{ext}"
        return str(p) if p.exists() else None

    def pick_folder(self):
        return None

    def quit(self):
        self.quit_called = True

    def hide_window(self):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-game", action="store_true")
    ap.add_argument("--update", help="pretend this version is on GitHub")
    a = ap.parse_args()
    app = DevApp(game=not a.no_game)
    app.updater = FakeUpdater(a.update)
    b = Bridge(Api(app), ROOT / "ui", port=a.port)
    print(b.url, flush=True)
    while True:
        time.sleep(3600)
