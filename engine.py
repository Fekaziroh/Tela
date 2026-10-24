"""Tela engine: reads the sensors, draws and sends frames to the screen in its own thread.

The window (app.py) and the console mode (cli.py) both use this engine.
"""
import json
import math
import os
import queue
import sys
import threading
import time
import traceback
from collections import deque
from pathlib import Path

import numpy as np

import config
import layout
from display import SimulatedScreen, TuringScreen
from hardware import DEMO_RAW, Detector, build, fields as hw_fields, summary as hw_summary
from render import SCREEN_TEXT, Renderer
from sensors import Collector, idle_seconds

VERSION = "1.5.1"
HERE = config.HERE
DATA = config.DATA


LANGUAGES = {0x16: "pt", 0x0A: "es", 0x04: "zh", 0x09: "en"}


def system_language():
    """pt, es, zh or en from the Windows display language (any other language uses English)."""
    if sys.platform == "win32":
        try:
            import ctypes
            return LANGUAGES.get(ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF, "en")
        except Exception:  # noqa: BLE001
            pass
    import locale
    lang = (locale.getlocale()[0] or os.environ.get("LANG", "en")).lower()[:2]
    return lang if lang in ("pt", "es", "zh") else "en"


def effective_language(setting):
    setting = str(setting or "auto").lower()
    return setting if setting in SCREEN_TEXT else system_language()


class Log:
    """Activity log: kept in memory for the window and written to tela.log (rotated at 512 KB)."""
    MAX_BYTES = 512 * 1024

    def __init__(self, file=None, echo=True):
        self.lines = deque(maxlen=300)
        self.file = Path(file) if file else None
        self.echo = echo
        self.count = 0
        self._lock = threading.Lock()

    def _rotate(self):
        try:
            if self.file and self.file.stat().st_size > self.MAX_BYTES:
                old = self.file.with_suffix(self.file.suffix + ".1")
                old.unlink(missing_ok=True)
                self.file.rename(old)
        except OSError:
            pass

    def __call__(self, msg):
        line = time.strftime("%H:%M:%S  ") + msg
        with self._lock:
            self.lines.append(line)
            self.count += 1
            if self.file:
                if self.count % 50 == 1:
                    self._rotate()
                try:
                    with open(self.file, "a", encoding="utf-8") as f:
                        f.write(time.strftime("%Y-%m-%d ") + line + "\n")
                except OSError:
                    pass
        if self.echo and sys.stdout is not None:
            try:
                print(line, flush=True)
            except Exception:  # noqa: BLE001
                pass


def changed_regions(new, old, tw=40, th=32):
    """Rectangles (x, y, w, h) that changed; only these are sent to the screen."""
    W, H = new.size
    if old is None or old.size != new.size:
        return [(0, 0, W, H)]
    diff = np.any(np.asarray(new) != np.asarray(old), axis=2)
    rects = []
    for ty in range(0, H, th):
        band = diff[ty:ty + th]
        changed = [bool(band[:, tx:tx + tw].any()) for tx in range(0, W, tw)]
        i = 0
        while i < len(changed):
            if not changed[i]:
                i += 1
                continue
            j = i
            while j < len(changed) and changed[j]:
                j += 1
            x0, x1 = i * tw, min(W, j * tw)
            sub = band[:, x0:x1]
            ys, xs = np.where(sub.any(1))[0], np.where(sub.any(0))[0]
            rects.append((x0 + int(xs[0]), ty + int(ys[0]), int(xs[-1] - xs[0] + 1), int(ys[-1] - ys[0] + 1)))
            i = j
    return rects


