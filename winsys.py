"""Windows integration: single instance, start with Windows, power/lock notifications, clipboard, uninstall."""
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from config import HERE

WINDOWS = sys.platform == "win32"
FROZEN = getattr(sys, "frozen", False)
NO_WINDOW = 0x08000000 if WINDOWS else 0
INSTANCE_PORT = 47614
TASK = "Tela"
OLD_TASKS = ["TelaV3", "TelaV2"]
_STARTUP = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
OLD_SHORTCUTS = [_STARTUP / "Telinha.lnk", _STARTUP / "TelaV2.lnk", _STARTUP / "TelaV3.lnk"]
OUR_EXES = ("tela.exe", "telav3.exe", "telav2.exe")


# ---------------------------------------------------------------- single instance
def ask_running_instance_to_show():
    """If Tela is already running, asks it to show its window and returns True."""
    try:
        with socket.create_connection(("127.0.0.1", INSTANCE_PORT), timeout=0.5) as s:
            s.sendall(b"mostrar")   # the same word TelaV3 understood
        return True
    except OSError:
        return False


def ask_running_instance_to_quit(timeout=12):
    """Asks a running Tela to close properly (it turns the screen off). True if one was running."""
    try:
        with socket.create_connection(("127.0.0.1", INSTANCE_PORT), timeout=0.5) as s:
            s.sendall(b"quit")
    except OSError:
        return False
    end = time.monotonic() + timeout
    while time.monotonic() < end:   # it is gone when the port is free again
        try:
            with socket.create_connection(("127.0.0.1", INSTANCE_PORT), timeout=0.3):
                pass
        except OSError:
            return True
        time.sleep(0.3)
    return True


def installed_by_setup():
    return FROZEN and (HERE / "unins000.exe").exists()


def instance_server(on_show, on_quit=None):
    try:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", INSTANCE_PORT))
        srv.listen(2)
    except OSError:
        return None

    def loop():
        while True:
            try:
                c, _ = srv.accept()
                with c:
                    msg = c.recv(16)
                    if msg == b"mostrar":
                        on_show()
                    elif msg == b"quit" and on_quit is not None:
                        on_quit()
            except OSError:
                return
    threading.Thread(target=loop, daemon=True, name="instance").start()
    return srv


def other_copies():
    """Other running copies (another folder or an old version). Returns (same_copy_running, [processes])."""
    try:
        import psutil
    except ImportError:
        return False, []
    me = os.getpid()
    my_exe = Path(sys.executable).resolve() if FROZEN else None
    same, others = False, []
    for p in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
        try:
            if p.pid in (me, os.getppid()):
                continue
            name = (p.info["name"] or "").lower()
            if name in OUR_EXES:
                exe = p.info["exe"]
                if my_exe is not None and exe and Path(exe).resolve() == my_exe:
                    same = True
                else:
                    others.append(p)
            elif name in ("python.exe", "pythonw.exe", "pyw.exe", "py.exe"):
                cmd = " ".join(p.info["cmdline"] or []).lower()
                if ("app.py" in cmd or "main.py" in cmd or "cli.py" in cmd) and "tela" in (p.cwd() or "").lower():
                    if my_exe is None and Path(p.cwd()).resolve() == HERE:
                        same = True
                    else:
                        others.append(p)
        except Exception:  # noqa: BLE001 — process gone or no access
            continue
    return same, others


def message_box(text, title="Tela!", question=False):
    """Native Windows dialog (no extra libraries). Returns True for Yes/OK."""
    if not WINDOWS:
        print(f"{title}: {text}")
        return not question
    import ctypes
    flags = (0x4 | 0x20) if question else 0x40   # MB_YESNO|MB_ICONQUESTION or MB_ICONINFORMATION
    return ctypes.windll.user32.MessageBoxW(None, text, title, flags | 0x10000) in (1, 6)   # IDOK, IDYES


def resolve_other_copies(texts):
    """Makes sure only one Tela runs. Returns False if this one should exit."""
    same, others = other_copies()
    if same or (not others and ask_running_instance_to_show()):
        ask_running_instance_to_show()
        return False
    if not others:
        return True
    folders = sorted({str(Path(p.info["exe"]).parent) if p.info.get("exe") else (p.info.get("name") or "?") for p in others})
    if not message_box(texts["other_copy"].format(folders="\n".join(f"  • {f}" for f in folders[:4])), question=True):
        return False
    for p in others:
        try:
            p.kill()
        except Exception:  # noqa: BLE001
            pass
    try:
        import psutil
        psutil.wait_procs(others, timeout=5)
    except Exception:  # noqa: BLE001
        pass
    subprocess.run(["taskkill", "/im", "PresentMon.exe", "/f"], creationflags=NO_WINDOW, capture_output=True)
    time.sleep(1.5)   # the COM port takes a moment to be released
    return True


# ---------------------------------------------------------------- start with Windows
def _powershell(cmd, check=True):
    return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                          creationflags=NO_WINDOW, capture_output=True, text=True, check=check)


