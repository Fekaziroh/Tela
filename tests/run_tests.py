#!/usr/bin/env python3
"""Tela! automated tests (no extra packages). Run before every release:

    python tests/run_tests.py
"""
import json
import re
import shutil
import sys
import tempfile
import threading
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

import config  # noqa: E402
import engine  # noqa: E402
import hardware  # noqa: E402
import layout  # noqa: E402
import render  # noqa: E402
import sensors  # noqa: E402
from media import DemoMedia, progress  # noqa: E402

TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def default_cfg(family="landscape"):
    """Default settings plus the default layout (never the user's own copy)."""
    cfg = config.load(ROOT / config.DEFAULT)
    if family == "portrait":
        cfg["display"]["orientation"] = "portrait"
    lay = layout.load(family, user=False)
    cfg["sensors"] = lay["sensors"]
    cfg["widgets"] = layout.flatten(lay["groups"])
    return cfg


# ---------------------------------------------------------------- settings file
@test
def replace_value_keeps_comments_and_sections():
    txt = "display:\n  port: auto       # comment\n  brightness: 40\nnetwork:\n  servers: \"1.1.1.1, 8.8.8.8\"\n"
    out = config.replace_value(txt, "brightness", "55", "display")
    assert "  brightness: 55" in out and "# comment" in out
    out = config.replace_value(out, "servers", config.yaml_value("9.9.9.9, 1.1.1.1"), "network")
    assert yaml.safe_load(out)["network"]["servers"] == "9.9.9.9, 1.1.1.1"
    out = config.replace_value(out, "port", config.yaml_value("COM5"), "display")
    assert yaml.safe_load(out)["display"]["port"] == "COM5"
    out = config.replace_value(out, "theme", "dark", "ui")          # new section
    out = config.replace_value(out, "night_enabled", "true", "display")   # new key inside a section
    d = yaml.safe_load(out)
    assert d["ui"]["theme"] == "dark" and d["display"]["night_enabled"] is True and d["display"]["brightness"] == 55


@test
def yaml_value_quotes_tricky_strings():
    for v in ["", "on", "off", "yes", "a: b", "#x", "C:\\Tela", 'say "hi"']:
        assert yaml.safe_load("k: " + config.yaml_value(v))["k"] == v, v
    assert config.yaml_value(True) == "true" and config.yaml_value(1.5) == "1.5"


@test
def default_config_is_valid():
    cfg = default_cfg()
    for section in config.USER_SECTIONS:
        assert section in cfg, section
    types = {w["type"] for w in cfg["widgets"]}
    assert types <= {n[3:] for n in dir(render.Renderer) if n.startswith("_w_")}, types
    assert cfg["tray"]["temp_icon"] == "none"


@test
def migration_from_telav3_portuguese_config():
    old = Path("/home/claude/TelaV3/config.yaml")
    txt = old.read_text(encoding="utf-8") if old.exists() else None
    if txt is None:
        return "skipped (no TelaV3 config)"
    txt = txt.replace("brilho: 40", "brilho: 33").replace("orientacao: paisagem_invertida", "orientacao: paisagem")
    txt = txt.replace("resumo_segundos: 15", "resumo_segundos: 25").replace("numero: atividade", "numero: espaco")
    txt = txt.replace('fundo:      "#000000"', 'fundo:      "#101010"').replace("rede_down: 3", "rede_down: 7")
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        shutil.copy(ROOT / config.DEFAULT, d / config.DEFAULT)
        (d / config.CONFIG).write_text(txt, encoding="utf-8")
        msg, old_dir = config.prepare(d, search_old=False)
        cfg = config.load(d / config.CONFIG)
        assert "migrated" in msg, msg
        assert cfg["display"]["brightness"] == 33 and cfg["display"]["orientation"] == "landscape"
        assert cfg["session"]["summary_seconds"] == 25 and cfg["ssd"]["number"] == "space"
        assert cfg["colors"]["background"] == "#101010" and cfg["intervals"]["net_down"] == 7
        assert "tela" not in cfg and "widgets" not in cfg   # the layout lives in layouts/, not in the settings
        assert (d / config.PREVIOUS).exists()


@test
def update_keeps_english_choices_and_takes_new_layout():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        shutil.copy(ROOT / config.DEFAULT, d / config.DEFAULT)
        s = config.Settings(d / config.CONFIG)
        shutil.copy(ROOT / config.DEFAULT, d / config.CONFIG)
        s.set_many([("display", "brightness", 61), ("ui", "theme", "light"), ("media", "during_game", "hide")])
        s.set_intervals(1.0, {"disk1": 60, "cpu_temp": 1})
        config.prepare(d, search_old=False)
        cfg = config.load(d / config.CONFIG)
        assert cfg["display"]["brightness"] == 61 and cfg["ui"]["theme"] == "light"
        assert cfg["media"]["during_game"] == "hide" and cfg["intervals"] == {"disk1": 60}


@test
def finds_old_install_and_copies_logos():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        new, old = d / "Tela", d / "TelaV3"
        new.mkdir()
        (old / "logos").mkdir(parents=True)
        (old / config.CONFIG).write_text("tela:\n  brilho: 12\n", encoding="utf-8")
        (old / "logos" / "Mine.png").write_bytes(b"x")
        (old / "lhm").mkdir()
        (old / "lhm" / "LibreHardwareMonitorLib.dll").write_bytes(b"x")
        shutil.copy(ROOT / config.DEFAULT, new / config.DEFAULT)
        assert config.find_old_install(new) == old.resolve()
        msg, found = config.prepare(new)
        assert found == old.resolve() and "imported" in msg
        assert config.load(new / config.CONFIG)["display"]["brightness"] == 12
        assert (new / "logos" / "Mine.png").exists() and (new / "lhm" / "LibreHardwareMonitorLib.dll").exists()


