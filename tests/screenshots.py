"""Screenshots for the README (English, dark theme, demo data).

    python tests/screenshots.py [out folder]        (needs: pip install playwright; playwright install chromium)

Starts tests/ui_server.py, seeds a few example games and profiles, and saves window.png, editor.png,
history.png, settings.png, screen-landscape.png and screen-portrait.png. Leaves no data behind.
"""
import asyncio
import base64
import math
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
import history  # noqa: E402

GAMES = [("Cyberpunk 2077", 72), ("Counter-Strike 2", 288), ("Forza Horizon 5", 118), ("Elden Ring", 59),
         ("Baldur's Gate 3", 94)]
CREATED = ["games", "profiles", "config.yaml", "layout_landscape.yaml", "layout_portrait.yaml", "version.txt"]


def seed():
    rnd = random.Random(3)
    cfg = {"history": {"save": True, "keep": 200}}
    for i, (name, avg) in enumerate(GAMES):
        series = [max(20, avg + rnd.gauss(0, avg * 0.08) + 8 * math.sin(j / 7)) for j in range(120)]
        history.save(cfg, {"name": name, "ended_at": time.time() - 3600 - i * 86400 * 1.3, "seconds": 3600 + i * 700,
                           "duration": f"{1 + i // 2}h {12 + i * 7}min", "fps_avg": avg, "fps_1low": avg * 0.68,
                           "fps_max": max(series), "max": {"cpu": 68 + i, "gpu": 63 + i, "hotspot": 79 + i},
                           "fps_series": series})


def cleanup(existing):
    for name in CREATED:
        p = config.DATA / name
        if name in existing or not p.exists():
            continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()


async def shoot(url, out):
    from playwright.async_api import async_playwright

    async def canvas(pg, path):
        d = await pg.eval_on_selector("#preview", "c => c.toDataURL('image/png')")
        path.write_bytes(base64.b64decode(d.split(",")[1]))

    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1180, "height": 760}, color_scheme="dark", device_scale_factor=2)
        await pg.goto(url)
        await pg.wait_for_timeout(2500)
        await pg.keyboard.press("Escape")
        await pg.click("#lang-btn")
        await pg.click("#lang-menu [data-l=en]")
        await pg.wait_for_timeout(3500)
        await pg.screenshot(path=out / "window.png")
        await canvas(pg, out / "screen-landscape.png")
        # editor with an element selected
        await pg.click("nav [data-tab=layout]")
        await pg.wait_for_timeout(1500)
        bx = await (await pg.query_selector('#stage-boxes .box[data-id="cpu"]')).bounding_box()
        await pg.mouse.click(bx["x"] + bx["width"] * 0.9, bx["y"] + bx["height"] * 0.95)
        await pg.wait_for_timeout(900)
        best = None
        for el in await pg.query_selector_all("#stage-boxes .ibox"):
            r = await el.bounding_box()
            if not best or r["width"] * r["height"] > best[0]:
                best = (r["width"] * r["height"], r)
        r = best[1]
        await pg.mouse.click(r["x"] + r["width"] / 2, r["y"] + r["height"] / 2)
        await pg.wait_for_timeout(900)
        await pg.evaluate("document.querySelector('#main').scrollTop = 0")
        await pg.screenshot(path=out / "editor.png")
        await pg.keyboard.press("Escape")
        await pg.keyboard.press("Escape")
        # history
        await pg.click("nav [data-tab=settings]")
        await pg.click("#hist-open")
        await pg.wait_for_timeout(500)
        await pg.click(".hist-row")
        await pg.wait_for_timeout(700)
        await pg.screenshot(path=out / "history.png")
        await pg.keyboard.press("Escape")
        # presets and profiles
        for name in ("Gaming", "Night"):
            await pg.click("#prof-new")
            await pg.wait_for_timeout(300)
            await pg.fill("#modal-body input", name)
            await pg.click("#modal-foot .pri")
            await pg.wait_for_timeout(500)
        await pg.evaluate("document.querySelector('#main').scrollTop = 0")
        await pg.wait_for_timeout(3000)
        await pg.screenshot(path=out / "settings.png")
        # portrait screen
        await pg.click("nav [data-tab=home]")
        await pg.click("#home-orient [data-v=portrait]")
        await pg.wait_for_timeout(5000)
        await canvas(pg, out / "screen-portrait.png")
        await pg.click("#home-orient [data-v=landscape]")
        await pg.wait_for_timeout(1500)
        await b.close()


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "docs")
    out.mkdir(parents=True, exist_ok=True)
    existing = {n for n in CREATED if (config.DATA / n).exists()}
    seed()
    srv = subprocess.Popen([sys.executable, str(ROOT / "tests" / "ui_server.py"), "--port", "8765"],
                           stdout=subprocess.PIPE, text=True, cwd=ROOT)
    try:
        url = srv.stdout.readline().strip()
        time.sleep(4)
        asyncio.run(shoot(url, out))
    finally:
        srv.terminate()
        srv.wait(10)
        cleanup(existing)
    print("saved in", out)


if __name__ == "__main__":
    main()
