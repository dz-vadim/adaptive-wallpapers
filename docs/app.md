# Adaptive Coffee Wallpaper — desktop app

A small cross-platform tray app that sets your desktop wallpaper by **season ×
time of day × weather**, picking from the 48 generated frames. It works
**without** the KDE Plasma plugin, so it's the way to go on GNOME, XFCE,
Cinnamon, MATE, Windows and macOS.

The KDE Plasma plugin (in `plasma-plugin/`) still exists and is the nicest
option on Plasma — this app is the portable alternative / Windows build.

## Get it

- **Prebuilt binary** — download from the
  [Releases](https://github.com/dz-vadim/adaptive-wallpapers/releases) page:
  - `adaptive-wallpaper-windows.zip` or `adaptive-wallpaper-linux.tar.gz`
    contain the app **plus all 48 wallpapers**. Unpack anywhere and run the
    binary.
  - The bare `adaptive-wallpaper(.exe)` is the app only — point it at a
    wallpapers folder (Settings → Browse, or `--folder`), or drop a
    `wallpapers/` folder next to it.
- **Build it yourself** — see [build.md](build.md).
- **Run from source** — `pip install PyQt6 && python -m adaptive_wallpaper`
  from the `app/` directory.

The binaries are **unsigned**, so SmartScreen / antivirus may warn on first
run — choose *More info → Run anyway*.

## Use it

Launch the binary: a coffee-cup icon appears in the system tray. Left-click
(or right-click → Settings…) opens the settings window. The app updates the
wallpaper on a timer and at login if you enable autostart.

Tray menu:

- **Update now** — re-pick and set immediately.
- **Settings…** — mode, folder, location, interval, manual overrides, preview.
- **Run at login** — add/remove from autostart.
- **Copy wallpapers to system…** — copy the bundled frames into your user data
  folder and point the config at it (so you can move/delete the unpacked zip).
- **Quit**.

### Modes

- **Adaptive** — season from the date, time of day from the real sun
  (sunrise/sunset via wttr.in; falls back to clock), weather from wttr.in.
  Offline → a sensible random weather. Any of season/time/weather can be pinned
  to a fixed value in Settings.
- **Carousel** — cycle through all frames on a fixed interval.

### Paths are automatic

The wallpapers folder is discovered in this order: the folder set in Settings →
`ADAPTIVE_WALLPAPER_DIR` env var → next to the binary → the installed data
folder → the repository layout. Config lives in the OS config dir
(`~/.config/adaptive-wallpaper` on Linux, `%APPDATA%\AdaptiveWallpaper` on
Windows).

## Command line

Handy for schedulers or headless setups:

```bash
adaptive-wallpaper --once                 # set one wallpaper and exit
adaptive-wallpaper --once --dry-run        # show the pick, change nothing
adaptive-wallpaper --once --weather cloudy --time evening
adaptive-wallpaper --install               # copy images + autostart + default config
adaptive-wallpaper --install --no-autostart
adaptive-wallpaper --uninstall             # remove autostart
adaptive-wallpaper --folder /path/to/wallpapers
```

## Credits

The 48 wallpapers are generated from an original reference artwork by
**mb0sco** and **steezyasfuck** — credit to them for the source art that
defined the composition, style and mood. The generated frames are derivative
works of that piece.