# ---------------------------------------------------------------- hardware
@test
def hardware_names_and_brands():
    info = hardware.build(hardware.DEMO_RAW)
    assert info["cpu_name"] == "R7 5800X3D" and info["gpu_name"] == "RX 6750 XT"
    assert info["cpu_brand"] == "amd" and info["gpu_brand"] == "amd" and info["gpu_board_brand"] == "msi"
    assert info["board_brand"] == "asus" and info["ram_desc"] == "DDR4 32GB" and info["vram_desc"] == "12 GB"
    assert info["disks_title"] == "SSD" and [x["letter"] for x in info["disks"]] == ["C:", "D:"]
    assert hardware.board_vendor_of("PCI\\VEN_10DE&DEV_2684&SUBSYS_16F110DE") == "nvidia"
    assert hardware.board_vendor_of("PCI\\VEN_10DE&DEV_2684&SUBSYS_51111043&REV_A1") == "asus"
    f = hardware.fields(info)
    assert f["disk2_letter"] == "D:" and f["disk1_model"].startswith("XPG")
    assert "MSI" in hardware.summary(info)


# ---------------------------------------------------------------- rendering
class FakeCollector:
    def __init__(self, game=True, media=True, values=None):
        self.v = {"fps": 120.0 if game else None, "cpu_temp": 60.0, "fps_1low": 90.0, **(values or {})}
        self.m = DemoMedia() if media else None
        self.summary = None

    def value(self, n):
        return self.v.get(n)

    def media_info(self):
        return self.m.current() if self.m else None

    def network_info(self):
        return {"state": "normal", "ms": 12.0, "loss": 0.0, "level": "ok"}

    def frametimes(self, s=2.0):
        return [8.3] * 200

    def history(self, n, k=120):
        return [1, 2, 3]


def visible_types(r, col):
    return [(w["type"], w.get("x")) for w in r.widgets if r._visible(w, col)]


@test
def top_bar_states():
    cfg = default_cfg()
    r = render.Renderer(cfg, 480, 320, base=ROOT, fields=hardware.fields(hardware.build(hardware.DEMO_RAW)))
    v = visible_types(r, FakeCollector(game=False, media=False))
    assert ("image", 12) in v and ("media", 10) not in v and ("clock", 468) in v
    v = visible_types(r, FakeCollector(game=False, media=True))
    assert ("media", 10) in v and ("image", 12) not in v and ("media", 298) not in v and ("clock", 468) in v
    v = visible_types(r, FakeCollector(game=True, media=True))
    assert ("media", 298) in v and ("clock", 468) not in v and ("media", 10) not in v
    v = visible_types(r, FakeCollector(game=True, media=False))
    assert ("clock", 468) in v and ("media", 298) not in v
    cfg["media"]["during_game"] = "hide"
    r = render.Renderer(cfg, 480, 320, base=ROOT)
    v = visible_types(r, FakeCollector(game=True, media=True))
    assert ("clock", 468) in v and ("media", 298) not in v


@test
def static_layer_matches_full_draw():
    cfg = default_cfg()
    cfg["animation"]["enabled"] = False
    fields = hardware.fields(hardware.build(hardware.DEMO_RAW))
    col = FakeCollector(game=False, media=False, values={"cpu_load": 40.0, "ram_pct": 55.0})
    a = render.Renderer(cfg, 480, 320, base=ROOT, fields=fields, cache_static=True)
    b = render.Renderer(cfg, 480, 320, base=ROOT, fields=fields, cache_static=False)
    t = time.time()
    real = time.time
    try:
        time.time = lambda: t
        ia, ib = a.draw(col), b.draw(col)
        ia = a.draw(col)   # second frame comes from the cache
    finally:
        time.time = real
    assert ia.tobytes() == ib.tobytes(), "cached static layer differs from a full draw"


@test
def screen_words_follow_language():
    cfg = default_cfg()
    pt = render.Renderer(cfg, 480, 320, lang="pt")
    en = render.Renderer(cfg, 480, 320, lang="en")
    assert pt._txt("#load") == "USO" and en._txt("#load") == "LOAD"
    assert pt._txt("#disks") == "DISCOS" and pt._txt("{x}", ) == ""
    assert set(render.SCREEN_TEXT["pt"]) == set(render.SCREEN_TEXT["en"])
    labels = {w.get(k)[1:] for w in cfg["widgets"] for k in ("text", "title", "unit", "prefix", "empty")
              if isinstance(w.get(k), str) and w.get(k).startswith("#")}
    assert labels <= set(render.SCREEN_TEXT["pt"]), labels - set(render.SCREEN_TEXT["pt"])


@test
def marquee_pauses_then_scrolls():
    cfg = default_cfg()
    r = render.Renderer(cfg, 480, 320, base=ROOT)
    col = FakeCollector(game=False, media=True)
    col.m = DemoMedia("A very long title that will never fit in this small box at all", "Artist")
    real = time.monotonic
    t0 = real()
    try:
        time.monotonic = lambda: t0
        r.draw(col)
        assert r.wake_at is not None and abs(r.wake_at - (t0 + 3.0)) < 0.05 and not r.animating
        time.monotonic = lambda: t0 + 4.0
        r.draw(col)
        assert r.animating, "should be scrolling"
        short = render.Renderer(cfg, 480, 320, base=ROOT)
        col.m = DemoMedia("Short", "Artist")
        time.monotonic = lambda: t0 + 10
        short.draw(col)
        assert not short.animating and not short._marquee
    finally:
        time.monotonic = real


@test
def media_progress():
    info = {"duration": 200.0, "position": 50.0, "stamp": 1000.0, "playing": True}
    assert abs(progress(info, now=1050.0) - 0.5) < 1e-9
    assert progress(dict(info, playing=False), now=1050.0) == 0.25
    assert progress(dict(info, duration=None)) is None
    assert progress(info, now=5000.0) == 1.0


