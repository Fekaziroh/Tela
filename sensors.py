"""Data collection: LibreHardwareMonitor (embedded or web server), PresentMon/RTSS (FPS), Windows (RAM, disks,
network, volume, ping) and the game sessions."""
import fnmatch
import json
import math
import random
import re
import struct
import subprocess
import sys
import threading
import time
import urllib.request
from collections import deque
from pathlib import Path

import psutil

_NUM = re.compile(r"[-+]?\d+(?:[.,]\d+)?")
WINDOWS = sys.platform == "win32"


def _number(txt):
    if txt is None:
        return None
    if isinstance(txt, (int, float)):
        return float(txt)
    m = _NUM.search(str(txt))
    return float(m.group().replace(",", ".")) if m else None


def is_admin():
    if not WINDOWS:
        return False
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # noqa: BLE001
        return False


def foreground_pid():
    if not WINDOWS:
        return None
    import ctypes
    from ctypes import wintypes
    u = ctypes.WinDLL("user32")
    u.GetForegroundWindow.restype = wintypes.HWND
    u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    pid = wintypes.DWORD(0)
    u.GetWindowThreadProcessId(u.GetForegroundWindow(), ctypes.byref(pid))
    return pid.value or None


def pids_with_windows():
    """Processes that own a visible top-level window (a minimized game still has one; a launcher hidden in the
    tray or a process left behind after the game closed does not). None outside Windows."""
    if not WINDOWS:
        return None
    import ctypes
    from ctypes import wintypes
    u = ctypes.WinDLL("user32")
    out = set()
    proc_t = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def each(hwnd, _):
        if u.IsWindowVisible(hwnd) and u.GetWindowTextLengthW(hwnd) > 0:
            pid = wintypes.DWORD(0)
            u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            out.add(pid.value)
        return True
    u.EnumWindows.argtypes = [proc_t, wintypes.LPARAM]
    u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    try:
        u.EnumWindows(proc_t(each), 0)
    except Exception:  # noqa: BLE001
        return None
    return out


def idle_seconds():
    """Seconds since the last keyboard/mouse input (0 outside Windows)."""
    if not WINDOWS:
        return 0.0
    import ctypes
    from ctypes import wintypes

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]
    li = LASTINPUTINFO()
    li.cbSize = ctypes.sizeof(li)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(li)):
        return 0.0
    return ((ctypes.windll.kernel32.GetTickCount() - li.dwTime) & 0xFFFFFFFF) / 1000.0


# ---------------------------------------------------------------- LibreHardwareMonitor (web server)
class LhmWeb:
    """Reads http://localhost:8085/data.json (Options > Remote Web Server > Run in LibreHardwareMonitor)."""

    def __init__(self, url):
        self.url = url
        self.sensors = []
        self.error = None

    def read(self):
        try:
            with urllib.request.urlopen(self.url, timeout=2) as r:
                tree = json.load(r)
        except Exception as e:  # noqa: BLE001
            self.error = f"{type(e).__name__}: {e}"
            self.sensors = []
            return
        self.error = None
        self.sensors = []
        self._walk(tree, [])

    def _walk(self, node, path):
        children = node.get("Children") or []
        sid = node.get("SensorId")
        text = node.get("Text", "")
        if sid or (not children and len(path) >= 3 and node.get("Value") not in (None, "")):
            self.sensors.append({
                "id": sid or "/" + "/".join(path[2:] + [text]),
                "name": text,
                "type": (node.get("Type") or "").lower(),
                "group": path[-1] if path else "",
                "hardware": " > ".join(path[2:-1]),
                "value": _number(node.get("Value")),
                "text": node.get("Value"),
            })
        for c in children:
            self._walk(c, path + [text])

    def find(self, selector):
        """'hardware|type|name[|avg|max|min|sum]' or an exact SensorId ('/amdcpu/0/load/0').

        hardware: part of the SensorId or hardware name (cpu, gpu, lpc, nvme...)
        type: temperature, load, clock, power, fan, smalldata, voltage...
        name: sensor name, * works as a wildcard ('Core #*')
        """
        parts = [p.strip() for p in selector.split("|")]
        if len(parts) == 1:
            target = parts[0].lower()
            return next((s["value"] for s in self.sensors if s["id"].lower() == target), None)
        hw, kind, name = (parts + ["", "", ""])[:3]
        agg = parts[3].lower() if len(parts) > 3 else ("avg" if "*" in name else "first")
        hw, kind, name = hw.lower(), kind.lower(), name.lower()
        found = []
        for s in self.sensors:
            idl = s["id"].lower()
            if hw and hw not in idl and hw not in s["hardware"].lower():
                continue
            if kind and not (kind == s["type"] or kind in idl.split("/") or s["group"].lower().startswith(kind)):
                continue
            if name and not fnmatch.fnmatchcase(s["name"].lower(), name):
                continue
            if s["value"] is not None:
                found.append(s["value"])
        if not found:
            return None
        if agg == "max":
            return max(found)
        if agg == "min":
            return min(found)
        if agg == "sum":
            return sum(found)
        if agg == "avg":
            return sum(found) / len(found)
        return found[0]

    def close(self):
        pass


# ---------------------------------------------------------------- LibreHardwareMonitor embedded
UNITS = {
    "temperature": " °C", "clock": " MHz", "load": " %", "power": " W", "fan": " RPM", "voltage": " V",
    "current": " A", "data": " GB", "smalldata": " MB", "control": " %", "level": " %", "frequency": " Hz",
    "throughput": " B/s", "energy": " mWh", "noise": " dBA", "conductivity": " µS/cm", "humidity": " %",
    "factor": "", "timespan": " s", "flow": " L/h",
}


