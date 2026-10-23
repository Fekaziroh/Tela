"""Hardware detection: short CPU/GPU/RAM/VRAM names, brands and disks with their drive letters.

Read from Windows (WMI/registry) in a thread and cached in hardware.json.
"""
import json
import re
import subprocess
import sys
import threading
from pathlib import Path

PS_DETECT = r"""
$ErrorActionPreference = 'SilentlyContinue'
$disks = @()
foreach ($d in Get-CimInstance Win32_DiskDrive) {
  foreach ($p in Get-CimAssociatedInstance -InputObject $d -ResultClassName Win32_DiskPartition) {
    foreach ($l in Get-CimAssociatedInstance -InputObject $p -ResultClassName Win32_LogicalDisk) {
      $disks += [pscustomobject]@{ model = "$($d.Model)".Trim(); letter = $l.DeviceID; index = $d.Index }
    }
  }
}
$physical = @(Get-PhysicalDisk | ForEach-Object { [pscustomobject]@{ id = [int]$_.DeviceId; media = "$($_.MediaType)"; bus = "$($_.BusType)" } })
$mem = @(Get-CimInstance Win32_PhysicalMemory | Select-Object SMBIOSMemoryType, ConfiguredClockSpeed, Capacity)
$board = Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1 Name, Manufacturer
$gpus = @(Get-CimInstance Win32_VideoController | Select-Object Name, AdapterCompatibility, PNPDeviceID)
$vram = @(Get-ItemProperty 'HKLM:\SYSTEM\ControlSet001\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\0*' |
          Where-Object { $_.'HardwareInformation.qwMemorySize' } |
          ForEach-Object { [pscustomobject]@{ name = $_.DriverDesc; bytes = [int64]$_.'HardwareInformation.qwMemorySize' } })
[pscustomobject]@{ disks = $disks; physical = $physical; memory = $mem; board = $board; cpu = $cpu; gpus = $gpus; vram = $vram; system = $env:SystemDrive } |
  ConvertTo-Json -Depth 4 -Compress
"""

RAM_TYPES = {20: "DDR", 21: "DDR2", 24: "DDR3", 26: "DDR4", 30: "LPDDR4", 34: "DDR5", 35: "LPDDR5"}
BRANDS = ["amd", "intel", "nvidia", "msi", "asus", "rog", "gigabyte", "aorus", "asrock", "evga", "zotac",
          "sapphire", "powercolor", "xfx", "corsair", "kingston", "samsung", "xpg", "adata", "crucial", "wd",
          "seagate", "biostar", "nzxt", "razer", "dell", "lenovo", "hp", "acer", "pny", "palit", "gainward",
          "galax", "inno3d", "colorful", "zotac"]

# PCI subsystem vendor = who built the graphics card (the chip maker is in VEN_)
PCI_VENDORS = {
    "1462": "msi", "1043": "asus", "1458": "gigabyte", "1849": "asrock", "3842": "evga", "19da": "zotac",
    "1da2": "sapphire", "174b": "sapphire", "148c": "powercolor", "1682": "xfx", "196e": "pny", "1569": "palit",
    "10b0": "gainward", "1b4c": "galax", "7377": "colorful", "1028": "dell", "103c": "hp", "17aa": "lenovo",
    "1025": "acer", "10de": "nvidia", "1002": "amd", "8086": "intel",
}

DEFAULTS = {
    "cpu_name": "CPU", "cpu_brand": "", "gpu_name": "GPU", "gpu_brand": "", "gpu_board_brand": "",
    "ram_desc": "", "ram_speed": "", "vram_desc": "", "vram_mb": 8192, "board_brand": "", "disks": [], "disks_title": "#disks",
}


def _list(x):
    return x if isinstance(x, list) else ([x] if x else [])


def cpu_short_name(n):
    n = re.sub(r"\((R|TM|tm)\)|CPU|Processor|\d+-Core|@.*$", "", n or "").strip()
    n = re.sub(r"\s+", " ", n)
    m = re.search(r"Ryzen\s+(\d)\s+(?:PRO\s+)?(\w+)", n, re.I)
    if m:
        return f"R{m.group(1)} {m.group(2).upper()}"
    m = re.search(r"Ryzen\s+(Threadripper\s+\w+|AI\s+\d\s+\w+)", n, re.I)
    if m:
        return m.group(1)
    m = re.search(r"Core\s+(Ultra\s+\d\s+\w+|i\d-\w+)", n, re.I)
    if m:
        return m.group(1)
    return re.sub(r"^(AMD|Intel)\s+", "", n)[:16] or "CPU"