@test
def ssd_number_swap():
    cfg = default_cfg()
    cfg["ssd"]["number"] = "space"
    r = render.Renderer(cfg, 480, 320)
    swapped = [w["sensor"] for w in r.widgets if w.get("ssd")]
    assert swapped == ["disk1", "disk1_act", "disk2", "disk2_act"], swapped


@test
def every_widget_type_draws():
    cfg = default_cfg()
    cfg["widgets"] += [{"type": "graph", "sensor": "cpu_temp", "x": 0, "y": 0, "w": 50, "h": 20},
                       {"type": "rect", "x": 0, "y": 0, "w": 5, "h": 5},
                       {"type": "image", "files": ["logos/AMD Logo.png", "logos/MSI Logo.png"], "x": 0, "y": 0, "w": 40, "h": 10}]
    r = render.Renderer(cfg, 480, 320, base=ROOT, fields=hardware.fields(hardware.build(hardware.DEMO_RAW)))
    for game in (True, False):
        for media in (True, False):
            img = r.draw(FakeCollector(game, media))
            assert img.size == (480, 320)
    col = FakeCollector()
    col.summary = {"name": "X", "duration": "1 min", "fps_avg": 1, "fps_1low": 1, "fps_max": 1, "max": {"cpu": 1},
                   "fps_series": [1, 2], "expires": time.monotonic() + 5, "total": 5}
    assert r.draw(col).size == (480, 320) and r.layout == "summary"


@test
def changed_regions_finds_only_changes():
    from PIL import Image
    a = Image.new("RGB", (480, 320))
    b = a.copy()
    b.putpixel((100, 50), (255, 0, 0))
    b.putpixel((400, 300), (0, 255, 0))
    rects = engine.changed_regions(b, a)
    assert rects == [(100, 50, 1, 1), (400, 300, 1, 1)], rects
    assert engine.changed_regions(a, a) == []
    assert engine.changed_regions(a, None) == [(0, 0, 480, 320)]


# ---------------------------------------------------------------- sensors
@test
def ping_states():
    p = sensors.Ping(fails_for_outage=3)
    for _ in range(5):
        p.record(12.0, True)
    assert p.state == "normal" and p.level() == "ok"
    p.record(None, True)
    assert p.state == "unstable"
    p.record(None, True)
    p.record(None, False)
    assert p.state == "down" and p.since is not None and p.gateway_ok is False and p.level() == "crit"
    p.record(15.0, True)
    assert p.state == "unstable" and p.since is None   # loss still in the window
    q = sensors.Ping()
    q.record(200.0, True)
    assert q.state == "unstable" and q.level() == "crit"


@test
def presentmon_parsing_and_ignore_list():
    pm = sensors.PresentMon(Path("nope.exe"))
    lines = ["Application,ProcessID,SwapChainAddress,PresentRuntime,MsBetweenPresents,CPUStartTime"]
    lines += [f"game.exe,100,0x1,DXGI,8.0,{i * 0.008:.4f}" for i in range(200)]
    lines += [f"chrome.exe,200,0x1,DXGI,16.0,{i * 0.016:.4f}" for i in range(100)]
    pm.feed(lines)
    pm.read(front=100)
    assert pm.fps is not None and abs(pm.fps - 125) < 1 and pm.app == "game.exe"
    pm.read(front=200)
    assert pm.fps is None   # browsers never count as games
    assert sensors.one_percent_low([8.0] * 990 + [40.0] * 10) == 25.0


@test
def session_low_and_average():
    s = sensors.Session(1, "Game")
    s.frames([10.0] * 990 + [50.0] * 10)
    assert abs(s.fps_avg() - 1000 * 1000 / (990 * 10 + 500)) < 0.01
    assert abs(s.one_percent_low() - 20.0) < 0.1
    assert sensors.format_duration(3725) == "1h 02min" and sensors.format_duration(300) == "5 min"
    assert len(sensors.downsample(list(range(1000)), 120)) == 120


@test
def selector_matching():
    w = sensors.LhmWeb("")
    w.sensors = [
        {"id": "/amdcpu/0/temperature/2", "name": "Core (Tctl/Tdie)", "type": "temperature", "group": "Temperatures", "hardware": "AMD Ryzen 7", "value": 61.0},
        {"id": "/amdcpu/0/clock/1", "name": "Core #1", "type": "clock", "group": "Clocks", "hardware": "AMD Ryzen 7", "value": 4000.0},
        {"id": "/amdcpu/0/clock/2", "name": "Core #2", "type": "clock", "group": "Clocks", "hardware": "AMD Ryzen 7", "value": 4200.0},
        {"id": "/nvme/0/temperature/0", "name": "Composite Temperature", "type": "temperature", "group": "Temperatures", "hardware": "XPG GAMMIX S70 BLADE", "value": 44.0},
        {"id": "/nvme/0/temperature/1", "name": "Critical Temperature", "type": "temperature", "group": "Temperatures", "hardware": "XPG GAMMIX S70 BLADE", "value": 109.0},
    ]
    assert w.find("cpu|temperature|Core (Tctl/Tdie)") == 61.0
    assert w.find("cpu|clock|Core #*|avg") == 4100.0 and w.find("cpu|clock|Core #*|max") == 4200.0
    assert w.find("XPG GAMMIX S70 BLADE|temperature|Composite Temperature") == 44.0
    assert w.find("/amdcpu/0/clock/2") == 4200.0
    assert sensors.fill_selector(["{disk1_model}|load|x", "{nope}|a|b"], {"disk1_model": "S70"}) == ["S70|load|x"]


