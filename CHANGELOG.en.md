# Changelog

All notable changes to Gamma are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0] — 2026-10-11

First public release.

### Added
- 12 built-in color temperature presets (1900K–7500K + special modes)
- Custom user presets with descriptions and hover tooltips
- Tkinter GUI: monitor selector, RGB gamma sliders, live gradient preview
- CLI: apply by name/ID, list monitors, cyclic preset switching, `--restore` for autostart
- Per-monitor configuration — independent gamma and brightness for each display
- Settings automatically restored at session start (`autostart-enable.sh`)
- Localization: Russian and English
- `install.sh` / `uninstall.sh` / `Makefile` installation paths and `.desktop` entry
- Logging to `gamma.log` for troubleshooting

### Requirements
- Python 3.10+
- X11 session with `xrandr` (Wayland is not supported)
