"""HWiNFO as an optional sensor source (Advanced › "Also read sensors from HWiNFO").

HWiNFO publishes its readings in shared memory ("Global\\HWiNFO_SENS_SM2") when "Shared Memory Support" is on in
its settings (in the free version that switch turns itself off every 12 hours). Tela! only opens what HWiNFO
created (it never creates the block, which would get in HWiNFO's way) and reads it; nothing is written.
The main values (CPU/GPU temperature, use, clock, power, fans) are picked by their names in HWiNFO and take the
place of LibreHardwareMonitor's when found; everything else still comes from LibreHardwareMonitor.
"""
import fnmatch
import struct
import sys

WINDOWS = sys.platform == "win32"
NAME = "Global\\HWiNFO_SENS_SM2"
HEADER = struct.Struct("<4sIIqIIIIII")             # packed, 44 bytes
READING = struct.Struct("<III128s128s16sdddd")     # first 316 bytes of each reading (newer versions add more)
SENSOR_NAME = struct.Struct("<II128s128s")
TYPES = {1: "temperature", 2: "voltage", 3: "fan", 4: "current", 5: "power", 6: "clock", 7: "usage", 8: "other"}

# alias -> (type, sensor name pattern, reading label patterns in order of preference); case-insensitive, * = wildcard
PICKS = {
    "cpu_temp": ("temperature", "*cpu*", ["cpu (tctl/tdie)", "cpu package", "cpu die (average)", "core max", "cpu"]),
    "cpu_load": ("usage", "*cpu*", ["total cpu usage", "cpu usage"]),
    "cpu_clock": ("clock", "*cpu*", ["core clocks (avg)", "average effective clock", "core 0 clock*", "core #0 clock*"]),
    "cpu_power": ("power", "*cpu*", ["cpu package power", "cpu ppt", "cpu power"]),
    "cpu_fan": ("fan", "*", ["cpu*", "cpu fan*", "fan1"]),
    "gpu_temp": ("temperature", "*gpu*", ["gpu temperature", "gpu core temperature", "gpu"]),
    "gpu_hotspot": ("temperature", "*gpu*", ["gpu hot spot temperature", "gpu hotspot*", "gpu junction*"]),
    "gpu_load": ("usage", "*gpu*", ["gpu core load", "gpu utilization", "gpu load"]),
    "gpu_clock": ("clock", "*gpu*", ["gpu clock", "gpu core clock", "gpu shader clock"]),
    "gpu_power": ("power", "*gpu*", ["gpu power", "total board power*", "gpu asic power", "gpu core power*"]),
    "gpu_fan": ("fan", "*gpu*", ["gpu fan*", "gpu fan1"]),
}


def _text(b):
    return b.split(b"\0", 1)[0].decode("latin-1", "replace").strip()


def parse(buf):
    """Shared-memory bytes → [{sensor, label, type, unit, value}]. Raises ValueError when it is not HWiNFO's."""
    if len(buf) < HEADER.size:
        raise ValueError("too small")
    sig, _ver, _rev, _poll, s_off, s_size, s_num, r_off, r_size, r_num = HEADER.unpack_from(buf, 0)
    if sig not in (b"HWiS", b"SiWH"):
        raise ValueError("HWiNFO is not sharing its sensors" if sig == b"DEAD" else "not HWiNFO")
    names = []
    for i in range(s_num):
        at = s_off + i * s_size
        if at + SENSOR_NAME.size > len(buf):
            break
        _sid, _inst, orig, user = SENSOR_NAME.unpack_from(buf, at)
        names.append(_text(user) or _text(orig))
    out = []
    for i in range(r_num):
        at = r_off + i * r_size
        if at + READING.size > len(buf):
            break
        kind, sidx, _rid, orig, user, unit, value, _mn, _mx, _avg = READING.unpack_from(buf, at)
        out.append({"sensor": names[sidx] if sidx < len(names) else "", "label": _text(user) or _text(orig),
                    "type": TYPES.get(kind, "other"), "unit": _text(unit), "value": value})
    return out


def pick(readings):
    """{alias: value} for the main values (only those found)."""
    out = {}
    for alias, (kind, sensor, labels) in PICKS.items():
        cands = [r for r in readings if r["type"] == kind and fnmatch.fnmatchcase(r["sensor"].lower(), sensor)]
        for pat in labels:
            hit = next((r for r in cands if fnmatch.fnmatchcase(r["label"].lower(), pat)), None)
            if hit is not None:
                v = hit["value"]
                if kind == "clock" and hit["unit"].lower() == "ghz":
                    v *= 1000.0
                if kind == "temperature" and hit["unit"].upper().endswith("F"):   # HWiNFO set to Fahrenheit
                    v = (v - 32.0) * 5.0 / 9.0
                out[alias] = v
                break
    return out


class Reader:
    """Reads HWiNFO's shared memory; `error` says why there is nothing (HWiNFO closed, sharing off...)."""

    def __init__(self):
        self.error = None
        self.count = 0

    def _bytes(self):
        import ctypes
        from ctypes import wintypes
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenFileMappingW.restype = wintypes.HANDLE
        k.OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
        k.MapViewOfFile.restype = ctypes.c_void_p
        k.MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
        k.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.VirtualQuery.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
        FILE_MAP_READ = 0x0004
        h = k.OpenFileMappingW(FILE_MAP_READ, False, NAME)
        if not h:
            raise OSError("HWiNFO is closed, or its \"Shared Memory Support\" is off")
        try:
            view = k.MapViewOfFile(h, FILE_MAP_READ, 0, 0, 0)
            if not view:
                raise OSError("could not read HWiNFO's shared memory")
            try:
                class MBI(ctypes.Structure):
                    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                                ("AllocationProtect", wintypes.DWORD), ("PartitionId", wintypes.WORD),
                                ("RegionSize", ctypes.c_size_t), ("State", wintypes.DWORD),
                                ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]
                mbi = MBI()
                k.VirtualQuery(view, ctypes.byref(mbi), ctypes.sizeof(mbi))
                head = ctypes.string_at(view, HEADER.size)
                f = HEADER.unpack(head)
                need = max(f[4] + f[5] * f[6], f[7] + f[8] * f[9], HEADER.size)
                return ctypes.string_at(view, min(need, mbi.RegionSize or need))
            finally:
                k.UnmapViewOfFile(view)
        finally:
            k.CloseHandle(h)

    def read(self):
        """{alias: value} (empty when HWiNFO is not available)."""
        if not WINDOWS:
            self.error = "Windows only"
            return {}
        try:
            readings = parse(self._bytes())
        except (OSError, ValueError, struct.error) as e:
            self.error, self.count = str(e), 0
            return {}
        self.error, self.count = None, len(readings)
        return pick(readings)
