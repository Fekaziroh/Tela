#!/usr/bin/env python3
"""Tela! — window (WebView2), tray icon and Windows integration.

  Tela.exe            opens the window
  Tela.exe --tray     starts hidden in the tray (used at Windows logon)
"""
import argparse
import threading
import time

import config
import winsys
from api import Api
from engine import HERE, VERSION, Engine, Log, effective_language
from icon import app_icon, temp_icon
from updater import Updater

TEXT = {
    "pt": {"open": "Abrir Tela!", "brightness": "Brilho", "last_summary": "Ver último resumo de jogo",
           "pause": "Pausar", "quit": "Sair", "in_tray": "A Tela! continua rodando aqui na bandeja.",
           "other_copy": "Outra cópia da Tela! (ou uma versão antiga, como a TelaV3) já está aberta:\n\n{folders}\n\n"
                         "Fechar ela e abrir esta?"},
    "es": {"open": "Abrir Tela!", "brightness": "Brillo", "last_summary": "Ver el último resumen de partida",
           "pause": "Pausar", "quit": "Salir", "in_tray": "Tela! sigue funcionando aquí en la bandeja.",
           "other_copy": "Ya hay otra copia de Tela! abierta (o una versión antigua, como TelaV3):\n\n{folders}\n\n"
                         "¿Cerrarla y abrir esta?"},
    "zh": {"open": "打开 Tela!", "brightness": "亮度", "last_summary": "查看上一局总结",
           "pause": "暂停", "quit": "退出", "in_tray": "Tela! 仍在托盘中运行。",
           "other_copy": "已有另一个 Tela!（或旧版本，例如 TelaV3）正在运行：\n\n{folders}\n\n关闭它并打开这个吗？"},
    "en": {"open": "Open Tela!", "brightness": "Brightness", "last_summary": "Show last game summary",
           "pause": "Pause", "quit": "Quit", "in_tray": "Tela! keeps running here in the tray.",
           "other_copy": "Another copy of Tela! (or an old version such as TelaV3) is already running:\n\n{folders}\n\n"
                         "Close it and open this one?"},
}


def windows_uses_dark_theme():
    if not winsys.WINDOWS:
        return True
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as k:
            return winreg.QueryValueEx(k, "AppsUseLightTheme")[0] == 0
    except OSError:
        return False


