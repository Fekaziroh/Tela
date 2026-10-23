"""Weather next to the date: temperature and sky for a city, from Open-Meteo (free, no account, no key).

Only the city name (to find its coordinates, once) and those coordinates (every 20 minutes) go online.
"""
import json
import threading
import time
import urllib.parse
import urllib.request

GEO = "https://geocoding-api.open-meteo.com/v1/search?count=1&format=json&name={city}&language={lang}"
NOW = ("https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
       "&current=temperature_2m,weather_code,is_day&hourly=precipitation_probability&forecast_hours=4"
       "&temperature_unit={unit}&timezone=auto")
RAIN_CHANCE = 60      # % chance in one of the next 2 hours = "rain at 15h" next to the weather
WET = {"drizzle", "rain", "showers", "snow", "storm"}
EVERY = 20 * 60
RETRY = 3 * 60

# WMO weather codes -> condition word (SCREEN_TEXT key "w_<name>")
CODES = {0: "clear", 1: "clear", 2: "partly", 3: "cloudy", 45: "fog", 48: "fog",
         51: "drizzle", 53: "drizzle", 55: "drizzle", 56: "drizzle", 57: "drizzle",
         61: "rain", 63: "rain", 65: "rain", 66: "rain", 67: "rain", 80: "showers", 81: "showers", 82: "showers",
         71: "snow", 73: "snow", 75: "snow", 77: "snow", 85: "snow", 86: "snow",
         95: "storm", 96: "storm", 99: "storm"}


def condition(code):
    try:
        return CODES.get(int(code), "cloudy")
    except (TypeError, ValueError):
        return None


def _get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Tela-weather"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 — fixed https URLs
        return json.loads(r.read().decode("utf-8"))


class Weather:
    """Keeps the current weather for the configured city, refreshed in the background."""

    def __init__(self, city, unit="celsius", lang="en", log=None, fetch=_get):
        self.city = str(city or "").strip()
        self.unit = "fahrenheit" if str(unit).lower().startswith("f") else "celsius"
        self.lang = lang
        self.log = log
        self._fetch = fetch
        self.place = None       # {"name", "country", "lat", "lon"}
        self.now = None         # {"temp", "code", "condition", "day", "at"}
        self.error = None
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread = None

    def key(self):
        return (self.city.lower(), self.unit)

    def start(self):
        if self.city and self._thread is None:
            self._thread = threading.Thread(target=self._loop, daemon=True, name="weather")
            self._thread.start()
        return self

    def close(self):
        self._stop.set()
        self._wake.set()

    def _say(self, msg):
        if self.log:
            self.log(msg)

    def _loop(self):
        while not self._stop.is_set():
            ok = self.refresh()
            self._wake.wait(EVERY if ok else (6 * 3600 if ok is None else RETRY))
            self._wake.clear()

    def refresh(self):
        try:
            if self.place is None:
                data = _ok(self._fetch(GEO.format(city=urllib.parse.quote(self.city), lang=self.lang)))
                res = (data.get("results") or [None])[0]
                if not res:
                    self.error = "city not found"
                    self._say(f"Weather: city not found ({self.city})")
                    return None          # wrong name: do not insist
                self.place = {"name": res.get("name"), "country": res.get("country"),
                              "lat": round(float(res["latitude"]), 3), "lon": round(float(res["longitude"]), 3)}
                self._say(f"Weather: {self.place['name']} ({self.place.get('country') or ''})")
            data = _ok(self._fetch(NOW.format(lat=self.place["lat"], lon=self.place["lon"], unit=self.unit)))
            cur = data.get("current") or {}
            cond = condition(cur.get("weather_code"))
            self.now = {"temp": float(cur["temperature_2m"]), "code": cur.get("weather_code"),
                        "condition": cond, "day": bool(cur.get("is_day", 1)),
                        "rain_at": None if cond in WET else rain_soon(data.get("hourly"), cur.get("time")),
                        "at": time.time()}
            self.error = None
            return True
        except Exception as e:  # noqa: BLE001 — offline: try again later, keep the last value a while
            self.error = f"{type(e).__name__}: {e}"
            return False

    def current(self):
        """The last reading, or None when there is none or it is older than 2 hours (offline)."""
        if self.now and time.time() - self.now["at"] < 2 * 3600:
            return self.now
        return None


def rain_soon(hourly, now):
    """Hour (0-23) of the first of the next 2 hours with a good chance of rain, or None."""
    try:
        times, chance = hourly["time"], hourly["precipitation_probability"]
        cur = str(now or "")[:13]                    # "2026-10-23T19"
        after = [(t, p) for t, p in zip(times, chance) if str(t)[:13] > cur][:2]
        for t, p in after:
            if p is not None and float(p) >= RAIN_CHANCE:
                return int(str(t)[11:13])
    except (KeyError, TypeError, ValueError):
        pass
    return None


def _ok(data):
    if not isinstance(data, dict) or data.get("error"):
        raise ValueError(str((data or {}).get("reason") or "bad answer"))
    return data


class DemoWeather:
    """Fixed weather for the demo mode and the screenshots."""
    city = "Demo"
    place = {"name": "São Paulo", "country": "Brasil"}
    error = None

    def __init__(self, unit="celsius"):
        f = str(unit).lower().startswith("f")
        self.now = {"temp": 75.0 if f else 24.0, "code": 2, "condition": "partly", "day": True, "rain_at": None,
                    "at": time.time()}

    def key(self):
        return ("demo",)

    def start(self):
        return self

    def close(self):
        pass

    def current(self):
        return self.now