class LhmEmbedded(LhmWeb):
    """Uses LibreHardwareMonitorLib.dll directly (through pythonnet), without opening LibreHardwareMonitor.

    The DLLs live in lhm/ (the installer downloads the .NET Framework 4.7.2 build from GitHub).
    Needs administrator rights for CPU temperatures and motherboard sensors.
    """

    def __init__(self, folder, disk_interval=2.0, controllers=False):
        super().__init__(url=None)
        self.folder = Path(folder)
        self.disk_interval = float(disk_interval)
        self.controllers = bool(controllers)
        self._last_update = {}
        self.computer = None
        self.start_error = None
        self.admin = is_admin()
        self._lock = threading.Lock()

    def _start(self):
        if not WINDOWS:
            raise RuntimeError("Windows only")
        if not (self.folder / "LibreHardwareMonitorLib.dll").exists():
            raise FileNotFoundError(f"LibreHardwareMonitorLib.dll is missing from {self.folder}")
        if str(self.folder) not in sys.path:
            sys.path.append(str(self.folder))
        try:
            from pythonnet import load
            load("netfx")
        except Exception:  # noqa: BLE001 — already loaded (the window loads it too)
            pass
        import clr  # noqa: F401
        clr.AddReference("LibreHardwareMonitorLib")
        from LibreHardwareMonitor.Hardware import Computer  # type: ignore
        c = Computer()
        c.IsCpuEnabled = True
        c.IsGpuEnabled = True
        c.IsMemoryEnabled = False          # RAM comes from Windows (psutil)
        c.IsMotherboardEnabled = True
        c.IsControllerEnabled = self.controllers
        c.IsStorageEnabled = True
        c.Open()
        self.computer = c

    def read(self):
        with self._lock:
            if self.computer is None and self.start_error is None:
                try:
                    self._start()
                except Exception as e:  # noqa: BLE001
                    self.start_error = f"{type(e).__name__}: {e}"
            if self.computer is None:
                self.error = self.start_error
                self.sensors = []
                return
            new = []
            try:
                for hw in self.computer.Hardware:
                    self._hardware(hw, new, [])
                self.error = None
            except Exception as e:  # noqa: BLE001
                self.error = f"{type(e).__name__}: {e}"
            self.sensors = new

    def _hardware(self, hw, out, parents):
        # disks: SMART/temperature change slowly; updated every 'disk_interval' s
        kind = str(hw.HardwareType)
        now = time.monotonic()
        key = str(hw.Identifier)
        if kind != "Storage" or now - self._last_update.get(key, 0) >= self.disk_interval:
            hw.Update()
            self._last_update[key] = now
        hw_name = " > ".join(parents + [str(hw.Name)])
        for s in hw.Sensors:
            stype = str(s.SensorType).lower()
            v = s.Value
            value = None if v is None else float(v)
            out.append({
                "id": str(s.Identifier),
                "name": str(s.Name),
                "type": stype,
                "group": str(s.SensorType),
                "hardware": hw_name,
                "value": value,
                "text": "-" if value is None else f"{value:.1f}{UNITS.get(stype, '')}",
            })
        for sub in hw.SubHardware:
            self._hardware(sub, out, parents + [str(hw.Name)])

    def close(self):
        with self._lock:
            if self.computer is not None:
                try:
                    self.computer.Close()
                except Exception:  # noqa: BLE001
                    pass
                self.computer = None


def make_reader(cfg, base):
    """Embedded monitor (default on Windows) or the LibreHardwareMonitor web server."""
    data = cfg.get("data") or {}
    source = str(data.get("source", "auto")).lower()
    web = LhmWeb(data.get("lhm_url", "http://localhost:8085/data.json"))
    if source == "web" or not WINDOWS:
        return web, web
    return LhmEmbedded(Path(base) / "lhm", data.get("disk_interval", 2), data.get("controllers", False)), web


# ---------------------------------------------------------------- RTSS (FPS)
class RTSS:
    """FPS from the RivaTuner Statistics Server shared memory (ships with MSI Afterburner)."""

    NAME = "RTSSSharedMemoryV2"

    def __init__(self):
        self.fps = self.frametime = self.app = None
        self.running = False
        self._ok = WINDOWS
        if self._ok:
            import ctypes
            from ctypes import wintypes
            self.ct = ctypes
            k = ctypes.WinDLL("kernel32", use_last_error=True)
            k.OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
            k.OpenFileMappingW.restype = wintypes.HANDLE
            k.MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
            k.MapViewOfFile.restype = ctypes.c_void_p
            k.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
            k.CloseHandle.argtypes = [wintypes.HANDLE]
            k.GetTickCount.restype = wintypes.DWORD
            self.k = k

    def read(self):
        self.fps = self.frametime = self.app = None
        self.running = False
        if not self._ok:
            return
        FILE_MAP_READ = 0x0004
        h = self.k.OpenFileMappingW(FILE_MAP_READ, False, self.NAME)
        if not h:
            return
        addr = self.k.MapViewOfFile(h, FILE_MAP_READ, 0, 0, 0)
        try:
            if not addr:
                return
            head = self.ct.string_at(addr, 20)
            signature, version, app_size, app_offset, app_count = struct.unpack_from("<5I", head)
            if signature != 0x52545353 or version < 0x00020000:
                return
            self.running = True
            now = self.k.GetTickCount()
            front = foreground_pid()
            best = None
            for i in range(app_count):
                e = self.ct.string_at(addr + app_offset + i * app_size, 284)
                pid = struct.unpack_from("<I", e, 0)[0]
                if pid == 0:
                    continue
                t0, t1, frames, ft = struct.unpack_from("<4I", e, 268)
                if t1 <= t0 or frames == 0 or ((now - t1) & 0xFFFFFFFF) > 3000:
                    continue
                name = e[4:264].split(b"\0", 1)[0].decode("mbcs", "replace")
                cand = (pid == front, t1, frames * 1000.0 / (t1 - t0), ft / 1000.0, name)
                if best is None or cand[:2] > best[:2]:
                    best = cand
            if best:
                _, _, self.fps, self.frametime, self.app = best
        finally:
            if addr:
                self.k.UnmapViewOfFile(addr)
            self.k.CloseHandle(h)


# ---------------------------------------------------------------- PresentMon (FPS without RTSS)
IGNORE_FPS = [
    "dwm.exe", "explorer.exe", "tela.exe", "chrome.exe", "msedge.exe", "msedgewebview2.exe", "firefox.exe",
    "opera.exe", "brave.exe", "discord.exe", "steamwebhelper.exe", "spotify.exe", "searchhost.exe",
    "startmenuexperiencehost.exe", "shellexperiencehost.exe", "textinputhost.exe", "applicationframehost.exe",
]


def _bind_to_job(proc):
    """The child process dies together with Tela, even when Tela is killed."""
    import ctypes
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)

    class BASIC(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

    class IO(ctypes.Structure):
        _fields_ = [(n, ctypes.c_ulonglong) for n in ("r", "w", "o", "rb", "wb", "ob")]

    class EXTENDED(ctypes.Structure):
        _fields_ = [("Basic", BASIC), ("Io", IO), ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t)]

    k.CreateJobObjectW.restype = wintypes.HANDLE
    k.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    job = k.CreateJobObjectW(None, None)
    info = EXTENDED()
    info.Basic.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    k.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
    k.AssignProcessToJobObject(job, int(proc._handle))
    return job  # the handle must stay open


