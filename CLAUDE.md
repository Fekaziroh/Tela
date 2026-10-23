# Tela! — notes for working on this project

Sensor panel app for the Turing Smart Screen 3.5" (rev A, 480×320, serial `USB35INCHIPSV2`), Windows only.
Python 3.13 + pywebview (WebView2) window, packaged with PyInstaller and an Inno Setup installer built by
GitHub Actions (`.github/workflows/release.yml`). The owner speaks Portuguese; code, comments, commits and
the repository are in English. The window is translated (pt, en, es, zh in `ui/i18n.js`, same keys in all).

## Map
- `app.py` entry point: window (pywebview) or browser fallback (`bridge.py`), tray, watchdog, setup flags
  (`--autostart on|off`, `--quit`, `--tray`, `--demo`, `--simulate`, `--browser`)
- `engine.py` thread: read sensors → `render.py` draws → `display.py` sends only changed regions
- `sensors.py` LibreHardwareMonitor (embedded via pythonnet), PresentMon/RTSS FPS, ping, volume, sessions
- `layout.py` blocks layout: `layouts/<family>.yaml` defaults, user copy `layout_<family>.yaml` in DATA
- `config.py` settings (`config.yaml` in DATA, defaults in `config_default.yaml`), migration from old copies.
  DATA = `%APPDATA%\Tela` when installed by the setup (unins000.exe next to the exe), else the program folder
- `api.py` everything the window calls; `ui/` window (app.js, editor.js, themes.js, wizard.js, history.js, i18n.js)
- `updater.py` update check/download/silent setup; `installer/changelog.py` notes for CHANGELOG.md and releases
- `history.py` saved games (one JSON per game in DATA/games or a chosen folder)
- `winsys.py` Windows integration (single instance on port 47614, scheduled task "Tela", power events)
- `tests/run_tests.py` dependency-free tests (run before every push; CI runs them on Windows)
- `tests/ui_server.py` serves the real UI in a browser with the engine in demo mode (for screenshots)

## Rules
- Versions: `engine.VERSION` (x.y.z). History numbering: 1.1.0 first app, 1.2.x second, 1.3.0–1.3.9, 1.4.x.
  Patch notes say only "Tela!" + version (never old names).
- Every user-visible change goes into `ui/changelog.js` (pt and en), then
  `python installer/changelog.py --markdown` regenerates CHANGELOG.md (a test checks they match).
- No brand logos in the repository (trademarks). `logos/` holds only a README.
- Log files, configs, layouts and caches are git-ignored; never commit user data.
- The owner wants suggestions mentioned, and no new update started before he finishes sending ideas.
- Releases: a push to main whose `engine.VERSION` has no release (and is not a draft in ui/changelog.js)
  makes the workflow create `v<version>` with `Tela-Setup-<version>.exe` and `Tela-Setup.exe` (the updater
  downloads the fixed name). Bump VERSION in engine.py and installer/Tela.iss together.
- `updater.py` checks GitHub every 6 h; `tests/ui_server.py --update 9.9.9` fakes a release for the UI.

## 1.4.1 (public release) — done
- [x] Quick UI: flag only on Home/Settings; no "Test colors" on Home; night slider as a sub-item;
      intervals per item easier to find; "Music" pill → "Media"; default dark window theme = Black;
      clean wording (no chatbot-like phrases)
- [x] Background image: Remove always works; changing screen theme does not keep a stale picture
- [x] Screen colors: "Custom" theme separate from the presets
- [x] Media: hides 5 s after pausing, with a fade; stays on the right while the game process is open
- [x] Transition when leaving the game summary (cascade like entering)
- [x] Window memory: preview drawn on a canvas (no data-URL buildup), low memory while in the tray
- [x] Game history: every summary saved; list, details, delete, export CSV, show on screen; retention
- [x] Changelog (1.1.0 → 1.4.1), patch notes view, "what's new" after an update
- [x] Updater: checks releases, animated button, tooltip with version, download + silent install + reopen
- [x] Workflow: create release automatically (versioned + `Tela-Setup.exe`), notes from the changelog
      (1.4.1 is marked `"draft": true` in ui/changelog.js: remove it in the final commit to publish)
- [x] README with screenshots and a download button (docs/*.png from tests/ui_server.py in English)
- [x] Squash history into one commit "Tela! 1.4.1", repository public, release v1.4.1 created by the workflow

## Later (agreed with the owner)
- Next updates: do not start before the owner finishes sending suggestions.
- 1.4.2: presets (performance/default/custom), profiles (save/load/import/export), element-level layout
  editor (delete/rotate/resize elements, drag from a palette, fonts and sizes, auto re-flow toggle)
- 1.4.5: editable screen texts (disks title SSD/HD/Disks, etc.)
- Free code signing for open source (SignPath) to remove the SmartScreen warning
