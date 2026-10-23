"""What is playing, read from the Windows media controls (the same ones the media keys use).

Works with Spotify, YouTube in the browser, Media Player, Deezer and any app that shows up in the
Windows media overlay. Uses the 'winrt' package (pywinrt).
"""
import io
import sys
import threading
import time

APP_NAMES = {"spotify": "Spotify", "chrome": "Chrome", "msedge": "Edge", "firefox": "Firefox", "opera": "Opera",
             "brave": "Brave", "zunemusic": "Media Player", "deezer": "Deezer", "tidal": "TIDAL",
             "applemusic": "Apple Music", "vlc": "VLC", "discord": "Discord"}


def app_name(app_id):
    a = (app_id or "").lower()
    return next((name for key, name in APP_NAMES.items() if key in a), app_id.split("!")[0].split(".")[0] if app_id else "")


def progress(info, now=None):
    """Fraction 0..1 of the track, or None when the app does not report the position."""
    if not info or not info.get("duration"):
        return None
    pos = info.get("position") or 0.0
    if info.get("playing") and info.get("stamp"):
        pos += (now or time.time()) - info["stamp"]
    return max(0.0, min(1.0, pos / info["duration"]))


def _seconds(v):
    """winrt TimeSpan arrives as datetime.timedelta (or an int of 100 ns ticks in old builds)."""
    if v is None:
        return 0.0
    if hasattr(v, "total_seconds"):
        return v.total_seconds()
    try:
        return int(v) / 10_000_000
    except (TypeError, ValueError):
        return 0.0


def _epoch(v):
    """winrt DateTime arrives as an aware datetime."""
    try:
        return v.timestamp()
    except Exception:  # noqa: BLE001
        return None


class Media:
    def __init__(self, ignore=""):
        ign = ignore.split(",") if isinstance(ignore, str) else (ignore or [])
        self.ignore = {x.strip().lower() for x in ign if x.strip()}
        self.info = None      # {"title", "artist", "app", "playing", "cover", "key", "position", "duration", "stamp"}
        self.error = None
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if sys.platform != "win32" or self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name="media")
        self._thread.start()

    def stop(self):
        self._stop.set()

    GRACE = 5.0   # seconds a paused (or closed) player stays on the screen
    FADE = 0.6    # then it fades out

    def current(self):
        """What is playing. After a pause it stays GRACE seconds (with 'paused_for') and then fades out."""
        i = self.info
        if not i or not i.get("title"):
            return None
        if i.get("playing"):
            return i
        since = getattr(self, "_paused_at", None)
        if since is None:
            return None
        gone = time.time() - since
        return dict(i, paused_for=gone) if gone < self.GRACE + self.FADE else None

    def _set(self, info):
        """New state from the media service; remembers when playback stopped."""
        if info and info.get("playing"):
            self._paused_at = None
        elif getattr(self, "_paused_at", None) is None and self.info and self.info.get("playing"):
            self._paused_at = time.time()
        self.info = info

    def _run(self):
        try:
            import asyncio
            from winrt.windows.media.control import (  # noqa: F401
                GlobalSystemMediaTransportControlsSessionManager as Manager,
                GlobalSystemMediaTransportControlsSessionPlaybackStatus as Status,
            )
        except Exception as e:  # noqa: BLE001
            self.error = f"winrt unavailable: {e}"
            return
        while not self._stop.is_set():   # restarts the loop if Windows drops the media service
            try:
                asyncio.run(self._loop(Manager, Status))
            except Exception as e:  # noqa: BLE001
                self.error = f"{type(e).__name__}: {e}"
                self.info = None
                self._stop.wait(5)

    async def _loop(self, Manager, Status):
        import asyncio
        manager = await Manager.request_async()
        while not self._stop.is_set():
            try:
                s = manager.get_current_session()
                if s is None:   # the player closed: keep the last song for the grace period
                    self._set(dict(self.info, playing=False) if self.info else None)
                else:
                    app = s.source_app_user_model_id or ""
                    if any(x in app.lower() for x in self.ignore):
                        self.info = None
                    else:
                        props = await s.try_get_media_properties_async()
                        playing = s.get_playback_info().playback_status == Status.PLAYING
                        key = (props.title, props.artist, app)
                        old = self.info if (self.info and self.info.get("key") == key) else None
                        cover = old["cover"] if old else await self._cover(props.thumbnail)
                        self._set({"title": props.title or "", "artist": props.artist or "", "app": app_name(app),
                                   "playing": playing, "cover": cover, "key": key, **self._timeline(s)})
                self.error = None
            except Exception as e:  # noqa: BLE001
                self.error = f"{type(e).__name__}: {e}"
            await asyncio.sleep(1.0)

    @staticmethod
    def _timeline(session):
        try:
            t = session.get_timeline_properties()
            start, end, pos = _seconds(t.start_time), _seconds(t.end_time), _seconds(t.position)
            duration = end - start
            if duration <= 1:
                return {"position": None, "duration": None, "stamp": None}
            stamp = _epoch(t.last_updated_time)
            now = time.time()
            # some apps report a stale timestamp: fall back to "now" if it is far off
            if stamp is None or stamp > now + 5 or now - stamp > 6 * 3600:
                stamp = now
            return {"position": pos - start, "duration": duration, "stamp": stamp}
        except Exception:  # noqa: BLE001
            return {"position": None, "duration": None, "stamp": None}

    @staticmethod
    async def _cover(ref):
        if ref is None:
            return None
        try:
            from PIL import Image
            from winrt.windows.storage.streams import Buffer, InputStreamOptions
            stream = await ref.open_read_async()
            size = int(stream.size)
            if not size or size > 8_000_000:
                return None
            buf = Buffer(size)
            await stream.read_async(buf, size, InputStreamOptions.READ_AHEAD)
            try:
                data = bytes(memoryview(buf))
            except TypeError:
                data = bytes(buf)
            im = Image.open(io.BytesIO(data)).convert("RGB")
            # some players send 16:9 art with black bars: keep the square in the middle
            w, h = im.size
            if w > h * 1.2:
                im = im.crop(((w - h) // 2, 0, (w + h) // 2, h))
            return im
        except Exception:  # noqa: BLE001
            return None


class DemoMedia(Media):
    """For the demo and previews."""

    def __init__(self, title="Midnight City", artist="M83", duration=243.0):
        super().__init__()
        from PIL import Image, ImageDraw
        cover = Image.new("RGB", (120, 120), "#2B1B4A")
        d = ImageDraw.Draw(cover)
        for i in range(6):
            d.ellipse([10 + i * 8, 10 + i * 8, 110 - i * 8, 110 - i * 8], outline=(255, 120 + i * 20, 80 + i * 25), width=4)
        self.info = {"title": title, "artist": artist, "app": "Spotify", "playing": True,
                     "cover": cover, "key": ("demo", title), "position": 61.0, "duration": duration, "stamp": time.time()}

    def start(self):
        pass