def task_exists(name=TASK):
    if not WINDOWS:
        return False
    r = subprocess.run(["schtasks", "/Query", "/TN", name], creationflags=NO_WINDOW, capture_output=True)
    return r.returncode == 0


def _delete_task(name):
    subprocess.run(["schtasks", "/Delete", "/TN", name, "/F"], creationflags=NO_WINDOW, capture_output=True)


def starts_with_windows():
    return WINDOWS and (task_exists(TASK) or any(task_exists(t) for t in OLD_TASKS)
                        or any(s.exists() for s in OLD_SHORTCUTS))


def set_start_with_windows(on):
    """Scheduled task with administrator rights: opens at logon without the UAC prompt."""
    if not WINDOWS:
        return
    for s in OLD_SHORTCUTS:
        s.unlink(missing_ok=True)
    for t in OLD_TASKS:
        if task_exists(t):
            _delete_task(t)
    if not on:
        _delete_task(TASK)
        return
    if FROZEN:
        exe, args = sys.executable, "--tray"
    else:   # running from source: pythonw app.py
        exe, args = str(Path(sys.executable).with_name("pythonw.exe")), f'"{HERE / "app.py"}" --tray'
    q = lambda s: s.replace("'", "''")   # noqa: E731
    _powershell(
        f"$a=New-ScheduledTaskAction -Execute '{q(exe)}' -Argument '{q(args)}' -WorkingDirectory '{q(str(HERE))}'; "
        "$t=New-ScheduledTaskTrigger -AtLogOn -User \"$env:USERDOMAIN\\$env:USERNAME\"; $t.Delay='PT10S'; "
        "$s=New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan) -AllowStartIfOnBatteries "
        "-DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew; "
        "$p=New-ScheduledTaskPrincipal -UserId \"$env:USERDOMAIN\\$env:USERNAME\" -RunLevel Highest -LogonType Interactive; "
        f"Register-ScheduledTask -TaskName '{TASK}' -Action $a -Trigger $t -Settings $s -Principal $p -Force | Out-Null")


def remove_old_versions():
    """Stops TelaV3/TelaV2 and removes their startup entries (keeping start with Windows for Tela!)."""
    if not WINDOWS:
        return
    subprocess.run(["taskkill", "/f", "/im", "TelaV3.exe", "/im", "TelaV2.exe"], creationflags=NO_WINDOW, capture_output=True)
    if starts_with_windows():
        set_start_with_windows(True)   # also deletes the old tasks and shortcuts
    else:
        for s in OLD_SHORTCUTS:
            s.unlink(missing_ok=True)
        for t in OLD_TASKS:
            if task_exists(t):
                _delete_task(t)


def refresh_start_with_windows(log):
    """On launch: if start with Windows is on (also an old TelaV3 task), points the task to this Tela.exe."""
    if not (WINDOWS and FROZEN):
        return
    try:
        if starts_with_windows():
            migrated = any(task_exists(t) for t in OLD_TASKS)
            set_start_with_windows(True)
            if migrated:
                log("Start with Windows moved from TelaV3 to Tela!")
    except Exception as e:  # noqa: BLE001
        log(f"Could not update the start with Windows task: {e}")


# ---------------------------------------------------------------- Windows notifications
def watch_windows_events(on_shutdown, on_lock=None, on_monitor=None, on_suspend=None):
    """Own invisible window (in a thread) that receives:
    - shutdown/restart/logoff (WM_ENDSESSION) -> on_shutdown()
    - PC locked/unlocked (Win+L)              -> on_lock(True/False)
    - monitor off/on                          -> on_monitor(True = off)
    - sleep/resume                            -> on_suspend(True = going to sleep)"""
    if not WINDOWS:
        return None
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    LRESULT = ctypes.c_ssize_t
    WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
    user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.DefWindowProcW.restype = LRESULT
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HMODULE
    user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                                       ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                       wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                    ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON),
                    ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HBRUSH),
                    ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR)]

    WM_QUERYENDSESSION, WM_ENDSESSION = 0x0011, 0x0016
    WM_WTSSESSION_CHANGE, WTS_SESSION_LOCK, WTS_SESSION_UNLOCK = 0x02B1, 0x7, 0x8
    WM_POWERBROADCAST, PBT_POWERSETTINGCHANGE = 0x0218, 0x8013

    def proc(hwnd, msg, wparam, lparam):
        try:
            if msg == WM_WTSSESSION_CHANGE and on_lock is not None:
                if wparam == WTS_SESSION_LOCK:
                    on_lock(True)
                elif wparam == WTS_SESSION_UNLOCK:
                    on_lock(False)
                return 0
            if msg == WM_POWERBROADCAST and on_suspend is not None and wparam in (0x4, 0x12):
                on_suspend(wparam == 0x4)   # 0x4 = going to sleep, 0x12 = resumed
                return 1
            if msg == WM_POWERBROADCAST and wparam == PBT_POWERSETTINGCHANGE and on_monitor is not None and lparam:
                # POWERBROADCAST_SETTING: GUID(16) + DataLength(4) + Data: 0 = off, 1 = on, 2 = dimmed
                on_monitor(ctypes.c_uint32.from_address(lparam + 20).value == 0)
                return 1
        except Exception:  # noqa: BLE001
            pass
        if msg == WM_QUERYENDSESSION:
            return 1
        if msg == WM_ENDSESSION:
            if wparam:
                try:
                    on_shutdown()
                except Exception:  # noqa: BLE001
                    pass
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    callback = WNDPROC(proc)

    def loop():
        wc = WNDCLASSW()
        wc.lpfnWndProc = callback
        wc.hInstance = kernel32.GetModuleHandleW(None)
        wc.lpszClassName = "TelaWindowsEvents"
        user32.RegisterClassW(ctypes.byref(wc))
        hwnd = user32.CreateWindowExW(0, wc.lpszClassName, "Tela", 0, 0, 0, 0, 0, None, None, wc.hInstance, None)
        try:
            ctypes.WinDLL("wtsapi32").WTSRegisterSessionNotification(wintypes.HWND(hwnd), 0)
        except Exception:  # noqa: BLE001
            pass
        try:   # monitor on/off (GUID_CONSOLE_DISPLAY_STATE)
            import uuid
            guid = (ctypes.c_ubyte * 16)(*uuid.UUID("6FE69556-704A-47A0-8F24-C28D936FDA47").bytes_le)
            user32.RegisterPowerSettingNotification.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
            user32.RegisterPowerSettingNotification.restype = wintypes.HANDLE
            user32.RegisterPowerSettingNotification(hwnd, ctypes.byref(guid), 0)
        except Exception:  # noqa: BLE001
            pass
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    threading.Thread(target=loop, daemon=True, name="windows-events").start()
    return callback   # must stay referenced while the app runs