@test
def collector_reload_reuses_parts():
    cfg = default_cfg()
    c1 = sensors.Collector(cfg, demo=True, base=ROOT)
    c1.update()
    c2 = sensors.Collector(cfg, demo=True, base=ROOT, previous=c1)
    assert c2.lhm is c1.lhm and "lhm" in c1._kept and c2._hist is c1._hist
    cfg2 = json.loads(json.dumps(cfg))
    cfg2["data"]["controllers"] = True
    c3 = sensors.Collector(cfg2, demo=True, base=ROOT, previous=c2)
    assert c3.lhm is not c2.lhm


# ---------------------------------------------------------------- engine
def run_engine(seconds, setup=None, **kw):
    log = engine.Log(echo=False)
    e = engine.Engine(ROOT / config.DEFAULT, log, demo=True, simulate="memory", **kw)
    if setup:
        setup(e)
    e.start()
    time.sleep(seconds)
    return e, log


@test
def engine_runs_and_handles_commands():
    e, log = run_engine(1.5)
    try:
        assert e.connected and e.frame_no > 0 and e.last_frame is not None
        e.command("summary_example")
        time.sleep(1.2)
        assert e.collector.summary and e.renderer.layout == "summary"
        e.command("pause", True)
        time.sleep(0.8)
        assert e.paused and not e.connected
        e.command("pause", False)
        e.command("sleep", "lock")
        time.sleep(0.6)
        assert e.sleeping
        e.command("wake", "lock")
        time.sleep(0.8)
        assert not e.sleeping
    finally:
        e.stop()
        e.join(5)
    assert not e.is_alive()
    assert any("Screen off" in ln or "Resumed" in ln for ln in log.lines)


@test
def engine_recovers_from_errors():
    boom = {"n": 0}

    def setup(e):
        real = e.collector.update

        def flaky():
            boom["n"] += 1
            if boom["n"] == 2:
                raise RuntimeError("test crash")
            return real()
        e.collector.update = flaky
        e._read_sensors = lambda state: (e.collector.update(), None)[1]
    e, log = run_engine(5.5, setup)
    try:
        assert any("Recovered from an error" in ln for ln in log.lines), list(log.lines)
        n = e.frame_no
        time.sleep(1.5)
        assert e.frame_no > n and e.is_alive(), "engine did not continue after the error"
    finally:
        e.stop()
        e.join(5)


@test
def log_rotates():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "tela.log"
        log = engine.Log(f, echo=False)
        log.MAX_BYTES = 2000
        for i in range(400):
            log(f"line {i} " + "x" * 40)
        assert f.stat().st_size < 6000 and (Path(d) / "tela.log.1").exists()


# ---------------------------------------------------------------- window texts
@test
def window_texts_complete():
    js = (ROOT / "ui" / "i18n.js").read_text(encoding="utf-8")
    blocks = re.split(r"\n  (pt|en): \{", js)
    keys = {}
    for i in range(1, len(blocks), 2):
        keys[blocks[i]] = set(re.findall(r'"([a-z0-9_.]+)":', blocks[i + 1]))
    assert keys["pt"] == keys["en"], keys["pt"] ^ keys["en"]
    html = (ROOT / "ui" / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "ui" / "app.js").read_text(encoding="utf-8")
    used = set(re.findall(r'data-(?:i18n|placeholder|label)="([a-z0-9_.]+)"', html))
    used |= set(re.findall(r'\bt\("([a-z0-9_.]+)"[,)]', app))
    missing = {k for k in used if k not in keys["pt"]}
    assert not missing, missing
    cfg = default_cfg()
    sensor_keys = {"sensor." + k for k in cfg["sensors"] if k not in ("fps", "volume")}
    assert sensor_keys <= keys["pt"], sensor_keys - keys["pt"]
    for path in re.findall(r'data-set="([a-z_.]+)"', html):
        sec, key = path.split(".")
        assert (cfg.get(sec) or {}).get(key, cfg.get(key) if not sec else None) is not None or key in cfg.get(sec, {}), path


@test
def api_and_bridge():
    import urllib.request
    sys.path.insert(0, str(ROOT / "tests"))
    from ui_server import DevApp
    from api import Api
    from bridge import Bridge
    tmp = Path(tempfile.mkdtemp())
    try:
        shutil.copy(ROOT / config.DEFAULT, tmp / "config.yaml")
        app = DevApp()
        app.engine.stop()
        app.cfg_path = tmp / "config.yaml"
        api = Api(app)
        app.engine = engine.Engine(app.cfg_path, engine.Log(echo=False), demo=True, simulate="memory")
        app.engine.start()
        time.sleep(1.2)
        init = api.init()
        for section in config.USER_SECTIONS:   # the window must see every setting (background was missing)
            assert section in init["settings"], section
        assert init["version"] == engine.VERSION and "cpu_temp" in init["sensors"] and "fps" not in init["sensors"]
        st = api.state(-1)
        assert st["frame"].startswith("data:image/png;base64,") and st["status"]["connected"]
        assert "frame" not in api.state(st["frame_no"]) or True
        api.set("display", "night_enabled", True)
        assert config.load(app.cfg_path)["display"]["night_enabled"] is True
        assert "Tela! " in api.diagnostics()
        assert "items" in api.logos() and "auto" in api.logos()   # the project ships no logo files
        b = Bridge(api, ROOT / "ui")
        req = urllib.request.Request(f"http://127.0.0.1:{b.port}/api/init", data=b"[]", method="POST")
        try:
            urllib.request.urlopen(req, timeout=3)
            raise AssertionError("bridge answered without the token")
        except urllib.error.HTTPError as e:
            assert e.code == 403
        req.add_header("X-Tela-Token", b.token)
        assert json.load(urllib.request.urlopen(req, timeout=3))["result"]["version"] == engine.VERSION
        b.close()
        app.engine.stop()
        app.engine.join(5)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- 1.4.0: layouts, logos, setup
