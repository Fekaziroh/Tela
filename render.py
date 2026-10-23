"""Draws the panel from the widget list in the config file."""
import datetime
import math
import re
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

from media import progress as media_progress

DEFAULT_FONTS = {
    "regular": ["bahnschrift.ttf", "segoeui.ttf", "DejaVuSans.ttf"],
    "bold": ["bahnschrift.ttf:Bold", "segoeuib.ttf", "DejaVuSans-Bold.ttf"],
}

DEFAULT_COLORS = {
    "background": "#000000", "panel": "#141414", "text": "#FFFFFF", "secondary": "#8C8C8C",
    "track": "#333333", "accent": "#FFFFFF", "warn": "#FF9F0A", "crit": "#FF453A",
}

# Words drawn on the screen. Layout texts starting with "#" are looked up here.
SCREEN_TEXT = {
    "pt": {
        "weekdays": ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"],
        "load": "USO", "clock": "CLOCK", "power": "CONSUMO", "fan": "FAN", "temp": "TEMP", "mem": "MEM",
        "network": "REDE", "volume": "VOLUME", "muted": "MUDO", "gb_used": " GB em uso", "disks": "DISCOS",
        "hotspot": "HOTSPOT ", "max": "máx ", "no_internet": "SEM INTERNET", "for": "há ",
        "router_ok": "roteador OK", "router_down": "sem resposta do roteador", "loss": "% perda",
        "summary": "RESUMO DA SESSÃO", "fps_avg": "FPS MÉDIO", "fps_1low": "1% LOW", "fps_max": "FPS MÁXIMO",
        "cpu_max": "CPU · MÁX", "gpu_max": "GPU · MÁX", "hotspot_max": "HOTSPOT · MÁX",
        "fps_session": "FPS DURANTE A SESSÃO", "example_game": "Exemplo de jogo",
    },
    "en": {
        "weekdays": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
        "load": "LOAD", "clock": "CLOCK", "power": "POWER", "fan": "FAN", "temp": "TEMP", "mem": "MEM",
        "network": "NET", "volume": "VOLUME", "muted": "MUTED", "gb_used": " GB used", "disks": "DISKS",
        "hotspot": "HOTSPOT ", "max": "max ", "no_internet": "NO INTERNET", "for": "for ",
        "router_ok": "router OK", "router_down": "router not responding", "loss": "% loss",
        "summary": "SESSION SUMMARY", "fps_avg": "AVG FPS", "fps_1low": "1% LOW", "fps_max": "MAX FPS",
        "cpu_max": "CPU · MAX", "gpu_max": "GPU · MAX", "hotspot_max": "HOTSPOT · MAX",
        "fps_session": "FPS DURING THE SESSION", "example_game": "Example game",
    },
    "es": {
        "weekdays": ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"],
        "load": "USO", "clock": "RELOJ", "power": "CONSUMO", "fan": "VENT.", "temp": "TEMP", "mem": "MEM",
        "network": "RED", "volume": "VOLUMEN", "muted": "SILENCIO", "gb_used": " GB en uso", "disks": "DISCOS",
        "hotspot": "HOTSPOT ", "max": "máx ", "no_internet": "SIN INTERNET", "for": "hace ",
        "router_ok": "router OK", "router_down": "el router no responde", "loss": "% pérdida",
        "summary": "RESUMEN DE LA SESIÓN", "fps_avg": "FPS MEDIO", "fps_1low": "1% LOW", "fps_max": "FPS MÁXIMO",
        "cpu_max": "CPU · MÁX", "gpu_max": "GPU · MÁX", "hotspot_max": "HOTSPOT · MÁX",
        "fps_session": "FPS DURANTE LA SESIÓN", "example_game": "Juego de ejemplo",
    },
    "zh": {
        "weekdays": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
        "load": "占用", "clock": "频率", "power": "功耗", "fan": "风扇", "temp": "温度", "mem": "显存",
        "network": "网络", "volume": "音量", "muted": "静音", "gb_used": " GB 已用", "disks": "磁盘",
        "hotspot": "热点 ", "max": "最高 ", "no_internet": "已断网", "for": "已 ",
        "router_ok": "路由器正常", "router_down": "路由器无响应", "loss": "% 丢包",
        "summary": "游戏总结", "fps_avg": "平均 FPS", "fps_1low": "1% LOW", "fps_max": "最高 FPS",
        "cpu_max": "CPU · 最高", "gpu_max": "GPU · 最高", "hotspot_max": "热点 · 最高",
        "fps_session": "本局 FPS", "example_game": "示例游戏",
    },
}
CJK_FONTS = {
    "regular": ["msyh.ttc", "simhei.ttf", "NotoSansCJK-Regular.ttc", "NotoSansSC-Regular.otf"],
    "bold": ["msyhbd.ttc", "simhei.ttf", "NotoSansCJK-Bold.ttc", "NotoSansSC-Bold.otf"],
}

STATIC_TYPES = {"panel", "text", "rect"}