# ---------------------------------------------------------------- small helpers
def open_path(path):
    if WINDOWS:
        os.startfile(str(path))  # noqa: S606
    else:
        subprocess.Popen(["xdg-open", str(path)])


def copy_to_clipboard(text):
    if not WINDOWS:
        return False
    import ctypes
    from ctypes import wintypes
    u, k = ctypes.windll.user32, ctypes.windll.kernel32
    k.GlobalAlloc.restype = wintypes.HGLOBAL
    k.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    k.GlobalLock.restype = wintypes.LPVOID
    k.GlobalLock.argtypes = [wintypes.HGLOBAL]
    k.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    u.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    data = text.encode("utf-16-le") + b"\0\0"
    for _ in range(5):
        if u.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        return False
    try:
        u.EmptyClipboard()
        h = k.GlobalAlloc(0x0002, len(data))   # GMEM_MOVEABLE
        p = k.GlobalLock(h)
        ctypes.memmove(p, data, len(data))
        k.GlobalUnlock(h)
        u.SetClipboardData(13, h)   # CF_UNICODETEXT
        return True
    finally:
        u.CloseClipboard()


def windows_version():
    if not WINDOWS:
        return sys.platform
    import platform
    v = sys.getwindowsversion()
    name = "Windows 11" if v.build >= 22000 else "Windows 10"
    return f"{name} (build {v.build}, {platform.machine()})"


def webview2_version():
    """WebView2 runtime version from the registry, or None."""
    if not WINDOWS:
        return None
    import winreg
    key = r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    for root, path in ((winreg.HKEY_LOCAL_MACHINE, key), (winreg.HKEY_CURRENT_USER, key.replace("WOW6432Node\\", ""))):
        try:
            with winreg.OpenKey(root, path) as k:
                v = winreg.QueryValueEx(k, "pv")[0]
                if v and v != "0.0.0.0":
                    return v
        except OSError:
            continue
    return None


def uninstall(log, delete_data=False):
    """Removes start with Windows and, after this process exits, the program: the Windows uninstaller when
    installed with the setup, or the folder itself for portable copies."""
    from config import DATA
    try:
        set_start_with_windows(False)
    except Exception as e:  # noqa: BLE001
        log(f"Could not remove start with Windows: {e}")
    if not WINDOWS:
        return
    import tempfile
    pid = os.getpid()
    lines = ["@echo off",
             ":wait", f"tasklist /fi \"PID eq {pid}\" | find \"{pid}\" >nul && (timeout /t 1 /nobreak >nul & goto wait)",
             "taskkill /im PresentMon.exe /f >nul 2>&1", "timeout /t 1 /nobreak >nul"]
    if installed_by_setup():
        lines.append(f"\"{HERE / 'unins000.exe'}\" /SILENT" + (" /DELETEDATA" if delete_data else ""))
    else:
        lines.append(f"rmdir /s /q \"{HERE}\"")
        if delete_data and DATA != HERE:
            lines.append(f"rmdir /s /q \"{DATA}\"")
    lines.append("(goto) 2>nul & del \"%~f0\"")
    bat = Path(tempfile.gettempdir()) / "uninstall_tela.bat"
    bat.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    subprocess.Popen(["cmd", "/c", str(bat)], cwd=tempfile.gettempdir(), creationflags=NO_WINDOW | 0x00000008)