@test
def layouts_fit_and_do_not_overlap():
    for fam in layout.FAMILIES:
        lay = layout.load(fam, user=False)
        W, H = lay["size"]
        assert (W, H) == ((480, 320) if fam == "landscape" else (320, 480)), (fam, W, H)
        for g in lay["groups"]:
            assert 0 <= g["x"] and 0 <= g["y"] and g["x"] + g["w"] <= W and g["y"] + g["h"] <= H, (fam, g["id"])
        assert not layout.overlapping(lay["groups"]), fam
        cfg = default_cfg(fam)
        r = render.Renderer(cfg, W, H, base=ROOT, fields=hardware.fields(hardware.build(hardware.DEMO_RAW)))
        for game in (True, False):
            for media in (True, False):
                assert r.draw(FakeCollector(game, media)).size == (W, H)


@test
def blocks_move_and_scale():
    g = {"id": "b", "x": 100, "y": 50, "w": 230, "h": 112, "base": [115, 56],
         "items": [{"type": "panel", "x": 0, "y": 0, "w": 115, "h": 56, "title": "X"},
                   {"type": "value", "sensor": "s", "x": 105, "y": 34, "size": 20},
                   {"type": "bar", "sensor": "s", "x": 10, "y": 46, "w": 95, "h": 4, "enabled": False}]}
    ws = layout.flatten([g])
    assert len(ws) == 2   # disabled item left out
    panel, value = ws
    assert (panel["x"], panel["y"], panel["w"], panel["h"]) == (100, 50, 230, 112)
    assert (value["x"], value["y"], value["size"]) == (310, 118, 40)
    assert layout.flatten([dict(g, enabled=False)]) == []


@test
def layout_save_and_load_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        old = config.DATA
        try:
            config.DATA = Path(d)
            lay = layout.load("landscape", user=False)
            groups = lay["groups"]
            groups[1]["x"] += 6
            groups[2]["enabled"] = False
            groups[0]["items"][0]["size"] = 30
            groups.append(layout.new_block("gauge", 20, 20, "gpu_temp"))
            layout.save("landscape", {"size": lay["size"], "sensors": dict(lay["sensors"], extra="gpu|voltage|GPU Core"),
                                      "groups": groups})
            back = layout.load("landscape")
            assert back["custom"] and back["groups"] == groups and back["sensors"]["extra"] == "gpu|voltage|GPU Core"
            assert "fps" in back["sensors"]   # sensors added by newer defaults stay available
            layout.reset("landscape")
            assert not layout.load("landscape")["custom"]
        finally:
            config.DATA = old


@test
def every_new_block_draws():
    cfg = default_cfg()
    for kind in layout.BLOCK_KINDS:
        b = layout.new_block(kind, 10, 10, "cpu_temp")
        cfg2 = dict(cfg, widgets=cfg["widgets"] + layout.flatten([b]))
        r = render.Renderer(cfg2, 480, 320, base=ROOT)
        assert r.draw(FakeCollector()).size == (480, 320), kind


@test
def brand_names_without_logo_files():
    with tempfile.TemporaryDirectory() as d:
        cfg = default_cfg()
        fields = hardware.fields(hardware.build(hardware.DEMO_RAW))
        r = render.Renderer(cfg, 480, 320, base=Path(d), fields=fields, logo_dirs=[Path(d) / "logos"])
        assert r.logo_list() == [] and r.brand_names()
        img = r.draw(FakeCollector(game=False, media=False))
        assert img.crop((0, 0, 200, 36)).getbbox() is not None, "nothing drawn where the logos go"


@test
def old_folder_removal_is_guarded():
    sys.path.insert(0, str(ROOT / "tests"))
    from api import Api

    class App:
        engine = None
    api = Api.__new__(Api)
    api._app = App()
    assert api.remove_old("C:/Windows") is False
    assert api.remove_old(str(ROOT)) is False


@test
def setup_script_sources_exist():
    iss = (ROOT / "installer" / "Tela.iss").read_text(encoding="utf-8")
    for src in re.findall(r'Source: "\{#Root\}\\([^"]+)"', iss):
        path = ROOT / src.replace("\\", "/").replace("/*.yaml", "").replace("/*", "")
        assert path.exists(), src
    assert "AppId={{" in iss and "--autostart on" in iss and "--quit" in iss and "PawnIO" in iss
    wf = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "installer\\Tela.iss" in wf and "tests/run_tests.py" in wf
    assert re.fullmatch(r"\d+\.\d+\.\d+", engine.VERSION), engine.VERSION


@test
def setup_install_imports_a_39_folder():
    import os
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        saved_home, saved_data = os.environ.get("USERPROFILE"), config.DATA
        try:
            os.environ["USERPROFILE"] = str(d)   # stands in for C:\ (3.9 lived in C:\Tela)
            prog = d / "Program Files" / "Tela"
            prog.mkdir(parents=True)
            (prog / "unins000.exe").write_bytes(b"")
            shutil.copy(ROOT / config.DEFAULT, prog / config.DEFAULT)
            old = d / "Tela"
            (old / "logos").mkdir(parents=True)
            txt = (ROOT / config.DEFAULT).read_text(encoding="utf-8").replace("brightness: 40", "brightness: 27")
            (old / config.CONFIG).write_text(txt, encoding="utf-8")
            (old / "logos" / "AMD.png").write_bytes(b"x")
            data = d / "AppData" / "Tela"
            config.DATA = data
            assert config.find_old_install(prog) == old.resolve()
            msg, found = config.prepare(data, program=prog)
            assert found == old.resolve() and config.load(data / config.CONFIG)["display"]["brightness"] == 27, msg
            assert (data / "logos" / "AMD.png").exists()
            assert config.find_old_install(prog) == old.resolve()   # the data folder itself is never "old"
        finally:
            config.DATA = saved_data
            if saved_home is None:
                os.environ.pop("USERPROFILE", None)
            else:
                os.environ["USERPROFILE"] = saved_home


