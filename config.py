"""Settings file: loading, editing single values (keeping comments), updates and migration from TelaV3."""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
CONFIG = "config.yaml"
DEFAULT = "config_default.yaml"
PREVIOUS = "config.previous.yaml"


def _data_folder():
    """Where the user's files live. Installed with the setup: %APPDATA%\\Tela. Otherwise (portable, source,
    old INSTALL.bat folders): next to the program."""
    if os.environ.get("TELA_DATA"):
        return Path(os.environ["TELA_DATA"])
    if getattr(sys, "frozen", False) and (HERE / "unins000.exe").exists():
        return Path(os.environ.get("APPDATA") or Path.home()) / "Tela"
    return HERE


DATA = _data_folder()

# sections whose simple values belong to the user; the screen layout always comes from the new version
USER_SECTIONS = ("display", "colors", "data", "animation", "fps", "session", "network", "ssd", "logos", "media",
                 "ui", "tray", "eco", "background", "custom_colors", "history",
                 "updates", "performance", "alerts", "theme", "weather", "texts", "rest")


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------- editing without losing comments
def yaml_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return f"{v:g}" if isinstance(v, float) else str(v)
    t = str(v)
    if t == "" or re.search(r"[:#,\[\]{}&*!|>'\"%@`]", t) or t.strip() != t or t.lower() in ("true", "false", "null", "yes", "no", "on", "off"):
        return '"' + t.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return t


def replace_value(txt, key, value, section=None):
    """Sets 'key' inside 'section' (None = top level) to an already formatted YAML value, keeping comments.
    Creates the key (and the section) when missing."""
    lines = txt.split("\n")
    pattern = re.compile(rf"^(\s*{re.escape(key)}:[ \t]*)(\"(?:[^\"\\]|\\.)*\"|'[^']*'|[^\s#]+)?([ \t]*(#.*)?)$")
    if section is None:
        span = range(len(lines))
        start = None
    else:
        start = next((i for i, ln in enumerate(lines) if re.match(rf"^{re.escape(section)}:[ \t]*(#.*)?$", ln)), None)
        if start is None:
            return txt.rstrip("\n") + f"\n\n{section}:\n  {key}: {value}\n"
        end = next((i for i in range(start + 1, len(lines))
                    if lines[i].strip() and not lines[i][0].isspace() and not lines[i].startswith("#")), len(lines))
        span = range(start + 1, end)
    for i in span:
        line = lines[i]
        if (section is None) == line[:1].isspace():   # right indentation level
            continue
        m = pattern.match(line)
        if m:
            rest = m.group(3) or ""
            if rest.startswith("#"):
                rest = " " + rest
            lines[i] = m.group(1) + value + rest
            return "\n".join(lines)
    if start is None:
        return txt.rstrip("\n") + f"\n{key}: {value}\n"
    end = start + 1
    while end < len(lines) and (lines[end][:1].isspace() and lines[end].strip()):
        end += 1
    lines.insert(end, f"  {key}: {value}")
    return "\n".join(lines)


def replace_intervals(txt, items):
    """Rewrites the whole 'intervals:' block."""
    block = "intervals:                     # slower items (seconds); they show the average of the period\n"
    block += "".join(f"  {k}: {float(v):g}\n" for k, v in items.items()) if items else "  {}\n"
    pattern = re.compile(r"^intervals:.*\n(?:[ \t]+.*\n|[ \t]*\n(?=[ \t]+\S))*", re.M)
    if pattern.search(txt):
        return pattern.sub(lambda _m: block, txt, count=1)
    m = re.search(r"^animation:", txt, re.M) or re.search(r"^sensors:", txt, re.M)
    pos = m.start() if m else len(txt)
    return txt[:pos] + block + "\n" + txt[pos:]


class Settings:
    """The user's config.yaml, edited one value at a time."""

    def __init__(self, path):
        self.path = Path(path)

    def set(self, section, key, value):
        txt = self.path.read_text(encoding="utf-8")
        self.path.write_text(replace_value(txt, key, yaml_value(value), section), encoding="utf-8")

    def set_many(self, items):
        txt = self.path.read_text(encoding="utf-8")
        for section, key, value in items:
            txt = replace_value(txt, key, yaml_value(value), section)
        self.path.write_text(txt, encoding="utf-8")

    def set_intervals(self, base, per_item):
        txt = replace_value(self.path.read_text(encoding="utf-8"), "interval", yaml_value(float(base)))
        items = {k: v for k, v in per_item.items() if v and float(v) > float(base)}
        self.path.write_text(replace_intervals(txt, items), encoding="utf-8")


