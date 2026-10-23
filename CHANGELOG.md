# Changelog

Every version of Tela!, newest first. Portuguese notes are in the app (Advanced › Patch notes).

## Tela! 1.4.2

### New

- Presets in Settings: Performance (less CPU and memory), Default and Custom, which is selected by itself when you change one of these options.
- Profiles: save the settings and layouts under a name, switch between them and export or import them to take to another PC.
- New version notice in the tray icon too, with an option to update from its menu.
- Tela! tells you when the connected screen is a model that is not supported yet.

### Fixes

- The automatic theme used graphite instead of black with Windows in dark mode.
- The tray icon (logo, CPU or GPU) only changed after restarting the app.

### Performance

- Drawing quality (high or normal) and the live preview in the window can be turned down to save CPU.

### Appearance and personalization

- The window title bar follows the theme (theme color on Windows 11; light or dark on Windows 10).
- Night brightness with the percentage next to the slider.
- The history keeps the last 15 games by default and asks before deleting when you lower the number.
- Patch notes split into categories.

## Tela! 1.4.1

### New

- Game history: every game summary is saved, with search, FPS graph, an option to show it on the screen again, delete and export to CSV. You choose how many to keep and the folder.
- Updates from the app: Tela! tells you when a new version is out and installs it with one click.
- Notes for every version in Advanced and a summary of what changed after each update.
- Custom screen color theme, separate from the ready-made ones.

### Fixes

- The background picture sometimes stayed on the screen after removing it.
- The screen could lose its connection during a transition.
- The FPS meter recovers by itself when it stops responding and shows why when it cannot start.
- The setup showed error 740 when opening Tela! at the end.

### Performance

- The window uses much less memory.

### Appearance and personalization

- Media hides 5 s after pausing, with a transition. While a game is open, even minimized, it stays on the right.
- Block transition also when leaving the game summary.
- The default dark window theme is now Black. Tidier Home and Settings.

## Tela! 1.4.0

### New

- New window, in Portuguese, English, Spanish and Chinese.
- Layout editor: drag, resize, turn blocks on and off, rename and pick sensors from a live list.
- Portrait screen as well as landscape, and both flipped.
- A real installer: no Python needed, downloads PawnIO and WebView2 only when missing and keeps the settings in %APPDATA%\Tela.
- First-run assistant that brings the settings from older versions.

### Appearance and personalization

- Window themes (automatic, ready-made or your own colors), screen color themes and background picture.

## Tela! 1.3.9

### New

- First setup (Setup.exe) built on GitHub.

### Fixes

- Automatic error recovery and an activity log that keeps itself tidy.

### Performance

- Lighter screen drawing.

## Tela! 1.3.8

### New

- Automatic hardware detection: CPU, GPU, RAM, VRAM and disk names with letters.
- Music and video playing at the top of the screen (Spotify, YouTube and others).
- Screen port choice, brightness and last summary from the tray icon.

### Fixes

- The screen reconnects by itself after sleep. The installer checks Windows, .NET and PawnIO.

## Tela! 1.3.7

### New

- Network with ping, packet loss and outage warning, saying whether the router answers.
- Night brightness. The screen turns off when the PC locks or the monitor sleeps.

### Fixes

- The installer keeps your settings.
- Switching apps with a game open no longer loses the session; each game has its own.

### Appearance and personalization

- Cascade transition between the panel and the summary. Screen background color.

## Tela! 1.3.6

### New

- Game summary when the game closes, with adjustable time and a "Preview" button.
- 1% low next to the frame time and the game's max temperature in the gauges.

## Tela! 1.3.5

### New

- Adjustable FPS interval and average, updating every 0.2 s.

### Fixes

- Only one Tela! open at a time: it asks before closing the other copy.

## Tela! 1.3.4

### New

- Frame time next to the FPS and Windows volume in its own block.
- Disks show live activity, with the bar showing used space.

### Appearance and personalization

- Screen colors editable in the window.

## Tela! 1.3.3

### New

- FPS through PresentMon, no RTSS or Afterburner needed.
- Uninstall button.

### Performance

- Program in a folder, nothing left in the temp folder.

## Tela! 1.3.2

### New

- Update interval per item, showing the average of the period.
- Option to turn animations on and off.

### Fixes

- The screen goes black when the app closes and when the PC shuts down or restarts.

## Tela! 1.3.1

### Fixes

- The hardware monitor download works again.

### Appearance and personalization

- Version in the window title.

## Tela! 1.3.0

### New

- Embedded hardware monitor, single installer and start through the Task Scheduler.

### Appearance and personalization

- Smooth animations: bars and gauges glide.

## Tela! 1.2.0

### New

- Window with a live preview, tray icon and start with Windows.
- Sensors read directly, without opening LibreHardwareMonitor, and its own executable.

## Tela! 1.1.0

### New

- First version: AIDA64-style sensor panel, running from the console.
