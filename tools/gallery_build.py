"""Builds the community gallery (the repository's "gallery" branch) from a folder of shared themes.

    python tools/gallery_build.py <folder>

<folder> holds the approved .tela-theme files and gallery.json:
    {"themes": [{"file": "sakura.tela-theme", "name": "Sakura", "author": "someone",
                 "link": "https://github.com/Fekaziroh/Tela/discussions/1", "added": "2026-10-24"}]}
It checks every theme (the same check as Import), draws its picture with demo values (landscape) and writes
index.json, themes/ and pictures/ into <folder>/out, ready to be committed on the "gallery" branch.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("TELA_DATA", tempfile.mkdtemp(prefix="tela-gallery-data-"))
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
import hardware  # noqa: E402
import layout  # noqa: E402
import render  # noqa: E402
import sensors  # noqa: E402
import themes  # noqa: E402


def picture(tid, out):
    cfg = config.load(ROOT / config.DEFAULT)
    cfg["theme"] = {"name": tid}
    layout.apply(cfg)
    cfg["colors"] = themes.colors(tid)
    cfg["animation"] = {"enabled": False}
    fields = hardware.fields(hardware.build(hardware.DEMO_RAW))
    col = sensors.Collector(cfg, demo=True, base=str(ROOT), fields=fields, demo_game=False, demo_media=True)
    for _ in range(60):
        col.update()
    r = render.Renderer(cfg, 480, 320, base=str(ROOT), fields=fields,
                        logo_dirs=[Path(tempfile.mkdtemp())])   # empty folder: brand names as text, no logos
    img = None
    for _ in range(3):
        img = r.draw(col)
    img.save(out, optimize=True)


def main(folder):
    src = Path(folder)
    meta = json.loads((src / "gallery.json").read_text(encoding="utf-8"))
    out = src / "out"
    shutil.rmtree(out, ignore_errors=True)
    (out / "themes").mkdir(parents=True)
    (out / "pictures").mkdir()
    index = []
    for it in meta["themes"]:
        f = src / it["file"]
        tid = themes.import_file(f)           # refuses anything that is not a valid theme
        stem = Path(it["file"]).stem
        shutil.copy(f, out / "themes" / it["file"])
        picture(tid, out / "pictures" / f"{stem}.png")
        index.append({**it, "picture": f"{stem}.png"})
        print("ok", it["file"])
    (out / "index.json").write_text(json.dumps({"themes": index}, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "README.md").write_text(
        "# Tela! community gallery\n\nThemes shared by people in "
        "[Discussions](https://github.com/Fekaziroh/Tela/discussions/categories/show-and-tell). "
        "Tela! lists them in Appearance › Gallery and imports one with a click.\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