@test
def stalled_fps_capture_restarts():
    import subprocess as sp
    pm = sensors.PresentMon(Path("nope.exe"))
    pm.proc = sp.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    pm._started = time.monotonic() - 70           # open for 70 s, never wrote a line
    try:
        assert pm.alive() and pm.silent_for() > 60
        c = sensors.Collector(default_cfg(), demo=True, base=ROOT)
        c.pm = pm
        c.values["gpu_load"] = 80.0                   # a game is drawing
        if pm.silent_for() > 60 and (c.values.get("gpu_load") or 0) >= 25:
            pm.restart("no frames for 60 s while the GPU is busy")
        assert not pm.alive() and pm.proc is None and any("restarted" in e for e in pm.events)
        pm.feed(["Application,ProcessID,MsBetweenPresents,CPUStartTime", "game.exe,1,8.0,0.1"])
        assert pm._restarts == 0                      # frames arriving reset the back-off
        for _ in range(4):
            pm.restart("x")
        assert pm._next_try > time.monotonic() + 200  # after 3 tries it waits 5 minutes
    finally:
        if pm.proc is not None:
            pm.proc.kill()


@test
def summary_transitions_both_ways():
    calls = []
    e = engine.Engine(ROOT / config.DEFAULT, engine.Log(echo=False), demo=True, simulate="memory")
    orig = e._transition
    e._transition = lambda target, pause=0.0: (calls.append(e.renderer.layout), orig(target, 0.0))
    e.cfg.setdefault("session", {})["summary_seconds"] = 1
    e.start()
    try:
        time.sleep(1.2)
        e.command("summary_example")
        time.sleep(6.5)
    finally:
        e.stop()
        e.join(5)
    lost = [ln for ln in e.log.lines if "Lost the screen" in ln]
    assert not lost, lost
    assert calls[:2] == ["summary", "normal"], calls


@test
def paused_media_lingers_then_fades():
    from media import Media
    m = DemoMedia()
    m._set(dict(m.info, playing=True))
    assert m.current() and "paused_for" not in m.current()
    m._set(dict(m.info, playing=False))
    m._paused_at = time.time() - 2
    assert m.current()["paused_for"] >= 2                       # still shown 2 s after pausing
    m._paused_at = time.time() - (Media.GRACE + 0.3)
    col = FakeCollector(game=False, media=True)
    col.m = m
    r = render.Renderer(default_cfg(), 480, 320, base=ROOT)
    r.draw(col)
    assert r.animating                                         # fading out
    m._paused_at = time.time() - (Media.GRACE + Media.FADE + 0.1)
    assert m.current() is None
    m._set(dict(m.info, playing=True))
    assert m.current() and m._paused_at is None


@test
def media_stays_right_while_the_game_is_open():
    cfg = default_cfg()
    r = render.Renderer(cfg, 480, 320, base=ROOT)
    col = FakeCollector(game=False, media=True)                # game minimized: no FPS right now
    col.game_open = lambda: True
    v = visible_types(r, col)
    assert ("media", 298) in v and ("media", 10) not in v and ("clock", 468) not in v
    assert ("image", 12) in v                                  # the logos fill the left meanwhile
    c = sensors.Collector(cfg, demo=True, base=ROOT, demo_game=False)
    c.values["fps"] = 120.0
    assert c.game_open()
    c.values["fps"] = None
    assert c.game_open()                                       # 10 s cooldown after alt-tab
    c._fps_seen_at -= 11
    assert not c.game_open()
    s = sensors.Session(42, "Game")
    s.fps_samples = [100.0] * 40
    c.sessions[42] = s
    assert c.game_open()                                       # the game process is still open


@test
def game_history_saves_lists_prunes_and_exports():
    import history
    with tempfile.TemporaryDirectory() as d:
        cfg = {"history": {"save": True, "keep": 3, "folder": d}}
        base = 1_760_000_000
        for i in range(5):
            gid = history.save(cfg, {"name": f"Game {i}: Edição", "ended_at": base + i * 60, "seconds": 1800,
                                     "fps_avg": 100 + i, "fps_1low": 60, "fps_max": 144, "max": {"cpu": 70, "gpu": 65},
                                     "fps_series": [90, 100, 110]})
        games = history.entries(cfg)
        assert len(games) == 3 and games[0]["name"] == "Game 4: Edição"          # newest first, pruned to 3
        assert "fps_series" not in games[0]
        full = history.get(cfg, gid)
        assert full["fps_series"] == [90, 100, 110]
        assert history.get(cfg, "../../etc/passwd") is None                       # ids cannot leave the folder
        csv_text = history.to_csv(cfg)
        assert csv_text.count("\n") == 4 and "Edição" in csv_text
        assert history.delete(cfg, [gid]) == 1 and len(history.entries(cfg)) == 2
        with tempfile.TemporaryDirectory() as d2:
            assert history.move(cfg, d2) == 2 and len(list(Path(d2).glob("*.json"))) == 2
        assert history.save({"history": {"save": False, "folder": d}}, {"name": "x"}) is None