class App:
    WATCHDOG_SECONDS = 60
    WATCHDOG_CHECK = 10

    def __init__(self, start_hidden=False, demo=False, simulate=False, force_browser=False):
        self.cfg_path = config.DATA / config.CONFIG
        self.log = Log(config.DATA / "tela.log", echo=False)
        self.demo, self.simulate = demo, simulate
        self.engine = Engine(self.cfg_path, self.log, demo=demo, simulate=simulate)
        self.api = Api(self)
        self.updater = Updater(VERSION, self.log, enabled=lambda: bool(
            (self.engine.cfg.get("updates") or {}).get("check", True)))
        self.start_hidden = start_hidden
        self.visible = not start_hidden   # while hidden in the tray the window gets no previews (saves CPU)
        self.force_browser = force_browser
        self.window = None
        self.window_kind = "none"
        self.bridge = None
        self.tray = None
        self._quit = threading.Event()
        self._told_tray = False
        self._tray_image = None
        self._tray_dirty = False
        self._accent = str((self.engine.cfg.get("ui") or {}).get("accent") or "#FFFFFF")
        self.lang = self.engine.lang
        self.T = TEXT.get(self.lang, TEXT["en"])

    # ------------------------------------------------------------ start
    def run(self):
        self.log(f"Tela! {VERSION} started" + (" (demo)" if self.demo else ""))
        self.engine.start()
        if not self.demo:
            self.updater.start()
        winsys.instance_server(self.show_window, lambda: threading.Thread(target=self.quit, daemon=True).start())
        self._events = winsys.watch_windows_events(self._windows_shutdown, self._locked, self._monitor_off,
                                                   lambda going: self.engine.command("suspend" if going else "resume"))
        threading.Thread(target=winsys.refresh_start_with_windows, args=(self.log,), daemon=True).start()
        threading.Thread(target=self._watchdog, daemon=True, name="watchdog").start()
        self.tray = self._make_tray()
        threading.Thread(target=self._tray_loop, daemon=True, name="tray-icon").start()
        if self.force_browser or not self._run_webview():
            self._run_browser()
        # the process must not end before the engine turns the screen off
        self.engine.stop()
        self.engine.join(8)

    def _run_webview(self):
        """Opens the WebView2 window. Blocks until the window is destroyed. False if it could not open."""
        try:
            import webview
        except Exception as e:  # noqa: BLE001
            self.log(f"Window component unavailable ({e}); opening in the browser instead")
            return False
        theme = str(((self.engine.cfg.get("ui") or {}).get("theme")) or "auto")
        dark = theme == "dark" or (theme == "auto" and windows_uses_dark_theme())
        try:
            self.window = webview.create_window(
                "Tela!", url=str(HERE / "ui" / "index.html"), js_api=self.api, width=1180, height=780,
                min_size=(480, 560), hidden=self.start_hidden, background_color="#111419" if dark else "#F7F8FA",
                text_select=True)
            self.window.events.closing += self._on_closing
            self.window_kind = "webview2"
            webview.start(gui="edgechromium" if winsys.WINDOWS else None, debug=False, private_mode=True)
        except Exception as e:  # noqa: BLE001
            self.log(f"The window could not open ({type(e).__name__}: {e}); opening in the browser instead")
            self.window, self.window_kind = None, "none"
            return self._quit.is_set()
        if not self._quit.is_set():   # window closed by Windows or crashed: keep running in the tray
            self.window = None
            self.visible = True
            self._run_browser(open_now=False)
        return True

    def _run_browser(self, open_now=None):
        from bridge import Bridge
        if self.bridge is None:
            self.bridge = Bridge(self.api, HERE / "ui")
        self.window_kind = "browser"
        self.visible = True
        if open_now if open_now is not None else not self.start_hidden:
            self.show_window()
        self._quit.wait()

    # ------------------------------------------------------------ window
    def _on_closing(self):
        if self._quit.is_set():
            return True
        threading.Timer(0.05, self.hide_window).start()
        return False

    def hide_window(self):
        self.visible = self.window is None   # browser mode: the tab decides by itself
        if self.window is not None:
            try:
                self.window.hide()
            except Exception:  # noqa: BLE001
                pass
            self._webview_memory(low=True)
        if not self._told_tray and self.tray is not None:
            self._told_tray = True
            try:
                self.tray.notify(self.T["in_tray"], "Tela!")
            except Exception:  # noqa: BLE001
                pass

    def show_window(self):
        self.visible = True
        if self.window is not None:
            self._webview_memory(low=False)
            try:
                self.window.show()
                self.window.restore()
            except Exception:  # noqa: BLE001
                pass
        elif self.bridge is not None:
            import webbrowser
            webbrowser.open(self.bridge.url)

    def _webview_memory(self, low):
        """Asks WebView2 to free memory while the window is in the tray (MemoryUsageTargetLevel, WebView2
        1.0.1661+). Best effort: pywebview does not document its native objects, so every step is optional."""
        try:
            form = self.window.native
            browser = getattr(form, "browser", None)
            control = getattr(browser, "webview", None) or getattr(browser, "web_view", None)
            core = control.CoreWebView2
            from Microsoft.Web.WebView2.Core import CoreWebView2MemoryUsageTargetLevel as Level  # type: ignore
            from System import Action  # type: ignore

            def apply():
                core.MemoryUsageTargetLevel = Level.Low if low else Level.Normal
            form.Invoke(Action(apply))
        except Exception:  # noqa: BLE001
            pass

    def _dialog(self, kind_name, ps_code, **kw):
        if self.window is not None:
            import webview
            kind = getattr(getattr(webview, "FileDialog", None), kind_name, None) or getattr(webview, kind_name + "_DIALOG")
            res = self.window.create_file_dialog(kind, **kw)
            if isinstance(res, (list, tuple)):
                return res[0] if res else None
            return res or None
        if winsys.WINDOWS:
            r = winsys._powershell("Add-Type -AssemblyName System.Windows.Forms; " + ps_code, check=False)
            out = (r.stdout or "").strip()
            return out or None
        return None

    def pick_save_path(self, name):
        return self._dialog("SAVE", "$d=New-Object System.Windows.Forms.SaveFileDialog; "
                            f"$d.FileName='{name}'; $d.Filter='CSV|*.csv'; if($d.ShowDialog() -eq 'OK'){{ $d.FileName }}",
                            save_filename=name, file_types=("CSV (*.csv)",))

    def pick_folder(self):
        return self._dialog("FOLDER", "$d=New-Object System.Windows.Forms.FolderBrowserDialog; "
                            "if($d.ShowDialog() -eq 'OK'){ $d.SelectedPath }")

    def pick_images(self):
        """File picker for logos: the window's own dialog, or a Windows dialog in browser mode."""
        if self.window is not None:
            import webview
            kind = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
            res = self.window.create_file_dialog(kind, allow_multiple=True,
                                                 file_types=("Images (*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.webp)",))
            return list(res or [])
        if winsys.WINDOWS:
            r = winsys._powershell(
                "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; "
                "$d.Multiselect=$true; $d.Filter='Images|*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.webp'; "
                "if($d.ShowDialog() -eq 'OK'){ $d.FileNames }", check=False)
            return [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]
        return []

    def set_tray_accent(self, color):
        """The tray icon's gauge arc follows the window accent color."""
        ui = self.engine.cfg.get("ui") or {}
        if color != ui.get("accent"):
            try:
                config.Settings(self.cfg_path).set("ui", "accent", color)
                ui["accent"] = color
            except OSError:
                pass
        if color != self._accent:
            self._accent = color
            self._tray_image = app_icon(64, color)
            self._tray_dirty = True

    def settings_changed(self, section, key, value):
        if (section, key) == ("ui", "language"):
            self.lang = effective_language(value)
            self.T = TEXT.get(self.lang, TEXT["en"])
            if self.tray is not None:
                try:
                    self.tray.menu = self._tray_menu()
                    self.tray.update_menu()
                except Exception:  # noqa: BLE001
                    pass

    # ------------------------------------------------------------ tray
    def _tray_menu(self):
        import pystray
        T = self.T

        def level(v):
            return pystray.MenuItem(f"{v}%", lambda *_: self.api.set("display", "brightness", v), radio=True,
                                    checked=lambda _i: self.engine.normal_brightness == v)
        return pystray.Menu(
            pystray.MenuItem(T["open"], lambda *_: self.show_window(), default=True),
            pystray.MenuItem(T["brightness"], pystray.Menu(*(level(v) for v in (10, 25, 40, 50, 75, 100)))),
            pystray.MenuItem(T["last_summary"], lambda *_: self.engine.command("summary_last"),
                             enabled=lambda _i: bool(self.engine.last_summary)),
            pystray.MenuItem(T["pause"], lambda *_: self.api.command("pause"), checked=lambda _i: self.engine.paused),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(T["quit"], lambda *_: self.quit()),
        )

    def _make_tray(self):
        try:
            import pystray
        except Exception:  # noqa: BLE001
            self.log("Tray icon unavailable (pystray missing)")
            return None
        self._tray_image = app_icon(64, self._accent)
        icon = pystray.Icon("tela", self._tray_image, f"Tela! {VERSION}", self._tray_menu())
        try:
            threading.Thread(target=icon.run, daemon=True, name="tray").start()
        except Exception as e:  # noqa: BLE001
            self.log(f"Tray icon unavailable: {e}")
            return None
        return icon

    def _tray_loop(self):
        """Tooltip with the temperatures and, if chosen, the temperature drawn in the icon."""
        shown = None
        while not self._quit.wait(3):
            if self.tray is None:
                continue
            e = self.engine
            ct, gt = e.value("cpu_temp"), e.value("gpu_temp")
            parts = [f"CPU {ct:.0f}°C" if ct is not None else None, f"GPU {gt:.0f}°C" if gt is not None else None]
            tip = f"Tela! {VERSION}" + ("  ·  " + "  ·  ".join(p for p in parts if p) if any(parts) else "")
            mode = str((e.cfg.get("tray") or {}).get("temp_icon", "none")).lower()
            want = None
            if mode in ("cpu", "gpu"):
                v = ct if mode == "cpu" else gt
                lim = (75, 85) if mode == "cpu" else (70, 80)
                want = ("temp", None if v is None else round(v), v is not None and v >= lim[0], v is not None and v >= lim[1])
            try:
                self.tray.title = tip[:120]
                if want != shown or self._tray_dirty:
                    self._tray_dirty = False
                    self.tray.icon = temp_icon(*want[1:]) if want else self._tray_image
                    shown = want
            except Exception:  # noqa: BLE001
                pass

    # ------------------------------------------------------------ Windows events
    def _locked(self, yes):
        if not yes:
            self.engine.command("wake", "lock")
        elif (self.engine.cfg.get("display") or {}).get("off_on_lock", True):
            self.engine.command("sleep", "lock")

    def _monitor_off(self, yes):
        if not yes:
            self.engine.command("wake", "monitor")
        elif (self.engine.cfg.get("display") or {}).get("off_with_monitor", True):
            self.engine.command("sleep", "monitor")

    def _windows_shutdown(self):
        self.log("Windows is shutting down: turning the screen off")
        self.engine.stop()
        self.engine.join(4)

    # ------------------------------------------------------------ watchdog
    def _watchdog(self):
        """Restarts the engine if it stops responding (e.g. a driver call that never returns)."""
        while not self._quit.wait(self.WATCHDOG_CHECK):
            e = self.engine
            stuck = (not e.paused and not e.sleeping and time.monotonic() - e.beat > self.WATCHDOG_SECONDS)
            if self._quit.is_set() or not (stuck or not e.is_alive()):
                continue
            self.log("The engine stopped responding: restarting it" if stuck else "The engine stopped: restarting it")
            e.stop()

            def release(old=e):
                for part in (old.screen, old.collector):
                    try:
                        part.close()
                    except Exception:  # noqa: BLE001
                        pass
            threading.Thread(target=release, daemon=True).start()
            time.sleep(2)
            new = Engine(self.cfg_path, self.log, demo=self.demo, simulate=self.simulate)
            new.last_summary = e.last_summary
            self.engine = new
            new.start()

    # ------------------------------------------------------------ exit
    def quit(self):
        if self._quit.is_set():
            return
        self._quit.set()
        self.log("Closing.")
        self.engine.stop()
        self.engine.join(8)
        if self.tray is not None:
            try:
                self.tray.stop()
            except Exception:  # noqa: BLE001
                pass
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:  # noqa: BLE001
                pass