def gpu_short_name(n):
    n = re.sub(r"\((R|TM)\)|Graphics|Series", "", n or "").strip()
    n = re.sub(r"^(NVIDIA|AMD|ATI|Intel)\s+", "", n, flags=re.I)
    n = re.sub(r"^(GeForce|Radeon(?=\s+RX)|Radeon\s+(?=Pro))\s*", "", n, flags=re.I)
    return re.sub(r"\s+", " ", n).strip()[:16] or "GPU"


def disk_short_name(model):
    words = [p for p in re.split(r"[\s_]+", model or "") if p]
    drop = {"xpg", "gammix", "spectrix", "adata", "samsung", "ssd", "nvme", "wd", "wdc", "wd_black", "black", "blue",
            "green", "red", "kingston", "crucial", "sandisk", "seagate", "firecuda", "barracuda", "intel", "hp", "lexar",
            "teamgroup", "team", "netac", "patriot", "corsair", "mp600", "msi", "spatium", "solidigm", "sk", "hynix"}
    rest = [p for p in words if p.lower() not in drop and not re.fullmatch(r"\d+(\.\d+)?\s*(tb|gb)", p, re.I)]
    name = " ".join(rest) or model or "SSD"
    return name[:12].upper().rstrip(" -_.")


ALIASES = {"micro-star": "msi", "asustek": "asus", "gigabyte technology": "gigabyte", "asrock": "asrock",
           "advanced micro devices": "amd", "authenticamd": "amd", "genuineintel": "intel", "nvidia": "nvidia"}


def brand_of(text):
    t = (text or "").lower()
    for alias, brand in ALIASES.items():
        if alias in t:
            return brand
    return next((b for b in BRANDS if re.search(rf"\b{b}\b", t)), "")


def board_vendor_of(pnp_id):
    """Card maker from the PCI id, e.g. PCI\\VEN_1002&DEV_73DF&SUBSYS_39811462 -> msi."""
    m = re.search(r"SUBSYS_[0-9A-F]{4}([0-9A-F]{4})", pnp_id or "", re.I)
    return PCI_VENDORS.get(m.group(1).lower(), "") if m else ""


def build(raw):
    """Turns the PowerShell output into the dictionary used by the app."""
    info = dict(DEFAULTS)
    cpu = raw.get("cpu") or {}
    info["cpu_name"] = cpu_short_name(cpu.get("Name"))
    maker = str(cpu.get("Manufacturer", "")).lower()
    info["cpu_brand"] = "amd" if "amd" in maker else ("intel" if "intel" in maker else brand_of(cpu.get("Name")))

    gpus = [g for g in _list(raw.get("gpus")) if g.get("Name") and not re.search(r"basic|virtual|parsec", g["Name"], re.I)]
    # a dedicated card wins over integrated graphics
    gpus.sort(key=lambda g: 0 if re.search(r"rtx|gtx|rx\s?\d|arc\s+[ab]\d|radeon pro", g["Name"], re.I) else 1)
    if gpus:
        g = gpus[0]
        info["gpu_name"] = gpu_short_name(g["Name"])
        info["gpu_brand"] = brand_of(g["Name"] + " " + str(g.get("AdapterCompatibility", "")))
        maker = board_vendor_of(g.get("PNPDeviceID"))
        info["gpu_board_brand"] = maker if maker not in ("", info["gpu_brand"]) else ""
        vram = [v for v in _list(raw.get("vram")) if v.get("bytes")]
        target = next((v for v in vram if (v.get("name") or "") == g["Name"]), vram[0] if vram else None)
        if target:
            mb = int(target["bytes"]) // 2**20
            info["vram_mb"] = mb
            info["vram_desc"] = f"{round(mb / 1024)} GB"

    mem = _list(raw.get("memory"))
    if mem:
        total = sum(int(m.get("Capacity") or 0) for m in mem) / 2**30
        kind = RAM_TYPES.get(int(mem[0].get("SMBIOSMemoryType") or 0), "")
        info["ram_desc"] = f"{kind} {round(total)}GB".strip()
        speed = max(int(m.get("ConfiguredClockSpeed") or 0) for m in mem)
        info["ram_speed"] = f"{speed} MT/s" if speed else ""

    info["board_brand"] = brand_of(str((raw.get("board") or {}).get("Manufacturer", "")))

    kinds = {}
    for f in _list(raw.get("physical")):
        media, bus = str(f.get("media", "")).upper(), str(f.get("bus", "")).upper()
        kinds[f.get("id")] = "SSD" if (media in ("SSD", "4") or bus in ("NVME", "17")) else ("HD" if media in ("HDD", "3") else "")
    system = (raw.get("system") or "C:").upper()
    disks, seen = [], set()
    for d in sorted(_list(raw.get("disks")), key=lambda d: (d.get("letter", "").upper() != system, d.get("letter", ""))):
        key = d.get("index", d.get("model"))
        if key in seen or not d.get("letter"):
            continue
        seen.add(key)
        kind = kinds.get(d.get("index")) or ("SSD" if re.search(r"ssd|nvme|\bsn\d|evo|\bnv\d", d.get("model", ""), re.I) else "")
        disks.append({"model": d.get("model", ""), "name": disk_short_name(d.get("model")), "letter": d["letter"].upper(),
                      "kind": kind})
    info["disks"] = disks
    used = {d["kind"] for d in disks[:2]}
    info["disks_title"] = "SSD" if used == {"SSD"} else ("HD" if used == {"HD"} else "#disks")
    return info


