# Adaptive Coffee Wallpaper — desktop app

Cross-platform tray app (PyQt6) that sets the desktop wallpaper by
**season × time of day × weather**, picking from the 48 generated frames.
The portable alternative to the KDE Plasma plugin — works on GNOME, XFCE,
Cinnamon, MATE, Windows and macOS.

```
adaptive_wallpaper/
├── engine.py          # season/time/weather → file (self-contained, mirrors scenes.py)
├── wallpaper.py       # cross-platform setters (KDE/GNOME/Cinnamon/MATE/XFCE/Win/macOS)
├── lockscreen.py      # lock-screen image + backup/restore (KDE/GNOME/Windows)
├── paths.py           # auto-detect wallpapers / config / data dirs
├── config.py          # JSON config in the OS config dir
├── installer.py       # copy images + icon + default config + autostart
├── i18n.py            # English / Ukrainian strings (tr())
├── icon.py            # custom app icon (same in every build)
├── style.py           # dark "coffee" theme (palette + QSS)
├── single_instance.py # one instance per user (QLocalServer)
├── settings_dialog.py # PyQt6 settings window (themed, reactive, live preview)
├── app.py             # tray icon, background timer, controller
├── __main__.py        # CLI / entry point
└── assets/            # adaptive-wallpaper.svg / .png / .ico
run.py                 # single entry script for Nuitka/PyInstaller
windows/installer.iss  # Inno Setup script → setup.exe
```

- **Usage & install:** [../docs/app.md](../docs/app.md)
- **Building binaries:** [../docs/build.md](../docs/build.md)

Quick start from source:

```bash
pip install PyQt6
python -m adaptive_wallpaper          # tray app
python -m adaptive_wallpaper --once   # set once and exit (for schedulers)
```
