"""Patch notes from ui/changelog.js (the single source).

    python installer/changelog.py --markdown        rewrites CHANGELOG.md
    python installer/changelog.py --notes 1.4.1     prints the GitHub release notes of a version
    python installer/changelog.py --ready 1.4.1     exit code 0 when that version can be released (not a draft)
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "ui" / "changelog.js"
MARKDOWN = ROOT / "CHANGELOG.md"


def load():
    text = SOURCE.read_text(encoding="utf-8")
    start = text.index("const CHANGELOG = ") + len("const CHANGELOG = ")
    end = text.index("\n];", start) + 2
    return json.loads(text[start:end])


def markdown(entries=None):
    out = ["# Changelog", "", "Every version of Tela!, newest first. Portuguese notes are in the app "
           "(Advanced › Patch notes).", ""]
    for e in entries or load():
        out += [f"## Tela! {e['v']}", ""] + [f"- {n}" for n in e["en"]] + [""]
    return "\n".join(out)


def release_notes(version):
    e = next((x for x in load() if x["v"] == version), None)
    if e is None:
        raise SystemExit(f"ui/changelog.js has no entry for {version}")
    lines = ["## What's new", ""] + [f"- {n}" for n in e["en"]]
    lines += ["", "<details><summary>Novidades (português)</summary>", ""] + [f"- {n}" for n in e["pt"]]
    lines += ["", "</details>", "", "## Install", "",
              "Download **Tela-Setup.exe** below and run it. Updating keeps your settings; "
              "Tela! 1.4.1 and newer update themselves from the window.", "",
              "Windows SmartScreen may warn because the setup is not code-signed: "
              "**More info › Run anyway**."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--notes")
    ap.add_argument("--ready")
    a = ap.parse_args()
    if a.ready:
        e = next((x for x in load() if x["v"] == a.ready), None)
        sys.exit(0 if e and not e.get("draft") else 1)
    if a.markdown:
        MARKDOWN.write_text(markdown(), encoding="utf-8")
    if a.notes:
        sys.stdout.reconfigure(encoding="utf-8")
        print(release_notes(a.notes), end="")
