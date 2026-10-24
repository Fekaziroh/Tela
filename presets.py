"""Performance presets: a few settings that decide how much CPU and memory Tela! uses.

The active preset is not stored: it is whatever preset matches the current values ("custom" otherwise),
so changing any of these settings by hand turns the choice into Custom by itself.
"""
# (section, key) -> value; section None = top level
PRESETS = {
    "default": {
        ("performance", "quality"): "high",      # 2x supersampled drawing
        ("performance", "preview"): True,        # live preview in the window
        (None, "interval"): 1.0,
        ("animation", "enabled"): True,
        ("fps", "update"): 0.2,
        ("network", "ping_interval"): 2,
        ("data", "disk_interval"): 2,
        ("eco", "enabled"): True,
        ("ui", "unload_hidden"): False,
    },
    "performance": {
        ("performance", "quality"): "normal",
        ("performance", "preview"): False,
        (None, "interval"): 2.0,
        ("animation", "enabled"): False,
        ("fps", "update"): 0.5,
        ("network", "ping_interval"): 5,
        ("data", "disk_interval"): 5,
        ("eco", "enabled"): True,
        ("ui", "unload_hidden"): True,
    },
}
ORDER = ("performance", "default")


def value(cfg, section, key):
    return cfg.get(key) if section is None else (cfg.get(section) or {}).get(key)


def _same(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b) and type(a) is type(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-9
    return str(a).lower() == str(b).lower()


def detect(cfg):
    for name in ORDER:
        if all(_same(value(cfg, s, k), v) for (s, k), v in PRESETS[name].items()):
            return name
    return "custom"


def items(name):
    """[(section, key, value)] to write for a preset."""
    return [(s, k, v) for (s, k), v in PRESETS[name].items()]