def _preload_dotnet():
    """The window and the hardware monitor share .NET (Framework): it starts once, here on the main thread,
    the default way, before the engine thread or the window touch it."""
    if not winsys.WINDOWS:
        return
    try:
        import clr  # noqa: F401
    except Exception:  # noqa: BLE001
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tray", "--minimizado", dest="tray", action="store_true")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--simulate", action="store_true")
    ap.add_argument("--browser", action="store_true", help="open the window in the default browser")
    ap.add_argument("--autostart", choices=("on", "off"), help="(setup) turn start with Windows on or off and exit")
    ap.add_argument("--quit", action="store_true", help="(setup) close a running Tela! properly and exit")
    a = ap.parse_args()

    if a.quit or a.autostart:
        if a.quit:
            winsys.ask_running_instance_to_quit()
        if a.autostart:
            if not (config.DATA / config.CONFIG).exists():
                try:   # import an older copy now: its start-with-Windows task still points to it
                    config.prepare()
                    (config.DATA / "version.txt").write_text(VERSION, encoding="utf-8")
                except Exception:  # noqa: BLE001
                    pass
            winsys.set_start_with_windows(a.autostart == "on")
        return

    # first launch, or a new version: (re)build config.yaml keeping the user's choices
    marker = config.DATA / "version.txt"
    try:
        current = marker.read_text(encoding="utf-8").strip()
    except OSError:
        current = None
    if current != VERSION or not (config.DATA / config.CONFIG).exists():
        try:
            config.prepare()
            marker.write_text(VERSION, encoding="utf-8")
            if current and current != VERSION:   # the window shows what changed since this version
                (config.DATA / "updated_from.txt").write_text(current, encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    try:
        lang = effective_language((config.load(config.DATA / config.CONFIG).get("ui") or {}).get("language"))
    except Exception:  # noqa: BLE001 — unreadable settings: the engine reports it in the activity log
        lang = effective_language("auto")
    texts = TEXT.get(lang, TEXT["en"])
    if winsys.WINDOWS:
        if not winsys.resolve_other_copies(texts):
            return
    elif winsys.ask_running_instance_to_show():
        return
    _preload_dotnet()
    App(start_hidden=a.tray, demo=a.demo, simulate=a.simulate, force_browser=a.browser).run()


if __name__ == "__main__":
    main()
