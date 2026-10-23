"""Guard process: a second, small copy of Tela! that watches the main one and reopens it when it hangs.

    Tela.exe --watchdog <pid> [--tray]       (started by Tela! itself; ends when the main copy ends)

The main copy is considered hung when BOTH its main window ("Tela!", visible) stays "Not responding" and the page
inside it stops calling Tela! for HUNG_UI seconds, or when it stops answering on the single-instance port for
HUNG_PING seconds (everything frozen, the screen too). Then it is killed and started again (in the tray if its
window was hidden). Only the main window counts: helper windows (keyboard/IME, events) can look "hung" while
everything is fine (1.4.7 restarted Tela! in a loop because of that). After MAX_RESTARTS restarts within
RESTART_WINDOW seconds the guard stays off until Tela! is opened again by hand. Imports stay light on purpose.
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
HUNG_UI = 20.0        # seconds with the window "Not responding" and no call from its page
HUNG_PING = 45.0      # seconds without any answer from the main copy
PAGE_SILENT = 15.0    # seconds without a call from the page inside the window
GRACE = 120.0         # the main copy may be busy while it starts
MAX_RESTARTS = 2
RESTART_WINDOW = 600.0


def log(line):
    """Same file as the main copy's activity log (DATA/tela.log)."""
    try:
        import config
        with open(config.DATA / "tela.log", "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S  ") + line + "\n")
    except Exception:  # noqa: BLE001
        pass


def main_window(pid):
    """(hwnd, visible) of Tela!'s own window (title "Tela!", a Windows Forms window), or None."""
    if not WINDOWS:
        return None
    import ctypes
    from ctypes import wintypes
    u = ctypes.WinDLL("user32")
    proc_t = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    u.EnumWindows.argtypes = [proc_t, wintypes.LPARAM]
    u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    u.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    found = []

    def each(hwnd, _):
        owner = wintypes.DWORD(0)
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value != pid:
            return True
        title, cls = ctypes.create_unicode_buffer(64), ctypes.create_unicode_buffer(128)
        u.GetWindowTextW(hwnd, title, 64)
        u.GetClassNameW(hwnd, cls, 128)
        if title.value == "Tela!" and cls.value.startswith("WindowsForms"):
            found.append((hwnd, bool(u.IsWindowVisible(hwnd))))
        return True
    try:
        u.EnumWindows(proc_t(each), 0)
    except Exception:  # noqa: BLE001
        return None
    return found[0] if found else None


def ui_hung(win):
    """True when the window is visible and Windows says it is "Not responding"."""
    if not WINDOWS or not win or not win[1]:
        return False
    import ctypes
    return bool(ctypes.WinDLL("user32").IsHungAppWindow(win[0]))


def answers():
    """None when the main copy does not answer; otherwise seconds since its page last called it (-1 = unknown,
    e.g. the window is in the tray)."""
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=3) as s:
            s.settimeout(3)
            s.sendall(b"ping")
            reply = s.recv(32)
    except OSError:
        return None
    if not reply.startswith(b"pong"):
        return None
    try:
        return float(reply[5:]) if reply[4:5] == b":" else -1.0
    except ValueError:
        return -1.0


def _restarts_file():
    import config
    return config.DATA / "guard_restarts.txt"


def recent_restarts(now=None):
    now = time.time() if now is None else now
    try:
        stamps = [float(x) for x in _restarts_file().read_text(encoding="utf-8").split()]
    except (OSError, ValueError):
        return []
    return [t for t in stamps if now - t < RESTART_WINDOW]


def note_restart():
    try:
        stamps = recent_restarts() + [time.time()]
        _restarts_file().write_text(" ".join(f"{t:.0f}" for t in stamps), encoding="utf-8")
    except OSError:
        pass


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
    if len(recent_restarts()) >= MAX_RESTARTS:
        log(f"Watchdog: Tela! was already reopened {MAX_RESTARTS} times in {RESTART_WINDOW / 60:.0f} min; "
            "the guard stays off until Tela! is opened again")
        return
    started = time.monotonic()
    ui_since = ping_since = None
    while alive(pid):
        time.sleep(EVERY)
        now = time.monotonic()
        if now - started < GRACE:
            continue
        win = main_window(pid)
        page = answers()
        ping_since = None if page is not None else (ping_since or now)
        # the window counts as hung only when its page stopped calling too (two signs, not one)
        frozen = ui_hung(win) and (page is None or page >= PAGE_SILENT)
        ui_since = (ui_since or now) if frozen else None
        reason = None
        if ui_since is not None and now - ui_since >= HUNG_UI:
            reason = f"the window \"Tela!\" did not respond for {now - ui_since:.0f} s (page silent {page if page is not None else '?'} s)"
        elif ping_since is not None and now - ping_since >= HUNG_PING:
            reason = f"Tela! did not answer for {now - ping_since:.0f} s"
        if reason and alive(pid):
            visible = bool(win and win[1])
            log(f"Watchdog: {reason}; closing and opening Tela! again")
            note_restart()
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
