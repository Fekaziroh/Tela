"""Temperature notices: discreet, only after the value stays above the limit, and never repeated quickly."""
import time


class TempAlerts:
    def __init__(self):
        self._above = {}      # part -> time it went above the limit
        self._told = {}       # part -> time of the last notice

    def check(self, cfg, temps, now=None):
        """temps = {"cpu": °C or None, "gpu": ...}. Returns [(part, temperature, limit)] to tell now."""
        a = cfg.get("alerts") or {}
        if not a.get("enabled"):
            self._above.clear()
            return []
        now = now if now is not None else time.monotonic()
        hold = float(a.get("seconds", 20))
        quiet = float(a.get("quiet_minutes", 15)) * 60
        out = []
        for part, temp in temps.items():
            limit = a.get(part)
            if temp is None or not limit:
                continue
            limit = float(limit)
            if temp < limit - 3:                      # back to normal (3 °C margin so it does not flicker)
                self._above.pop(part, None)
                continue
            if temp < limit:
                continue
            since = self._above.setdefault(part, now)
            if now - since >= hold and now - self._told.get(part, -1e9) >= quiet:
                self._told[part] = now
                out.append((part, temp, limit))
        return out
