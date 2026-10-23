#!/usr/bin/env python3
"""Tela console mode (no window), used for diagnostics.

  python cli.py              runs on the screen, printing the log
  python cli.py --list       lists every sensor available on this PC
  python cli.py --test       paints the screen red/green/blue/white
  python cli.py --simulate   no screen; saves preview.png on every update
  python cli.py --demo       fake data (layout tests without sensors)
"""
import argparse
import time

import config
from engine import HERE, Engine, Log
from sensors import RTSS, LhmEmbedded, is_admin, make_reader


def sensor_rows(cfg, reader=None):
    """[(hardware, selector, value text)] of every sensor. 'reader' = an open reader (the window passes the engine's)."""
    notes = []
    lhm = reader
    if lhm is None:
        lhm, web = make_reader(cfg, HERE)
        lhm.read()
        if isinstance(lhm, LhmEmbedded) and lhm.start_error:
            notes.append(f"embedded monitor unavailable: {lhm.start_error}; using the LibreHardwareMonitor web server")
            lhm = web
            lhm.read()
    rows = []
    if lhm.error:
        notes.append(f"could not read the sensors: {lhm.error}")
    for s in lhm.sensors:
        parts = s["id"].strip("/").split("/")
        token = parts[0] if parts else ""
        kind = s["type"] or (parts[2] if len(parts) > 2 else s["group"].lower())
        rows.append((s["hardware"], f"{token}|{kind}|{s['name']}", str(s["text"])))
    rt = RTSS()
    rt.read()
    extras = [("sys.ram_pct", ""), ("sys.ram_used_gb", ""), ("sys.cpu_pct", ""), ("sys.disk_pct:C:", ""),
              ("sys.net_down_mbps", ""), ("sys.net_up_mbps", ""), ("sys.volume", ""), ("fps.value", ""),
              ("fps.frametime", "")]
    rows += [("Windows / FPS", sel, val) for sel, val in extras]
    return rows, notes


def sensor_text(cfg, reader=None):
    rows, notes = sensor_rows(cfg, reader)
    out, current = [f"({n})" for n in notes], None
    for hw, sel, val in rows:
        if hw != current:
            current = hw
            out.append(f"\n=== {hw} ===")
        out.append(f"  {val:>14}   \"{sel}\"")
    return "\n".join(out)


def color_test(engine, log):
    from PIL import Image
    s = engine.screen
    log("Test mode: connecting (the reset takes ~5 s)...")
    s.connect()
    log(f"Connected on {s.port_in_use}. Brightness {s.brightness}%")
    for name, c in [("red", "#FF0000"), ("green", "#00FF00"), ("blue", "#0000FF"), ("white", "#FFFFFF")]:
        t = time.monotonic()
        s.send_image(Image.new("RGB", (s.width, s.height), c), 0, 0)
        log(f"{name} sent ({time.monotonic() - t:.1f} s)")
        time.sleep(3)
    s.close()


def main():
    ap = argparse.ArgumentParser(description="Tela! sensor panel for the Turing Smart Screen 3.5\"")
    ap.add_argument("--config", default=str(HERE / config.CONFIG))
    ap.add_argument("--list", action="store_true", help="list the available sensors and exit")
    ap.add_argument("--test", action="store_true", help="paint the screen with solid colors")
    ap.add_argument("--simulate", action="store_true", help="no screen; save preview.png")
    ap.add_argument("--demo", action="store_true", help="fake data")
    ap.add_argument("--once", action="store_true", help="draw one frame and exit")
    a = ap.parse_args()
    from pathlib import Path
    if not Path(a.config).exists():
        config.prepare(search_old=False)

    if a.list:
        if not is_admin():
            print("(no administrator rights: CPU and motherboard temperatures may be missing)\n")
        print(sensor_text(config.load(a.config)))
        return

    log = Log(echo=True)
    engine = Engine(a.config, log, demo=a.demo, simulate=a.simulate, once=a.once)
    if a.test:
        color_test(engine, log)
        return
    log("Tela started (console)" + (" — demo" if a.demo else ""))
    engine.start()
    try:
        while engine.is_alive():
            engine.join(0.5)
    except KeyboardInterrupt:
        log("Closing.")
        engine.stop()
        engine.join(8)


if __name__ == "__main__":
    main()
