"""Functions the window calls (pywebview js_api, or the local HTTP bridge in the browser fallback).

Every public method returns plain JSON-friendly data. Attributes start with '_' so pywebview does not
expose them to the page.
"""
import base64
import io
import json
import re
import shutil
import threading
import time
from pathlib import Path

import psutil

import config
import winsys
from display import list_ports
from engine import HERE, VERSION, system_language
from render import DEFAULT_COLORS, Renderer

NOT_FOR_INTERVALS = {"fps", "volume"}
UI_ONLY = {("ui", "theme"), ("tray", "temp_icon")}


def _png_data_url(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=False, compress_level=1)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _read_version(folder):
    for name in ("version.txt", "versao.txt"):
        try:
            return (HERE / folder / name).read_text(encoding="utf-8").strip()
        except OSError:
            continue
    return None


class Api:
    def __init__(self, app):
        self._app = app
        self._reload_timer = None
        self._lock = threading.Lock()
        self._thumbs = {}
        self._proc = psutil.Process()
        self._proc.cpu_percent(None)
        self._child_cpu = {}

    # ------------------------------------------------------------ helpers
    @property
    def _engine(self):
        return self._app.engine

    @property
    def _settings(self):
        return config.Settings(self._app.cfg_path)

    def _cfg(self):
        try:
            return config.load(self._app.cfg_path)
        except Exception:  # noqa: BLE001
            return self._engine.cfg

    def _schedule_reload(self):
        """Several quick changes (sliders, typing) end in a single reload."""
        with self._lock:
            if self._reload_timer is not None:
                self._reload_timer.cancel()
            self._reload_timer = threading.Timer(0.6, lambda: self._engine.command("reload"))
            self._reload_timer.daemon = True
            self._reload_timer.start()

    # ------------------------------------------------------------ startup data
    def init(self):
        cfg = self._cfg()
        sensors = [k for k in (self._engine.cfg.get("sensors") or {}) if k not in NOT_FOR_INTERVALS]
        info = self._engine.hw.info
        return {
            "version": VERSION, "system_language": system_language(), "windows": winsys.WINDOWS,
            "demo": self._engine.demo, "settings": self._user_settings(cfg), "sensors": sensors,
            "ports": [{"device": d, "label": lbl} for d, lbl in list_ports()],
            "autostart": winsys.starts_with_windows(), "default_colors": DEFAULT_COLORS,
            "disks": [{"letter": d["letter"], "name": d["name"], "kind": d["kind"]} for d in info.get("disks", [])],
            "folder": str(config.DATA),
            "themes": self._load_themes(),
            "updated_from": self._updated_from(),
        }

    @staticmethod
    def _updated_from():
        try:
            return (config.DATA / "updated_from.txt").read_text(encoding="utf-8").strip() or None
        except OSError:
            return None

    def news_seen(self):
        """The "what's new" window was shown after an update."""
        (config.DATA / "updated_from.txt").unlink(missing_ok=True)
        return True

    # ------------------------------------------------------------ updates
    def update_check(self):
        up = getattr(self._app, "updater", None)
        return up.check() if up else None

    def open_release_page(self):
        import webbrowser
        from updater import PAGE
        up = getattr(self._app, "updater", None)
        webbrowser.open((up.info or {}).get("page", PAGE) if up else PAGE)
        return True

    def update_install(self):
        up = getattr(self._app, "updater", None)
        if not up:
            return False
        return up.install(lambda: threading.Thread(target=self._app.quit, daemon=True).start())

    @staticmethod
    def _user_settings(cfg):
        keep = tuple(config.USER_SECTIONS) + ("intervals",)   # every section the user can change
        out = {k: {kk: vv for kk, vv in (cfg.get(k) or {}).items() if not isinstance(vv, list)} for k in keep}
        out["interval"] = cfg.get("interval", 1.0)
        return out

    # ------------------------------------------------------------ live state
    def state(self, since=-1):
        if getattr(self._app, "visible", True) is False:
            return {"hidden": True}
        e = self._engine
        st = e.status()
        c = e.collector
        out = {"status": st, "frame_no": e.frame_no, "log": list(e.log.lines)[-120:], "log_count": e.log.count}
        if e.frame_no != since and e.last_frame is not None:
            out["frame"] = _png_data_url(e.last_frame)
        net = c.network_info() if c else {"state": None}
        out["network"] = {k: net.get(k) for k in ("state", "ms", "loss", "since", "gateway_ok", "level")}
        m = c.media_info() if c else None
        from media import progress
        out["media"] = {"title": m["title"], "artist": m["artist"], "app": m.get("app"), "progress": progress(m)} if m else None
        out["media_error"] = getattr(c.media, "error", None) if (c and c.media) else None
        out["media_enabled"] = bool(c and c.media is not None)
        last = e.last_summary
        out["last_game"] = {k: last.get(k) for k in ("name", "duration", "fps_avg", "fps_1low", "fps_max", "max", "ended_at")} if last else None
        out["hardware"] = self._hardware_line()
        out["usage"] = self._usage_total()
        out["disks"] = [{"letter": d["letter"], "name": d["name"], "kind": d["kind"]}
                        for d in e.hw.info.get("disks", [])]   # detection finishes after the window opens
        out["temps"] = {"cpu": e.value("cpu_temp"), "gpu": e.value("gpu_temp")}
        up = getattr(self._app, "updater", None)
        out["update"] = up.snapshot() if up else None
        return out

    def _hardware_line(self):
        from hardware import summary
        return summary(self._engine.hw.info)

    def _usage_total(self):
        now = time.monotonic()
        if now - getattr(self, "_usage_at", 0) > 2:
            u = self.usage()
            self._usage_cache = {"cpu": round(sum(v["cpu"] for v in u.values()), 1),
                                 "ram_mb": sum(v["ram_mb"] for v in u.values())}
            self._usage_at = now
        return self._usage_cache

    # ------------------------------------------------------------ window themes
    @staticmethod
    def _themes_file():
        return config.DATA / "themes.json"

    def _load_themes(self):
        try:
            data = json.loads(self._themes_file().read_text(encoding="utf-8"))
            return [x for x in data if isinstance(x, dict) and x.get("name") and isinstance(x.get("colors"), dict)]
        except (OSError, ValueError):
            return []

    def save_theme(self, name, colors):
        name = str(name).strip()[:30] or "Tema"
        clean = {k: str(v)[:7] for k, v in (colors or {}).items() if re.fullmatch(r"#[0-9a-fA-F]{6}", str(v))}
        themes = [x for x in self._load_themes() if x["name"] != name] + [{"name": name, "colors": clean}]
        self._themes_file().write_text(json.dumps(themes, ensure_ascii=False, indent=1), encoding="utf-8")
        return themes

    def delete_theme(self, name):
        themes = [x for x in self._load_themes() if x["name"] != name]
        self._themes_file().write_text(json.dumps(themes, ensure_ascii=False, indent=1), encoding="utf-8")
        return themes

    def set_tray_accent(self, color):
        if re.fullmatch(r"#[0-9a-fA-F]{6}", str(color)):
            self._app.set_tray_accent(color)
        return True

    def usage(self):
        """CPU/RAM used by Tela itself, its window (WebView2) and PresentMon."""
        groups = {"app": [0.0, 0], "window": [0.0, 0], "presentmon": [0.0, 0]}
        try:
            procs = [self._proc] + self._proc.children(recursive=True)
        except Exception:  # noqa: BLE001
            procs = [self._proc]
        ncpu = psutil.cpu_count() or 1
        for p in procs:
            try:
                name = p.name().lower()
                key = "presentmon" if "presentmon" in name else ("window" if "webview" in name else "app")
                if p.pid == self._proc.pid:
                    cpu = p.cpu_percent(None)
                else:
                    if p.pid not in self._child_cpu:
                        self._child_cpu[p.pid] = p
                        p.cpu_percent(None)
                    cpu = self._child_cpu[p.pid].cpu_percent(None)
                groups[key][0] += cpu / ncpu
                groups[key][1] += p.memory_info().rss
            except Exception:  # noqa: BLE001
                continue
        return {k: {"cpu": round(v[0], 1), "ram_mb": round(v[1] / 2**20)} for k, v in groups.items()}

    # ------------------------------------------------------------ settings
    def set(self, section, key, value):
        section = section or None
        self._settings.set(section, key, value)
        if (section, key) == ("display", "brightness"):
            self._engine.command("brightness", int(value))
        elif (section, key) == ("display", "orientation"):
            self._engine.command("orientation", value)
        elif (section, key) not in UI_ONLY:
            self._schedule_reload()
        self._app.settings_changed(section, key, value)
        return True

    def set_many(self, items):
        self._settings.set_many([(s or None, k, v) for s, k, v in items])
        self._schedule_reload()
        return True

    def preview_brightness(self, value):
        """While the slider moves: changes the screen without saving."""
        self._engine.command("brightness", int(value))
        return True

    def set_intervals(self, base, items):
        self._settings.set_intervals(float(base), {k: float(v) for k, v in items.items()})
        self._schedule_reload()
        return True

    def reset_colors(self):
        self._settings.set_many([("colors", k, v) for k, v in DEFAULT_COLORS.items()])
        self._schedule_reload()
        return DEFAULT_COLORS

    SCREEN_THEMES = {
        "dark": dict(DEFAULT_COLORS),
        "light": {"background": "#D9DEE4", "panel": "#F5F7F9", "text": "#111418", "secondary": "#5B6470", "track": "#C5CBD3",
                  "accent": "#111418", "warn": "#C77700", "crit": "#D6342C"},
        "red": {"background": "#120406", "panel": "#2A0A0D", "text": "#FFFFFF", "secondary": "#C9A3A6", "track": "#4A1B20",
                "accent": "#ED1C24", "warn": "#FFB340", "crit": "#FF453A"},
        "ice": {"background": "#05080C", "panel": "#0D1620", "text": "#EAF6FF", "secondary": "#7E93A8", "track": "#1E2D3D",
                "accent": "#8FD3FF", "warn": "#FFB340", "crit": "#FF5A52"},
    }

    def screen_theme(self, name):
        if name == "custom":   # the user's own colors, kept apart from the ready-made themes
            cfg = self._cfg()
            colors = {**DEFAULT_COLORS, **(cfg.get("colors") or {}), **(cfg.get("custom_colors") or {})}
        else:
            colors = self.SCREEN_THEMES.get(name)
        if not colors:
            return False
        self._settings.set_many([("colors", k, v) for k, v in colors.items()])
        self._schedule_reload()
        return colors

    def set_screen_color(self, key, value):
        """Editing a color edits the custom theme: the screen switches to it, the presets stay untouched."""
        cfg = self._cfg()
        custom = {**DEFAULT_COLORS, **(cfg.get("colors") or {}), **(cfg.get("custom_colors") or {})}
        if not (cfg.get("custom_colors") or {}):
            custom = {**DEFAULT_COLORS, **(cfg.get("colors") or {})}   # first edit starts from what is on screen
        custom[key] = value
        self._settings.set_many([("custom_colors", k, v) for k, v in custom.items()] +
                                [("colors", k, v) for k, v in custom.items()])
        self._schedule_reload()
        return custom

    def screen_themes(self):
        return self.SCREEN_THEMES

    def pick_background(self):
        paths = self._app.pick_images()
        if not paths:
            return None
        src = Path(paths[0])
        folder = config.DATA / "backgrounds"
        folder.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, folder / src.name)
        except OSError as e:
            self._engine.log(f"Could not copy {src.name}: {e}")
            return None
        rel = f"backgrounds/{src.name}"
        self._settings.set("background", "image", rel)
        self._schedule_reload()
        return rel

    def set_autostart(self, on):
        try:
            winsys.set_start_with_windows(bool(on))
            self._engine.log("Starts with Windows" if on else "No longer starts with Windows")
        except Exception as e:  # noqa: BLE001
            self._engine.log(f"Could not change start with Windows: {e}")
        return winsys.starts_with_windows()

    def ports(self):
        return [{"device": d, "label": lbl} for d, lbl in list_ports()]

    # ------------------------------------------------------------ commands
    def command(self, name, value=None):
        allowed = {"pause", "test", "summary_example", "summary_last", "reload"}
        if name not in allowed:
            return False
        if name == "pause":
            value = not self._engine.paused if value is None else bool(value)
            self._engine.paused = value   # shows at once; the engine confirms right after
        self._engine.command(name, value)
        return True

    def open_folder(self):
        winsys.open_path(config.DATA)
        return True

    def edit_config(self):
        if winsys.WINDOWS:
            import subprocess
            subprocess.Popen(["notepad.exe", str(self._app.cfg_path)])
        else:
            winsys.open_path(self._app.cfg_path)
        return True

    def copy(self, text):
        return winsys.copy_to_clipboard(text)

    def quit(self):
        threading.Timer(0.1, self._app.quit).start()
        return True

    def hide(self):
        self._app.hide_window()
        return True

    def uninstall(self, delete_data=False):
        winsys.uninstall(self._engine.log, bool(delete_data))
        threading.Timer(0.2, self._app.quit).start()
        return True

    # ------------------------------------------------------------ game history
    def history_list(self):
        import history
        cfg = self._cfg()
        return {"games": history.entries(cfg), "folder": str(history.folder(cfg))}

    def history_get(self, gid):
        import history
        return history.get(self._cfg(), gid)

    def history_delete(self, ids):
        import history
        n = history.delete(self._cfg(), list(ids))
        self._engine.log(f"{n} game(s) deleted from the history")
        return n

    def history_show(self, gid):
        import history
        g = history.get(self._cfg(), gid)
        if g:
            self._engine.command("summary_show", g)
        return bool(g)

    def history_export(self):
        import history
        path = self._app.pick_save_path("tela-games.csv")
        if not path:
            return None
        Path(path).write_text(history.to_csv(self._cfg()), encoding="utf-8-sig")
        return path

    def history_folder(self):
        import history
        d = history.folder(self._cfg())
        d.mkdir(parents=True, exist_ok=True)
        winsys.open_path(d)
        return True

    def history_choose_folder(self):
        import history
        new = self._app.pick_folder()
        if not new:
            return None
        cfg = self._cfg()
        history.move(cfg, new)
        self._settings.set("history", "folder", str(new))
        self._schedule_reload()
        return str(new)

    # ------------------------------------------------------------ old version (first-run assistant)
    def old_install(self):
        old = config.find_old_install(HERE)
        return str(old) if old else None

    def remove_old(self, path):
        """Deletes the old TelaV3 folder. Only the folder found by old_install, never anything else."""
        old = config.find_old_install(HERE)
        if not old or Path(path).resolve() != old or old in (HERE.resolve(), config.DATA.resolve()):
            return False
        winsys.remove_old_versions()
        shutil.rmtree(old, ignore_errors=True)
        self._engine.log(f"Old version folder removed: {old}")
        return not old.exists()

    # ------------------------------------------------------------ layout editor
    def _family(self):
        import layout
        return layout.family((self._cfg().get("display") or {}).get("orientation"))

    def layout_get(self):
        import layout
        fam = self._family()
        lay = layout.load(fam)
        size = lay.get("size") or ([320, 480] if fam == "portrait" else [480, 320])
        return {"family": fam, "size": size, "groups": lay.get("groups") or [], "custom": lay.get("custom", False),
                "sensors": self.sensor_values(), "kinds": list(layout.BLOCK_KINDS)}

    def sensor_values(self):
        """Configured sensors with their value now (for the picker)."""
        import layout
        c = self._engine.collector
        lay = layout.load(self._family())
        out = []
        for name in (lay.get("sensors") or {}):
            v = c.values.get(name) if c else None
            out.append({"name": name, "value": None if v is None else round(float(v), 2)})
        return out

    def layout_save(self, groups):
        import layout
        fam = self._family()
        lay = layout.load(fam)
        layout.save(fam, {"size": lay.get("size"), "sensors": lay.get("sensors"), "groups": groups})
        self._engine.command("reload")
        return True

    def layout_reset(self):
        import layout
        layout.reset(self._family())
        self._engine.command("reload")
        self._engine.log("Layout restored to the default")
        return self.layout_get()

    def layout_new_block(self, kind, x=10, y=10, sensor=None):
        import layout
        return layout.new_block(kind, int(x), int(y), sensor)

    def add_sensor(self, selector, groups=None):
        """Adds a sensor from the full list (e.g. 'gpu|voltage|GPU Core') and returns its name."""
        import layout
        fam = self._family()
        lay = layout.load(fam)
        sensors = dict(lay.get("sensors") or {})
        for name, sel in sensors.items():
            if sel == selector:
                return name
        base = re.sub(r"[^a-z0-9]+", "_", selector.split("|")[-1].lower()).strip("_")[:24] or "sensor"
        name, i = base, 2
        while name in sensors:
            name, i = f"{base}_{i}", i + 1
        sensors[name] = selector
        layout.save(fam, {"size": lay.get("size"), "sensors": sensors, "groups": groups or lay.get("groups")})
        self._engine.command("reload")
        return name

    # ------------------------------------------------------------ logos
    def logos(self):
        cfg = self._cfg()
        r = Renderer(cfg, 480, 320, base=config.DATA, fields=self._renderer_fields(), logo_dirs=self._logo_dirs())
        white = str((cfg.get("logos") or {}).get("color", "white")).lower() == "white"
        auto = [Path(p).name for p in r.logo_list("auto")]
        items = []
        for name, path in r.available_logos().items():
            items.append({"name": name, "label": Path(name).stem.replace(" Logo", "").replace("_", " "),
                          "thumb": self._thumb(path, white)})
        if not items:
            auto = r.brand_names()
        lc = cfg.get("logos") or {}
        files = lc.get("files", "")
        files = [n.strip() for n in (files.split(",") if isinstance(files, str) else files) if n and n.strip()]
        return {"items": items, "auto": auto, "files": files}

    def _renderer_fields(self):
        from hardware import fields
        return fields(self._engine.hw.info)

    @staticmethod
    def _logo_dirs():
        return [config.DATA / "logos", HERE / "logos"]

    def _thumb(self, path, white):
        path = Path(path)
        try:
            key = (str(path), path.stat().st_mtime, white)
        except OSError:
            return None
        if key not in self._thumbs:
            from PIL import Image
            try:
                im = Image.open(path).convert("RGBA")
                if white:
                    im = Renderer.tint(im, "#FFFFFF")
                box = im.getchannel("A").getbbox()
                if box:
                    im = im.crop(box)
                im.thumbnail((240, 44), Image.LANCZOS)
                self._thumbs[key] = _png_data_url(im)
            except Exception:  # noqa: BLE001
                self._thumbs[key] = None
        return self._thumbs[key]

    def add_logos(self):
        paths = self._app.pick_images()
        folder = config.DATA / "logos"
        folder.mkdir(exist_ok=True)
        added = 0
        for p in paths or []:
            try:
                shutil.copy2(p, folder / Path(p).name)
                added += 1
            except OSError as e:
                self._engine.log(f"Could not copy {Path(p).name}: {e}")
        if added:
            self._engine.log(f"{added} logo(s) added")
        return self.logos()

    def open_logos_folder(self):
        folder = config.DATA / "logos"
        folder.mkdir(exist_ok=True)
        winsys.open_path(folder)
        return True

    # ------------------------------------------------------------ tools
    def sensors(self):
        from cli import sensor_rows
        c = self._engine.collector
        reader = c.lhm if (c is not None and not c.demo and c.lhm.sensors) else None
        if c is not None and c.demo:
            return {"rows": [], "notes": ["demo"]}
        rows, notes = sensor_rows(self._engine.cfg, reader)
        return {"rows": [{"hardware": h, "selector": s, "value": v} for h, s, v in rows], "notes": notes}

    def diagnostics(self):
        e = self._engine
        st = e.status()
        cfg = self._cfg()
        lines = [f"Tela! {VERSION} — diagnostics {time.strftime('%Y-%m-%d %H:%M')}",
                 f"System: {winsys.windows_version()} · administrator: {'yes' if st.get('admin') else 'no'}",
                 f"WebView2: {winsys.webview2_version() or 'not found'} · window: {self._app.window_kind}",
                 f"Folders: program {HERE} · data {config.DATA}"]
        scr = e.screen
        state = "paused" if st["paused"] else ("connected" if st["connected"] else f"not connected ({st.get('screen_error') or 'connecting'})")
        lines.append(f"Screen: {state} · port {st.get('port') or (cfg.get('display') or {}).get('port')} · "
                     f"{getattr(scr, 'orientation', '?')} · brightness {getattr(scr, 'brightness', '?')}%"
                     + (f" · off: {', '.join(st['sleeping'])}" if st["sleeping"] else ""))
        ports = list_ports()
        lines.append("Ports: " + (", ".join(f"{d} ({lbl})" for d, lbl in ports) or "none"))
        c = e.collector
        n = len(getattr(c.lhm, "sensors", []) or []) if c else 0
        lines.append(f"Sensors: {st.get('source')} · LibreHardwareMonitor {_read_version('lhm') or '?'} · {n} sensors"
                     + (f" · error: {st['lhm_error']}" if st.get("lhm_error") else "")
                     + (f" · embedded failed: {st['embedded_error']}" if st.get("embedded_error") else ""))
        f = st.get("fps") or {}
        lines.append(f"FPS: {f.get('source') or 'none'} · PresentMon {_read_version('presentmon') or 'not installed'}"
                     + (f" · {f['fps']:.0f} FPS in {f.get('app')}" if f.get("fps") else "")
                     + (f" · error: {f['error']}" if f.get("error") else ""))
        if c and c.media is not None:
            lines.append(f"Media: {'error: ' + c.media.error if c.media.error else 'ok'}"
                         + (f" · playing {c.media.info.get('app')}" if c.media.info else ""))
        else:
            lines.append("Media: off")
        net = c.network_info() if c else {}
        if net.get("state"):
            lines.append(f"Network: {net['state']} · {net.get('ms') or '--'} ms · loss {net.get('loss') or 0:.0f}% · "
                         f"router {'ok' if net.get('gateway_ok') else ('no reply' if net.get('gateway_ok') is False else '?')}")
        lines.append("Hardware: " + self._hardware_line())
        u = self.usage()
        lines.append("Usage: " + " · ".join(f"{k} {v['cpu']}% CPU {v['ram_mb']} MB" for k, v in u.items() if v["ram_mb"]))
        lines.append(f"Eco mode: {'on' if st.get('eco') else 'off'}")
        try:
            default = config.load(HERE / config.DEFAULT)
            changed = [f"{s}.{k}={v}" for s, k, v in config.user_values(cfg)[0]
                       if (default.get(s) or {}).get(k) != v and s is not None]
            lines.append("Changed settings: " + (", ".join(changed) or "none"))
        except Exception:  # noqa: BLE001
            pass
        lines.append("")
        lines.append("--- activity log")
        lines += list(e.log.lines)[-80:]
        return "\n".join(lines)
