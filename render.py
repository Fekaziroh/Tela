"""Draws the panel from the widget list in the config file."""
import datetime
import math
import re
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter, ImageFont

from media import progress as media_progress

DEFAULT_FONTS = {
    "regular": ["bahnschrift.ttf", "segoeui.ttf", "DejaVuSans.ttf"],
    "bold": ["bahnschrift.ttf:Bold", "segoeuib.ttf", "DejaVuSans-Bold.ttf"],
}

# fonts an element can choose in the layout editor (all come with Windows 10/11; DejaVu is the Linux fallback)
FONT_FAMILIES = {
    "segoe": (["segoeui.ttf"], ["segoeuib.ttf"]),
    "arial": (["arial.ttf"], ["arialbd.ttf"]),
    "verdana": (["verdana.ttf"], ["verdanab.ttf"]),
    "trebuchet": (["trebuc.ttf"], ["trebucbd.ttf"]),
    "georgia": (["georgia.ttf"], ["georgiab.ttf"]),
    "consolas": (["consola.ttf", "DejaVuSansMono.ttf"], ["consolab.ttf", "DejaVuSansMono-Bold.ttf"]),
    "impact": (["impact.ttf"], ["impact.ttf"]),
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
        "used": "USADO", "duration": "DURAÇÃO",
        "w_clear": "ensolarado", "w_clear_night": "céu limpo", "w_partly": "parc. nublado", "w_cloudy": "nublado",
        "w_fog": "neblina", "w_drizzle": "garoa", "w_rain": "chuva", "w_showers": "pancadas", "w_snow": "neve",
        "w_storm": "tempestade", "w_rain_at": ", chuva às {h}h",
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
        "used": "USED", "duration": "DURATION",
        "w_clear": "sunny", "w_clear_night": "clear", "w_partly": "partly cloudy", "w_cloudy": "cloudy",
        "w_fog": "fog", "w_drizzle": "drizzle", "w_rain": "rain", "w_showers": "showers", "w_snow": "snow",
        "w_storm": "storm", "w_rain_at": ", rain at {h}:00",
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
        "used": "USADO", "duration": "DURACIÓN",
        "w_clear": "soleado", "w_clear_night": "despejado", "w_partly": "parc. nublado", "w_cloudy": "nublado",
        "w_fog": "niebla", "w_drizzle": "llovizna", "w_rain": "lluvia", "w_showers": "chubascos", "w_snow": "nieve",
        "w_storm": "tormenta", "w_rain_at": ", lluvia a las {h}h",
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
        "used": "已用", "duration": "时长",
        "w_clear": "晴", "w_clear_night": "晴朗", "w_partly": "多云", "w_cloudy": "阴", "w_fog": "雾",
        "w_drizzle": "毛毛雨", "w_rain": "雨", "w_showers": "阵雨", "w_snow": "雪", "w_storm": "雷雨", "w_rain_at": "，{h}点有雨",
    },
}
# fonts for titles in other scripts (Windows fonts first, Linux fallbacks after)
SCRIPT_FONTS = {
    "ko": (["malgun.ttf", "NotoSansCJK-Regular.ttc"], ["malgunbd.ttf", "NotoSansCJK-Bold.ttc"]),
    "ja": (["YuGothM.ttc", "meiryo.ttc", "msgothic.ttc", "msyh.ttc", "NotoSansCJK-Regular.ttc"],
           ["YuGothB.ttc", "meiryob.ttc", "msgothic.ttc", "msyhbd.ttc", "NotoSansCJK-Bold.ttc"]),
    "zh": (["msyh.ttc", "simhei.ttf", "NotoSansCJK-Regular.ttc"], ["msyhbd.ttc", "simhei.ttf", "NotoSansCJK-Bold.ttc"]),
}
_KANA = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff\uff66-\uff9f]")
_HANGUL = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]")
_HAN = re.compile(r"[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff01-\uff60]")