# ---------------------------------------------------------------- migration from TelaV3 (Portuguese keys)
PT_SECTIONS = {
    "tela": ("display", {"porta": "port", "orientacao": "orientation", "apagar_ao_sair": "off_on_exit",
                         "apagar_bloqueio": "off_on_lock", "apagar_monitor": "off_with_monitor",
                         "noite_ativa": "night_enabled", "noite_brilho": "night_brightness",
                         "noite_inicio": "night_start", "noite_fim": "night_end", "brilho": "brightness"}),
    "animacao": ("animation", {"ativa": "enabled", "duracao": "duration", "fps": "fps"}),
    "dados": ("data", {"fonte": "source", "lhm_url": "lhm_url", "intervalo_discos": "disk_interval",
                       "controladoras": "controllers", "rede_interface": "net_interface"}),
    "fps": ("fps", {"atualizacao": "update", "media": "average", "fonte": "source"}),
    "sessao": ("session", {"resumo": "summary", "resumo_segundos": "summary_seconds", "minimo_minutos": "min_minutes"}),
    "rede": ("network", {"ping": "ping", "servidores": "servers", "intervalo_ping": "ping_interval",
                         "falhas_queda": "fails_for_outage", "alerta_ms": "warn_ms", "critico_ms": "crit_ms",
                         "alerta_perda": "warn_loss", "critico_perda": "crit_loss"}),
    "ssd": ("ssd", {"numero": "number"}),
    "cores": ("colors", {"fundo": "background", "painel": "panel", "texto": "text", "secundario": "secondary",
                         "trilho": "track", "destaque": "accent", "alerta": "warn", "critico": "crit"}),
    "logos": ("logos", {"modo": "mode", "arquivos": "files", "cor": "color", "troca_a_cada": "switch_every",
                        "transicao": "fade"}),
    "midia": ("media", {"ativa": "enabled", "ignorar": "ignore"}),
}
PT_VALUES = {
    ("display", "orientation"): {"paisagem": "landscape", "paisagem_invertida": "landscape_flipped",
                                 "retrato": "portrait", "retrato_invertido": "portrait_flipped"},
    ("data", "source"): {"embutido": "embedded"},
    ("ssd", "number"): {"atividade": "activity", "espaco": "space"},
    ("logos", "mode"): {"lista": "list"},
    ("logos", "color"): {"branco": "white"},
}
PT_SENSORS = {"rede_down": "net_down", "rede_up": "net_up", "disco1": "disk1", "disco2": "disk2", "disco_c": "disk1",
              "disco_d": "disk2", "disco1_ativ": "disk1_act", "disco2_ativ": "disk2_act", "cpu_uso": "cpu_load",
              "gpu_uso": "gpu_load", "ram_usada_gb": "ram_used_gb"}


def is_portuguese(cfg):
    return "tela" in cfg or any(isinstance(w, dict) and "tipo" in w for w in cfg.get("widgets") or [])


def user_values(cfg):
    """[(section, key, value)] of simple values to carry over, in English keys."""
    out = []
    if is_portuguese(cfg):
        for pt_section, (section, keys) in PT_SECTIONS.items():
            for pt_key, v in (cfg.get(pt_section) or {}).items():
                if pt_key in keys and v is not None and not isinstance(v, (list, dict)):
                    key = keys[pt_key]
                    v = PT_VALUES.get((section, key), {}).get(v, v) if isinstance(v, str) else v
                    out.append((section, key, v))
        interval = cfg.get("intervalo")
        intervals = {PT_SENSORS.get(k, k): v for k, v in (cfg.get("intervalos") or {}).items()}
    else:
        for section in USER_SECTIONS:
            for key, v in (cfg.get(section) or {}).items():
                if v is not None and not isinstance(v, (list, dict)):
                    out.append((section, key, v))
        interval = cfg.get("interval")
        intervals = dict(cfg.get("intervals") or {})
    if isinstance(interval, (int, float)):
        out.append((None, "interval", interval))
    return out, {k: v for k, v in intervals.items() if isinstance(v, (int, float))}


def merge(default_txt, cfg):
    """Default text with the user's choices written in."""
    values, intervals = user_values(cfg)
    txt = default_txt
    for section, key, v in values:
        txt = replace_value(txt, key, yaml_value(v), section)
    if intervals or "intervals" in cfg or "intervalos" in cfg:
        txt = replace_intervals(txt, intervals)
    if cfg and "theme" not in cfg:   # from 1.4.5 or older: keep the screen as it was and tell about the new themes
        txt = replace_value(txt, "name", "full", "theme")
        txt = replace_value(txt, "notice", "true", "theme")
    return txt