class Renderer:
    def __init__(self, cfg, width, height, ss=2, base=None, fields=None, lang="pt", cache_static=True, logo_dirs=None):
        self.W, self.H, self.S = width, height, ss
        self.fields = fields or {}
        self.base = Path(base) if base else Path.cwd()
        self.logo_dirs = [Path(p) for p in (logo_dirs or [self.base / "logos"])]
        bg = cfg.get("background") or {}
        self.bg_image = str(bg.get("image") or "")
        self.bg_dim = max(0.0, min(0.9, float(bg.get("dim", 40)) / 100))
        self.panel_opacity = max(0.2, min(1.0, float(bg.get("panel_opacity", 100)) / 100)) if self.bg_image else 1.0
        self.words = SCREEN_TEXT.get(lang, SCREEN_TEXT["en"])
        self._images = {}
        self._frame = None
        self.logos_cfg = cfg.get("logos") or {}
        mcfg = cfg.get("media") or {}
        self.media_in_game = str(mcfg.get("during_game", "date")).lower() == "date"
        self.media_progress = bool(mcfg.get("progress", True))
        anim = cfg.get("animation") or {}
        self.anim_enabled = bool(anim.get("enabled", True))
        self.anim_duration = max(0.05, float(anim.get("duration", 0.6)))
        self._anims = {}
        self._now = time.monotonic()
        self.animating = False   # True while something is still moving
        self.wake_at = None      # monotonic time of the next scheduled change (marquee pauses)
        self.colors = {**DEFAULT_COLORS, **(cfg.get("colors") or {})}
        self.widgets = cfg.get("widgets") or []
        if str((cfg.get("ssd") or {}).get("number", "activity")).lower() == "space":
            self.widgets = [self._swap_ssd(w) for w in self.widgets]
        f = cfg.get("fonts") or {}
        self.font_lists = {k: f.get(k) or v for k, v in DEFAULT_FONTS.items()}
        if lang == "zh":   # Chinese needs a font with the characters (Microsoft YaHei comes with Windows)
            self.font_lists = {k: CJK_FONTS[k] + v for k, v in self.font_lists.items()}
        self._fonts = {}
        self._glyphs = {}
        self._measure = {}
        self.cache_static = cache_static
        self._static = None
        self._shown = {}         # widget id -> monotonic time it became visible (for the fade-in)
        self._marquee = {}       # (widget id, line) -> [text, start time]
        self._first = True
        self.layout = "normal"
        self.current_widgets = self.widgets

    @staticmethod
    def _swap_ssd(w):
        """Items marked 'ssd: true': swap activity <-> used space between the number and the bar."""
        if not w.get("ssd") or not w.get("sensor"):
            return w
        w = dict(w)
        s = w["sensor"]
        w["sensor"] = s[:-4] if s.endswith("_act") else s + "_act"
        w.pop("alerts", None)
        if w.get("type") == "value":
            w["alerts"] = [{"above": 90, "color": "warn"}]   # "disk almost full" moves to the number
        return w

    def _txt(self, t):
        """{field} -> detected value (CPU name, drive letter...); '#key' -> word in the screen language."""
        if not isinstance(t, str):
            return t
        if "{" in t:
            t = re.sub(r"\{(\w+)\}", lambda m: str(self.fields.get(m.group(1), "")), t)
        if t.startswith("#"):
            return self.words.get(t[1:], t[1:])
        return t

    def _num(self, v, default):
        try:
            return float(self._txt(v)) if isinstance(v, str) else float(v)
        except (TypeError, ValueError):
            return default

    # ------------------------------------------------------------ helpers
    def color(self, c, default="text"):
        c = default if c is None else c
        return self.colors.get(c, c)

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self._fonts:
            px = max(1, int(round(size * self.S)))
            ft = None
            for name in self.font_lists["bold" if bold else "regular"]:
                file, _, var = name.partition(":")
                try:
                    ft = ImageFont.truetype(file, px)
                except OSError:
                    continue
                if var:
                    try:
                        ft.set_variation_by_name(var)
                    except Exception:  # noqa: BLE001
                        pass
                break
            self._fonts[key] = ft or ImageFont.load_default(px)
        return self._fonts[key]

    def _baseline(self, parts, y):
        return y * self.S + max(self._cap(ft) for _, ft, _ in parts) / 2

    def _cap(self, ft):
        key = ("cap", id(ft))
        v = self._measure.get(key)
        if v is None:
            v = self._measure[key] = -ft.getbbox("H", anchor="ls")[1]
        return v

    def _length(self, text, ft):
        key = (text, id(ft))
        v = self._measure.get(key)
        if v is None:
            if len(self._measure) > 4000:
                self._measure.clear()
            v = self._measure[key] = ft.getlength(text)
        return v

    def _text(self, d, x, y, text, ft, fill):
        """Draws text at the baseline (x, y). Rendered glyph runs are cached: numbers and labels repeat a lot."""
        key = (text, id(ft))
        hit = self._glyphs.get(key)
        if hit is None:
            if len(self._glyphs) > 1500:
                self._glyphs.clear()
            hit = self._glyphs[key] = ft.getmask2(text, mode="L", anchor="ls")
        mask, (ox, oy) = hit
        if mask.size[0] and mask.size[1]:
            d.draw.draw_bitmap((int(round(x)) + ox, int(round(y)) + oy), mask, d._getink(fill)[0])

    def _line(self, d, x, y, parts, align="left"):
        """Draws several (text, font, color) runs on the same baseline, vertically centered on y."""
        parts = [p for p in parts if p[0]]
        if not parts:
            return
        lengths = [self._length(t, ft) for t, ft, _ in parts]
        base = self._baseline(parts, y)
        cx = x * self.S
        if align == "right":
            cx -= sum(lengths)
        elif align == "center":
            cx -= sum(lengths) / 2
        for (t, ft, c), w in zip(parts, lengths, strict=True):
            self._text(d, cx, base, t, ft, c)
            cx += w

    def _alert_color(self, w, v, default):
        color = default
        if v is not None:
            for a in sorted(w.get("alerts") or [], key=lambda a: a["above"]):
                if v >= a["above"]:
                    color = self.color(a["color"])
        return color

    @staticmethod
    def _format(w, v, empty):
        if v is None:
            return empty
        try:
            return w.get("format", "{:.0f}").format(v * w.get("scale", 1))
        except (ValueError, TypeError):
            return str(v)

    def _smooth(self, w, v):
        """Value shown in bars/gauges: slides from the old value to the new one (ease-out)."""
        key = id(w)
        if not self.anim_enabled or v is None:
            self._anims.pop(key, None)
            return v
        a = self._anims.get(key)
        if a is None:
            self._anims[key] = [v, v, self._now]
            return v

        def current():
            start, end, t0 = a
            f = min(1.0, (self._now - t0) / self.anim_duration)
            return start + (end - start) * (1 - (1 - f) ** 3)

        if v != a[1]:
            a[:] = [current(), v, self._now]
        x = current()
        if self._now - a[2] < self.anim_duration:
            self.animating = True
        return x

    def _fraction(self, w, v):
        if v is None:
            return 0.0
        mn, mx = self._num(w.get("min", 0), 0.0), self._num(w.get("max", 100), 100.0)
        return 0.0 if mx == mn else max(0.0, min(1.0, (v - mn) / (mx - mn)))

    def _value_parts(self, w, v):
        size = w.get("size", 14)
        unit_size = w.get("unit_size", max(8, round(size * 0.55)))
        color = self._alert_color(w, v, self.color(w.get("color"), "text"))
        parts = []
        if w.get("prefix"):
            parts.append((self._txt(w["prefix"]), self.font(unit_size), self.color(w.get("prefix_color"), "secondary")))
        parts.append((self._format(w, v, str(self._txt(w.get("empty", "--")))), self.font(size, w.get("bold", False)), color))
        if w.get("unit") and v is not None:
            parts.append((self._txt(w["unit"]), self.font(unit_size), self.color(w.get("unit_color"), "secondary")))
        return parts

    def _wake(self, t):
        if self.wake_at is None or t < self.wake_at:
            self.wake_at = t

    # ------------------------------------------------------------ visibility
    def _visible(self, w, col):
        if w.get("requires") and not self.fields.get(w["requires"]):
            return False   # e.g. the 2nd disk only shows if it exists
        conds = w.get("when")
        if not conds:
            return True
        conds = [conds] if isinstance(conds, str) else conds
        fps = col.value("fps") is not None
        # a game counts while its process is open (minimized or alt-tabbed too), see Collector.game_open
        game = fps or (hasattr(col, "game_open") and col.game_open())
        media = bool(col.media_info()) if hasattr(col, "media_info") else False
        state = {"game": game, "no_game": not game, "fps": fps, "no_fps": not fps, "media": media,
                 "no_media": not media, "media_in_game": game and media and self.media_in_game,
                 # logos: no FPS on the left and the music is not there either
                 "logos": not fps and not (media and not game)}
        state["no_media_in_game"] = not state["media_in_game"]
        return all(state.get(c, True) for c in conds)

    # ------------------------------------------------------------ widgets
    def _w_panel(self, d, w, col):
        S = self.S
        x, y, wd, h = w["x"], w["y"], w["w"], w["h"]
        k = w.get("k", 1)
        border = w.get("border")
        fill = self.color(w.get("color"), "panel")
        opacity = self.panel_opacity if w.get("color") is None else 1.0
        box = [x * S, y * S, (x + wd) * S - 1, (y + h) * S - 1]
        if opacity < 0.999:   # translucent panels over a background image
            layer = Image.new("L", self._frame.size, 0)
            ImageDraw.Draw(layer).rounded_rectangle(box, radius=w.get("radius", 6 * k) * S, fill=int(255 * opacity))
            self._frame.paste(Image.new("RGB", self._frame.size, fill), (0, 0), layer)
            if border:
                d.rounded_rectangle(box, radius=w.get("radius", 6 * k) * S, outline=self.color(border), width=S)
        else:
            d.rounded_rectangle(box, radius=w.get("radius", 6 * k) * S, fill=fill,
                                outline=self.color(border) if border else None, width=S if border else 0)
        if w.get("title") or w.get("subtitle"):
            size = w.get("title_size", 12 * k)
            sub = self._txt(w.get("subtitle", ""))
            self._line(d, x + 10 * k, y + 14 * k, [
                (self._txt(w.get("title", "")), self.font(size, True), self.color(w.get("title_color"), "secondary")),
                (("  " if w.get("title") and sub else "") + sub, self.font(size), self.color("text")),
            ])

    def _w_network(self, d, w, col):
        """Network panel with 3 states: normal (ping in the title), unstable (orange border, loss) and down."""
        x, y, wd, h = w["x"], w["y"], w["w"], w["h"]
        info = col.network_info() if hasattr(col, "network_info") else {"state": None}
        state = info.get("state")
        cx = x + wd / 2
        T = self.words
        k = w.get("k", 1)

        def f(size, bold=False):
            return self.font(size * k, bold)
        if state == "down":
            since = info.get("since") or time.time()
            sec = int(time.time() - since)
            elapsed = f"{sec // 3600}:{sec // 60 % 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60:02d}:{sec % 60:02d}"
            self._w_panel(d, {"x": x, "y": y, "w": wd, "h": h, "color": w.get("down_color", "#3A1010"), "border": "crit", "k": k}, col)
            self._line(d, cx, y + 16 * k, [(T["no_internet"], f(11, True), self.color("crit"))], "center")
            self._line(d, cx, y + 33 * k, [(T["for"], f(10), self.color("secondary")),
                                       (elapsed, f(13, True), self.color("text"))], "center")
            gw = info.get("gateway_ok")
            txt = T["router_ok"] if gw else (T["router_down"] if gw is False else "")
            self._line(d, cx, y + 47 * k, [(txt, f(8), self.color("secondary"))], "center")
            self._wake(self._now + 1.0 - (time.time() % 1.0))   # the timer ticks every second
            return
        level = info.get("level", "ok")
        level_color = {"ok": "text", "warn": "warn", "crit": "crit"}[level]
        border = None if state in (None, "normal") else ("crit" if level == "crit" else "warn")
        loss = info.get("loss") or 0
        if state == "unstable" and loss >= 1:
            self._w_panel(d, {"x": x, "y": y, "w": wd, "h": h, "border": border, "k": k}, col)
            self._line(d, x + 10 * k, y + 14 * k, [(f"{loss:.0f}", f(11, True), self.color("crit")),
                                           (T["loss"], f(8), self.color("crit"))], "left")
        else:
            self._w_panel(d, {"x": x, "y": y, "w": wd, "h": h, "title": self._txt(w.get("title", "#network")),
                              "border": border, "k": k}, col)
        if info.get("ms") is not None:
            self._line(d, x + wd - 10 * k, y + 14 * k, [(f"{info['ms']:.0f}", f(11, True), self.color(level_color)),
                                                (" ms", f(8), self.color("secondary"))], "right")
        for i, (label, sensor) in enumerate((("DOWN", w.get("sensor_down", "net_down")), ("UP", w.get("sensor_up", "net_up")))):
            yy = y + 31 * k + i * 15 * k
            self._line(d, x + 10 * k, yy, [(label, f(9), self.color("secondary"))], "left")
            v = col.value(sensor)
            self._line(d, x + wd - 10 * k, yy, [("--" if v is None else f"{v:.1f}", f(13), self.color("text")),
                                            (" Mbps", f(7), self.color("secondary"))], "right")

    MARQUEE_PAUSE = 3.0     # seconds still at the start and at the end
    MARQUEE_SPEED = 22.0    # screen pixels per second

    def _clipped_text(self, x, y, width, text, ft, color, key):
        """Text that fits the width. If it is longer, it slides slowly to show the end and comes back
        (or gets '…' when animations are off)."""
        S = self.S
        avail = width * S
        tw = ft.getlength(text)
        d = ImageDraw.Draw(self._frame)
        if tw <= avail:
            self._marquee.pop(key, None)
            self._line(d, x, y, [(text, ft, color)])
            return
        if not self.anim_enabled:
            while text and ft.getlength(text + "…") > avail:
                text = text[:-1]
            self._line(d, x, y, [(text.rstrip() + "…", ft, color)])
            return
        st = self._marquee.get(key)
        if st is None or st[0] != text:
            st = self._marquee[key] = [text, self._now]
        distance = (tw - avail) / S + 4
        scroll = distance / self.MARQUEE_SPEED
        cycle = 2 * self.MARQUEE_PAUSE + scroll
        t = (self._now - st[1]) % cycle
        if t < self.MARQUEE_PAUSE:
            offset = 0.0
            self._wake(self._now + self.MARQUEE_PAUSE - t)
        elif t < self.MARQUEE_PAUSE + scroll:
            offset = (t - self.MARQUEE_PAUSE) * self.MARQUEE_SPEED
            self.animating = True
        else:
            offset = distance
            self._wake(self._now + cycle - t)
        # draws on a strip and pastes it clipped, with soft edges where text is hidden
        half = max(9.0, ft.size / S * 0.85)
        top = int((y - half) * S)
        hgt = int(2 * half * S)
        strip = Image.new("L", (int(avail), hgt), 0)
        base = self._baseline([(text, ft, color)], y) - top
        ImageDraw.Draw(strip).text((-offset * S, base), text, font=ft, fill=255, anchor="ls")
        fade = max(2, min(int(8 * S), int(avail) // 4))
        ramp = Image.linear_gradient("L").rotate(90, expand=True).resize((fade, hgt))   # 0 -> 255 left to right
        mask = Image.new("L", strip.size, 255)
        if offset > 0.5:
            mask.paste(ramp, (0, 0))
        if offset < distance - 0.5:
            mask.paste(ramp.transpose(Image.FLIP_LEFT_RIGHT), (int(avail) - fade, 0))
        strip = ImageChops.multiply(strip, mask)
        self._frame.paste(Image.new("RGB", strip.size, color), (int(x * S), top), strip)

    def _w_media(self, d, w, col):
        """Music/video playing. Paused: stays a few seconds, then fades out."""
        info = col.media_info() if hasattr(col, "media_info") else None
        if not info:
            return
        from media import Media
        gone = info.get("paused_for")
        alpha = 1.0
        if gone is not None:
            if gone >= Media.GRACE:
                alpha = max(0.0, 1.0 - (gone - Media.GRACE) / Media.FADE) if self.anim_enabled else 0.0
                self.animating = True
            else:
                self._wake(self._now + Media.GRACE - gone)
        if alpha <= 0:
            return
        if alpha < 1:
            before = self._frame.copy()
            self._draw_media(d, w, info)
            self._frame.paste(Image.blend(before, self._frame, alpha * alpha * (3 - 2 * alpha)))
        else:
            self._draw_media(d, w, info)

    def _draw_media(self, d, w, info):
        """Cover + title + artist, with a progress line.
        progress: bottom (default) | below_title | beside_artist | none; show_time adds '1:23 / 3:45'."""
        S = self.S
        k = w.get("k", 1)
        x, y, wd, h = w["x"], w["y"], w["w"], w["h"]
        tx = x
        cover = info.get("cover")
        if cover is not None and w.get("cover", True):
            side = h
            key = ("cover", info.get("key"), round(side * S))
            im = self._images.get(key)
            if im is None:
                n = max(1, round(side * S))
                im = cover.resize((n, n), Image.LANCZOS)
                mask = Image.new("L", im.size, 0)
                ImageDraw.Draw(mask).rounded_rectangle([0, 0, n - 1, n - 1], radius=5 * k * S, fill=255)
                im.putalpha(mask)
                self._images = {kk: v for kk, v in self._images.items() if kk[0] != "cover"}
                self._images[key] = im
            self._frame.paste(im, (int(x * S), int(y * S)), im)
            tx = x + side + 7 * k
        width = x + wd - tx
        f1, f2 = self.font(w.get("size", 11), True), self.font(w.get("artist_size", 9 * k))
        sub = info["artist"] or info.get("app", "")
        mode = str(w.get("progress", "bottom")).lower() if w.get("progress", True) not in (False, None) else "none"
        prog = media_progress(info) if (self.media_progress and mode != "none") else None
        tline = None
        if prog is not None and w.get("show_time") and info.get("duration"):
            tline = f"{self._mmss(prog * info['duration'])} / {self._mmss(info['duration'])}"
        ft = self.font(max(6.0, w.get("artist_size", 9 * k) - 1))
        tw = self._length(tline, ft) / S + 5 * k if tline else 0
        if prog is None:
            ty, ay, line = y + h * 0.3, y + h * 0.78, None
        elif mode == "below_title":
            ty, ay, line = y + h * 0.24, y + h * 0.82, (tx, y + h * 0.5 - 1 * k, width)
        elif mode == "beside_artist":
            ty, ay = y + h * 0.3, y + h * 0.78
            aw = min(self._length(sub, f2) / S + 6 * k, width * 0.55)
            line = (tx + aw, ay - 1 * k, width - aw)
        else:
            ty, ay, line = y + h * 0.26, y + h * 0.68, (tx, y + h - 2 * k, width)
        self._clipped_text(tx, ty, width, info["title"], f1, self.color("text"), (id(w), "title"))
        artist_width = (line[0] - tx - 4 * k) if (line and mode == "beside_artist") else width
        self._clipped_text(tx, ay, max(10, artist_width), sub, f2, self.color("secondary"), (id(w), "artist"))
        if line is None:
            return
        lx, ly, lw = line
        lw -= tw
        th = 2 * k
        if lw > 4:
            d.rounded_rectangle([lx * S, ly * S, (lx + lw) * S, (ly + th) * S], radius=th * S / 2, fill=self.color("track"))
            if prog > 0:
                d.rounded_rectangle([lx * S, ly * S, (lx + max(th, lw * prog)) * S, (ly + th) * S], radius=th * S / 2,
                                    fill=self.color(w.get("color"), "accent"))
        if tline:
            self._line(d, lx + lw + tw, ly + th / 2, [(tline, ft, self.color("secondary"))], "right")
            self._wake(self._now + 1.0 - (time.time() % 1.0))   # the time ticks every second

    @staticmethod
    def _mmss(sec):
        sec = int(max(0, sec))
        return f"{sec // 3600}:{sec // 60 % 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60}:{sec % 60:02d}"

    def _w_rect(self, d, w, col):
        S = self.S
        x, y, wd, h = w["x"], w["y"], w["w"], w["h"]
        d.rectangle([x * S, y * S, (x + wd) * S - 1, (y + h) * S - 1], fill=self.color(w.get("color"), "track"))

    def _w_text(self, d, w, col):
        self._line(d, w["x"], w["y"], [(str(self._txt(w.get("text", ""))), self.font(w.get("size", 12), w.get("bold", False)),
                                        self.color(w.get("color"), "text"))], w.get("align", "left"))

    def _w_value(self, d, w, col):
        v = col.value(w.get("sensor"))
        self._line(d, w["x"], w["y"], self._value_parts(w, v), w.get("align", "left"))

    def _w_clock(self, d, w, col):
        now = datetime.datetime.now()
        fmt = w.get("format", "%H:%M").replace("{weekday}", self.words["weekdays"][now.weekday()])
        self._line(d, w["x"], w["y"], [(now.strftime(fmt), self.font(w.get("size", 24), w.get("bold", False)),
                                        self.color(w.get("color"), "text"))], w.get("align", "left"))

    def _w_bar(self, d, w, col):
        S = self.S
        v = col.value(w.get("sensor"))
        x, y, wd, h = w["x"], w["y"], w["w"], w.get("h", 4)
        r = h / 2 * S
        d.rounded_rectangle([x * S, y * S, (x + wd) * S, (y + h) * S], radius=r, fill=self.color(w.get("track_color"), "track"))
        f = self._fraction(w, self._smooth(w, v))
        if f > 0:
            c = self._alert_color(w, v, self.color(w.get("color"), "accent"))
            d.rounded_rectangle([x * S, y * S, (x + max(h, wd * f)) * S, (y + h) * S], radius=r, fill=c)

    def _w_gauge(self, d, w, col):
        S = self.S
        v = col.value(w.get("sensor"))
        k = w.get("k", 1)
        cx, cy, r, th = w["cx"], w["cy"], w["radius"], w.get("thickness", 7 * k)
        tw = max(1, int(round(th * S)))
        a0, a1 = w.get("start_angle", 135), w.get("end_angle", 405)
        box = [(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S]
        rr = (r - th / 2) * S

        def cap(ang, c):
            a = math.radians(ang)
            px, py = cx * S + rr * math.cos(a), cy * S + rr * math.sin(a)
            e = th * S / 2
            d.ellipse([px - e, py - e, px + e, py + e], fill=c)

        track = self.color(w.get("track_color"), "track")
        d.arc(box, a0, a1, fill=track, width=tw)
        cap(a0, track)
        cap(a1, track)
        f = self._fraction(w, self._smooth(w, v))
        if f > 0:
            c = self._alert_color(w, v, self.color(w.get("color"), "accent"))
            end = a0 + f * (a1 - a0)
            d.arc(box, a0, end, fill=c, width=tw)
            cap(a0, c)
            cap(end, c)
        wv = {"size": 26, **w, "color": w.get("text_color", "text")}
        vmax = col.value(w["max_sensor"]) if w.get("max_sensor") else None
        dy = w.get("offset_y", 0) * k - (4 * k if vmax is not None else 0)
        self._line(d, cx, cy + dy, self._value_parts(wv, v), "center")
        if vmax is not None:
            self._line(d, cx, cy + 20 * k, [(self.words["max"], self.font(8 * k), self.color("secondary")),
                                            (f"{vmax:.0f}°", self.font(9 * k, True), self.color("secondary"))], "center")

    def _w_graph(self, d, w, col):
        S = self.S
        x, y, wd, h = w["x"], w["y"], w["w"], w["h"]
        n = int(w.get("points", 60))
        hist = list(col.history(w.get("sensor"), max(n, 120)))[-n:]
        d.line([x * S, (y + h) * S, (x + wd) * S, (y + h) * S], fill=self.color(w.get("track_color"), "track"), width=S)
        vals = [v for v in hist if v is not None]
        if len(hist) < 2 or not vals:
            return
        mn = float(w.get("min", 0))
        mx = float(w["max"]) if "max" in w else max(max(vals) * 1.15, mn + 1e-6)
        step = wd / (n - 1)
        x0 = x + wd - step * (len(hist) - 1)
        pts = []
        for i, v in enumerate(hist):
            f = 0.0 if v is None else max(0.0, min(1.0, (v - mn) / (mx - mn)))
            pts.append(((x0 + i * step) * S, (y + h - f * h) * S))
        fill = w.get("fill_color", "#2A2A2A")
        if fill:
            d.polygon(pts + [(pts[-1][0], (y + h) * S), (pts[0][0], (y + h) * S)], fill=self.color(fill))
        d.line(pts, fill=self.color(w.get("color"), "accent"), width=max(1, int(1.5 * S)), joint="curve")

    @staticmethod
    def tint(im, color):
        """Makes a logo a single color, keeping its shape. Logos on a solid background lose the background."""
        alpha = im.getchannel("A")
        if alpha.getextrema()[0] == 255:   # no transparency: the corner color is the background
            bg = Image.new("RGB", im.size, im.getpixel((0, 0))[:3])
            diff = ImageChops.difference(im.convert("RGB"), bg).convert("L")
            alpha = diff.point(lambda p: 0 if p < 24 else min(255, p * 3))
        solid = Image.new("RGBA", im.size, color)
        solid.putalpha(alpha)
        return solid

    def _load_image(self, file, wpx, hpx, tint=None):
        key = (file, wpx, hpx, tint)
        if key not in self._images:
            im = None
            try:
                path = Path(file)
                if not path.is_absolute():
                    path = self.base / path
                im = Image.open(path).convert("RGBA")
                if tint:
                    im = self.tint(im, tint)
                box = im.getchannel("A").getbbox()
                if box:
                    im = im.crop(box)
                f = min(wpx / im.width, hpx / im.height)   # fits the box, keeping the aspect ratio
                im = im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))), Image.LANCZOS)
            except (OSError, ValueError):
                im = None
            self._images[key] = im
        return self._images[key]

    BRAND_WORDS = {
        "amd": ["amd", "radeon", "ryzen"], "nvidia": ["nvidia", "geforce", "rtx", "gtx"],
        "intel": ["intel", "core", "arc"], "msi": ["msi"], "asus": ["asus", "rog", "tuf"],
        "gigabyte": ["gigabyte", "aorus"], "asrock": ["asrock"], "evga": ["evga"], "zotac": ["zotac"],
        "sapphire": ["sapphire"], "powercolor": ["powercolor"], "xfx": ["xfx"], "pny": ["pny"],
    }
    IMAGE_EXT = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")

    def available_logos(self):
        """{file name: full path}; the user's folder wins over the program's."""
        found = {}
        for folder in reversed(self.logo_dirs):
            try:
                for p in folder.iterdir():
                    if p.suffix.lower() in self.IMAGE_EXT:
                        found[p.name] = str(p)
            except OSError:
                continue
        return dict(sorted(found.items(), key=lambda kv: kv[0].lower()))

    def logo_list(self, mode=None):
        """Logos that rotate: picked by the hardware brands (auto) or the user's list."""
        paths = self.available_logos()
        every = list(paths)
        lc = self.logos_cfg
        mode = mode or str(lc.get("mode", "auto")).lower()
        if mode == "list":
            names = lc.get("files", "")
            names = [n.strip() for n in (names.split(",") if isinstance(names, str) else names) if n and n.strip()]
            chosen = [n for n in names if n in every]
        else:
            chosen, brands = [], set()
            for key in ("cpu_brand", "gpu_brand", "gpu_board_brand", "board_brand"):
                brand = self.fields.get(key) or ""
                if not brand or brand in brands:   # one logo per brand (AMD CPU + AMD GPU = one logo)
                    continue
                brands.add(brand)
                words = self.BRAND_WORDS.get(brand, [brand])
                for n in every:
                    stem = n.lower().rsplit(".", 1)[0]
                    if any(re.search(rf"(^|[^a-z]){p}([^a-z]|$)", stem) for p in words) and n not in chosen:
                        chosen.append(n)
                        break
            if not chosen:
                chosen = every[:2]
        return [paths[n] for n in chosen]

    def brand_names(self):
        """Brands as text, for when there are no logo files."""
        out = []
        for key in ("cpu_brand", "gpu_brand", "gpu_board_brand", "board_brand"):
            b = (self.fields.get(key) or "").upper()
            if b and b not in out:
                out.append(b)
        return out

    def _w_image(self, d, w, col):
        """Image(s) inside the x,y,w,h box. With several, they rotate every 'switch_every' seconds."""
        tint = None
        if w.get("files") == "logos":   # uses the logo settings (auto by brand, or a list)
            files = self.logo_list()
            lc = self.logos_cfg
            every = max(1.0, float(lc.get("switch_every", 20)))
            fade = min(float(lc.get("fade", 1.2)), every / 2) if self.anim_enabled else 0
            if str(lc.get("color", "white")).lower() == "white":
                tint = self.color("text")
        else:
            files = [a for a in (w.get("files") or [w.get("file")]) if a]
            every = max(1.0, float(w.get("switch_every", 15)))
            fade = min(float(w.get("fade", 0.8)), every / 2) if self.anim_enabled else 0
        S = self.S
        x, y, wd, h = w["x"], w["y"], w["w"], w["h"]
        if not files and w.get("files") == "logos":   # no logo files: the brand names as text
            names = self.brand_names()
            if names:
                name = names[int(time.time() // every) % len(names)]
                self._line(d, x, y + h / 2, [(name, self.font(h * 1.05, True), self.color("text"))])
                if len(names) > 1:
                    self._wake(self._now + every - time.time() % every)
            return
        if not files:
            return
        t = time.time()
        idx = int(t // every) % len(files)
        phase = t % every
        layers = [(files[idx], 1.0)]
        if len(files) > 1:
            if fade > 0 and phase < fade:
                a = phase / fade  # 1st half: the old one fades out; 2nd half: the new one fades in
                if a < 0.5:
                    k = 1 - a * 2
                    layers = [(files[(idx - 1) % len(files)], k * k * (3 - 2 * k))]
                else:
                    k = a * 2 - 1
                    layers = [(files[idx], k * k * (3 - 2 * k))]
                self.animating = True
            else:
                self._wake(self._now + (every - phase))
        for file, alpha in layers:
            im = self._load_image(file, int(wd * S), int(h * S), tint)
            if im is None or alpha <= 0:
                continue
            align = w.get("align", "left")
            px = x * S
            if align == "center":
                px += (wd * S - im.width) / 2
            elif align == "right":
                px += wd * S - im.width
            py = y * S + (h * S - im.height) / 2
            mask = im.getchannel("A")
            if alpha < 1:
                mask = mask.point(lambda p, k=alpha: int(p * k))
            self._frame.paste(im, (int(px), int(py)), mask)

    def _w_frametime(self, d, w, col):
        """Time of each frame (PresentMon) over the last seconds. Spikes = stutters."""
        if col.value(w.get("fps_sensor", "fps")) is None:
            return
        times = col.frametimes(float(w.get("seconds", 2.0)))
        if len(times) < 2:
            return
        S = self.S
        x, y, wd, h = w["x"], w["y"], w["w"], w["h"]
        n = max(2, int(wd))
        # one column per pixel, keeping the worst frame of each column (spikes do not disappear)
        cols = [max(times[int(i * len(times) / n):max(int((i + 1) * len(times) / n), int(i * len(times) / n) + 1)])
                for i in range(n)]
        ordered = sorted(times)
        median = ordered[len(ordered) // 2]
        ceiling = max(median * 2.2, float(w.get("min_scale", 12)))
        d.line([x * S, (y + h) * S, (x + wd) * S, (y + h) * S], fill=self.color(w.get("track_color"), "track"), width=S)
        pts = [((x + i * wd / max(1, n - 1)) * S, (y + h - min(1.0, ms / ceiling) * h) * S) for i, ms in enumerate(cols)]
        fill = w.get("fill_color", "#2A2A2A")
        if fill:
            d.polygon(pts + [(pts[-1][0], (y + h) * S), (pts[0][0], (y + h) * S)], fill=self.color(fill))
        d.line(pts, fill=self.color(w.get("color"), "accent"), width=max(1, int(1.2 * S)), joint="curve")
        k = w.get("k", 1)
        if w.get("show_ms", True):
            self._line(d, x, y - 7 * k, [(f"{median:.1f}", self.font(8 * k, True), self.color("text")),
                                         (" ms", self.font(7 * k), self.color("secondary"))], "left")
        low = col.value(w.get("low_sensor", "fps_1low")) if w.get("show_1low", True) else None
        if low is not None:
            self._line(d, x + wd, y - 7 * k, [("1% ", self.font(7 * k), self.color("secondary")),
                                              (f"{low:.0f}", self.font(8 * k, True), self.color("text"))], "right")
        self.animating = True  # keeps drawing while there is a game

    # ------------------------------------------------------------ game session summary
    def _summary_layout(self, r):
        T = self.words

        def tile(x, y, w, h, label, key, unit, size):
            return [{"type": "panel", "x": x, "y": y, "w": w, "h": h},
                    {"type": "text", "text": label, "x": x + 12, "y": y + 16, "size": 9, "color": "secondary", "bold": True},
                    {"type": "value", "sensor": key, "x": x + 12, "y": y + h - 26, "size": size, "bold": True,
                     "unit": unit, "unit_size": 12}]
        left = max(0.0, r["expires"] - time.monotonic())
        W, H = self.W, self.H
        lay = [
            {"type": "text", "text": T["summary"], "x": 12, "y": 14, "size": 10, "color": "secondary", "bold": True},
            {"type": "text", "text": r["duration"], "x": W - 12, "y": 14, "size": 10, "color": "secondary", "align": "right"},
            {"type": "text", "text": r["name"][:28 if W > H else 22], "x": 12, "y": 40, "size": 22 if W > H else 19, "bold": True},
        ]
        tw = (W - 8 - 8) / 3   # three tiles with 4 px gaps
        if W > H:
            rows, big, small, graph = (62, 78), 30, 26, (218, H - 4 - 218 - 4)
            temps_y, temps_h = 144, 70
        else:
            rows, big, small = (60, 72), 24, 20
            temps_y, temps_h = 136, 62
            graph = (202, H - 4 - 202 - 4)
        tile_x = [4, 4 + tw + 4, 4 + 2 * (tw + 4)]
        for x, label, key in zip(tile_x, ("fps_avg", "fps_1low", "fps_max"), ("r.fps_avg", "r.fps_1low", "r.fps_max"), strict=True):
            lay += tile(x, rows[0], tw, rows[1], T[label], key, "", big)
        for x, label, key in zip(tile_x, ("cpu_max", "gpu_max", "hotspot_max"), ("r.cpu", "r.gpu", "r.hotspot"), strict=True):
            lay += tile(x, temps_y, tw, temps_h, T[label], key, "°C", small)
        gy, gh = graph
        lay += [
            {"type": "panel", "x": 4, "y": gy, "w": W - 8, "h": gh},
            {"type": "text", "text": T["fps_session"], "x": 16, "y": gy + 14, "size": 9, "color": "secondary", "bold": True},
            {"type": "graph", "sensor": "r.fps_series", "x": 16, "y": gy + 26, "w": W - 32, "h": gh - 36, "points": 120, "min": 0},
            {"type": "rect", "x": 0, "y": H - 4, "w": max(1, round(W * min(1.0, left / r["total"]))), "h": 4,
             "color": "accent"},
        ]
        return lay

    def transition_steps(self):
        """Blocks of the target screen, in the order they come in: top, panels (top to bottom, left to right)
        and, in the summary, the graph revealed in slices from left to right."""
        panels = sorted((w for w in self.current_widgets if w.get("type") in ("panel", "network")),
                        key=lambda w: (w["y"], w["x"]))
        if not panels:
            return [[(0, 0, self.W, self.H)]]
        steps = []
        top = min(p["y"] for p in panels)
        if top > 2:
            steps.append([(0, 0, self.W, top - 2)])
        for p in panels:
            x0, y0 = max(0, p["x"] - 2), max(0, p["y"] - 2)
            x1, y1 = min(self.W, p["x"] + p["w"] + 2), min(self.H, p["y"] + p["h"] + 2)
            has_graph = any(w.get("type") == "graph" and p["x"] <= w.get("x", -1) < p["x"] + p["w"]
                            and p["y"] <= w.get("y", -1) < p["y"] + p["h"] for w in self.current_widgets)
            if self.layout == "summary" and has_graph:
                slices = 8
                width = (x1 - x0) / slices
                for i in range(slices):
                    a, b = round(x0 + i * width), round(x0 + (i + 1) * width)
                    steps.append([(a, y0, b - a, y1 - y0)])
            else:
                steps.append([(x0, y0, x1 - x0, y1 - y0)])
        # block positions can be fractional (scaled layouts); the screen works in whole pixels
        return [[(int(round(x)), int(round(y)), int(round(w)), int(round(h))) for x, y, w, h in step] for step in steps]

    class _SummaryData:
        """Makes the summary look like a collector to the widgets."""

        def __init__(self, r):
            self.hist = list(r.get("fps_series") or [])
            self.v = {"r.fps_avg": r["fps_avg"], "r.fps_1low": r["fps_1low"], "r.fps_max": r["fps_max"],
                      **{f"r.{k}": v for k, v in r["max"].items()}}

        def value(self, name):
            return self.v.get(name)

        def history(self, name, n=120):
            return self.hist

        def frametimes(self, seconds=2.0):
            return []

    # ------------------------------------------------------------ frame
    def _draw(self, w, d, col):
        fn = getattr(self, "_w_" + str(w.get("type")), None)
        if fn is None:
            raise ValueError(f"unknown widget type: {w.get('type')!r}")
        fn(d, w, col)

    def _static_layer(self):
        if self._static is None:
            img = Image.new("RGB", (self.W * self.S, self.H * self.S), self.color("background"))
            self._paste_background(img)
            self._frame = img
            d = ImageDraw.Draw(img)
            for w in self.widgets:
                if self._is_static(w) and self._visible(w, None):
                    self._draw(w, d, None)
            self._static = img
        return self._static.copy()

    def _paste_background(self, img):
        """Background image, cropped to fill the screen and darkened so the numbers stay readable."""
        if not self.bg_image:
            return
        try:
            path = Path(self.bg_image)
            if not path.is_absolute():
                path = self.base / path
            im = Image.open(path).convert("RGB")
        except (OSError, ValueError):
            return
        W, H = img.size
        f = max(W / im.width, H / im.height)
        im = im.resize((max(W, round(im.width * f)), max(H, round(im.height * f))), Image.LANCZOS)
        left, top = (im.width - W) // 2, (im.height - H) // 2
        im = im.crop((left, top, left + W, top + H))
        if self.bg_dim > 0:
            im = Image.blend(im, Image.new("RGB", im.size, self.color("background")), self.bg_dim)
        img.paste(im)

    def _is_static(self, w):
        return self.cache_static and w.get("type") in STATIC_TYPES and not w.get("when")

    def draw(self, col):
        S = self.S
        self._now = time.monotonic()
        self.animating = False
        self.wake_at = None
        widgets = self.widgets
        summary = getattr(col, "summary", None)
        self.layout = "normal"
        if summary:
            widgets = self._summary_layout(summary)
            col = self._SummaryData(summary)
            self.layout = "summary"
            self.animating = True   # the countdown bar moves
            img = Image.new("RGB", (self.W * S, self.H * S), self.color("background"))
        else:
            img = self._static_layer()
        self._frame = img
        d = ImageDraw.Draw(img)
        self.current_widgets = widgets
        for w in widgets:
            if self.layout == "normal" and self._is_static(w):
                continue
            if not self._visible(w, col):
                self._shown.pop(id(w), None)
                continue
            fade = float(w.get("fade_in", 0.5)) if (w.get("fade") and self.anim_enabled) else 0
            since = self._shown.setdefault(id(w), -1e9 if self._first else self._now)
            alpha = min(1.0, (self._now - since) / fade) if fade else 1.0
            if alpha < 1.0:
                before = img.copy()
                self._draw(w, d, col)
                img.paste(Image.blend(before, img, alpha * alpha * (3 - 2 * alpha)))
                self.animating = True
            else:
                self._draw(w, d, col)
        self._first = False
        return img.reduce(S) if S != 1 else img   # box average of the supersampled frame (as sharp as LANCZOS, 10x faster)
