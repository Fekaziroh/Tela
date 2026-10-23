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
- `presets.py` Performance/Default/Custom (detected from values); `profiles.py` named snapshots (.tela-profile)
- `history.py` saved games (one JSON per game in DATA/games or a chosen folder)
- `winsys.py` Windows integration (single instance on port 47614, scheduled task "Tela", power events)
- `tests/run_tests.py` dependency-free tests (run before every push; CI runs them on Windows)
- `tests/ui_server.py` serves the real UI in a browser with the engine in demo mode (for screenshots)

## Rules
- Versions: `engine.VERSION` (x.y.z). History numbering: 1.1.0 first app, 1.2.x second, 1.3.0–1.3.9, 1.4.x.
  Patch notes say only "Tela!" + version (never old names).
- Every user-visible change goes into `ui/changelog.js` (pt and en, categories new/fix/perf/look), then
  `python installer/changelog.py --markdown` regenerates CHANGELOG.md (a test checks they match).
- No brand logos in the repository (trademarks). `logos/` holds only a README.
- Log files, configs, layouts and caches are git-ignored; never commit user data.
- Commits (owner's rule): ONE commit per version. While a version is in progress, amend that single commit
  ("Tela! x.y.z (in progress)") and force push; at release it becomes "Tela! x.y.z". Author
  `Fekaziroh <Fekaziroh@users.noreply.github.com>`, only the line `Co-Authored-By: Claude ...` at the end,
  NEVER a "Claude-Session:" link. (The 1.4.1 commit still has one: tag v1.4.1 points to it and this session
  cannot move tags.)
- This session cannot create or delete releases/tags: only the workflow (GITHUB_TOKEN) creates releases;
  the owner deletes them in the GitHub UI (Releases › Delete, then Tags › delete the tag).
- The owner wants suggestions mentioned, and no new update started before he finishes sending ideas.
- Owner's rule (from 1.4.4 on): every new version is first published as a TEST version (`"beta": true` in
  ui/changelog.js → GitHub pre-release); he updates from the app with "Receive test versions" on; when he
  approves, remove "beta" and push (the workflow promotes it to the stable release).
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

## Versioning
- 1.x.0 = big change (new interface = 1.5.0); 1.x.y = each update of features and fixes.
- Urgent fix between updates takes the next number (the updater only reads three numbers, never 1.4.2.1);
  planned updates then move one number forward. Updates are known by name, the number is given at release.
- Only the latest version gets fixes.

## Roadmap (owner's roadmap file of 2026-10-23, organized; on hold until he says to start)
- The living roadmap is the owner's Claude doc "Tela! — Roadmap" (https://claude.ai/artifact/2HAXJyThY8ZJLaarXTfAQz):
  he writes ideas under "Ideias novas"; at the start of a session read it, sort new ideas into versions,
  empty that list, keep these notes in sync. Under "Ideias do Claude" the owner writes OK in front of the
  suggestions he approves: move those into a version. Decided: Performance preset keeps update checks on; tray
  consumption goes on a second line of the tooltip.
- 1.4.2 Presets, profiles and fixes: presets Performance (pause preview while the window is open, lower
  drawing quality, longer intervals) / Default / Custom (automatic when anything differs); profiles
  save/load/import/export; FIX "auto" window theme falls back to graphite (CSS defaults in style.css and the
  startup background in app.py are graphite: make them black); FIX tray icon option (Logo/CPU/GPU) only
  applies after a restart (tray.temp_icon is UI_ONLY in api.py, the tray loop reads engine.cfg); title bar
  color follows the theme (Win 11 caption color, Win 10 only dark/light); history default keep = 15 and a
  confirmation before deleting when the number is lowered (only the default changes); update notice in the
  tray icon; compatibility section in README + release notes, warning when the screen is not supported;
  night brightness: drop the "brightness at this time" label, % in front of the slider; patch notes
  rewritten with categories per version (new / fixes / performance / appearance), no "Later:" style lines
- 1.4.3 (also) Test channel: option "Receive test versions" in Advanced; the updater then also sees
  prereleases (GET /releases, newest non-draft); the workflow publishes a version marked "beta": true in
  ui/changelog.js as a prerelease (not latest), so only the owner/testers get it
- 1.4.3 (also) quick UI: "interval per item" grouped by component (CPU/GPU/RAM/Disks/Network), collapsible,
  showing only items that differ from the base first + "Show all"; night brightness: times above the slider,
  24 h; patch notes: more space and a divider between versions
