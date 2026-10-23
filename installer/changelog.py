"""Patch notes from ui/changelog.js (the single source).

    python installer/changelog.py --markdown        rewrites CHANGELOG.md
    python installer/changelog.py --notes 1.4.1     prints the GitHub release notes of a version
    python installer/changelog.py --ready 1.4.1     exit code 0 when that version can be released (not a draft)
    python installer/changelog.py --channel 1.4.1   prints draft | test | stable
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "ui" / "changelog.js"
MARKDOWN = ROOT / "CHANGELOG.md"
CATEGORIES = ("new", "fix", "perf", "look")
TITLES = {"en": {"new": "New", "fix": "Fixes", "perf": "Performance", "look": "Appearance and personalization"},
          "pt": {"new": "Novidades", "fix": "Correções", "perf": "Desempenho", "look": "Aparência e personalização"}}


def load():
    text = SOURCE.read_text(encoding="utf-8")
    start = text.index("const CHANGELOG = ") + len("const CHANGELOG = ")
    end = text.index("\n];", start) + 2
    return json.loads(text[start:end])


def _section(notes, lang, level="###"):
    out = []
    for c in CATEGORIES:
        if notes.get(c):
            out += [f"{level} {TITLES[lang][c]}", ""] + [f"- {n}" for n in notes[c]] + [""]
    return out


def markdown(entries=None):
    out = ["# Changelog", "", "Every version of Tela!, newest first. Portuguese notes are in the app "
           "(Advanced › Patch notes).", ""]
    for e in entries or load():
        out += [f"## Tela! {e['v']}", ""] + _section(e["en"], "en")
    return "\n".join(out)


def release_notes(version):
    e = next((x for x in load() if x["v"] == version), None)
    if e is None:
        raise SystemExit(f"ui/changelog.js has no entry for {version}")
    lines = _section(e["en"], "en")
    lines += ["<details><summary>Novidades em português</summary>", ""] + _section(e["pt"], "pt", "####")
    lines += ["</details>", "", "## Install", "",
              "Download **Tela-Setup.exe** below and run it. Updating keeps your settings; "
              "Tela! 1.4.1 and newer update themselves from the window.", "",
              "Requirements: Windows 10 or 11 (64-bit) and a Turing Smart Screen 3.5\" revision A. "
              "See [Compatibility](https://github.com/Fekaziroh/Tela#compatibility).", "",
              "Windows SmartScreen may warn because the setup is not code-signed: "
              "**More info › Run anyway**."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--notes")
    ap.add_argument("--ready")
    ap.add_argument("--channel")
    a = ap.parse_args()
    if a.channel:
        e = next((x for x in load() if x["v"] == a.channel), None)
        print("draft" if not e or e.get("draft") else "test" if e.get("beta") else "stable")
        sys.exit(0)
    if a.ready:
        e = next((x for x in load() if x["v"] == a.ready), None)
        sys.exit(0 if e and not e.get("draft") else 1)
    if a.markdown:
        MARKDOWN.write_text(markdown(), encoding="utf-8")
    if a.notes:
        sys.stdout.reconfigure(encoding="utf-8")
        print(release_notes(a.notes), end="")