def text_script(text):
    """'ja', 'ko', 'zh' when the text needs a CJK font, else None (kana decides Japanese over Chinese)."""
    if not text or text.isascii():
        return None
    if _KANA.search(text):
        return "ja"
    if _HANGUL.search(text):
        return "ko"
    if _HAN.search(text):
        return "zh"
    return None


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
        self.art = str((cfg.get("layout") or {}).get("art") or "")   # the theme's own picture behind the blocks
        self.rest_widgets = list((cfg.get("layout") or {}).get("rest") or [])   # the theme's own Rest screen
        self.show_game = bool((cfg.get("fps") or {}).get("show_game", False))   # the game's name under the FPS
        vis = cfg.get("visual") or {}
        # Visual mode (Appearance › Screen mode): a picture, photos, a GIF or the clock instead of the sensors
        self.visual = vis if str((cfg.get("display") or {}).get("mode", "functional")).lower() == "visual" else None
        self.bg_dim = max(0.0, min(0.9, float(bg.get("dim", 40)) / 100))
        self.panel_opacity = max(0.2, min(1.0, float(bg.get("panel_opacity", 100)) / 100)) if self.bg_image else 1.0
        self.words = dict(SCREEN_TEXT.get(lang, SCREEN_TEXT["en"]))
        # the user's own words for the screen labels (Settings › Screen texts)
        self.words.update({k: str(v)[:24] for k, v in (cfg.get("texts") or {}).items()
                           if k in self.words and isinstance(v, (str, int, float)) and str(v).strip()})
        self._images = {}
        self._frame = None
        self.logos_cfg = cfg.get("logos") or {}
        self.weather_cfg = cfg.get("weather") or {}
        self.summary_cfg = cfg.get("session") or {}
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
        self._slots = self._group_slots(self.widgets)
        f = cfg.get("fonts") or {}
        self.font_lists = {k: f.get(k) or v for k, v in DEFAULT_FONTS.items()}
        if lang == "zh":   # Chinese needs a font with the characters (Microsoft YaHei comes with Windows)
            self.font_lists = {k: CJK_FONTS[k] + v for k, v in self.font_lists.items()}
        self._fonts = {}
        self._family = None      # font family of the element being drawn (layout editor choice)
        self._palette = None     # colors of the block being drawn (Layout editor: the block's own colors)
        self._font_meta = {}     # id(font) -> (size, bold), to find the same size in another script
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
    def _named(self, name):
        pal = self._palette
        if pal and name in pal:
            return pal[name]
        return self.colors.get(name, name)

    def color(self, c, default="text"):
        c = default if c is None else c
        if isinstance(c, str) and "@" in c:   # "accent@18" = the accent at 18% over the panel color
            name, _, pct = c.partition("@")
            try:
                a = max(0.0, min(1.0, float(pct) / 100))
                top, under = ImageColor.getrgb(self._named(name)), ImageColor.getrgb(self._named("panel"))
                return "#%02X%02X%02X" % tuple(round(u + (t - u) * a) for t, u in zip(top, under))
            except (ValueError, TypeError):
                return self._named(name)
        return self._named(c)

    def font(self, size, bold=False):
        fam = self._family if self._family in FONT_FAMILIES else None
        key = (size, bold, fam)
        if key not in self._fonts:
            px = max(1, int(round(size * self.S)))
            ft = None
            names = self.font_lists["bold" if bold else "regular"]
            if fam:
                names = FONT_FAMILIES[fam][1 if bold else 0] + list(names)
            for name in names:
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
            self._font_meta[id(self._fonts[key])] = (size, bold)
        return self._fonts[key]

    def _script_font(self, text, ft):
        """The same size in a font that has the characters (Japanese, Korean, Chinese titles)."""
        script = text_script(text)
        meta = self._font_meta.get(id(ft))
        if not script or not meta:
            return ft
        size, bold = meta
        key = ("script", script, size, bold)
        if key not in self._fonts:
            px = max(1, int(round(size * self.S)))
            found = None
            for name in SCRIPT_FONTS[script][1 if bold else 0]:
                try:
                    found = ImageFont.truetype(name, px)
                    break
                except OSError:
                    continue
            self._fonts[key] = found or ft
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

    def _line(self, d, x, y, parts, align="left", spacing=0):
        """Draws several (text, font, color) runs on the same baseline, vertically centered on y.
        spacing: extra pixels between letters (big clocks, where bold digits touch)."""
        parts = [(t, self._script_font(t, ft), c) for t, ft, c in parts if t]
        if not parts:
            return
        if spacing:
            parts = [(ch, ft, c) for t, ft, c in parts for ch in t]
        lengths = [self._length(t, ft) + spacing * self.S for t, ft, _ in parts]
        if spacing:
            lengths[-1] -= spacing * self.S
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
    @staticmethod
    def _group_slots(widgets):
        """Per block: which shared places are really filled (an item turned off frees its place)."""
        slots = {}
        for w in widgets:
            when = w.get("when") or []
            when = [when] if isinstance(when, str) else when
            s = slots.setdefault(w.get("group"), set())
            if w.get("type") == "media":
                s.add("media_right" if "media_in_game" in when else "media_left")
            if w.get("type") == "value" and w.get("sensor") == "fps":
                s.add("fps")
        return slots

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
        slots = self._slots.get(w.get("group"), {"fps", "media_left", "media_right"})
        state = {"game": game, "no_game": not game, "fps": fps, "no_fps": not fps, "media": media,
                 "no_media": not media,
                 "media_in_game": game and media and self.media_in_game and "media_right" in slots,
                 # logos: the FPS is not on the left and the media is not there either (counting only the
                 # items that are turned on in this block, so turning one off shows the logos instead)
                 "logos": not (fps and "fps" in slots) and not (media and not game and "media_left" in slots),
                 # themes with one media place: it shows the media whenever it would appear anywhere
                 "media_any": media and (not game or self.media_in_game)}
        state["no_media_any"] = not state["media_any"]
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
        if w.get("opacity") is not None and not self.bg_image:   # the theme's own translucency over its picture
            opacity = max(0.0, min(1.0, float(w["opacity"])))
        box = [x * S, y * S, (x + wd) * S - 1, (y + h) * S - 1]
        radius = w.get("radius", 6 * k) * S
        if w.get("shadow"):   # soft shadow under the panel
            self._shadow(box, radius, float(w["shadow"]) * k)
        if w.get("gradient") or w.get("gloss"):
            self._fancy_panel(box, radius, w, fill, opacity)
            if border:
                d.rounded_rectangle(box, radius=radius, outline=self.color(border), width=S)
        elif opacity < 0.999:   # translucent panels over a background image
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

    def _shadow(self, box, radius, px):
        S = self.S
        off = max(1, int(px * S))
        pad = off * 3
        x0, y0 = int(box[0]) - pad, int(box[1]) - pad
        bw, bh = int(box[2] - box[0]) + 2 * pad, int(box[3] - box[1]) + 2 * pad + off
        mask = Image.new("L", (bw, bh), 0)
        ImageDraw.Draw(mask).rounded_rectangle([pad, pad + off, bw - pad, bh - pad], radius=radius, fill=90)
        mask = mask.filter(ImageFilter.GaussianBlur(off))
        self._frame.paste(Image.new("RGB", (bw, bh), "#000000"), (x0, y0), mask)

    def _fancy_panel(self, box, radius, w, fill, opacity):
        """Panel with a vertical gradient ("gradient": [top, bottom]) and/or a glossy highlight on its upper part
        ("gloss": 0..1), like the glass buttons of the 2000s."""
        x0, y0, x1, y1 = (int(v) for v in box)
        bw, bh = max(1, x1 - x0 + 1), max(1, y1 - y0 + 1)
        g = w.get("gradient")
        if g:
            top, bottom = (ImageColor.getrgb(self.color(c)) for c in (g + g)[:2])
            col_ = Image.new("RGB", (1, 256))
            col_.putdata([tuple(round(a + (b - a) * i / 255) for a, b in zip(top, bottom)) for i in range(256)])
            body = col_.resize((bw, bh), Image.BILINEAR)
        else:
            body = Image.new("RGB", (bw, bh), fill)
        shape = Image.new("L", (bw, bh), 0)
        ImageDraw.Draw(shape).rounded_rectangle([0, 0, bw - 1, bh - 1], radius=radius, fill=int(255 * opacity))
        self._frame.paste(body, (x0, y0), shape)
        gloss = float(w.get("gloss") or 0)
        if gloss > 0:
            S = self.S
            gh = max(2, int(bh * 0.46))
            ramp = Image.new("L", (1, 256))
            ramp.putdata([int(255 * gloss * (1 - i / 255) ** 1.6) for i in range(256)])
            ramp = ramp.resize((bw, gh), Image.BILINEAR)
            hl = Image.new("L", (bw, bh), 0)
            hl.paste(ramp, (0, 0))
            inner = Image.new("L", (bw, bh), 0)
            inset = max(1, S)
            ImageDraw.Draw(inner).rounded_rectangle([inset, inset, bw - 1 - inset, gh + radius], radius=max(0, radius - inset),
                                                    fill=255)
            hl = ImageChops.multiply(hl, inner)
            self._frame.paste(Image.new("RGB", (bw, bh), "#FFFFFF"), (x0, y0), hl)

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
        ft = self._script_font(text, ft)
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

    def weather_text(self, col):
        """' · 24° cloudy' for the "{weather}" mark in clock formats ('' with no city or no answer)."""
        info = col.weather_info() if hasattr(col, "weather_info") else None
        if not info:
            return ""
        parts = []
        if self.weather_cfg.get("temperature", True) and info.get("temp") is not None:
            unit = "°F" if str(self.weather_cfg.get("unit", "")).lower().startswith("f") else "°"
            parts.append(f"{info['temp']:.0f}{unit}")
        if self.weather_cfg.get("condition", True) and info.get("condition"):
            key = "w_clear_night" if info["condition"] == "clear" and not info.get("day", True) else f"w_{info['condition']}"
            parts.append(self.words.get(key, ""))
            if info.get("rain_at") is not None:   # rain coming in the next 2 hours
                parts[-1] += self.words.get("w_rain_at", " · rain at {h}").format(h=info["rain_at"])
        text = " ".join(p for p in parts if p)
        return f" · {text}" if text else ""

    def _w_clock(self, d, w, col):
        now = datetime.datetime.now()
        fmt = w.get("format", "%H:%M").replace("{weekday}", self.words["weekdays"][now.weekday()])
        if "{weather}" in fmt:
            fmt = fmt.replace("{weather}", self.weather_text(col).replace("%", "%%"))
        if "{weather_only}" in fmt:   # the weather alone, without the " · " that joins it to the date
            fmt = fmt.replace("{weather_only}", self.weather_text(col).removeprefix(" · ").replace("%", "%%"))
        self._line(d, w["x"], w["y"], [(now.strftime(fmt), self.font(w.get("size", 24), w.get("bold", False)),
                                        self.color(w.get("color"), "text"))], w.get("align", "left"),
                   w.get("spacing", 0))

    def _w_bar(self, d, w, col):
        S = self.S
        v = col.value(w.get("sensor"))
        x, y, wd, h = w["x"], w["y"], w["w"], w.get("h", 4)
        f = self._fraction(w, self._smooth(w, v))
        c = self._alert_color(w, v, self.color(w.get("color"), "accent"))
        track = self.color(w.get("track_color"), "track")
        style = str(w.get("style") or "")
        if style == "ascii":   # [#######.....] in a fixed-width font
            cells = int(w.get("cells") or 12)
            n = int(round(f * cells))
            ft = self.font(w.get("size", h * 1.6), w.get("bold", False))
            chars = str(w.get("chars") or "#.")
            full, empty = chars[0], chars[1] if len(chars) > 1 else " "
            br = w.get("brackets", "[]")
            self._line(d, x, y + h / 2, [(br[:1], ft, track), (full * n, ft, c), (empty * (cells - n), ft, track),
                                         (br[1:2], ft, track)])
            return
        if style == "segments":   # separate blocks, like an old level meter
            cells = int(w.get("cells") or 10)
            gap = float(w.get("gap", 2))
            cw = (wd - gap * (cells - 1)) / cells
            n = f * cells
            for i in range(cells):
                x0 = x + i * (cw + gap)
                d.rectangle([x0 * S, y * S, (x0 + cw) * S - 1, (y + h) * S - 1], fill=c if i < n - 0.25 else track)
            return
        r = (w.get("radius", h / 2)) * S
        d.rounded_rectangle([x * S, y * S, (x + wd) * S, (y + h) * S], radius=r, fill=track)
        if f > 0:
            d.rounded_rectangle([x * S, y * S, (x + max(h, wd * f)) * S, (y + h) * S], radius=r, fill=c)
        if w.get("gloss"):   # a light streak on the upper half (glass look)
            x0, y0 = int(x * S), int(y * S)
            bw, bh = max(1, int(wd * S)), max(1, int(h * 0.5 * S))
            hl = Image.new("L", (bw, bh), 0)
            ImageDraw.Draw(hl).rounded_rectangle([S, S // 2, bw - 1 - S, bh - 1], radius=r / 2, fill=int(255 * float(w["gloss"])))
            self._frame.paste(Image.new("RGB", (bw, bh), "#FFFFFF"), (x0, y0), hl)

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

        if w.get("fill") or w.get("gloss"):   # a filled disc inside the ring ("bubble"), maybe with a glass shine
            inner = [box[0] + tw, box[1] + tw, box[2] - tw, box[3] - tw]
            if w.get("fill"):
                d.ellipse(inner, fill=self.color(w["fill"]))
            if w.get("gloss"):
                ix0, iy0, ix1, iy1 = (int(v) for v in inner)
                bw, bh = max(2, ix1 - ix0), max(2, iy1 - iy0)
                key = ("shine", bw, bh, w["gloss"])
                hl = self._images.get(key)
                if hl is None:
                    hl = Image.new("L", (bw, bh), 0)
                    ImageDraw.Draw(hl).ellipse([bw * 0.16, bh * 0.05, bw * 0.84, bh * 0.5], fill=int(255 * float(w["gloss"])))
                    hl = self._images[key] = hl.filter(ImageFilter.GaussianBlur(max(1, bw // 40)))
                self._frame.paste(Image.new("RGB", (bw, bh), "#FFFFFF"), (ix0, iy0), hl)
        track = self.color(w.get("track_color"), "track")
        d.arc(box, a0, a1, fill=track, width=tw)
        if (a1 - a0) % 360:
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
        pick = w.get("pick")   # a fixed one (e.g. CPU brand on the left, GPU board brand on the right)
        if not files and w.get("files") == "logos":   # no logo files: the brand names as text
            names = self.brand_names()
            if names:
                if pick is not None:
                    name = names[int(pick) % len(names)]
                else:
                    name = names[int(time.time() // every) % len(names)]
                    if len(names) > 1:
                        self._wake(self._now + every - time.time() % every)
                align = w.get("align", "left")
                ax = x + (wd if align == "right" else wd / 2 if align == "center" else 0)
                self._line(d, ax, y + h / 2, [(name, self.font(h * 1.05, True), self.color("text"))], align)
            return
        if not files:
            return
        t = time.time()
        idx = int(t // every) % len(files)
        phase = t % every
        layers = [(files[idx], 1.0)]
        if pick is not None:
            layers = [(files[int(pick) % len(files)], 1.0)]
        elif len(files) > 1:
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
        fs = float(w.get("label_size", 8)) * k
        ms_part = [(f"{median:.1f}", self.font(fs, True), self.color("text")),
                   (" ms", self.font(fs * 0.875), self.color("secondary"))] if w.get("show_ms", True) else []
        low = col.value(w.get("low_sensor", "fps_1low")) if w.get("show_1low", True) else None
        low_part = [("1% ", self.font(fs * 0.875), self.color("secondary")),
                    (f"{low:.0f}", self.font(fs, True), self.color("text"))] if low is not None else []
        if w.get("labels") == "right":   # both labels after the graph, on its middle line
            parts = ms_part + ([("   ", self.font(fs), self.color("text"))] if ms_part and low_part else []) + low_part
            if parts:
                self._line(d, x + wd + 6 * k, y + h / 2, parts, "left")
        else:
            if ms_part:
                self._line(d, x, y - 7 * k, ms_part, "left")
            if low_part:
                self._line(d, x + wd, y - 7 * k, low_part, "right")
        self.animating = True  # keeps drawing while there is a game

    # ------------------------------------------------------------ game session summary
    def _summary_layout(self, r):
        """Game summary screen. Settings › Game summary chooses what shows (FPS, temperatures, graph,
        duration) and where the graph goes; the rows that stay grow to use the space."""
        T = self.words
        sc = self.summary_cfg
        show = lambda k: sc.get(k, True) is not False   # noqa: E731
        W, H = self.W, self.H
        land = W > H

        def tile(x, y, w, h, base, label, key, unit, size):
            k = min(1.45, max(1.0, h / base))
            return [{"type": "panel", "x": x, "y": y, "w": w, "h": h},
                    {"type": "text", "text": label, "x": x + 12, "y": y + 16, "size": 9, "color": "secondary", "bold": True},
                    {"type": "value", "sensor": key, "x": x + 12, "y": y + h - 26 - (h - base) / 2, "size": round(size * k),
                     "bold": True, "unit": unit, "unit_size": 12}]
        left = max(0.0, r["expires"] - time.monotonic())
        lay = [
            {"type": "text", "text": T["summary"], "x": 12, "y": 14, "size": 10, "color": "secondary", "bold": True},
            {"type": "text", "text": r["name"][:28 if land else 22], "x": 12, "y": 40, "size": 22 if land else 19, "bold": True},
        ]
        if r.get("icon"):   # the game's own icon before its name
            ih = 24 if land else 21
            lay.append({"type": "image", "file": r["icon"], "x": 12, "y": 40 - ih / 2, "w": ih, "h": ih})
            lay[-2]["x"] = 12 + ih + 7
            lay[-2]["text"] = r["name"][:26 if land else 19]
        if show("show_duration") and r.get("duration"):
            lay.insert(1, {"type": "text", "text": r["duration"], "x": W - 12, "y": 14, "size": 10, "color": "secondary",
                           "align": "right"})
        parts = []
        if show("show_fps"):
            parts.append(["fps", 78 if land else 72])
        if show("show_temps"):
            parts.append(["temps", 70 if land else 62])
        if show("show_graph"):
            parts.insert(0 if str(sc.get("graph", "bottom")) == "top" else len(parts), ["graph", 0])
        y0 = 62 if land else 60
        avail = H - 8 - y0 - 4 * max(0, len(parts) - 1)
        fixed = sum(h for _, h in parts)
        rows = [p for p in parts if p[0] != "graph"]
        if any(p[0] == "graph" for p in parts):
            for p in parts:
                if p[0] == "graph":
                    p[1] = max(48, avail - fixed)
        elif rows:   # no graph: the tiles share the space
            extra = max(0, avail - fixed) / len(rows)
            for p in rows:
                p[1] = p[1] + extra
        tw = (W - 8 - 8) / 3   # three tiles with 4 px gaps
        tile_x = [4, 4 + tw + 4, 4 + 2 * (tw + 4)]
        y = y0
        for kind, h in parts:
            if kind == "fps":
                base, big = (78, 30) if land else (72, 24)
                for x, label, key in zip(tile_x, ("fps_avg", "fps_1low", "fps_max"), ("r.fps_avg", "r.fps_1low", "r.fps_max"), strict=True):
                    lay += tile(x, y, tw, h, base, T[label], key, "", big)
            elif kind == "temps":
                base, small = (70, 26) if land else (62, 20)
                for x, label, key in zip(tile_x, ("cpu_max", "gpu_max", "hotspot_max"), ("r.cpu", "r.gpu", "r.hotspot"), strict=True):
                    lay += tile(x, y, tw, h, base, T[label], key, "°C", small)
            else:
                lay += [
                    {"type": "panel", "x": 4, "y": y, "w": W - 8, "h": h},
                    {"type": "text", "text": T["fps_session"], "x": 16, "y": y + 14, "size": 9, "color": "secondary", "bold": True},
                    {"type": "graph", "sensor": "r.fps_series", "x": 16, "y": y + 26, "w": W - 32, "h": h - 36, "points": 120, "min": 0},
                ]
            y += h + 4
        lay.append({"type": "rect", "x": 0, "y": H - 4, "w": max(1, round(W * min(1.0, left / r["total"]))), "h": 4,
                    "color": "accent"})
        return lay

    def _visual_files(self):
        out = []
        files = self.visual.get("files") or ""
        for f in (files.split("|") if isinstance(files, str) else files):
            if not str(f).strip():
                continue
            p = Path(str(f))
            p = p if p.is_absolute() else self.base / p
            if p.suffix.lower() in self.IMAGE_EXT and p.is_file():
                out.append(p)
        return out

    def _fit(self, im):
        """Fills the screen (cropping the excess), at the supersampled size."""
        W, H = self.W * self.S, self.H * self.S
        im = im.convert("RGB")
        f = max(W / im.width, H / im.height)
        im = im.resize((max(W, round(im.width * f)), max(H, round(im.height * f))), Image.LANCZOS)
        left, top = (im.width - W) // 2, (im.height - H) // 2
        return im.crop((left, top, left + W, top + H))

    def _gif_frames(self, path):
        """The GIF's frames at the screen's own size (memory: about 40 MB at most, ~90 frames)."""
        key = ("gif", str(path), self.W, self.H)
        if key not in self._images:
            frames = []
            limit = max(10, int(40e6 // (self.W * self.H * 3)))
            S = self.S
            try:
                from PIL import ImageSequence
                self.S = 1
                with Image.open(path) as im:
                    for fr in ImageSequence.Iterator(im):
                        frames.append((self._fit(fr.convert("RGBA")), max(0.05, (fr.info.get("duration") or 100) / 1000)))
                        if len(frames) >= limit:   # long GIFs: the first frames only
                            break
            except (OSError, ValueError):
                frames = []
            finally:
                self.S = S
            self._images[key] = frames
        return self._images[key]

    def _visual(self, col):
        """Visual mode: (widgets, base picture). Clock = the theme's Rest screen; image, photos (one after the
        other) and GIF fill the screen, optionally with the clock over them."""
        S = self.S
        kind = str(self.visual.get("kind", "clock")).lower()
        files = self._visual_files()
        img = None
        if kind == "gif" and files:
            frames = self._gif_frames(files[0])
            if frames:
                total = sum(d for _, d in frames)
                t = time.monotonic() % total
                for fr, d in frames:
                    if t < d:
                        img = fr.resize((self.W * S, self.H * S), Image.NEAREST) if S != 1 else fr.copy()
                        self._wake(self._now + max(0.02, d - t))
                        break
                    t -= d
                self.animating = True
        elif kind in ("image", "photos") and files:
            every = max(3.0, float(self.visual.get("every", 15)))
            idx = int(time.time() // every) % len(files) if kind == "photos" else 0
            key = ("visual", str(files[idx]), self.W, self.H, S)
            if key not in self._images:
                try:
                    self._images[key] = self._fit(Image.open(files[idx]))
                except (OSError, ValueError):
                    self._images[key] = None
            if self._images[key] is not None:
                img = self._images[key].copy()
            if kind == "photos" and len(files) > 1:
                self._wake(self._now + every - time.time() % every)
        if img is None:   # the clock (or no picture chosen yet)
            img = Image.new("RGB", (self.W * S, self.H * S), self.color("background"))
            self._paste_background(img)
            return self._rest_layout(), img
        if self.visual.get("clock", True):   # a small clock in a corner, over the picture
            return [{"type": "panel", "x": self.W - 104, "y": self.H - 40, "w": 96, "h": 32, "color": "#000000",
                     "opacity": 0.55, "radius": 10, "group": "visual"},
                    {"type": "clock", "format": "%H:%M", "x": self.W - 56, "y": self.H - 24, "size": 18,
                     "bold": True, "align": "center", "color": "#FFFFFF", "group": "visual"}], img
        return [], img

    def _game_name(self, d, col):
        """Settings › FPS › Show the game's name: small, under the FPS of the theme, while a game is running."""
        if col.value("fps") is None:
            return
        name = getattr(col, "game_name", None)
        if not name:
            return
        fps = next((w for w in self.current_widgets if w.get("type") == "value" and w.get("sensor") == "fps"
                    and self._visible(w, col)), None)
        if fps is None:
            return
        size = float(fps.get("size", 14))
        x, y = fps["x"], fps["y"] + size * 0.62 + 6
        align = fps.get("align", "left")
        below = [w["y"] for w in self.current_widgets if w.get("type") in ("panel", "network")
                 and w.get("group") != fps.get("group") and w.get("y", 0) > fps["y"]]
        below += [w["y"] + w["h"] for w in self.current_widgets if w.get("type") == "panel"   # a bar around the FPS
                  and w.get("group") == fps.get("group") and w["y"] <= fps["y"] <= w["y"] + w["h"]]
        if below and y + 6 > min(below):   # no room under the FPS: right after it, on the same line
            width = sum(self._length(t, ft) for t, ft, _ in self._value_parts(fps, col.value("fps"))) / self.S
            x = x + width + 8 if align == "left" else x - width - 8
            y, name = fps["y"], str(name)[:16]
        self._line(d, x, y, [(str(name)[:28], self.font(9.5), self.color("secondary"))], align)

    def _rest_layout(self):
        """Rest screen: a big clock, the date and the weather, in the theme's colors (and over its picture)."""
        if getattr(self, "_rest_widgets", None) is None and self.rest_widgets:
            self._rest_widgets = [dict(w, group="rest") for w in self.rest_widgets]
        if getattr(self, "_rest_widgets", None) is None:
            W, H = self.W, self.H
            land = W > H
            cy = H * (0.40 if land else 0.38)
            big = 104 if land else 84
            self._rest_widgets = [
                {"type": "clock", "format": "%H:%M", "x": W / 2, "y": cy, "align": "center", "size": big, "bold": True,
                 "spacing": 2},
                {"type": "clock", "format": "{weekday} %d/%m", "x": W / 2, "y": cy + big * 0.66, "align": "center",
                 "size": 20 if land else 18, "color": "secondary"},
                {"type": "clock", "format": "{weather_only}", "x": W / 2, "y": cy + big * 0.66 + 30, "align": "center",
                 "size": 17 if land else 15, "color": "accent"},
                {"type": "value", "sensor": "cpu_temp", "x": W / 2 - 12, "y": H - 18, "align": "right", "size": 13,
                 "unit": "°", "prefix": "CPU ", "color": "secondary"},
                {"type": "value", "sensor": "gpu_temp", "x": W / 2 + 12, "y": H - 18, "align": "left", "size": 13,
                 "unit": "°", "prefix": "GPU ", "color": "secondary"},
            ]
        return self._rest_widgets

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
        before, before_pal = self._family, self._palette
        self._family = w.get("font")
        self._palette = w.get("palette")
        try:
            rot = float(w.get("rotate") or 0) % 360
            if not rot:
                fn(d, w, col)
                return
            # rotated element: drawn alone on a transparent layer, turned around its center, then laid on the frame
            base = self._frame
            layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
            self._frame = layer
            try:
                fn(ImageDraw.Draw(layer), w, col)
            finally:
                self._frame = base
            box = layer.getbbox()
            if not box:
                return
            cx, cy = self._center(w, box)
            turned = layer.rotate(-rot, resample=Image.BICUBIC, center=(cx, cy))
            base.paste(turned, (0, 0), turned)
        finally:
            self._family, self._palette = before, before_pal

    def _center(self, w, box):
        """Rotation center in frame pixels: the element's box when it has one, else what was drawn."""
        S = self.S
        if "cx" in w and "cy" in w:
            return w["cx"] * S, w["cy"] * S
        if "w" in w and "h" in w and "x" in w and "y" in w:
            return (w["x"] + w["w"] / 2) * S, (w["y"] + w["h"] / 2) * S
        return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2

    def item_box(self, w, col):
        """Screen rectangle [x, y, w, h] an element covers (for the layout editor), or None if it draws nothing."""
        S = self.S
        base = getattr(self, "_frame", None)
        layer = Image.new("RGBA", (self.W * S, self.H * S), (0, 0, 0, 0))
        self._frame = layer
        try:
            self._draw(dict(w, fade=False), ImageDraw.Draw(layer), col)
        except Exception:  # noqa: BLE001
            return None
        finally:
            self._frame = base
        box = layer.getbbox()
        if not box:
            return None
        return [box[0] / S, box[1] / S, (box[2] - box[0]) / S, (box[3] - box[1]) / S]

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
        """Background image, cropped to fill the screen and darkened so the numbers stay readable.
        Without one, the theme's own picture (made for the screen size, not darkened)."""
        if not self.bg_image:
            if self.art:
                art = self._load_art()
                if art is not None:
                    img.paste(art)
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

    def _load_art(self):
        key = ("art", self.art, self.W, self.H, self.S)
        if key not in self._images:
            try:
                im = Image.open(self.art).convert("RGB")
                f = max(self.W * self.S / im.width, self.H * self.S / im.height)
                im = im.resize((max(self.W * self.S, round(im.width * f)), max(self.H * self.S, round(im.height * f))),
                               Image.LANCZOS)
                left, top = (im.width - self.W * self.S) // 2, (im.height - self.H * self.S) // 2
                self._images[key] = im.crop((left, top, left + self.W * self.S, top + self.H * self.S))
            except (OSError, ValueError):
                self._images[key] = None
        return self._images[key]

    def _is_static(self, w):
        # "over": drawn after the moving elements (a label on top of a filled gauge)
        return self.cache_static and w.get("type") in STATIC_TYPES and not w.get("when") and not w.get("over")

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
        elif self.visual is not None:
            widgets, img = self._visual(col)
            self.layout = "visual"
        elif getattr(col, "rest", False):   # Rest: the PC is idle, a big clock with the date and the weather
            widgets = self._rest_layout()
            self.layout = "rest"
            img = Image.new("RGB", (self.W * S, self.H * S), self.color("background"))
            self._paste_background(img)
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
        if self.show_game and self.layout == "normal":
            self._game_name(d, col)
        self._first = False
        self.hires = img   # the supersampled frame: the window's sharp preview
        return img.reduce(S) if S != 1 else img   # box average of the supersampled frame (as sharp as LANCZOS, 10x faster)