- 1.4.3 Element-level layout editor: delete/rotate/resize gauges, icons, texts; palette to drag elements in;
  fonts and sizes; automatic re-flow on/off; top bar split into its items (clock, logos, FPS...);
  Layout tab gives priority to the screen layout (window theme and app settings lower / elsewhere)
- 1.4.4 Orientation, portrait and organization: orientation in Layout + shortcut on Home (out of Settings ›
  screen connection); portrait layout using the space better, media mini player in the date's place during a
  game; frametime graph bigger, customizable, integrated with the FPS;
  search in Settings
- 1.4.5 Themes and personalization (moved up from 1.5.0, owner's focus): at least 5 themes with different
  shapes and arrangements (bars, gauges, graphs, drawings), not only colors, each in landscape and portrait,
  built on the 1.4.3 element system; NEW DEFAULT THEME = the "first version" look (owner's picture of the old
  TelaV2 screen): top bar with brand logo left, big clock center, second brand logo right (brand names as
  text when no logo files; FPS takes a logo's place during a game); two big panels CPU and GPU (name in the
  title, ring gauge with temperature, rows USO/CLOCK/CONSUMO/FAN with units); bottom row RAM, SSD, and ONE
  block joining Network (UP/DOWN) and Volume; cleaner than today, dark background, thin borders. Existing
  users keep their layout and get a notice. Also: editable screen texts; disks title automatic + manual;
  weather (city, temperature on by default, condition; Open-Meteo, only the city goes online) next to the
  date in the themes; export/import a theme as a file (with the 1.4.2 profiles); automatic re-flow also for
  the elements inside a block (deleting/resizing one rearranges the others)
- 1.4.6 History: average per game, compare two games, game icon before the name in the summary
- 1.5.0 New window interface: visual identity (mockups first), deeper performance mode, sharper preview tied
  to the preset, review of settings/files/data
- Undecided, later: Lite build (decide after measuring the Performance preset); "Landscape" screen mode
  (picture, clock, slideshow, GIF; real video probably too slow for the USB link)
- 1.4.3 (also) updater/tray: roll back to an older release (Advanced › Updates: list releases, reinstall
  the chosen setup; Inno allows downgrades; "skip this version" so the notice does not insist); tray tooltip
  with Tela!'s CPU/RAM (program + window); 
- 1.4.3 (also) signing prep: version resource in Tela.exe (product "Tela!", version) via PyInstaller
  --version-file; "About" section in Advanced (version, license, credits, independent-project notice)
- SignPath: owner applied (README has "Code signing policy"); when approved, wire SignPath signing of
  Tela.exe and Tela-Setup.exe into release.yml and update that README section. Owner also submits the
  setup to Microsoft (wdsi/filesubmission) for SmartScreen reputation

## 1.4.2 — in progress (draft in ui/changelog.js)
- [x] Fixes, presets, profiles, tray update notice, history 15, compatibility, categorized notes, prints
- [x] Published as v1.4.2 (owner tests the update from 1.4.1; if bad he deletes release + tag, fixes go to 1.4.3)

## 1.4.3 — in progress (draft in ui/changelog.js)
- [x] Fixes (top bar place freed for logos, clear item names), quick UI, screen-off schedule, tray usage line
- [x] Updates: test channel ("beta": true → pre-release), rollback list + skip version
- [x] Element editor: element boxes measured by api.layout_boxes (render.item_box), move/resize/rotate/delete,
      font per element (render.FONT_FAMILIES), palette drag (pointer events), block reflow (ui.reflow)
- [x] Version resource (installer/version_info.py), About card, GitHub issue forms
- [x] Published as stable v1.4.3 (1.4.2 cannot see test versions, so this one had to be stable)

## Compatibility notes (applied to README in 1.4.2)
Compatibility section (also in release notes):
- System: Windows 10 and 11, 64-bit. Windows 7/8 not supported; Windows on ARM untested.
- Screen: Turing Smart Screen 3.5" revision A (USB `USB35INCHIPSV2`). 2.1", 5", 8.8" and 3.5" revision B
  use other protocols: not supported yet.
- Components: .NET Framework 4.7.2+ (built into an updated Windows 10); WebView2 and PawnIO installed by
  the setup when missing.
- Hardware: AMD, NVIDIA and Intel CPUs/GPUs (LibreHardwareMonitor).
- FPS: DirectX 9-12 and Vulkan games through PresentMon; OpenGL may not show; RTSS optional.
- Permission: administrator (sensors); the setup handles it.
- Languages: Portuguese, English, Spanish, Chinese.
- Versioning rules above and "only the latest version gets fixes".
