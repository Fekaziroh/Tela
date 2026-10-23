"""Guard process: a second, small copy of Tela! that watches the main one and reopens it when it hangs.

    Tela.exe --watchdog <pid> [--tray]       (started by Tela! itself; ends when the main copy ends)

The main copy is considered hung when its window stays "Not responding" for HUNG_UI seconds, or when it stops
answering on the single-instance port for HUNG_PING seconds (everything frozen, the screen too). Then it is
killed and started again (in the tray if its window was hidden). Imports stay light on purpose.
"""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

WINDOWS = sys.platform == "win32"
FROZEN = getattr(sys, "frozen", False)
PORT = 47614
EVERY = 2.0
HUNG_UI = 20.0        # seconds with the window "Not responding"
HUNG_PING = 45.0      # seconds without any answer from the main copy
GRACE = 60.0          # the main copy may be busy while it starts


def log(line):
    """Same file as the main copy's activity log (DATA/tela.log)."""
    try:
        import config
        with open(config.DATA / "tela.log", "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S  ") + line + "\n")
    except Exception:  # noqa: BLE001
        pass


def windows_of(pid):
    """[(hwnd, visible)] top-level windows of a process."""
    if not WINDOWS:
        return []
    import ctypes
    from ctypes import wintypes
    u = ctypes.WinDLL("user32")
    proc_t = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    u.EnumWindows.argtypes = [proc_t, wintypes.LPARAM]
    u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    out = []

    def each(hwnd, _):
        owner = wintypes.DWORD(0)
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and u.GetWindowTextLengthW(hwnd) > 0:
            out.append((hwnd, bool(u.IsWindowVisible(hwnd))))
        return True
    try:
        u.EnumWindows(proc_t(each), 0)
    except Exception:  # noqa: BLE001
        return []
    return out


def ui_hung(wins):
    if not WINDOWS or not wins:
        return False
    import ctypes
    u = ctypes.WinDLL("user32")
    return any(u.IsHungAppWindow(h) for h, _ in wins)


def answers():
    """True when the main copy replies on its single-instance port."""
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=3) as s:
            s.settimeout(3)
            s.sendall(b"ping")
            return s.recv(8) == b"pong"
    except OSError:
        return False


def alive(pid):
    try:
        import psutil
        p = psutil.Process(pid)
        return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
    except Exception:  # noqa: BLE001
        return False


def kill_tree(pid):
    try:
        import psutil
        p = psutil.Process(pid)
        kids = p.children(recursive=True)
        p.kill()
        for k in kids:
            if k.pid == os.getpid():   # this guard is a child of the main copy too
                continue
            try:
                k.kill()
            except Exception:  # noqa: BLE001
                pass
        p.wait(10)
    except Exception:  # noqa: BLE001
        pass


def start_main(hidden):
    here = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
    cmd = [sys.executable] if FROZEN else [sys.executable, str(here / "app.py")]
    cmd += ["--recovered"] + (["--tray"] if hidden else [])
    flags = 0
    if WINDOWS:
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen(cmd, cwd=str(here), creationflags=flags, close_fds=True)


def watch(pid):
    started = time.monotonic()
    ui_since = ping_since = None
    while alive(pid):
        time.sleep(EVERY)
        now = time.monotonic()
        if now - started < GRACE:
            continue
        wins = windows_of(pid)
        ui_since = (ui_since or now) if ui_hung(wins) else None
        ping_since = None if answers() else (ping_since or now)
        reason = None
        if ui_since is not None and now - ui_since >= HUNG_UI:
            reason = f"the window did not respond for {now - ui_since:.0f} s"
        elif ping_since is not None and now - ping_since >= HUNG_PING:
            reason = f"Tela! did not answer for {now - ping_since:.0f} s"
        if reason and alive(pid):
            visible = any(v for _, v in wins)
            log(f"Watchdog: {reason}; closing and opening Tela! again")
            kill_tree(pid)
            start_main(hidden=not visible)
            return


def main(argv):
    try:
        pid = int(argv[argv.index("--watchdog") + 1])
    except (ValueError, IndexError):
        return
    watch(pid)


def launch(pid):
    """Starts the guard for this process (called by the main copy)."""
    here = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
    cmd = [sys.executable] if FROZEN else [sys.executable, str(here / "app.py")]
    cmd += ["--watchdog", str(pid)]
    flags = 0x08000000 if WINDOWS else 0   # CREATE_NO_WINDOW
    try:
        return subprocess.Popen(cmd, cwd=str(here), creationflags=flags, close_fds=True,
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return None


if __name__ == "__main__":
    main(sys.argv)
    os._exit(0)