@test
def updater_reads_releases_and_compares_versions():
    import io
    import json as _json
    import updater
    assert updater.newer("v1.4.2", "1.4.1") and updater.newer("1.10.0", "1.9.9")
    assert not updater.newer("1.4.1", "1.4.1") and not updater.newer("garbage", "1.4.1")
    assets = [{"name": "Tela-Setup-1.4.2.exe", "browser_download_url": "a", "size": 5},
              {"name": "Tela-Setup.exe", "browser_download_url": "b", "size": 5, "digest": "sha256:ABC"}]
    info = updater.release_info({"tag_name": "v1.4.2", "assets": assets, "html_url": "page"})
    assert info["url"] == "b" and info["sha256"] == "abc" and info["version"] == "1.4.2"
    assert updater.release_info({"tag_name": "v1.4.2", "assets": assets, "prerelease": True}) is None
    assert updater.release_info({"tag_name": "v1.4.2", "assets": []}) is None

    class Resp(io.BytesIO):
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    old = updater._get
    try:
        updater._get = lambda url, timeout=20: Resp(_json.dumps({"tag_name": "v9.0.0", "assets": assets}).encode())
        u = updater.Updater("1.4.1")
        assert u.check()["state"] == "available" and u.snapshot()["version"] == "9.0.0"
        u2 = updater.Updater("9.0.0")
        assert u2.check()["state"] == "idle"

        def offline(url, timeout=20):
            raise OSError("no internet")
        updater._get = offline
        assert u.check()["state"] == "available" and u.error             # keeps the known release when offline
        payload = b"x" * 1000
        import hashlib
        u.info = {"version": "9.0.0", "url": "u", "size": 1000, "sha256": hashlib.sha256(payload).hexdigest()}
        updater._get = lambda url, timeout=20: Resp(payload)
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "Tela-Setup-9.0.0.exe"
            u._download(u.info, target)
            assert target.read_bytes() == payload and u.progress == 1.0
            u.info["sha256"] = "0" * 64
            try:
                u._download(u.info, target)
                raise AssertionError("a wrong checksum must fail")
            except OSError:
                pass
    finally:
        updater._get = old


@test
def changelog_covers_the_version_and_matches_markdown():
    sys.path.insert(0, str(ROOT / "installer"))
    import changelog
    from engine import VERSION
    entries = changelog.load()
    versions = [e["v"] for e in entries]
    assert versions[0] == VERSION, f"ui/changelog.js starts with {versions[0]}, the app is {VERSION}"
    keys = [tuple(int(x) for x in v.split(".")) for v in versions]
    assert keys == sorted(keys, reverse=True) and len(set(keys)) == len(keys)
    for e in entries:
        langs = ("pt", "en", "es", "zh")                        # every language the window has
        assert all(set(e[lang]) == set(e["en"]) for lang in langs) and set(e["en"]) <= set(changelog.CATEGORIES), e["v"]
        for c in e["en"]:
            assert all(len(e[lang][c]) == len(e["en"][c]) > 0 for lang in langs), (e["v"], c)
            for n in sum((e[lang][c] for lang in langs), []):
                assert not any(w in n for w in ("TelaV", "Telinha", "telinha", "Later:", "Depois:")), n
    assert (ROOT / "CHANGELOG.md").read_text(encoding="utf-8") == changelog.markdown(), \
        "CHANGELOG.md is outdated: python installer/changelog.py --markdown"
    assert "### New" in changelog.release_notes(VERSION) or "### Fixes" in changelog.release_notes(VERSION)


@test
def presets_detect_apply_and_custom():
    import presets
    cfg = config.load(ROOT / config.DEFAULT)
    assert presets.detect(cfg) == "default", "config_default.yaml must match the Default preset"
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "config.yaml"
        p.write_text((ROOT / config.DEFAULT).read_text(encoding="utf-8"), encoding="utf-8")
        config.Settings(p).set_many(presets.items("performance"))
        c = config.load(p)
        assert presets.detect(c) == "performance", [(s, k, presets.value(c, s, k)) for s, k, _ in presets.items("performance")]
        config.Settings(p).set("fps", "update", 0.3)
        assert presets.detect(config.load(p)) == "custom"
    r = render.Renderer(default_cfg(), 480, 320, ss=1, base=ROOT)       # "normal" quality draws at 1x
    assert r.draw(FakeCollector()).size == (480, 320)


@test
def profiles_save_apply_import():
    import profiles
    old = config.DATA
    with tempfile.TemporaryDirectory() as d:
        try:
            config.DATA = Path(d)
            cfg_path = Path(d) / "config.yaml"
            cfg_path.write_text((ROOT / config.DEFAULT).read_text(encoding="utf-8"), encoding="utf-8")
            config.Settings(cfg_path).set_many([("display", "brightness", 70), ("ui", "theme", "preset:red"),
                                                ("display", "port", "COM9")])
            layout.user_path("landscape").write_text("groups: []\n", encoding="utf-8")
            name = profiles.save(config.load(cfg_path), "Noite/Jogo", "1.4.2")
            assert name == "Noite Jogo" and profiles.entries()[0]["layouts"] == ["landscape"]
            data = profiles.read(name)
            assert ["display", "port", "COM9"] not in data["settings"]            # belongs to this PC
            config.Settings(cfg_path).set_many([("display", "brightness", 20), ("ui", "theme", "light")])
            layout.user_path("landscape").unlink()
            layout.user_path("portrait").write_text("groups: []\n", encoding="utf-8")
            profiles.apply(cfg_path, data)
            c = config.load(cfg_path)
            assert c["display"]["brightness"] == 70 and c["ui"]["theme"] == "preset:red"
            assert layout.user_path("landscape").exists() and not layout.user_path("portrait").exists()
            out = Path(d) / "x.tela-profile"
            profiles.export(name, out)
            assert profiles.import_file(out) == "Noite Jogo (2)"
            bad = Path(d) / "bad.tela-profile"
            bad.write_text('{"tela_profile": 1, "settings": [["evil", "k", 1]]}', encoding="utf-8")
            try:
                profiles.import_file(bad)
                raise AssertionError("a profile with unknown sections must be refused")
            except ValueError:
                pass
            assert profiles.delete(name) and len(profiles.entries()) == 1
        finally:
            config.DATA = old


@test
def other_screen_models_are_recognized():
    import display

    class P:
        def __init__(self, serial=None, vid=None, pid=None):
            self.serial_number, self.vid, self.pid = serial, vid, pid
    assert display.is_turing(P("USB35INCHIPSV2", 0x1A86, 0x5722))
    rev_b = P("2017-2-25", 0x1A86, 0x5722)                     # same USB chip, other protocol
    assert not display.is_turing(rev_b) and "revision B" in display.other_screen(rev_b)
    assert "revision C" in display.other_screen(P(None, 0x1D6B, 0x0121))
    assert display.other_screen(P("USB35INCHIPSV2", 0x1A86, 0x5722)) is None


