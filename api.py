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
UI_ONLY = {("ui", "theme"), ("tray", "temp_icon"), ("ui", "reflow"), ("ui", "unload_hidden"), ("ui", "guard")}


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
            "recovered": bool(getattr(self._app, "recovered", False)),
        }

    @staticmethod
    def _updated_from():
        try:
            return (config.DATA / "updated_from.txt").read_text(encoding="utf-8").strip() or None
        except OSError:
            return None

    def recovered_seen(self):
        self._app.recovered = False
        return True

    @staticmethod
    def _theme_imported():
        """A theme opened with a double click (Tela.exe --import-theme): its id, once."""
        p = config.DATA / "theme_imported.txt"
        try:
            tid = p.read_text(encoding="utf-8").strip()
            p.unlink()
            return tid or None
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

    def screen_apps(self):
        """Known programs for these screens running now (the first-run assistant warns about them)."""
        return sorted({n for _, n in winsys.screen_apps()}) if winsys.WINDOWS else []

    def close_conflict(self):
        """Closes the known program that holds the screen so Tela! can use it."""
        fn = getattr(self._app, "close_conflict", None)
        return fn() if fn else 0

    def open_url(self, url):
        """Opens one of the project's own pages in the browser (nothing else)."""
        import webbrowser
        if str(url).startswith("https://github.com/Fekaziroh/Tela"):
            webbrowser.open(url)
            return True
        return False

    def open_release_page(self):
        import webbrowser
        from updater import PAGE
        up = getattr(self._app, "updater", None)
        webbrowser.open((up.info or {}).get("page", PAGE) if up else PAGE)
        return True

    def update_releases(self):
        up = getattr(self._app, "updater", None)
        try:
            return {"releases": up.releases() if up else [], "current": VERSION,
                    "skip": (self._cfg().get("updates") or {}).get("skip") or ""}
        except Exception as e:  # noqa: BLE001
            return {"error": f"{type(e).__name__}: {e}"}

    def update_install_version(self, version, skip_current=True):
        """Installs a chosen release (usually an older one); optionally stops offering the current version."""
        up = getattr(self._app, "updater", None)
        if not up:
            return False
        info = next((r for r in up.releases() if r["version"] == version), None)
        if not info:
            return False
        if skip_current:
            self.set("updates", "skip", VERSION)
        else:   # going to the skipped version (or a newer one) means it is wanted again
            from updater import newer
            sk = str((self._cfg().get("updates") or {}).get("skip") or "")
            if sk and not newer(sk, version):
                self.set("updates", "skip", "")
        self._engine.log(f"Going to version {version}")
        return up.install(lambda: threading.Thread(target=self._app.quit, daemon=True).start(), info)

    def update_unskip(self):
        self.set("updates", "skip", "")
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
        self._page_seen = time.monotonic()   # the page is alive (the guard process asks for this)
        if getattr(self._app, "visible", True) is False:
            return {"hidden": True}
        e = self._engine
        st = e.status()
        c = e.collector
        out = {"status": st, "frame_no": e.frame_no, "log": list(e.log.lines)[-120:], "log_count": e.log.count}
        preview = bool((e.cfg.get("performance") or {}).get("preview", True)) or getattr(self, "_peek", 0) > time.time()
        out["preview"] = preview
        if preview and e.frame_no != since and e.last_frame is not None:
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
        out["conflict"] = sorted({n for _, n in getattr(self._app, "conflict", [])})
        out["theme_imported"] = self._theme_imported()
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

    def set_title_bar(self, caption, text, dark):
        hexes = all(re.fullmatch(r"#[0-9a-fA-F]{6}", str(c)) for c in (caption, text))
        if hexes and hasattr(self._app, "set_title_bar"):
            self._app.set_title_bar(caption, text, bool(dark))
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
        else:   # no reload for these, but the tray and the window read them from the running settings
            self._engine.cfg.setdefault(section, {})[key] = value
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

    # ------------------------------------------------------------ screen texts and weather
    SCREEN_WORDS = ("load", "clock", "power", "fan", "temp", "used", "mem", "network", "volume", "disks", "hotspot",
                    "summary", "fps_avg", "fps_1low", "fps_max", "cpu_max", "gpu_max", "hotspot_max", "fps_session")

    def screen_words(self):
        """The words drawn on the screen in the current language, and the user's own ones."""
        from render import SCREEN_TEXT
        base = SCREEN_TEXT.get(self._engine.lang, SCREEN_TEXT["en"])
        mine = self._cfg().get("texts") or {}
        custom = {k: str(v) for k, v in mine.items() if k in self.SCREEN_WORDS and v not in (None, "")}
        return {"keys": list(self.SCREEN_WORDS), "words": {k: base.get(k, "").strip() for k in self.SCREEN_WORDS},
                "custom": custom, "all": {**{k: v.strip() for k, v in base.items() if isinstance(v, str)}, **custom}}

    def set_screen_word(self, key, value):
        if key not in self.SCREEN_WORDS:
            return False
        value = str(value or "").strip()[:24]
        self._settings.set("texts", key, value)
        self._schedule_reload()
        return True

    def reset_screen_words(self):
        mine = self._cfg().get("texts") or {}
        if mine:
            self._settings.set_many([("texts", k, "") for k in mine])
            self._schedule_reload()
        return True

    def weather_status(self):
        c = self._engine.collector
        w = getattr(c, "weather", None) if c else None
        if w is None:
            return {"state": "off"}
        now = w.current()
        place = w.place or {}
        r = self._engine.renderer
        text = r.weather_text(c).lstrip(" ·") if r is not None and now else ""
        return {"state": "ok" if now else ("error" if w.error else "waiting"), "place": place.get("name"),
                "country": place.get("country"), "text": text, "error": w.error}

    # ------------------------------------------------------------ screen themes (layout + colors)
    def theme_list(self):
        import themes
        cfg = self._cfg()
        return {"themes": themes.entries(self._engine.lang), "current": themes.current(cfg),
                "notice": bool((cfg.get("theme") or {}).get("notice"))}

    def theme_apply(self, tid):
        """Switches the screen theme. The colors the user had on the current theme are kept for it."""
        import themes
        if not themes.exists(tid):
            return False
        cfg = self._cfg()
        themes.keep_colors(themes.current(cfg), cfg.get("colors") or {})
        colors = themes.colors_for(tid)
        self._settings.set_many([("theme", "name", tid), ("theme", "notice", False)] +
                                [("colors", k, v) for k, v in colors.items()])
        self._engine.command("reload")
        self._engine.log(f"Screen theme: {themes.name(themes.load(tid), 'en')}")
        return {"colors": colors, "current": tid}

    def theme_colors_reset(self):
        """Back to the current theme's own colors."""
        import themes
        cfg = self._cfg()
        tid = themes.current(cfg)
        colors = themes.colors(tid)
        themes.keep_colors(tid, colors)
        self._settings.set_many([("colors", k, v) for k, v in colors.items()])
        self._schedule_reload()
        return colors

    def theme_notice_seen(self):
        self.set("theme", "notice", False)
        return True

    def _theme_render(self, tid, fam=None, ss=2):
        """The theme drawn with the live values (for the hover preview and the gallery)."""
        import layout
        import themes
        e = self._engine
        cfg = dict(e.cfg)
        fam = fam or self._family()
        lay = layout.load(fam, theme=tid)
        cfg.update(sensors=lay.get("sensors") or {}, widgets=layout.flatten(lay.get("groups")),
                   colors=themes.colors_for(tid) if tid != themes.current(self._cfg()) else e.cfg.get("colors"),
                   animation={"enabled": False})
        W, H = (320, 480) if fam == "portrait" else (480, 320)
        r0 = getattr(e, "renderer", None)
        r = Renderer(cfg, W, H, ss=ss, base=config.DATA, fields=getattr(r0, "fields", None), lang=e.lang,
                     cache_static=False, logo_dirs=getattr(r0, "logo_dirs", None))
        col = e.collector
        if col is not None and getattr(col, "summary", None):   # the preview shows the theme, not the summary
            class _NoSummary:
                def __init__(self, c):
                    self._c = c
                    self.summary = None

                def __getattr__(self, name):
                    return getattr(self._c, name)
            col = _NoSummary(col)
        return r.draw(col)

    def theme_preview(self, tid):
        import themes
        if not themes.exists(tid) or self._engine.collector is None:
            return None
        try:
            return _png_data_url(self._theme_render(tid))
        except Exception as e:  # noqa: BLE001
            self._engine.log(f"Theme preview failed: {e}")
            return None

    def theme_thumbs(self):
        """Small pictures of every theme in the current orientation: {id: data URL}."""
        import themes
        out = {}
        fam = self._family()
        for t in themes.entries(self._engine.lang):
            key = (t["id"], fam, t["edited"], json.dumps(t["colors"], sort_keys=True))
            hit = self._thumbs.get(("theme",) + key)
            if hit and time.monotonic() - hit[0] < 300:
                out[t["id"]] = hit[1]
                continue
            try:
                img = self._theme_render(t["id"], fam, ss=1)
                img = img.resize((img.width // 2, img.height // 2), 1)   # LANCZOS
                url = _png_data_url(img)
            except Exception:  # noqa: BLE001
                url = None
            self._thumbs[("theme",) + key] = (time.monotonic(), url)
            out[t["id"]] = url
        return out

    def theme_save_as(self, name):
        import themes
        cfg = self._cfg()
        new = themes.save_as(themes.current(cfg), name, cfg.get("colors"), self._engine.lang)
        self._engine.log(f"Theme saved: {name}")
        self.theme_apply(new)
        return self.theme_list()

    def theme_new(self, name):
        """A new theme from scratch (only the clock), used at once so it can be built in the Layout tab."""
        import themes
        new = themes.new_theme(name, self._cfg().get("colors"))
        self._engine.log(f"New theme: {name}")
        self.theme_apply(new)
        return self.theme_list()

    def theme_rename(self, tid, name):
        import themes
        themes.rename(tid, name)
        return self.theme_list()

    def theme_delete(self, tid):
        import themes
        cfg = self._cfg()
        was = themes.current(cfg)
        if not themes.delete(tid):
            return self.theme_list()
        self._engine.log(f"Theme deleted: {tid}")
        if was == tid:
            self.theme_apply(themes.DEFAULT)
        return self.theme_list()

    def theme_reset(self, tid=None):
        """Undoes the layout editor's changes to a theme (both orientations) and its colors."""
        import themes
        cfg = self._cfg()
        tid = tid or themes.current(cfg)
        themes.reset(tid)
        if tid == themes.current(cfg):
            self.theme_colors_reset()
            self._engine.command("reload")
        else:
            themes.keep_colors(tid, themes.colors(tid))
        self._engine.log(f"Theme restored: {tid}")
        return self.theme_list()

    def theme_export(self, tid=None):
        import themes
        cfg = self._cfg()
        tid = tid or themes.current(cfg)
        nm = re.sub(r"[\\/:*?\"<>|']+", " ", themes.name(themes.load(tid), self._engine.lang)).strip() or "theme"
        path = self._app.pick_save_path(f"{nm}{themes.EXT}", "Tela! theme", themes.EXT.lstrip("."))
        if not path:
            return None
        colors = cfg.get("colors") if tid == themes.current(cfg) else None
        themes.export(tid, path, colors, self._engine.lang)
        self._engine.log(f"Theme exported: {path}")
        return path

    def theme_import(self):
        import themes
        path = self._app.pick_open_path("Tela! theme", themes.EXT.lstrip("."))
        if not path:
            return None
        try:
            tid = themes.import_file(path)
        except Exception as e:  # noqa: BLE001 — a broken or foreign file
            return {"error": str(e)}
        self._engine.log(f"Theme imported: {tid}")
        out = self.theme_list()
        out["imported"] = tid
        return out

    def gallery_list(self, force=False):
        """Community gallery: the shared themes with their pictures."""
        import gallery
        try:
            items = gallery.items(bool(force))
        except Exception as e:  # noqa: BLE001 — offline, GitHub down, a broken list
            self._engine.log(f"Gallery: {e}")
            return {"error": True, "share": gallery.SHARE_URL}
        return {"items": [dict(it, picture=gallery.picture(it)) for it in items], "share": gallery.SHARE_URL}

    def gallery_import(self, gid):
        import gallery
        import shutil
        import themes
        it = next((x for x in gallery.items() if x["id"] == gid), None)
        if it is None:
            return {"error": "missing"}
        tmp = None
        try:
            tmp = gallery.download(it)
            tid = themes.import_file(tmp)
        except Exception as e:  # noqa: BLE001
            self._engine.log(f"Gallery import of {gid}: {e}")
            return {"error": str(e)}
        finally:
            if tmp is not None:
                shutil.rmtree(tmp.parent, ignore_errors=True)
        self._engine.log(f"Theme imported from the gallery: {it['name']}")
        out = self.theme_list()
        out["imported"] = tid
        return out

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
        allowed = {"pause", "release", "reconnect", "test", "summary_example", "summary_last", "reload"}
        if name not in allowed:
            return False
        if name == "pause":
            value = not self._engine.paused if value is None else bool(value)
            self._engine.paused = value   # shows at once; the engine confirms right after
        elif name == "release":
            value = not self._engine.released if value is None else bool(value)
            self._engine.released = value
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

    def restart(self):
        """Closes Tela! and opens it again (when something got stuck)."""
        fn = getattr(self._app, "restart", None)
        if fn is None:
            return False
        threading.Timer(0.1, fn).start()
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
        import gameicons
        cfg = self._cfg()
        games = history.entries(cfg)
        icons = {}
        for g in games:
            n = g.get("name") or ""
            if n not in icons:
                icons[n] = gameicons.data_url(n)
        return {"games": games, "per_game": history.per_game(games), "icons": {k: v for k, v in icons.items() if v},
                "folder": str(history.folder(cfg))}

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

    # ------------------------------------------------------------ presets and profiles
    def preset(self):
        import presets
        return presets.detect(self._cfg())

    def preset_apply(self, name):
        import presets
        if name not in presets.PRESETS:
            return False
        self._settings.set_many(presets.items(name))
        self._schedule_reload()
        self._engine.log(f"Preset: {name}")
        return self._user_settings(self._cfg())

    def preview_peek(self, seconds=60):
        """Shows the live preview for a while even when the preset turned it off."""
        self._peek = time.time() + float(seconds)
        return True

    def profiles(self):
        import profiles
        return profiles.entries()

    def profile_save(self, name):
        import profiles
        n = profiles.save(self._cfg(), name, VERSION)
        self._engine.log(f"Profile saved: {n}")
        return n

    def profile_load(self, name):
        import profiles
        profiles.apply(self._app.cfg_path, profiles.read(name))
        self._engine.log(f"Profile loaded: {name}")
        self._engine.command("reload")
        cfg = self._cfg()
        return {"settings": self._user_settings(cfg)}

    def profile_delete(self, name):
        import profiles
        return profiles.delete(name)

    def profile_export(self, name):
        import profiles
        path = self._app.pick_save_path(f"{name}{profiles.EXT}", "Tela! profile", profiles.EXT.lstrip("."))
        if not path:
            return None
        profiles.export(name, path)
        return path

    def profile_import(self):
        import profiles
        path = self._app.pick_open_path("Tela! profile", profiles.EXT.lstrip("."))
        if not path:
            return None
        try:
            return {"name": profiles.import_file(path)}
        except (OSError, ValueError) as e:
            return {"error": str(e)}

    def history_count(self):
        import history
        return len(history.entries(self._cfg()))

    def history_set_keep(self, n):
        """Changes how many games are kept and deletes the older ones now."""
        import history
        n = max(0, int(n))
        self._settings.set("history", "keep", n)
        cfg = self._cfg()
        cfg.setdefault("history", {})["keep"] = n
        removed = history.prune(cfg)
        if removed:
            self._engine.log(f"{removed} old game(s) deleted from the history")
        self._engine.cfg.setdefault("history", {})["keep"] = n
        return removed

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

    def _theme(self):
        import themes
        return themes.current(self._cfg())

    def layout_get(self):
        import layout
        import themes
        fam = self._family()
        lay = layout.load(fam, theme=self._theme())
        size = lay.get("size") or ([320, 480] if fam == "portrait" else [480, 320])
        try:
            tname = themes.name(themes.load(lay["theme"]), self._engine.lang)
        except KeyError:
            tname = lay["theme"]
        return {"family": fam, "size": size, "groups": lay.get("groups") or [], "custom": lay.get("custom", False),
                "sensors": self.sensor_values(), "kinds": list(layout.BLOCK_KINDS),
                "theme": lay["theme"], "theme_name": tname}

    def sensor_values(self):
        """Configured sensors with their value now (for the picker)."""
        import layout
        c = self._engine.collector
        lay = layout.load(self._family(), theme=self._theme())
        out = []
        for name in (lay.get("sensors") or {}):
            v = c.values.get(name) if c else None
            out.append({"name": name, "value": None if v is None else round(float(v), 2)})
        return out

    def layout_save(self, groups):
        import layout
        fam, theme = self._family(), self._theme()
        lay = layout.load(fam, theme=theme)
        layout.save(fam, {"size": lay.get("size"), "sensors": lay.get("sensors"), "groups": groups}, theme)
        self._engine.command("reload")
        return True

    def layout_boxes(self, groups):
        """Where each element of each block lands on the screen: {block id: [[x, y, w, h] | None, ...]}.
        Measured by drawing every element alone, so texts and values get their real size."""
        import layout
        from render import Renderer
        e = self._engine
        r0 = getattr(e, "renderer", None)
        cfg = dict(e.cfg, widgets=[])
        W, H = (r0.W, r0.H) if r0 else (480, 320)
        r = Renderer(cfg, W, H, ss=1, base=config.DATA, fields=getattr(r0, "fields", None), lang=e.lang,
                     cache_static=False, logo_dirs=getattr(r0, "logo_dirs", None))
        col = e.collector
        out = {}
        for g in groups or []:
            boxes = []
            for it in g.get("items") or []:
                w = layout.flatten([dict(g, enabled=True, items=[dict(it, enabled=True)])])
                box = r.item_box(w[0], col) if w else None
                if box is None and w:   # draws nothing right now (e.g. media with nothing playing): its frame
                    f = w[0]
                    if "w" in f and "h" in f:
                        box = [f["x"], f["y"], f["w"], f["h"]]
                    else:
                        x, y = f.get("x", f.get("cx", 0)), f.get("y", f.get("cy", 0))
                        box = [x - 12, y - 8, 24, 16]
                boxes.append(box)
            out[g["id"]] = boxes
        return out

    def layout_reset(self):
        import layout
        layout.reset(self._family(), self._theme())
        self._engine.command("reload")
        self._engine.log("Layout restored to the theme's original")
        return self.layout_get()

    def layout_new_block(self, kind, x=10, y=10, sensor=None):
        import layout
        return layout.new_block(kind, int(x), int(y), sensor)

    def add_sensor(self, selector, groups=None):
        """Adds a sensor from the full list (e.g. 'gpu|voltage|GPU Core') and returns its name."""
        import layout
        fam, theme = self._family(), self._theme()
        lay = layout.load(fam, theme=theme)
        sensors = dict(lay.get("sensors") or {})
        for name, sel in sensors.items():
            if sel == selector:
                return name
        base = re.sub(r"[^a-z0-9]+", "_", selector.split("|")[-1].lower()).strip("_")[:24] or "sensor"
        name, i = base, 2
        while name in sensors:
            name, i = f"{base}_{i}", i + 1
        sensors[name] = selector
        layout.save(fam, {"size": lay.get("size"), "sensors": sensors, "groups": groups or lay.get("groups")}, theme)
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
        return fields(self._engine.hw.info, self._cfg())

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
        state = "released" if st.get("released") else "paused" if st["paused"] else ("connected" if st["connected"] else f"not connected ({st.get('screen_error') or 'connecting'})")
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
        if c and getattr(c, "sessions", None):
            from sensors import pids_with_windows
            wins = pids_with_windows()
            now = time.monotonic()
            lines.append("Game sessions: " + "; ".join(
                f"{sv.name} (pid {pid}, {len(sv.fps_samples)} s with FPS, last {now - sv.last_fps:.0f} s ago, "
                f"window {'?' if wins is None else ('yes' if pid in wins else 'no')})" for pid, sv in c.sessions.items())
                + f" · counts as game now: {'yes' if c.game_open() else 'no'}")
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