class Engine(threading.Thread):
    REFRESH_EVERY = 20 * 60   # seconds between whole-picture refreshes (not during a game)
    def __init__(self, cfg_path, log, demo=False, simulate=False, once=False, demo_game=True, demo_media=True):
        super().__init__(daemon=True, name="engine")
        self.cfg_path = Path(cfg_path)
        self.log = log
        self.demo, self.simulate, self.once = demo, simulate, once
        self.demo_game, self.demo_media = demo_game, demo_media
        self.commands = queue.Queue()
        self._halt = threading.Event()
        self.paused = False          # frozen: the screen keeps the last picture, the port stays open
        self.released = False        # the port is closed so another program can use the screen
        self.connected = False
        self.screen_error = None
        self.last_frame = None
        self.frame_no = 0
        self.screen = self.collector = self.renderer = None
        self._previous = None
        self._last_error = self._render_error = None
        self._prev_layout = None
        self._wipe = False           # next frame: black screen first, then the whole picture
        self._full_at = 0.0          # when the whole picture was last sent
        self._sleep = set()          # reasons for a black screen: "lock", "monitor", "suspend"
        self.eco = False
        self.beat = time.monotonic()  # heartbeat for the watchdog
        self.last_summary = self._load_last_game()
        self.hw = Detector(DATA)
        if demo:
            self.hw.info = build(DEMO_RAW)
        else:
            self.hw.detect_in_background(lambda: self.command("hardware"))
        self.normal_brightness = 40
        self._load()

    # ------------------------------------------------------------ settings
    def _load(self):
        try:
            cfg = config.load(self.cfg_path)
        except Exception as e:  # noqa: BLE001 — a damaged file must not stop the screen
            self.log(f"Settings file error ({e}); using the defaults")
            cfg = config.load(HERE / config.DEFAULT)
        layout.apply(cfg)
        dcfg = cfg.get("display") or {}
        orient = dcfg.get("orientation", "landscape")
        port = dcfg.get("port", "auto")
        brightness = dcfg.get("brightness", 40)
        simulate = self.simulate or dcfg.get("simulate", False)
        target_port = "simulated" if simulate else port
        if self.screen is None or getattr(self.screen, "port", None) != target_port:
            if self.screen is not None:
                self.screen.close()
                self.connected = False
            self.screen = (SimulatedScreen(orient, None if self.simulate == "memory" else DATA / "preview.png")
                           if simulate else TuringScreen(port, orient, brightness))
        elif self.screen.orientation != orient:
            self.screen.set_orientation(orient)
            self._previous = None
        self.cfg = cfg
        self.lang = effective_language((cfg.get("ui") or {}).get("language"))
        self.normal_brightness = int(brightness)
        self._apply_brightness()
        self.off_on_exit = bool(dcfg.get("off_on_exit", True))
        old = self.collector
        fields = hw_fields(self.hw.info, cfg)
        self.collector = Collector(cfg, demo=self.demo, base=HERE, fields=fields, demo_game=self.demo_game,
                                   demo_media=self.demo_media, previous=old)
        if old is not None:
            old.close()
        if self.collector.last_summary is None:
            self.collector.last_summary = self.last_summary
        ss = 1 if str((cfg.get("performance") or {}).get("quality", "high")).lower() == "normal" else 2
        old_r = self.renderer
        self.renderer = Renderer(cfg, self.screen.width, self.screen.height, ss=ss, base=DATA, fields=fields, lang=self.lang,
                                 logo_dirs=[DATA / "logos", HERE / "logos"],
                                 cache_static=not (cfg.get("layout") or {}).get("overlap"))
        theme = (cfg.get("layout") or {}).get("theme")
        if old_r is not None and theme != getattr(self, "_theme", theme):
            self._wipe = True   # another theme: clean the screen and send it whole (no leftovers)
        self._theme = theme
        self.interval = float(cfg.get("interval", 1.0))
        self.anim_step = 1.0 / max(1.0, float((cfg.get("animation") or {}).get("fps", 8)))
        self.fast_step = max(0.05, float((cfg.get("fps") or {}).get("update", 0.2)))
        ecfg = cfg.get("eco") or {}
        self.eco_enabled = bool(ecfg.get("enabled", True))
        self.eco_after = max(0.5, float(ecfg.get("idle_minutes", 5))) * 60
        self.eco_interval = max(self.interval, float(ecfg.get("interval", 3)))
        self.eco = False
        rcfg = cfg.get("rest") or {}
        self.rest_enabled = bool(rcfg.get("enabled", False))
        self.rest_after = max(1.0, float(rcfg.get("idle_minutes", 10))) * 60
        self.rest = False

    # ------------------------------------------------------------ last game (kept on disk)
    @staticmethod
    def _load_last_game():
        try:
            data = json.loads((DATA / "last_game.json").read_text(encoding="utf-8"))
            return data if data.get("name") else None
        except (OSError, ValueError):
            return None

    def _save_last_game(self, s):
        try:
            keep = {k: v for k, v in s.items() if k not in ("start", "expires")}
            (DATA / "last_game.json").write_text(json.dumps(keep, ensure_ascii=False), encoding="utf-8")
        except (OSError, TypeError, ValueError):
            pass

    # ------------------------------------------------------------ commands (thread-safe)
    def command(self, name, value=None):
        self.commands.put((name, value))

    def stop(self):
        self._halt.set()
        self.commands.put(("nothing", None))

    @property
    def stopped(self):
        return self._halt.is_set()

    @staticmethod
    def in_hours(start, end, now=None):
        """True when the local time is between two "HH:MM" times (the range may cross midnight)."""
        try:
            t = now or time.localtime()
            m = t.tm_hour * 60 + t.tm_min
            a = [int(x) for x in str(start).split(":")]
            b = [int(x) for x in str(end).split(":")]
            s, e = a[0] * 60 + a[1], b[0] * 60 + b[1]
            return (s <= m < e) if s < e else (m >= s or m < e)
        except (ValueError, IndexError):
            return False

    def _target_brightness(self):
        """Normal brightness, or the night one during the configured hours."""
        d = self.cfg.get("display") or {}
        if not d.get("night_enabled"):
            return self.normal_brightness
        night = self.in_hours(d.get("night_start", "22:00"), d.get("night_end", "07:00"))
        return int(d.get("night_brightness", 15)) if night else self.normal_brightness

    def _check_schedule(self):
        """Screen off during the configured hours ("off" schedule in Settings)."""
        d = self.cfg.get("display") or {}
        want = bool(d.get("off_enabled")) and self.in_hours(d.get("off_start", "02:00"), d.get("off_end", "07:00"))
        if want != ("schedule" in self._sleep):
            self._on_command("sleep" if want else "wake", "schedule")

    def _apply_brightness(self):
        target = self._target_brightness()
        if self.screen is not None and self.screen.brightness != target:
            self.screen.set_brightness(target)

    @property
    def sleeping(self):
        return bool(self._sleep)

    def _on_command(self, name, value):
        if name == "brightness":
            self.normal_brightness = int(value)
            self._apply_brightness()
        elif name in ("sleep", "wake"):
            before = self.sleeping
            (self._sleep.add if name == "sleep" else self._sleep.discard)(value)
            if self.sleeping and not before:
                if self.connected:
                    try:
                        self.screen.turn_off()
                    except Exception:  # noqa: BLE001
                        pass
                self.log("Screen off (" + {"lock": "PC locked", "monitor": "monitor asleep", "schedule": "scheduled hours"}.get(value, value) + ")")
            elif before and not self.sleeping:
                if self.connected:
                    try:
                        self.screen.turn_on()
                    except Exception:  # noqa: BLE001
                        pass
                self._previous = None
                self.log("Screen back on")
        elif name == "orientation":
            self.screen.set_orientation(value)
            self._previous = None
            self._reload()   # portrait and landscape use different layouts
        elif name == "pause":      # freeze: nothing is sent; on resume only what changed goes out
            self.paused = bool(value)
            self.log("Paused: the screen keeps the last picture" if self.paused else "Resumed")
        elif name == "release":    # close the port so another program can use the screen
            self.released = bool(value)
            if self.released:
                if self.connected:
                    self.screen.close()
                    self.connected = False
                self._previous = None
                self.log("Screen released for other programs")
            else:
                self.log("Taking the screen back")
        elif name == "reconnect":  # the screen froze or shows garbage: open the port again and send everything
            try:
                self.screen.close()
            except Exception:  # noqa: BLE001
                pass
            self.connected = False
            self._previous = None
            self.released = False
            self.log("Reconnecting the screen")
        elif name == "test":
            from PIL import Image
            try:
                if not self.connected:
                    self.screen.connect()
                    self.connected = True
                self.log("Color test on the screen...")
                for c in ("#FF0000", "#00FF00", "#0000FF", "#FFFFFF"):
                    self.screen.send_image(Image.new("RGB", (self.screen.width, self.screen.height), c), 0, 0)
                    self.screen.end_frame()
                    self._wait(1.2)
                self.log("Color test finished")
            except Exception as e:  # noqa: BLE001
                self.log(f"Color test failed: {type(e).__name__}: {e}")
                self.screen.close()
                self.connected = False
            self._previous = None
        elif name == "suspend":      # PC going to sleep: black screen and release the port
            if self.connected:
                try:
                    self.screen.turn_off()
                except Exception:  # noqa: BLE001
                    pass
                self.screen.close()
                self.connected = False
            self._sleep.add("suspend")
            self.log("PC going to sleep")
        elif name == "resume":       # back from sleep: the screen rebooted too; reconnect from scratch
            self.log("PC woke up: reconnecting the screen")
            self.screen.close()
            self.connected = False
            self._previous = None
            self._wait(3)
            self._sleep.discard("suspend")
        elif name == "summary_show":   # a game from the history
            r = value
            if r:
                now = time.monotonic()
                total = float((self.cfg.get("session") or {}).get("summary_seconds", 15))
                import gameicons
                icon = gameicons.find(r.get("name"))
                self.collector.summary = dict(r, start=now, expires=now + 3 + total, total=total,
                                              duration=r.get("duration") or "", max=r.get("max") or {},
                                              icon=str(icon) if icon else None)
                self.log(f"Showing the summary of {r.get('name')}")
        elif name == "rest_preview":   # Settings › Rest › See how it looks
            self._rest_preview_until = time.monotonic() + 10
            self._update_rest()
        elif name == "summary_last":
            r = self.collector.last_summary
            if r:
                now = time.monotonic()
                total = float((self.cfg.get("session") or {}).get("summary_seconds", 15))
                self.collector.summary = dict(r, start=now, expires=now + 3 + total, total=total)
                self.log(f"Showing the summary of {r['name']} again")
            else:
                self.log("No game summary yet")
        elif name == "summary_example":
            now = time.monotonic()
            total = float((self.cfg.get("session") or {}).get("summary_seconds", 15))
            self.collector.summary = {
                "name": SCREEN_TEXT[self.lang if self.lang in SCREEN_TEXT else "en"]["example_game"],
                "duration": "1h 07min", "fps_avg": 118.0, "fps_1low": 84.0, "fps_max": 162.0,
                "max": {"cpu": 78.0, "gpu": 72.0, "hotspot": 88.0},
                "fps_series": [118 + 18 * math.sin(i / 9) - (35 if i % 53 == 0 else 0) for i in range(120)],
                "start": now, "expires": now + 3 + total, "total": total,
            }
            self.log(f"Showing an example summary for {total:g} s")
        elif name == "hardware":
            self.log("Hardware: " + hw_summary(self.hw.info))
            self._reload()
        elif name == "reload":
            self._reload()

    def _reload(self):
        try:
            self._load()
            self.log("Settings applied")
        except Exception as e:  # noqa: BLE001
            self.log(f"Settings file error: {e}")

    def _wait(self, sec):
        end = time.monotonic() + sec
        while not self._halt.is_set():
            self.beat = time.monotonic()
            left = end - time.monotonic()
            if left <= 0:
                return
            try:
                name, value = self.commands.get(timeout=min(left, 5))
            except queue.Empty:
                continue
            if name != "nothing":
                self._on_command(name, value)

    # ------------------------------------------------------------ state
    def status(self):
        st = self.collector.status if self.collector else {}
        return {
            "paused": self.paused, "released": self.released, "connected": self.connected, "screen_error": self.screen_error,
            "sleeping": sorted(self._sleep), "eco": self.eco,
            "port": getattr(self.screen, "port_in_use", None), "demo": st.get("demo", False),
            "lhm_error": st.get("lhm"), "fps": st.get("fps"), "source": st.get("source"),
            "admin": st.get("admin"), "embedded_error": st.get("embedded_error"), "hwinfo": st.get("hwinfo"),
        }

    def value(self, name):
        return self.collector.values.get(name) if self.collector else None

    # ------------------------------------------------------------ main loop
    def _send_frame(self):
        """Draws and sends only what changed. Returns False on error (after waiting to retry)."""
        try:
            img = self.renderer.draw(self.collector)
            self._render_error = None
        except Exception as e:  # noqa: BLE001 — error in the layout
            msg = f"Layout error: {e}"
            if msg != self._render_error:
                self.log(msg)
                self._render_error = msg
            self._wait(2)
            return False
        self.last_frame = img
        self.frame_no += 1
        self.hires_no = self.frame_no   # renderer.hires matches this frame (transitions send pieces after it)
        try:
            if not self.connected:
                self.screen.connect()
                self.connected, self._previous, self._last_error, self.screen_error = True, None, None, None
                self.log(f"Screen connected ({self.screen.port_in_use})")
            t0 = time.monotonic()
            wipe = self._wipe
            if wipe:
                self._wipe = False
                if self._previous is None or not self.renderer.anim_enabled:
                    self._previous = None   # no animation: the whole new picture at once
            elif t0 - self._full_at > self.REFRESH_EVERY and not self.collector.in_game():
                self._previous = None   # now and then the whole picture again: clears any pixel that went stale
            first = self._previous is None
            layout = self.renderer.layout
            anim = (self.cfg.get("animation") or {})
            if wipe and not first:   # another theme: every pixel is sent again (no leftovers of the old one)
                self._play(str(anim.get("transition_theme", "cascade")), img, whole=True)
            elif not first and self._prev_layout is not None and layout != self._prev_layout and self.renderer.anim_enabled:
                self._play(str(anim.get("transition_summary", "cascade")), img)   # summary or Rest coming in/out
            else:
                for x, y, w, h in changed_regions(img, self._previous):
                    self.screen.send_image(img.crop((x, y, x + w, y + h)), x, y)
                self.screen.end_frame()
            self._prev_layout = layout
            self._previous = img
            if first:
                if not self._full_at:
                    self.log(f"Full frame sent ({time.monotonic() - t0:.1f} s)")
                self._full_at = time.monotonic()
        except (OSError, RuntimeError) as e:   # serial/USB errors (SerialException is an OSError)
            msg = f"{type(e).__name__}: {e}"
            self.screen_error = msg
            if msg != self._last_error:
                self.log(("Lost the screen connection: " if self.connected else "Could not open the screen: ") + msg)
                self._last_error = msg
            self.screen.close()
            self.connected = False
            self._wait(5)
            return False
        except Exception as e:  # noqa: BLE001 — a bug while sending: keep the connection, resend everything
            where = traceback.extract_tb(e.__traceback__)[-1]
            msg = f"Error sending a frame: {type(e).__name__}: {e} ({Path(where.filename).name}:{where.lineno})"
            if msg != self._last_error:
                self.log(msg)
                self._last_error = msg
            self._previous = None
            self._wait(1)
            return False
        return True

    TRANSITIONS = ("cascade", "eink", "glitch", "curtain", "none")

    def _play(self, kind, target, whole=False):
        """Settings › Transitions: how a new screen comes in (theme change; summary and Rest)."""
        kind = kind if kind in self.TRANSITIONS else "cascade"
        if kind == "cascade":
            return self._transition(target, whole=whole)
        if kind == "eink":
            return self._fx_eink(target)
        if kind == "glitch":
            return self._fx_glitch(target)
        if kind == "curtain":
            return self._fx_curtain(target)
        self._full(target)

    def _full(self, img):
        self.screen.send_image(img, 0, 0)
        self.screen.end_frame()
        self.last_frame = img
        self.frame_no += 1

    def _fx_frames(self, frames):
        for img, pause in frames:
            if self._halt.is_set():
                break
            self._full(img)
            time.sleep(pause)

    def _fx_eink(self, target):
        """Like an e-ink reader's full refresh: the new picture in negative, black, white, then the picture with a
        faint ghost of the old one, then clean."""
        from PIL import Image, ImageChops
        W, H = target.size
        old = self._previous if self._previous is not None and self._previous.size == target.size else target
        self._fx_frames([(ImageChops.invert(target), 0.06), (Image.new("RGB", (W, H), "#000000"), 0.05),
                         (Image.new("RGB", (W, H), "#FFFFFF"), 0.05), (Image.blend(target, old, 0.12), 0.12)])
        self._full(target)

    def _fx_glitch(self, target):
        """A few frames of rows sliding sideways, mixing the old and the new screen, then the new one."""
        import numpy as np
        from PIL import Image
        old = self._previous if self._previous is not None and self._previous.size == target.size else target
        a, b = np.asarray(old), np.asarray(target)
        rng = np.random.default_rng()
        frames = []
        for k in range(3):
            mix = (rng.random((a.shape[0], 1, 1)) < (k + 1) / 4)
            img = np.where(mix, b, a).copy()
            for _ in range(8):
                y, h = int(rng.integers(0, a.shape[0] - 8)), int(rng.integers(2, 14))
                img[y:y + h] = np.roll(img[y:y + h], int(rng.integers(-24, 24)), axis=1)
            frames.append((Image.fromarray(img), 0.04))
        self._fx_frames(frames)
        self._full(target)

    def _fx_curtain(self, target, step=32):
        """The new screen slides down over the old one, a band at a time (only the bands are sent)."""
        W, H = target.size
        for y in range(0, H, step):
            if self._halt.is_set():
                break
            self.screen.send_image(target.crop((0, y, W, min(H, y + step))), 0, y)
            self.screen.end_frame()
            time.sleep(0.02)
        self.last_frame = target
        self.frame_no += 1

    def _transition(self, target, pause=0.05, whole=False):
        """Screen change in cascade: each block of the target screen comes in at a time.
        whole: every pixel of each block is sent, and then the gaps between blocks (a theme change: nothing of the
        previous theme may stay on the screen)."""
        from PIL import Image
        current = self._previous.copy()
        covered = Image.new("RGB", target.size, "#000000") if whole else None
        for rects in self.renderer.transition_steps():
            for x, y, w, h in rects:
                if w <= 0 or h <= 0:
                    continue
                piece = target.crop((x, y, x + w, y + h))
                current.paste(piece, (x, y))
                if whole:
                    covered.paste((255, 255, 255), (x, y, x + w, y + h))
                    self.screen.send_image(piece, x, y)
                    continue
                for rx, ry, rw, rh in changed_regions(piece, self._previous.crop((x, y, x + w, y + h))):
                    self.screen.send_image(piece.crop((rx, ry, rx + rw, ry + rh)), x + rx, y + ry)
            self.screen.end_frame()
            self.last_frame = current.copy()
            self.frame_no += 1
            if self._halt.is_set():
                break
            time.sleep(pause)
        rest = changed_regions(Image.new("RGB", target.size, "#ffffff"), covered) if whole else changed_regions(target, current)
        for x, y, w, h in rest:   # what is left (gaps between panels)
            self.screen.send_image(target.crop((x, y, x + w, y + h)), x, y)
        self.screen.end_frame()
        self.last_frame = target
        self.frame_no += 1

    def _read_sensors(self, state):
        try:
            self.collector.update()
        except Exception as e:  # noqa: BLE001
            self.log(f"Sensor read error: {e}")
        c = self.collector
        while c.events:
            self.log(c.events.pop(0))
        if c.last_summary is not None and c.last_summary is not self.last_summary:
            self.last_summary = c.last_summary
            self._save_last_game(c.last_summary)
            try:
                import history
                if history.save(self.cfg, c.last_summary):
                    self.log(f"Game saved to the history: {c.last_summary.get('name')}")
            except Exception as e:  # noqa: BLE001
                self.log(f"Could not save the game to the history: {e}")
        st = c.status
        source = st.get("source")
        if source and source != state.get("source"):
            if source == "embedded":
                self.log("Sensors: embedded monitor" + ("" if st.get("admin") else
                         " (no administrator rights: CPU and motherboard temperatures may be missing)"))
            else:
                reason = st.get("embedded_error")
                self.log("Sensors: LibreHardwareMonitor web server" + (f" (embedded monitor unavailable: {reason})" if reason else ""))
            state["source"] = source
        lhm = st.get("lhm")
        if lhm != state.get("lhm"):
            if lhm:
                self.log(f"Sensors unavailable ({lhm})")
            elif state.get("lhm"):
                self.log("Sensors OK")
            state["lhm"] = lhm

    def _update_eco(self):
        c = self.collector
        want = (self.eco_enabled and not self.demo and not c.in_game() and not c.summary
                and idle_seconds() >= self.eco_after)
        if want != self.eco:
            self.eco = want
            anim = bool((self.cfg.get("animation") or {}).get("enabled", True))
            self.renderer.anim_enabled = anim and not want
            self.log("Eco mode on (you are away)" if want else "Eco mode off")

    _rest_preview_until = 0.0

    def _update_rest(self):
        """Rest: with the PC idle (no game), the screen shows a big clock, the date and the weather; any use of
        the PC brings the theme back. Settings › Rest (next to the screen-off options)."""
        c = self.collector
        now = time.monotonic()
        preview = now < self._rest_preview_until
        want = preview or (self.rest_enabled and not self.demo and not c.in_game() and not c.summary
                           and idle_seconds() >= self.rest_after)
        if want != self.rest:
            self.rest = want
            if not preview:
                self.log("Rest screen on (the PC is idle)" if want else "Rest screen off")
        c.rest = want

    def _cycle(self, state):
        t0 = time.monotonic()
        self.beat = t0
        self._read_sensors(state)
        self._update_eco()
        self._update_rest()
        self._apply_brightness()
        next_read = t0 + (self.eco_interval if self.eco else self.interval)
        # between reads: frames only while something moves or a change is due
        while not self._halt.is_set() and not self.paused and not self.released and not self.sleeping:
            t_frame = time.monotonic()
            self.beat = t_frame
            if not self._send_frame():
                return
            if self.once:
                self._halt.set()
                return
            while not self._halt.is_set() and not self.paused and not self.released and not self.sleeping:
                left = next_read - time.monotonic()
                if left <= 0:
                    break
                r = self.renderer
                if r.animating:
                    self._wait(min(left, max(0.0, self.anim_step - (time.monotonic() - t_frame))))
                else:
                    due = (r.wake_at - time.monotonic()) if r.wake_at else left
                    self._wait(min(left, self.fast_step, max(0.0, due)))
                try:
                    changed = False if self.eco else self.collector.update_fast()
                except Exception:  # noqa: BLE001
                    changed = False
                if changed or r.animating or (r.wake_at and time.monotonic() >= r.wake_at):
                    break
            if time.monotonic() >= next_read:
                return

    def run(self):
        state = {}
        crashes = deque(maxlen=5)
        while not self._halt.is_set():
            try:
                self._check_schedule()
                if self.paused or self.released or self.sleeping:
                    if self.paused and not self.released and not self.sleeping:
                        self._read_sensors(state)   # values (and the game sessions) stay current while frozen
                        self._wait(self.interval)
                    else:
                        self._wait(0.5)
                    continue
                self._cycle(state)
            except Exception as e:  # noqa: BLE001 — never let the screen die: log, reset and continue
                crashes.append(time.monotonic())
                where = traceback.extract_tb(e.__traceback__)[-1]
                self.log(f"Recovered from an error: {type(e).__name__}: {e} ({Path(where.filename).name}:{where.lineno})")
                try:
                    self.screen.close()
                except Exception:  # noqa: BLE001
                    pass
                self.connected = False
                self._previous = None
                busy = len(crashes) == crashes.maxlen and crashes[-1] - crashes[0] < 60
                self._wait(30 if busy else 3)
        self._shutdown()

    def _shutdown(self):
        if self.connected and self.off_on_exit and not self.sleeping:
            try:
                self.screen.turn_off()
                self.log("Screen off")
            except Exception:  # noqa: BLE001
                pass
        self.screen.close()
        self.connected = False
        try:
            self.collector.close()
        except Exception:  # noqa: BLE001
            pass
