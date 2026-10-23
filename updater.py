"""Checks GitHub for a newer Tela! release, downloads its setup and runs it silently.

Only talks to api.github.com and the release download (github.com / objects.githubusercontent.com).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

REPO = "Fekaziroh/Tela"
LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
PAGE = f"https://github.com/{REPO}/releases/latest"
EVERY = 6 * 3600      # seconds between automatic checks
FIRST = 90            # first check after the start (the PC is busy right after logon)


def parse_version(text):
    """'v1.4.2' -> (1, 4, 2); None when it is not a version."""
    m = re.match(r"^\s*v?(\d+)\.(\d+)(?:\.(\d+))?\s*$", str(text or ""))
    return tuple(int(x or 0) for x in m.groups()) if m else None


def newer(remote, local):
    r, lo = parse_version(remote), parse_version(local)
    return bool(r and lo and r > lo)


def pick_asset(assets):
    """The setup to download: the fixed name first, else any Tela-Setup*.exe."""
    exes = [a for a in assets or [] if str(a.get("name", "")).lower().endswith(".exe")]
    for a in exes:
        if a["name"].lower() == "tela-setup.exe":
            return a
    return next((a for a in exes if a["name"].lower().startswith("tela-setup")), None)


def release_info(data):
    """The fields Tela! needs from a GitHub 'release' object."""
    if not data or data.get("draft") or data.get("prerelease"):
        return None
    version = str(data.get("tag_name") or "").lstrip("vV")
    asset = pick_asset(data.get("assets"))
    if not parse_version(version) or not asset:
        return None
    digest = str(asset.get("digest") or "")
    return {"version": version, "url": asset.get("browser_download_url"), "size": int(asset.get("size") or 0),
            "sha256": digest.split(":", 1)[1].lower() if digest.startswith("sha256:") else None,
            "page": data.get("html_url") or PAGE}


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Tela-updater", "Accept": "application/vnd.github+json"})
    return urllib.request.urlopen(req, timeout=timeout)   # noqa: S310 — fixed https URLs


class Updater:
    """state: idle | checking | available | downloading | installing | error"""

    def __init__(self, version, log=None, enabled=lambda: True):
        self.version = version
        self.log = log
        self.enabled = enabled
        self.state = "idle"
        self.info = None
        self.progress = 0.0
        self.error = None
        self.checked_at = None
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._thread = None

    def _say(self, msg):
        if self.log:
            self.log(msg)

    def snapshot(self):
        return {"state": self.state, "version": (self.info or {}).get("version"), "progress": round(self.progress, 3),
                "error": self.error, "page": (self.info or {}).get("page", PAGE), "checked_at": self.checked_at}

    def start(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._loop, daemon=True, name="updater")
            self._thread.start()

    def _loop(self):
        self._wake.wait(FIRST)
        while True:
            self._wake.clear()
            if self.enabled() and self.state in ("idle", "available", "error"):
                self.check()
            self._wake.wait(EVERY)

    def check(self):
        """Asks GitHub for the latest release. Returns the snapshot."""
        with self._lock:
            if self.state in ("checking", "downloading", "installing"):
                return self.snapshot()
            self.state, self.error = "checking", None
        try:
            with _get(LATEST) as r:
                info = release_info(json.loads(r.read().decode("utf-8")))
            self.checked_at = time.time()
            if info and newer(info["version"], self.version):
                if (self.info or {}).get("version") != info["version"]:
                    self._say(f"New version available: {info['version']}")
                self.info, self.state = info, "available"
            else:
                self.info, self.state = None, "idle"
        except Exception as e:  # noqa: BLE001 — offline, rate limit, no release yet (404)
            self.state = "available" if self.info else "idle"
            self.error = f"{type(e).__name__}: {e}"
        return self.snapshot()

    def install(self, quit_app):
        """Downloads the setup in the background, then runs it silently and closes Tela!."""
        with self._lock:
            if self.state != "available" or not self.info:
                return False
            self.state, self.progress, self.error = "downloading", 0.0, None
        threading.Thread(target=self._install, args=(dict(self.info), quit_app), daemon=True, name="update").start()
        return True

    def _install(self, info, quit_app):
        try:
            path = Path(tempfile.gettempdir()) / f"Tela-Setup-{info['version']}.exe"
            self._download(info, path)
            self.state = "installing"
            self._say(f"Installing version {info['version']}")
            if sys.platform == "win32":
                # the setup closes Tela! by itself (PrepareToInstall) and opens it again at the end
                flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                subprocess.Popen([str(path), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"],
                                 creationflags=flags, close_fds=True)
            time.sleep(1.5)
            quit_app()
        except Exception as e:  # noqa: BLE001
            self.state, self.error = "available", f"{type(e).__name__}: {e}"
            self._say(f"The update failed: {self.error}")

    def _download(self, info, path):
        h = hashlib.sha256()
        got = 0
        part = path.with_suffix(".part")
        with _get(info["url"], timeout=60) as r, open(part, "wb") as f:
            total = int(r.headers.get("Content-Length") or info.get("size") or 0)
            while True:
                chunk = r.read(256 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                h.update(chunk)
                got += len(chunk)
                self.progress = got / total if total else 0.0
        if info.get("size") and got != info["size"]:
            raise OSError(f"incomplete download ({got} of {info['size']} bytes)")
        if info.get("sha256") and h.hexdigest() != info["sha256"]:
            raise OSError("the downloaded file does not match the release checksum")
        if path.exists():
            os.remove(path)
        part.rename(path)
        self.progress = 1.0