class PresentMon:
    """Runs PresentMon (Intel, open source) hidden and computes the FPS of the foreground program.
    Needs administrator rights. Programs in 'ignore' (browsers, Discord...) never count as games."""

    FULL_ARGS = ["--output_stdout", "--no_console_stats", "--stop_existing_session",
                 "--session_name", "Tela", "--no_track_display", "--no_track_input", "--no_track_gpu",
                 "--exclude", "dwm.exe"]
    MIN_ARGS = ["--output_stdout", "--no_console_stats", "--stop_existing_session", "--session_name", "Tela"]

    def __init__(self, exe, ignore=None):
        self.exe = Path(exe)
        self.ignore = {n.lower() for n in (IGNORE_FPS if ignore is None else ignore)}
        self.ignore.add("tela.exe")
        self.proc = None
        self.error = None
        self.running = False
        self.fps = self.frametime = self.app = self.pid = None
        self._frames = {}     # pid -> deque[(cpu_time, ms_between_presents, arrival)]
        self._names = {}
        self._lock = threading.Lock()
        self._next_try = 0.0
        self._started = 0.0
        self._args = self.FULL_ARGS
        self._job = None
        self.events = []    # messages for the activity log
        self._last_line = 0.0
        self._restarts = 0
        self.window = 0.5   # seconds averaged for the FPS (lower = reacts faster, oscillates more)

    def available(self):
        return WINDOWS and self.exe.exists()

    def alive(self):
        """The process is running. Recent versions only write their first line once frames arrive,
        so with no game open this is the only sign that FPS measuring works."""
        return self.proc is not None and self.proc.poll() is None

    SESSION_NAMES = re.compile(r"^(tela|telav3|telav2)$", re.I)

    @classmethod
    def clear_stale_sessions(cls):
        """Stops capture sessions left behind by Tela/TelaV3 when they were closed by force. Windows keeps
        them until a restart and only allows a few per provider, which silently starves new captures."""
        if not WINDOWS:
            return []
        try:
            out = subprocess.run(["logman", "query", "-ets"], capture_output=True, text=True, timeout=10,
                                 creationflags=0x08000000).stdout or ""
        except Exception:  # noqa: BLE001
            return []
        stopped = []
        for line in out.splitlines():
            name = line.split()[0] if line.strip() else ""
            if cls.SESSION_NAMES.match(name):
                subprocess.run(["logman", "stop", name, "-ets"], capture_output=True, timeout=10, creationflags=0x08000000)
                stopped.append(name)
        return stopped

    def silent_for(self):
        """Seconds the running PresentMon has gone without writing anything."""
        if not self.alive():
            return 0.0
        return time.monotonic() - max(self._started, self._last_line)

    def restart(self, reason):
        """Recovers a capture that stopped receiving frames, without restarting the PC."""
        self._restarts += 1
        self.events.append(f"FPS capture restarted: {reason}")
        self.stop()
        self._next_try = time.monotonic() + (0 if self._restarts <= 3 else 300)   # do not insist forever

    def _start(self):
        stale = self.clear_stale_sessions()
        if stale:
            self.events.append("Cleared stuck FPS capture sessions: " + ", ".join(stale))
        self.proc = subprocess.Popen(
            [str(self.exe), *self._args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL, creationflags=0x08000000, text=True, encoding="utf-8",
            errors="replace", bufsize=1)
        self._started = time.monotonic()
        self._messages = deque(maxlen=4)   # what PresentMon says when it fails (shown in the window)
        threading.Thread(target=self._read_errors, args=(self.proc, self._messages), daemon=True,
                         name="presentmon-errors").start()
        try:
            self._job = _bind_to_job(self.proc)
        except Exception:  # noqa: BLE001
            self._job = None
        threading.Thread(target=self._read_output, args=(self.proc,), daemon=True, name="presentmon").start()

    def feed(self, lines):
        """Parses PresentMon CSV lines (separate from the thread so it can be tested)."""
        head = None
        i_app = i_pid = i_ms = i_t = None
        for line in lines:
            self._last_line = time.monotonic()
            parts = [p.strip() for p in line.strip().split(",")]
            if len(parts) < 3:
                continue
            if head is None:
                names = [p.lower() for p in parts]
                if "processid" not in names:
                    continue
                head = names
                i_app = names.index("application") if "application" in names else 0
                i_pid = names.index("processid")
                i_ms = next((names.index(c) for c in ("msbetweenpresents", "frametime") if c in names), None)
                i_t = next((names.index(c) for c in ("cpustarttime", "timeinseconds") if c in names), None)
                self.running = i_ms is not None
                continue
            try:
                pid = int(parts[i_pid])
                ms = float(parts[i_ms])
                t = float(parts[i_t]) if i_t is not None else None
            except (ValueError, IndexError, TypeError):
                continue
            if ms <= 0:
                continue
            self._restarts = 0
            with self._lock:
                dq = self._frames.get(pid)
                if dq is None:
                    dq = self._frames[pid] = deque(maxlen=3000)
                dq.append((t, ms, time.monotonic()))
                self._names[pid] = parts[i_app]

    def _read_output(self, proc):
        self.feed(proc.stdout)
        self.running = False

    @staticmethod
    def _read_errors(proc, messages):
        for line in proc.stderr:
            line = line.strip()
            if line:
                messages.append(line[:200])

    def _exit_reason(self):
        code = self.proc.returncode
        said = " / ".join(getattr(self, "_messages", []) or [])
        return f"PresentMon closed (exit code {code})" + (f": {said}" if said else "")

    def read(self, front=None):
        self.fps = self.frametime = self.app = self.pid = None
        if self.proc is not None or self.available():
            now = time.monotonic()
            if self.proc is None or self.proc.poll() is not None:
                if self.proc is not None:
                    reason = self._exit_reason()
                    if reason != self.error:
                        self.error = reason
                        self.events.append(reason)
                    if now - self._started < 5 and self._args is self.FULL_ARGS:
                        self._args = self.MIN_ARGS   # this PresentMon version rejected an option
                        self._next_try = 0
                    self.proc = None
                if not self.available():
                    self.error = "PresentMon not found"
                    return
                if now >= self._next_try:
                    try:
                        self._start()
                    except Exception as e:  # noqa: BLE001
                        self.error = f"{type(e).__name__}: {e}"
                    self._next_try = now + 15
                return
            if self.running:
                self.error = None
        elif not self._frames:
            self.error = "PresentMon not found"
            return
        self.compute(foreground_pid() if front is None else front)

    def compute(self, front):
        now = time.monotonic()
        with self._lock:
            for pid in [p for p, dq in self._frames.items() if not dq or now - dq[-1][2] > 2.0]:
                self._frames.pop(pid, None)
            dq = self._frames.get(front)
            name = self._names.get(front, "")
            if not dq or name.lower() in self.ignore:
                return
            last_t, last_arrival = dq[-1][0], dq[-1][2]
            if last_t is not None:
                window = [ms for t, ms, _ in dq if t is not None and t >= last_t - self.window]
            else:
                window = [ms for _, ms, c in dq if c >= last_arrival - self.window]
        if window:
            avg = sum(window) / len(window)
            self.fps, self.frametime, self.app, self.pid = 1000.0 / avg, avg, name, front

    def frames_since(self, pid, arrival):
        """Frames (ms) of pid that arrived after 'arrival'. Returns (list, last_arrival)."""
        with self._lock:
            dq = self._frames.get(pid)
            if not dq:
                return [], arrival
            return [ms for _, ms, c in dq if c > arrival], dq[-1][2]

    def recent_times(self, seconds=2.0):
        if self.pid is None:
            return []
        with self._lock:
            dq = self._frames.get(self.pid)
            if not dq:
                return []
            last_t, last_c = dq[-1][0], dq[-1][2]
            if last_t is not None:
                return [ms for t, ms, _ in dq if t is not None and t >= last_t - seconds]
            return [ms for _, ms, c in dq if c >= last_c - seconds]

    def stop(self):
        if self.proc is not None and self.proc.poll() is None:
            try:
                self.proc.terminate()
                self.proc.wait(3)
            except Exception:  # noqa: BLE001
                try:
                    self.proc.kill()
                except Exception:  # noqa: BLE001
                    pass
            self.clear_stale_sessions()   # a killed PresentMon leaves its session behind
        self.proc = None
        self.running = False


# ---------------------------------------------------------------- game sessions
def one_percent_low(times_ms):
    """1% low: average FPS of the worst 1% of frames."""
    if len(times_ms) < 50:
        return None
    worst = sorted(times_ms, reverse=True)[:max(1, len(times_ms) // 100)]
    return 1000.0 / (sum(worst) / len(worst))


GENERIC = {"", "game", "application", "launcher", "unity", "unreal engine", "unrealengine", "ue4", "ue5",
           "directx", "client", "shipping", "win64", "main"}


def game_name(exe):
    """Friendly game name (description stored in the .exe), or the file name."""
    base = Path(exe).stem if exe else "Game"
    for suffix in ("-Win64-Shipping", "-WinGDK-Shipping", "_x64", "-Win64", "_dx12", "_dx11", "x64"):
        if base.lower().endswith(suffix.lower()):
            base = base[: -len(suffix)]
    if not exe or not WINDOWS:
        return base
    try:
        import ctypes
        from ctypes import wintypes
        v = ctypes.WinDLL("version")
        size = v.GetFileVersionInfoSizeW(exe, None)
        if not size:
            return base
        buf = ctypes.create_string_buffer(size)
        v.GetFileVersionInfoW(exe, 0, size, buf)
        ptr, n = ctypes.c_void_p(), wintypes.UINT()
        langs = []
        if v.VerQueryValueW(buf, "\\VarFileInfo\\Translation", ctypes.byref(ptr), ctypes.byref(n)) and n.value >= 4:
            data = ctypes.string_at(ptr, n.value)
            langs = [f"{struct.unpack_from('<H', data, i)[0]:04x}{struct.unpack_from('<H', data, i + 2)[0]:04x}"
                     for i in range(0, n.value - 3, 4)]
        langs += ["040904b0", "040904e4", "041604b0"]
        for field in ("FileDescription", "ProductName"):
            for lang in langs:
                if v.VerQueryValueW(buf, f"\\StringFileInfo\\{lang}\\{field}", ctypes.byref(ptr), ctypes.byref(n)) and n.value:
                    txt = ctypes.wstring_at(ptr, n.value).strip("\x00 ").strip()
                    if txt and txt.lower() not in GENERIC and len(txt) <= 40:
                        return txt
    except Exception:  # noqa: BLE001
        pass
    return base


class Session:
    """One play session: from the game's first frame until its process exits."""
    BINS = 5001          # frametime histogram: 0.05 ms per bin, up to 250 ms

    def __init__(self, pid, name):
        self.pid, self.name = pid, name
        self.start = time.monotonic()
        self.hist = [0] * self.BINS
        self.n = 0
        self.sum_ms = 0.0
        self.fps_samples = []   # one per second with the game in the foreground
        self.last_fps = time.monotonic()   # when it last had FPS in the foreground
        self.fps_max = None
        self.maxima = {}        # sensor -> highest value
        self.last_arrival = 0.0

    def frames(self, times):
        for ms in times:
            self.hist[min(self.BINS - 1, int(ms * 20))] += 1
            self.n += 1
            self.sum_ms += ms

    def fps_avg(self):
        return 1000.0 * self.n / self.sum_ms if self.sum_ms else None

    def one_percent_low(self):
        if self.n < 100:
            return None
        target = max(1, self.n // 100)
        missing, total = target, 0.0
        for i in range(self.BINS - 1, -1, -1):
            c = self.hist[i]
            if c:
                k = min(c, missing)
                total += k * (i + 0.5) / 20
                missing -= k
                if missing <= 0:
                    break
        return 1000.0 / (total / target)

    def duration(self):
        return time.monotonic() - self.start


def format_duration(sec):
    m = int(sec // 60)
    return f"{m // 60}h {m % 60:02d}min" if m >= 60 else f"{m} min"


def downsample(values, n=120):
    vals = [v for v in values if v is not None]
    if len(vals) <= n:
        return vals
    step = len(vals) / n
    return [sum(vals[int(i * step):int((i + 1) * step)]) / max(1, int((i + 1) * step) - int(i * step)) for i in range(n)]


# ---------------------------------------------------------------- ping / internet outage
class Ping:
    """Pings the router and the internet in the background (Windows ICMP API, no ping.exe).
    state: 'normal' | 'unstable' | 'down' | None (off)."""

    def __init__(self, servers=("1.1.1.1", "8.8.8.8"), interval=2.0, fails_for_outage=3, limits=(60, 150, 2, 10)):
        self.servers = [x.strip() for x in servers if str(x).strip()]
        self.interval = max(1.0, float(interval))
        self.fails_for_outage = int(fails_for_outage)
        self.warn_ms, self.crit_ms, self.warn_loss, self.crit_loss = limits
        self.ms = None
        self.loss = None
        self.state = None
        self.since = None           # time.time() when the outage began
        self.gateway = None
        self.gateway_ok = None
        self._results = deque(maxlen=30)
        self._rtts = deque(maxlen=3)
        self._fails = 0
        self._first_fail = None
        self._stop = threading.Event()
        self._thread = None

    def _prepare(self):
        import ctypes
        from ctypes import wintypes
        self.ct, self.wt = ctypes, wintypes
        self.ip = ctypes.WinDLL("iphlpapi")
        self.ip.IcmpCreateFile.restype = wintypes.HANDLE
        self.ip.IcmpSendEcho.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p, wintypes.WORD,
                                         ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD]
        self.ip.IcmpSendEcho.restype = wintypes.DWORD
        self.ip.IcmpCloseHandle.argtypes = [wintypes.HANDLE]
        self.ip.GetBestRoute.argtypes = [wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
        self.handle = self.ip.IcmpCreateFile()

    @staticmethod
    def _ip_dword(ip):
        import socket
        return int.from_bytes(socket.inet_aton(ip), "little")

    def _ping(self, ip, timeout_ms=1000):
        try:
            dest = self._ip_dword(ip)
        except OSError:
            return None
        data = b"tela-----ping"
        resp = self.ct.create_string_buffer(64 + len(data) + 8)
        n = self.ip.IcmpSendEcho(self.handle, dest, data, len(data), None, resp, len(resp), timeout_ms)
        if not n:
            return None
        status, rtt = struct.unpack_from("<II", resp.raw, 4)   # ICMP_ECHO_REPLY: Address, Status, RoundTripTime
        return float(rtt) if status == 0 else None

    def _find_gateway(self):
        try:
            row = (self.wt.DWORD * 14)()
            if self.ip.GetBestRoute(self._ip_dword(self.servers[0] if self.servers else "1.1.1.1"), 0,
                                    self.ct.byref(row)) == 0 and row[3]:
                import socket
                return socket.inet_ntoa(int(row[3]).to_bytes(4, "little"))
        except Exception:  # noqa: BLE001
            pass
        return None

    def start(self):
        if not WINDOWS or not self.servers or self._thread is not None:
            return
        self._prepare()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="ping")
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        gw_at = 0.0
        while not self._stop.is_set():
            t0 = time.monotonic()
            try:
                if t0 - gw_at > 30:
                    self.gateway, gw_at = self._find_gateway(), t0
                self.record(next((r for r in (self._ping(x) for x in self.servers) if r is not None), None),
                            self._ping(self.gateway) is not None if self.gateway else None)
            except Exception:  # noqa: BLE001
                pass
            self._stop.wait(max(0.2, self.interval - (time.monotonic() - t0)))

    def record(self, rtt, gateway_ok):
        """Accounts one cycle (separate from the loop so it can be tested)."""
        self.gateway_ok = gateway_ok
        self._results.append(rtt is not None)
        if rtt is not None:
            self._rtts.append(rtt)
            self._fails = 0
            self.since = None
        else:
            self._fails += 1
            if self._fails == 1:
                self._first_fail = time.time()
        self.loss = 100.0 * self._results.count(False) / len(self._results)
        if self._fails >= self.fails_for_outage:
            self.state, self.ms = "down", None
            self.since = self.since or self._first_fail or time.time()
            return
        self.ms = sum(self._rtts) / len(self._rtts) if self._rtts else None
        bad = (self.ms is not None and self.ms >= self.warn_ms) or self.loss >= self.warn_loss
        self.state = "unstable" if bad else "normal"

    def level(self):
        """'ok' | 'warn' | 'crit' to color ping/loss."""
        if self.state == "down":
            return "crit"
        if (self.ms or 0) >= self.crit_ms or (self.loss or 0) >= self.crit_loss:
            return "crit"
        if self.state == "unstable":
            return "warn"
        return "ok"


# ---------------------------------------------------------------- Windows volume (Core Audio)
class Volume:
    """Master volume of the default output device (the same as the Windows sound icon).
    None when muted. Follows device changes (headphones/speakers)."""

    def __init__(self):
        self._ok = WINDOWS
        self._vol = None
        self._got_at = 0.0
        self._com_ok = False
        if self._ok:
            import ctypes
            from ctypes import wintypes
            self.ct, self.wt = ctypes, wintypes
            self.ole = ctypes.OleDLL("ole32")

    def _guid(self, txt):
        import uuid
        ct = self.ct

        class GUID(ct.Structure):
            _fields_ = [("d", ct.c_ubyte * 16)]
        g = GUID()
        g.d[:] = uuid.UUID(txt).bytes_le
        return g

    def _method(self, obj, index, *types):
        vtbl = self.ct.cast(obj, self.ct.POINTER(self.ct.POINTER(self.ct.c_void_p)))[0]
        return self.ct.WINFUNCTYPE(self.ct.HRESULT, self.ct.c_void_p, *types)(vtbl[index])

    def _release(self, obj):
        if obj:
            try:
                self.ct.WINFUNCTYPE(self.ct.c_ulong, self.ct.c_void_p)(
                    self.ct.cast(obj, self.ct.POINTER(self.ct.POINTER(self.ct.c_void_p)))[0][2])(obj)
            except Exception:  # noqa: BLE001
                pass

    def _connect(self):
        ct = self.ct
        if not self._com_ok:
            try:
                self.ole.CoInitializeEx(None, 0)  # COINIT_MULTITHREADED
            except OSError:
                pass
            self._com_ok = True
        enum, dev, vol = ct.c_void_p(), ct.c_void_p(), ct.c_void_p()
        self.ole.CoCreateInstance(ct.byref(self._guid("BCDE0395-E52F-467C-8E3D-C4579291692E")), None, 23,
                                  ct.byref(self._guid("A95664D2-9614-4F35-A746-DE8DB63617E6")), ct.byref(enum))
        try:
            # IMMDeviceEnumerator::GetDefaultAudioEndpoint(eRender, eMultimedia)
            self._method(enum, 4, ct.c_int, ct.c_int, ct.POINTER(ct.c_void_p))(enum, 0, 1, ct.byref(dev))
            # IMMDevice::Activate(IID_IAudioEndpointVolume)
            self._method(dev, 3, ct.c_void_p, self.wt.DWORD, ct.c_void_p, ct.POINTER(ct.c_void_p))(
                dev, ct.byref(self._guid("5CDF2C82-841E-4546-9722-0CF74078229A")), 23, None, ct.byref(vol))
        finally:
            self._release(dev)
            self._release(enum)
        self._release(self._vol)
        self._vol = vol

    def read(self):
        if not self._ok:
            return None
        ct = self.ct
        try:
            now = time.monotonic()
            if self._vol is None or now - self._got_at > 5:   # re-checks the default device
                self._connect()
                self._got_at = now
            level, mute = ct.c_float(), self.wt.BOOL()
            self._method(self._vol, 9, ct.POINTER(ct.c_float))(self._vol, ct.byref(level))   # GetMasterVolumeLevelScalar
            self._method(self._vol, 15, ct.POINTER(self.wt.BOOL))(self._vol, ct.byref(mute))  # GetMute
            return None if mute.value else round(level.value * 100)
        except OSError:
            self._release(self._vol)
            self._vol = None
            return None


# ---------------------------------------------------------------- Windows counters (psutil)
class System:
    def __init__(self, interface=None):
        self.interface = interface
        self._net = None
        self.v = {}
        self.volume = Volume()
        psutil.cpu_percent(None)

    def _net_bytes(self):
        c = psutil.net_io_counters(pernic=True)
        if self.interface and self.interface in c:
            x = c[self.interface]
            return x.bytes_sent, x.bytes_recv
        sent = recv = 0
        for name, x in c.items():
            n = name.lower()
            if n == "lo" or "loopback" in n:
                continue
            sent += x.bytes_sent
            recv += x.bytes_recv
        return sent, recv

    def read(self):
        m = psutil.virtual_memory()
        v = {
            "sys.ram_pct": m.percent,
            "sys.ram_used_gb": (m.total - m.available) / 2**30,
            "sys.ram_total_gb": m.total / 2**30,
            "sys.cpu_pct": psutil.cpu_percent(None),
        }
        now = time.monotonic()
        sent, recv = self._net_bytes()
        if self._net:
            t, s0, r0 = self._net
            dt = now - t
            if dt > 0:
                v["sys.net_up_mbps"] = max(0, sent - s0) * 8 / dt / 1e6
                v["sys.net_down_mbps"] = max(0, recv - r0) * 8 / dt / 1e6
                v["sys.net_up_mbs"] = max(0, sent - s0) / dt / 2**20
                v["sys.net_down_mbs"] = max(0, recv - r0) / dt / 2**20
        self._net = (now, sent, recv)
        v["sys.volume"] = self.volume.read()
        v["sys.app_cpu"], v["sys.app_ram_mb"] = self.app_usage()
        self.v = v

    def app_usage(self):
        """CPU (% of the whole PC) and RAM (MB) used by Tela itself, its window and PresentMon."""
        if not hasattr(self, "_me"):
            self._me, self._procs = psutil.Process(), {}
        cpu = ram = 0.0
        try:
            procs = [self._me] + self._me.children(recursive=True)
        except Exception:  # noqa: BLE001
            procs = [self._me]
        alive = set()
        for p in procs:
            try:
                q = self._procs.get(p.pid)
                if q is None:
                    q = self._procs[p.pid] = p
                    q.cpu_percent(None)
                alive.add(p.pid)
                cpu += q.cpu_percent(None)
                ram += q.memory_info().rss
            except Exception:  # noqa: BLE001
                continue
        for pid in set(self._procs) - alive:
            self._procs.pop(pid, None)
        return round(cpu / (psutil.cpu_count() or 1), 2), round(ram / 2**20)

    def read_fast(self):
        self.v["sys.volume"] = self.volume.read()

    def get(self, key):
        if key.startswith("sys.disk_pct:"):
            path = key.split(":", 1)[1]
            if path.endswith(":"):
                path += "\\"
            try:
                return psutil.disk_usage(path).percent
            except Exception:  # noqa: BLE001
                return None
        return self.v.get(key)


# ---------------------------------------------------------------- demo data
DEMO = {
    "cpu_temp": (40, 82), "cpu_load": (3, 90), "cpu_clock": (3400, 4500), "cpu_power": (30, 120),
    "cpu_fan": (700, 1600), "gpu_temp": (35, 75), "gpu_hotspot": (45, 92), "gpu_load": (0, 99),
    "gpu_clock": (500, 2650), "gpu_mem_clock": (2000, 2250), "gpu_power": (20, 210), "gpu_fan": (0, 2200),
    "vram_mb": (1500, 9000), "ssd1_temp": (40, 50), "ssd2_temp": (30, 40), "ram_pct": (30, 70),
    "ram_used_gb": (9, 22), "net_down": (0, 600), "net_up": (0, 80), "fps": (110, 144),
    "volume": (20, 80), "app_cpu": (0.3, 1.2), "app_ram": (88, 96), "disk1_act": (0, 30), "disk2_act": (0, 15), "disk1": (42, 42.5), "disk2": (71, 71.5),
}


def fill(txt, fields):
    """Replaces {field} with the detected value. Returns None if a field is missing."""
    if not isinstance(txt, str) or "{" not in txt:
        return txt
    missing = []

    def sub(m):
        v = fields.get(m.group(1))
        if v in (None, ""):
            missing.append(m.group(1))
            return ""
        return str(v)
    out = re.sub(r"\{(\w+)\}", sub, txt)
    return None if missing else out


def fill_selector(sel, fields):
    if isinstance(sel, list):
        lst = [x for x in (fill_selector(i, fields) for i in sel) if x is not None]
        return lst or None
    return fill(sel, fields)


# ---------------------------------------------------------------- collector
class Collector:
    def __init__(self, cfg, demo=False, base=".", fields=None, demo_game=True, demo_media=True, previous=None):
        data = cfg.get("data") or {}
        self.cfg = cfg
        prev = previous if (previous is not None and previous.demo == demo) else None

        def same(section):
            return prev is not None and (prev.cfg.get(section) or {}) == (cfg.get(section) or {})
        self._kept = set()   # parts taken over by the next collector (not closed with this one)
        self.fields = fields or {}
        self.aliases = {k: fill_selector(v, self.fields) for k, v in (cfg.get("sensors") or {}).items()}
        self.demo = demo
        self.demo_game = demo_game
        self.source_cfg = str(data.get("source", "auto")).lower()
        self.base_interval = float(cfg.get("interval", 1.0))
        self.intervals = {k: float(v) for k, v in (cfg.get("intervals") or {}).items() if v}
        self._published, self._published_at, self._acc = {}, {}, {}
        if same("data"):    # reuses the open hardware monitor (opening it again takes seconds)
            self.lhm, self._lhm_web, self.sys, self._embedded_error = prev.lhm, prev._lhm_web, prev.sys, prev._embedded_error
            prev._kept.add("lhm")
        else:
            self.lhm, self._lhm_web = (LhmWeb(""), LhmWeb("")) if demo else make_reader(cfg, base)
            self.sys = System(data.get("net_interface"))
            self._embedded_error = None
        self.rtss = prev.rtss if prev is not None else RTSS()
        ncfg = cfg.get("network") or {}
        self.ping = None
        if same("network"):
            self.ping = prev.ping
            prev._kept.add("ping")
        elif ncfg.get("ping", True) and not demo:
            servers = ncfg.get("servers", "1.1.1.1, 8.8.8.8")
            servers = servers.split(",") if isinstance(servers, str) else servers
            self.ping = Ping(servers, ncfg.get("ping_interval", 2), ncfg.get("fails_for_outage", 3),
                             (float(ncfg.get("warn_ms", 60)), float(ncfg.get("crit_ms", 150)),
                              float(ncfg.get("warn_loss", 2)), float(ncfg.get("crit_loss", 10))))
            self.ping.start()
        mcfg = cfg.get("media") or {}
        self.media = None
        if same("media") and prev.media is not None and not demo:
            self.media = prev.media
            prev._kept.add("media")
        elif mcfg.get("enabled", True):
            from media import DemoMedia, Media
            if demo:
                self.media = DemoMedia() if demo_media else None
            else:
                self.media = Media(mcfg.get("ignore", ""))
                self.media.start()
        self.weather = None
        wcfg = cfg.get("weather") or {}
        if wcfg.get("enabled", True) and (str(wcfg.get("city") or "").strip() or demo):
            import weather
            lang = str((cfg.get("ui") or {}).get("language") or "en")
            lang = lang if lang in ("pt", "en", "es", "zh") else "en"
            if demo:
                self.weather = weather.DemoWeather(wcfg.get("unit", "celsius"))
            else:
                w = weather.Weather(wcfg.get("city"), wcfg.get("unit", "celsius"), lang,
                                    log=lambda m: self.events.append(m))
                old = getattr(prev, "weather", None)
                if old is not None and old.key() == w.key():
                    self.weather = old
                    old.log = w.log
                    prev._kept.add("weather")
                else:
                    self.weather = w.start()
        scfg = cfg.get("session") or {}
        self.summary_enabled = bool(scfg.get("summary", True))
        self.summary_seconds = float(scfg.get("summary_seconds", 15))
        self.summary_min = float(scfg.get("min_minutes", 5)) * 60
        self.session_temps = scfg.get("temperatures") or {"cpu": "cpu_temp", "gpu": "gpu_temp", "hotspot": "gpu_hotspot"}
        self.sessions = {}            # pid -> Session (one per open program)
        self._front_pid = None
        self._last_pid = None
        self.summary = None           # summary data while it is on screen
        self.last_summary = None      # the latest one, for "show again"
        self.events = []              # messages for the activity log
        fcfg = cfg.get("fps") or {}
        self.fps_source = str(fcfg.get("source", "auto")).lower()
        self.pm = None
        if same("fps") and prev.pm is not None:
            self.pm = prev.pm
            self.pm.ignore = {n.lower() for n in (fcfg.get("ignore") or IGNORE_FPS)} | {"tela.exe"}
            prev._kept.add("pm")
        elif self.fps_source in ("auto", "presentmon") and WINDOWS and not demo:
            pm = PresentMon(Path(base) / "presentmon" / "PresentMon.exe", fcfg.get("ignore"))
            pm.window = max(0.1, float(fcfg.get("average", 0.5)))
            if pm.available():
                self.pm = pm
        self.values = dict(prev.values) if prev is not None else {}
        self._hist = prev._hist if prev is not None else {}
        self._demo = prev._demo if prev is not None else {}
        if prev is not None:   # changing a setting mid-game keeps the sessions and the summary
            self.sessions, self.summary, self.last_summary = prev.sessions, prev.summary, prev.last_summary
            self._last_pid = prev._last_pid

    @property
    def source(self):
        return "embedded" if isinstance(self.lhm, LhmEmbedded) else "web"

    def close(self):
        if "lhm" not in self._kept:
            self.lhm.close()
        for name in ("pm", "ping", "media"):
            part = getattr(self, name)
            if part is not None and name not in self._kept:
                part.stop()
        if self.weather is not None and "weather" not in self._kept:
            self.weather.close()

    def weather_info(self):
        return self.weather.current() if self.weather is not None else None

    def media_info(self):
        return self.media.current() if self.media is not None else None

    def network_info(self):
        """Connection state for the 'network' widget."""
        if self.demo:
            return getattr(self, "_net_demo", {"state": "normal", "ms": 14.0, "loss": 0.0, "since": None,
                                               "gateway_ok": True, "level": "ok"})
        p = self.ping
        if p is None or p.state is None:
            return {"state": None}
        return {"state": p.state, "ms": p.ms, "loss": p.loss, "since": p.since,
                "gateway_ok": p.gateway_ok, "level": p.level()}

    @property
    def status(self):
        if self.demo:
            return {"demo": True}
        emb = isinstance(self.lhm, LhmEmbedded)
        return {"lhm": self.lhm.error, "source": self.source, "admin": self.lhm.admin if emb else is_admin(),
                "embedded_error": self._embedded_error, "fps": self.fps_info()}

    def in_game(self):
        return self.values.get("fps") is not None

    GAME_COOLDOWN = 10.0

    def game_open(self):
        """A game is running even if it is not in front: FPS now, FPS in the last seconds (alt-tab),
        or a game still open in the background (see _background_games)."""
        if self.values.get("fps") is not None:
            self._fps_seen_at = time.monotonic()
            return True
        if time.monotonic() - getattr(self, "_fps_seen_at", -1e9) < self.GAME_COOLDOWN:
            return True
        return bool(getattr(self, "_game_in_background", False))

    BACKGROUND_GAME_MINUTES = 30

    def _background_games(self, now):
        """Sessions that still count as an open game while not in front: they had FPS for 30 s or more, had
        FPS in the last half hour, and the program still has a window (minimized counts). A process left
        behind after the game closed, or a launcher hidden in the tray, no longer holds the "game" layout."""
        cands = [s for s in self.sessions.values() if s.pid != self._front_pid and len(s.fps_samples) >= 30
                 and now - s.last_fps < self.BACKGROUND_GAME_MINUTES * 60]
        if not cands:
            return []
        windows = pids_with_windows()
        return [s for s in cands if windows is None or s.pid in windows]

    def update(self):
        if self.demo:
            for name, (lo, hi) in DEMO.items():
                v = self._demo.get(name, (lo + hi) / 2)
                v = min(hi, max(lo, v + random.uniform(-0.12, 0.12) * (hi - lo)))
                self._demo[name] = v
            raw = dict(self._demo)
            if not self.demo_game:
                raw["fps"] = None
        else:
            self.lhm.read()
            # "auto": if the embedded library failed to load, use the LibreHardwareMonitor web server
            if isinstance(self.lhm, LhmEmbedded) and self.lhm.start_error and self.source_cfg == "auto":
                self._embedded_error = self.lhm.start_error
                self.lhm = self._lhm_web
                self.lhm.read()
            self.sys.read()
            if self.pm is not None:
                self.pm.read()
                if self.pm.silent_for() > 60 and (self.values.get("gpu_load") or 0) >= 25:
                    self.pm.restart("no frames for 60 s while the GPU is busy")
                if self.pm.events:
                    self.events += self.pm.events
                    self.pm.events.clear()
            if self.pm is None or self.fps_source == "auto":
                self.rtss.read()
            raw = {name: self._resolve(sel) for name, sel in self.aliases.items()}
        updated = self._apply_intervals(raw)
        self._update_sessions()
        for name in updated:   # every sensor keeps its last values, so a graph shows them as soon as it appears
            if name not in self._hist and name in self.aliases:
                self._hist[name] = deque(maxlen=120)
        for name, dq in self._hist.items():
            if name in updated or name not in self.values:
                dq.append(self.value(name))

    # ------------------------------------------------------------ game sessions
    @staticmethod
    def _alive(pid):
        try:
            return psutil.pid_exists(pid) and psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
        except Exception:  # noqa: BLE001
            return False

    @property
    def session(self):
        """Session shown on screen: the foreground game's, or the last one that was in front."""
        return self.sessions.get(self._front_pid) or self.sessions.get(self._last_pid)

    def make_summary(self, s, now=None):
        now = time.monotonic() if now is None else now
        return {
            "name": s.name, "duration": format_duration(s.duration()), "seconds": s.duration(),
            "fps_avg": s.fps_avg(), "fps_1low": s.one_percent_low(), "fps_max": s.fps_max,
            "max": {k: s.maxima.get(t) for k, t in self.session_temps.items()},
            "fps_series": downsample(s.fps_samples), "start": now, "ended_at": time.time(),
            "expires": now + 3 + self.summary_seconds, "total": self.summary_seconds,  # +3 s for the entrance
        }

    def _update_sessions(self):
        """One session per program: switching windows does not end the game that stayed open.
        The session ends (and shows the summary) when THAT process exits."""
        now = time.monotonic()
        if self.summary and now >= self.summary["expires"]:
            self.summary = None
        pm = self.pm
        game_pid = pm.pid if (pm is not None and pm.fps is not None) else None
        self._front_pid = game_pid

        if game_pid and game_pid not in self.sessions:
            exe = None
            try:
                exe = psutil.Process(game_pid).exe()
            except Exception:  # noqa: BLE001
                pass
            new = Session(game_pid, game_name(exe) if exe else Path(pm.app or "Game").stem)
            frames, new.last_arrival = pm.frames_since(game_pid, 0.0)
            new.frames(frames)
            self.sessions[game_pid] = new
            self.events.append(f"Session started: {new.name}")
        if game_pid:
            self._last_pid = game_pid

        for pid, s in list(self.sessions.items()):
            if self._alive(pid):
                continue
            del self.sessions[pid]
            self.events.append(f"Session ended: {s.name} ({format_duration(s.duration())})")
            # a real game? it stayed in front with FPS for at least 1 min (or the minimum, if lower)
            played = len(s.fps_samples) >= min(60, self.summary_min)
            if s.duration() >= self.summary_min and s.n >= 100 and played:
                summary = self.make_summary(s, now)
                self.last_summary = dict(summary)
                if self.summary_enabled:
                    self.summary = summary

        self._game_in_background = bool(self._background_games(now))
        for s in self.sessions.values():
            for t in self.session_temps.values():
                v = self.values.get(t)
                if v is not None:
                    s.maxima[t] = v if s.maxima.get(t) is None else max(s.maxima[t], v)

        current = self.sessions.get(game_pid)
        if current is not None:
            frames, current.last_arrival = pm.frames_since(current.pid, current.last_arrival)
            current.frames(frames)
            current.fps_samples.append(pm.fps)
            current.last_fps = now
            current.fps_max = pm.fps if current.fps_max is None else max(current.fps_max, pm.fps)
            self.values["fps_1low"] = one_percent_low(pm.recent_times(10))
        elif self.demo and self.demo_game:
            self.values["fps_1low"] = 96.0
        else:
            self.values["fps_1low"] = None

        shown = self.session
        for t in self.session_temps.values():
            self.values[f"{t}_max"] = shown.maxima.get(t) if shown else (
                (self.values.get(t) or 0) + 6 if self.demo and self.demo_game and self.values.get(t) else None)

    @staticmethod
    def _is_fast(sel):
        if isinstance(sel, list):
            return any(Collector._is_fast(x) for x in sel)
        return isinstance(sel, str) and (sel.startswith(("fps.", "rtss.")) or sel == "sys.volume")

    def update_fast(self):
        """Only FPS and volume (cheap to read) between full reads. Returns True if something changed."""
        fast = [n for n, sel in self.aliases.items() if self._is_fast(sel)]
        if not fast or self.demo:
            return False
        if self.pm is not None:
            self.pm.read()
        if self.pm is None or self.fps_source == "auto":
            self.rtss.read()
        self.sys.read_fast()
        changed = False
        for name in fast:
            v = self._resolve(self.aliases[name])
            old = self.values.get(name)
            if v != old:
                # FPS: ignores changes smaller than 1 frame (avoids pointless redraws)
                if v is not None and old is not None and abs(v - old) < 1:
                    continue
                self.values[name] = v
                changed = True
        return changed

    def _apply_intervals(self, raw):
        """Items with their own interval only change every N seconds, showing the average of the period.
        Returns the names that got a new value."""
        now = time.monotonic()
        values, updated = {}, set()
        for name, v in raw.items():
            iv = self.intervals.get(name, 0)
            if iv <= self.base_interval + 1e-6:
                values[name] = v
                updated.add(name)
                continue
            if v is not None:
                self._acc.setdefault(name, []).append(v)
            t = self._published_at.get(name)
            if t is None or now - t >= iv - 0.05:
                vals = self._acc.pop(name, [])
                self._published[name] = sum(vals) / len(vals) if vals else v
                self._published_at[name] = now
                updated.add(name)
            values[name] = self._published.get(name)
        # keeps values computed by the sessions (1% low, maxima) between reads
        for k in ("fps_1low",):
            if k in self.values and k not in values:
                values[k] = self.values[k]
        self.values = values
        return updated

    def _resolve(self, sel):
        if sel is None:
            return None
        if isinstance(sel, list):
            for s in sel:
                v = self._resolve(s)
                if v is not None:
                    return v
            return None
        if isinstance(sel, (int, float)):
            return float(sel)
        s = str(sel).strip()
        if s.startswith("sys."):
            return self.sys.get(s)
        if s.startswith(("rtss.", "fps.")):
            return self._fps(s)
        return self.lhm.find(s)

    def frametimes(self, seconds=2.0):
        """Frame times (ms) of the foreground game in the last 'seconds'."""
        if self.demo:
            base = 1000.0 / max(1.0, self.values.get("fps") or 120)
            n = int(seconds * 1000 / base)
            t = time.time()
            return [base * (1 + 0.08 * math.sin((t * 40 + i) * 0.7) + (1.6 if (i + int(t * 30)) % 97 == 0 else 0))
                    for i in range(n)]
        if self.pm is not None:
            return self.pm.recent_times(seconds)
        return []

    def _fps(self, key):
        """PresentMon when a game is in front; otherwise RTSS (if it is open)."""
        field = "frametime" if key.endswith("frametime") else "fps"
        if self.pm is not None and self.pm.fps is not None:
            return getattr(self.pm, field)
        if self.fps_source == "presentmon":
            return None
        return getattr(self.rtss, field)

    def fps_info(self):
        if self.pm is not None and self.pm.fps is not None:
            return {"source": "PresentMon", "running": True, "fps": self.pm.fps, "app": self.pm.app}
        if self.rtss.fps is not None and self.fps_source != "presentmon":
            return {"source": "RTSS", "running": True, "fps": self.rtss.fps, "app": self.rtss.app}
        if self.pm is not None and (self.pm.running or self.pm.alive()):
            return {"source": "PresentMon", "running": True, "fps": None, "app": None}
        if self.rtss.running:
            return {"source": "RTSS", "running": True, "fps": None, "app": None}
        error = self.pm.error if self.pm is not None else None
        return {"source": None, "running": False, "fps": None, "app": None, "error": error}

    def value(self, name):
        if name is None:
            return None
        if name in self.values:
            return self.values[name]
        if self.demo:
            return None
        v = self._resolve(name)
        self.values[name] = v
        return v

    def history(self, name, n=120):
        if name not in self._hist:
            self._hist[name] = deque(maxlen=max(int(n), 2))
        return self._hist[name]