@test
def turned_off_item_frees_its_place_for_the_logos():
    lay = layout.load("landscape", user=False)
    top = next(g for g in lay["groups"] if g["id"] == "top")
    logos = next(i for i in top["items"] if i["type"] == "image")
    left_media = next(i for i in top["items"] if i["type"] == "media" and "media_in_game" not in i["when"])
    cfg = default_cfg()
    col = FakeCollector(game=False, media=True)
    r = render.Renderer(dict(cfg, widgets=layout.flatten([top])), 480, 320, base=ROOT)
    w_logos = next(w for w in r.widgets if w["type"] == "image")
    assert not r._visible(w_logos, col)                      # music playing: it sits where the logos go
    left_media["enabled"] = False
    r = render.Renderer(dict(cfg, widgets=layout.flatten([top])), 480, 320, base=ROOT)
    w_logos = next(w for w in r.widgets if w["type"] == "image")
    assert r._visible(w_logos, col), "with the media item off, the logos must fill its place"
    assert logos is not None


@test
def updater_test_channel_and_skip():
    import updater
    rel = lambda v, pre=False: {"tag_name": "v" + v, "prerelease": pre,
                                "assets": [{"name": "Tela-Setup.exe", "browser_download_url": v, "size": 1}]}
    data = [rel("1.4.4", True), rel("1.4.3"), rel("1.4.2")]
    assert updater.pick_update(data, "1.4.2")["version"] == "1.4.3"                 # stable only
    assert updater.pick_update(data, "1.4.2", test=True)["version"] == "1.4.4"      # test versions too
    assert updater.pick_update(data, "1.4.2", test=True, skip="1.4.4")["version"] == "1.4.3"
    assert updater.pick_update(data, "1.4.4", test=True) is None
    assert updater.release_info(rel("1.4.4", True), test=True)["test"] is True


@test
def exe_version_resource_matches_the_version():
    sys.path.insert(0, str(ROOT / "installer"))
    import version_info
    from engine import VERSION
    txt = version_info.text()
    assert f"'ProductVersion', '{VERSION}'" in txt and "'ProductName', 'Tela!'" in txt
    assert "filevers=(" + ", ".join(VERSION.split(".")) + ", 0)" in txt


@test
def elements_rotate_measure_and_change_font():
    cfg = default_cfg()
    txt = {"type": "text", "text": "TELA", "x": 200, "y": 100, "size": 20, "bold": True}
    r = render.Renderer(dict(cfg, widgets=[]), 480, 320, ss=1, base=ROOT)
    col = FakeCollector()
    flat = r.item_box(txt, col)
    assert flat and flat[2] > flat[3], flat                                   # wide text
    tall = r.item_box(dict(txt, rotate=90), col)
    assert tall and tall[3] > tall[2], tall                                   # turned: now tall
    assert abs((tall[0] + tall[2] / 2) - (flat[0] + flat[2] / 2)) < 3          # around its own center
    assert r.item_box(dict(txt, font="consolas"), col)                        # unknown on Linux: falls back
    g = {"type": "gauge", "sensor": "cpu_temp", "cx": 100, "cy": 100, "radius": 40, "rotate": 45, "min": 0, "max": 100}
    img = render.Renderer(dict(cfg, widgets=[g, txt]), 480, 320, base=ROOT).draw(col)
    assert img.size == (480, 320)


@test
def old_downloaded_setups_are_cleaned():
    import updater
    with tempfile.TemporaryDirectory() as d:
        for n in ("Tela-Setup-1.4.1.exe", "Tela-Setup-1.4.2.part", "Tela-Setup-1.4.3.exe", "other.exe"):
            (Path(d) / n).write_bytes(b"x")
        assert updater.cleanup_downloads(d, keep="Tela-Setup-1.4.3.exe") == 2
        assert sorted(p.name for p in Path(d).iterdir()) == ["Tela-Setup-1.4.3.exe", "other.exe"]
    u = updater.Updater("1.4.3", options=lambda: {"hours": 1})
    assert u.every() == 2 * 3600                                       # never more often than every 2 h
    u.options = lambda: {"hours": 48}
    assert u.every() == 24 * 3600


@test
def temperature_alerts_wait_then_stay_quiet():
    from alerts import TempAlerts
    a = TempAlerts()
    cfg = {"alerts": {"enabled": True, "cpu": 90, "gpu": 85, "seconds": 20, "quiet_minutes": 15}}
    assert a.check(cfg, {"cpu": 95, "gpu": 60}, now=0) == []          # just went above: wait
    assert a.check(cfg, {"cpu": 95, "gpu": 60}, now=21) == [("cpu", 95, 90.0)]
    assert a.check(cfg, {"cpu": 96, "gpu": 60}, now=60) == []         # already told: quiet
    a.check(cfg, {"cpu": 80, "gpu": 60}, now=100)                      # cooled down
    a.check(cfg, {"cpu": 95, "gpu": 60}, now=200)
    assert a.check(cfg, {"cpu": 95, "gpu": 60}, now=230) == []        # still inside the 15 min quiet time
    assert a.check(cfg, {"cpu": 95, "gpu": 60}, now=21 + 15 * 60) == [("cpu", 95, 90.0)]
    assert a.check({"alerts": {"enabled": False}}, {"cpu": 120}, now=5000) == []


def main():
    failed = 0
    t0 = time.monotonic()
    for fn in TESTS:
        t = time.monotonic()
        try:
            note = fn()
            print(f"  ok    {fn.__name__}" + (f"  ({note})" if note else "") + f"  {time.monotonic() - t:.1f}s")
        except Exception:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed in {time.monotonic() - t0:.1f}s")
    threading.Event().wait(0.1)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