def _task_folder(name):
    """Folder of the program started by a Windows scheduled task (TelaV3/TelaV2), if it exists."""
    if sys.platform != "win32":
        return None
    try:
        r = subprocess.run(["schtasks", "/Query", "/TN", name, "/XML"], capture_output=True, text=True,
                           creationflags=0x08000000, timeout=10)
        m = re.search(r"<WorkingDirectory>(.*?)</WorkingDirectory>", r.stdout or "") or \
            re.search(r"<Command>(.*?)</Command>", r.stdout or "")
        if m:
            p = Path(m.group(1).strip().strip('"'))
            return p if p.is_dir() else p.parent
    except Exception:  # noqa: BLE001
        pass
    return None


def find_old_install(here):
    """Most recently used older copy (folder copies of Tela 3.9, TelaV3, TelaV2) with a config.yaml,
    other than this folder and the data folder."""
    import os
    here = Path(here).resolve()
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    places = [_task_folder("Tela"), _task_folder("TelaV3"), _task_folder("TelaV2")]
    for root in (Path("C:/"), home, home / "Desktop", home / "Downloads", home / "Documents", here.parent):
        for name in ("Tela", "TelaV3", "TelaV2", "Telinha"):
            places.append(root / name)
        try:
            places += [p for p in root.glob("Tela*") if p.is_dir()]
        except OSError:
            pass
    skip = {here}
    try:
        skip.add(DATA.resolve())
    except OSError:
        pass
    found = []
    for p in places:
        try:
            if p and (p / CONFIG).is_file() and p.resolve() not in skip and not (p / "unins000.exe").exists():
                found.append(p.resolve())
        except OSError:
            continue
    if not found:
        return None
    return max(set(found), key=lambda p: (p / CONFIG).stat().st_mtime)


def prepare(folder=None, search_old=True, program=None):
    """Install/update: creates config.yaml from the default or updates the existing one keeping the user's
    choices. 'folder' = data folder (default DATA); the default file comes from 'program' (default HERE,
    or 'folder' when only that is given). Returns (message, old_folder_or_None)."""
    folder = Path(folder or DATA)
    program = Path(program or (folder if program is None and folder != DATA else HERE))
    folder.mkdir(parents=True, exist_ok=True)
    user, default = folder / CONFIG, program / DEFAULT
    if not default.exists():
        return "config_default.yaml is missing", None
    txt = default.read_text(encoding="utf-8")
    old = None
    source = user if user.exists() else None
    if source is None and (program / CONFIG).exists() and program.resolve() != folder.resolve():
        source = program / CONFIG          # the setup was installed over a portable folder
    if source is None and search_old:
        old = find_old_install(program)
        source = old / CONFIG if old else None
    if source is None:
        user.write_text(txt, encoding="utf-8")
        return "settings created", None
    try:
        cfg = load(source)
    except Exception:  # noqa: BLE001 — broken file: keep a copy and start from the default
        if source == user:
            user.replace(folder / PREVIOUS)
        user.write_text(txt, encoding="utf-8")
        return "settings file was damaged: recreated (copy in config.previous.yaml)", old
    merged = merge(txt, cfg)
    if source == user:
        shutil.copyfile(user, folder / PREVIOUS)
    user.write_text(merged, encoding="utf-8")
    if source.parent != folder:
        copied = copy_from_old(source.parent, folder, program)
        if old:
            return f"settings imported from {old}" + (f" ({copied} logos copied)" if copied else ""), old
        return "settings imported", None
    return ("settings migrated from TelaV3" if is_portuguese(cfg) else "settings updated, your choices were kept"), None


def copy_from_old(old, new, program=None):
    """Brings over what the old version already has: the user's own logos and the downloaded components
    (hardware monitor and PresentMon), so they are not downloaded again. Returns how many logos were copied."""
    for part in ("lhm", "presentmon"):
        src, dst = Path(old) / part, Path(program or new) / part
        if src.is_dir() and not dst.exists():
            try:
                shutil.copytree(src, dst)
            except OSError:
                shutil.rmtree(dst, ignore_errors=True)
    src, dst = Path(old) / "logos", Path(new) / "logos"
    if not src.is_dir():
        return 0
    dst.mkdir(exist_ok=True)
    n = 0
    for f in src.iterdir():
        if f.is_file() and not (dst / f.name).exists():
            try:
                shutil.copy2(f, dst / f.name)
                n += 1
            except OSError:
                pass
    return n