def fields(info, cfg=None):
    """Values the layout can use as {name} in texts and sensor selectors."""
    t = {k: v for k, v in info.items() if not isinstance(v, (list, dict))}
    for i, d in enumerate(info.get("disks", [])[:4], start=1):
        t[f"disk{i}_name"], t[f"disk{i}_letter"], t[f"disk{i}_model"] = d["name"], d["letter"], d["model"]
    title = str(((cfg or {}).get("ssd") or {}).get("title") or "").strip()
    if title:   # the user's own title for the disks block (Settings); empty = SSD, HD or Disks by the hardware
        t["disks_title"] = title[:20]
    return t


def summary(info):
    """One line for the activity log: 'R7 5800X3D · RX 6750 XT (MSI) · ASUS · 2 SSDs'."""
    gpu = info.get("gpu_name", "GPU")
    if info.get("gpu_board_brand"):
        gpu += f" ({info['gpu_board_brand'].upper()})"
    parts = [info.get("cpu_name", "CPU"), gpu]
    if info.get("board_brand"):
        parts.append(info["board_brand"].upper())
    n = len(info.get("disks") or [])
    if n:
        parts.append(f"{n} {'disk' if n == 1 else 'disks'}")
    return " · ".join(parts)


DEMO_RAW = {"cpu": {"Name": "AMD Ryzen 7 5800X3D", "Manufacturer": "AuthenticAMD"},
            "gpus": [{"Name": "AMD Radeon RX 6750 XT", "PNPDeviceID": "PCI\\VEN_1002&DEV_73DF&SUBSYS_39811462&REV_C1"}],
            "vram": [{"name": "AMD Radeon RX 6750 XT", "bytes": 12 * 2**30}],
            "memory": [{"SMBIOSMemoryType": 26, "Capacity": 16 * 2**30, "ConfiguredClockSpeed": 3600}] * 2,
            "board": {"Manufacturer": "ASUSTeK COMPUTER INC."},
            "disks": [{"model": "XPG GAMMIX S70 BLADE", "letter": "C:", "index": 0},
                      {"model": "XPG SPECTRIX S50 LITE", "letter": "D:", "index": 1}],
            "physical": [{"id": 0, "media": "SSD"}, {"id": 1, "media": "SSD"}]}


class Detector:
    def __init__(self, folder):
        self.file = Path(folder) / "hardware.json"
        self.info = dict(DEFAULTS)
        try:
            cached = json.loads(self.file.read_text(encoding="utf-8"))
            if "cpu_name" in cached:   # caches from TelaV3 used other keys
                self.info.update(cached)
                self.cached = True
            else:
                self.cached = False
        except (OSError, ValueError):
            self.cached = False

    def detect(self):
        """Runs PowerShell (a few seconds). Returns True if something changed."""
        if sys.platform != "win32":
            return False
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", PS_DETECT],
                           capture_output=True, text=True, timeout=40, creationflags=0x08000000)
        new = build(json.loads(r.stdout or "{}"))
        if new == self.info and self.cached:
            return False
        self.info = new
        self.cached = True
        try:
            self.file.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass
        return True

    def detect_in_background(self, on_change):
        def task():
            try:
                if self.detect():
                    on_change()
            except Exception:  # noqa: BLE001
                pass
        threading.Thread(target=task, daemon=True, name="detect-hardware").start()
