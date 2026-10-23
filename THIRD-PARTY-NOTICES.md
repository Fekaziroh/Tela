# Third-party software

Tela! ships with, or is built from, the following projects. Each keeps its own license.

| Project | Used for | License | Source |
|---|---|---|---|
| LibreHardwareMonitorLib | hardware sensors (shipped in `lhm\`, unmodified) | MPL-2.0 | https://github.com/LibreHardwareMonitor/LibreHardwareMonitor |
| PresentMon | FPS and frame times (shipped in `presentmon\`, unmodified) | MIT | https://github.com/GameTechDev/PresentMon |
| PawnIO | driver for CPU/motherboard sensors (downloaded by the setup from its official release, only when missing) | see project | https://github.com/namazso/PawnIO.Setup |
| Microsoft Edge WebView2 Runtime | draws the window (downloaded from Microsoft, only when missing) | Microsoft | https://developer.microsoft.com/microsoft-edge/webview2/ |
| Python | runtime bundled in `_internal\` | PSF-2.0 | https://www.python.org |
| pythonnet, clr_loader | .NET from Python | MIT | https://github.com/pythonnet/pythonnet |
| pywebview | window | BSD-3-Clause | https://github.com/r0x0r/pywebview |
| Pillow | drawing | MIT-CMU | https://github.com/python-pillow/Pillow |
| NumPy | image comparison | BSD-3-Clause | https://github.com/numpy/numpy |
| pyserial | screen connection | BSD-3-Clause | https://github.com/pyserial/pyserial |
| psutil | system counters | BSD-3-Clause | https://github.com/giampaolo/psutil |
| PyYAML | settings files | MIT | https://github.com/yaml/pyyaml |
| pystray | tray icon | LGPL-3.0 | https://github.com/moses-palmer/pystray |
| pywinrt | Windows media controls | MIT | https://github.com/pywinrt/pywinrt |
| bottle, proxy_tools, typing_extensions | pywebview dependencies | MIT / BSD / PSF | https://pypi.org |

The screen protocol is based on turing-smart-screen-python by mathoudebine (GPL-3.0); no code from it is
included: https://github.com/mathoudebine/turing-smart-screen-python

Brand names shown on the screen are trademarks of their owners. Tela! ships no brand logos.
