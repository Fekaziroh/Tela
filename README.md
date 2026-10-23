# Tela!

**A free, modern alternative to the official Turing Smart Screen software.**

> [!NOTE]
> **Tela! is a fan-made, independent project.** It has no connection with Turing, XuanFang, Kipye or any
> other maker or seller of these screens, and none of them supports or reviews it. Brand names such as
> Turing, AMD, NVIDIA or Intel appear here only to say what Tela! works with, and belong to their owners.
>
> Questions about the screen itself or the app that came with it go to the store where you bought it.
> Issues here are for Tela! only.

[![Download for Windows](https://img.shields.io/badge/Download-Tela--Setup.exe-2ea44f?style=for-the-badge)](https://github.com/Fekaziroh/Tela/releases/latest/download/Tela-Setup.exe)
[![Latest version](https://img.shields.io/github/v/release/Fekaziroh/Tela?style=for-the-badge&label=version&color=444)](https://github.com/Fekaziroh/Tela/releases)
[![Changelog](https://img.shields.io/badge/changelog-what's%20new-444?style=for-the-badge)](CHANGELOG.md)
[![Windows 10/11](https://img.shields.io/badge/Windows-10%20%7C%2011-444?style=for-the-badge)](#compatibility)
[![License MIT](https://img.shields.io/badge/license-MIT-444?style=for-the-badge)](LICENSE)

<p align="center">
  <img src="https://raw.githubusercontent.com/Fekaziroh/Tela/screenshots/screen-landscape.png" width="480" alt="The 3.5 inch screen in landscape">
  &nbsp;
  <img src="https://raw.githubusercontent.com/Fekaziroh/Tela/screenshots/screen-portrait.png" width="214" alt="The 3.5 inch screen in portrait">
</p>

Those small USB screens sold on AliExpress and Amazon come with an app that only shows a few fixed sensors.
Tela! turns the 3.5" model into a real hardware dashboard, in the spirit of the AIDA64 sensor panel:
any sensor your PC has, live FPS from your games, what you are listening to, and a layout you arrange
yourself, all set up from a clean window instead of config files.

- CPU, GPU, RAM, VRAM, disks, network and volume, read by an embedded LibreHardwareMonitor
- **FPS** with frame-time graph and 1% low (PresentMon, or RTSS when it is open)
- **Game summary** when a game closes: average/1% low/max FPS, max temperatures, FPS graph
- **Game history**: every summary is saved; search it, see the FPS graph, export to CSV
- **Music and video** playing (Spotify, YouTube, any app in the Windows media controls) with progress line;
  during a game it moves to the date's place
- Network panel with ping, packet loss and internet outage warning
- **Layout editor**: drag, resize, turn blocks on and off, rename, pick sensors from a live list; edit every
  element (move, resize, rotate, font and size) and drag new ones from a palette
- Landscape and portrait (and both flipped), screen color themes, background picture
- Window themes (automatic, ready-made or your own colors), Portuguese, English, Spanish and Chinese
- Turns the screen off when the PC locks, the monitor sleeps, the PC sleeps or Tela! closes
- **Presets** (Performance, Default, Custom) and **profiles** you can save, switch, export and import
- Temperature alerts, screen off at set hours, search in Settings
- Eco mode when you are away, automatic recovery, diagnostics report
- Updates itself: a button lights up when a new version is out

![The Tela! window](https://raw.githubusercontent.com/Fekaziroh/Tela/screenshots/window.png)

| Layout editor | Game history |
|---|---|
| ![Layout editor](https://raw.githubusercontent.com/Fekaziroh/Tela/screenshots/editor.png) | ![Game history](https://raw.githubusercontent.com/Fekaziroh/Tela/screenshots/history.png) |

![Presets and profiles](https://raw.githubusercontent.com/Fekaziroh/Tela/screenshots/settings.png)

## Install

Download **[Tela-Setup.exe](https://github.com/Fekaziroh/Tela/releases/latest/download/Tela-Setup.exe)**
(always the latest version) and run it. The setup:

- installs Tela! in *Program Files* with a Start menu shortcut and an entry in *Settings › Apps*
- includes the hardware monitor and PresentMon
- downloads the **PawnIO** driver (CPU and motherboard temperatures) and **Microsoft WebView2** only if
  they are missing
- can start Tela! with Windows (no administrator prompt at logon)

When a new version is out, the version number next to the Tela! name lights up: click it and Tela!
downloads the setup, installs it and opens again. Settings, layouts, themes and the game history are kept
in `%APPDATA%\Tela`.

> Windows SmartScreen may warn the first time because the setup has no paid code-signing certificate:
> click **More info › Run anyway**.

See [Compatibility](#compatibility) before buying a screen for Tela!.

## Compatibility

| | Supported |
|---|---|
| **Windows** | Windows 10 and 11, 64-bit. Windows 7 and 8 are not supported; Windows on ARM is untested. |
| **Screen** | Turing Smart Screen 3.5" **revision A** (USB serial `USB35INCHIPSV2`). The 2.1", 5" and 8.8" models and the 3.5" revision B (XuanFang) use other protocols and are not supported yet; Tela! tells you when it finds one. |
| **Components** | .NET Framework 4.7.2 or newer (included in an updated Windows 10). WebView2 and PawnIO are installed by the setup when missing. |
| **Hardware** | AMD, NVIDIA and Intel CPUs and GPUs (through LibreHardwareMonitor). |
| **FPS** | DirectX 9 to 12 and Vulkan games through PresentMon. OpenGL games may not show FPS. RTSS is optional. |
| **Permissions** | Administrator, to read the sensors. The setup takes care of it. |
| **Languages** | Portuguese, English, Spanish and Chinese. |

Versions are numbered 1.x.y: a new middle number (1.5.0) is a big change, each 1.x.y is an update with
features and fixes. Only the latest version receives fixes, and Tela! updates itself from the window.

## Privacy

Everything stays on your PC. Tela! only goes online to ping the servers you configure (for the network
panel) and to ask GitHub whether there is a new version (can be turned off in *Advanced › Updates*); the
setup downloads PawnIO and WebView2 from their official sources when they are missing.

## Code signing policy

The setup is not code-signed yet, so Windows may show a warning when you download or open it. We applied
for free code signing for open-source projects from [SignPath.io](https://signpath.io), with a certificate
by the [SignPath Foundation](https://signpath.org); this section will say so when it is in place.

- Every release is built from this repository by GitHub Actions (`.github/workflows/release.yml`); nothing
  is built on a personal PC.
- Committers and reviewers: [Fekaziroh](https://github.com/Fekaziroh). Approver of each signed release:
  [Fekaziroh](https://github.com/Fekaziroh).
- Privacy: see [Privacy](#privacy). Tela! sends no data about you anywhere.

## Building

Every push builds the setup on GitHub Actions (`.github/workflows/release.yml`). When the version in
`engine.py` has no release yet, the workflow publishes one with the notes from `ui/changelog.js`. To build on a Windows PC: install Python 3.13 and Inno Setup 6, then run
`powershell -ExecutionPolicy Bypass -File build.ps1`. Tests: `python tests/run_tests.py`.

Without the setup, `python app.py` runs Tela! from the source folder (`--demo` uses fake data,
`--simulate` draws to `preview.png` instead of the screen).

## Acknowledgements

The screen protocol is based on the work of
[turing-smart-screen-python](https://github.com/mathoudebine/turing-smart-screen-python) by mathoudebine,
another open-source project for these screens (no code from it is included). Sensors come from
[LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) and FPS from
[PresentMon](https://github.com/GameTechDev/PresentMon); see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

## License

MIT. See [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) for the projects Tela! uses.
