# Windows setup

The adaptive wallpaper script works on Windows 10/11. It picks a PNG from the
`wallpapers/` folder based on season, time of day and weather, then sets it as
the desktop wallpaper via the Win32 API.

## Requirements

- **Python 3** (3.10+). Install from <https://www.python.org/downloads/> and
  tick *"Add Python to PATH"* during setup.
- **No extra dependencies** are needed just to *set* the wallpaper — the script
  uses only the standard library plus the project's `scripts/scenes.py`.
  - `google-genai` is **not** required for setting wallpaper; it's only needed
    for *generating* images.
  - `pip install pillow` is only needed if you also run image-generation/editing
    tooling — skip it otherwise.

## Option 1 — prebuilt exe (no Python needed)

Grab **adaptive-wallpaper-windows.zip** from the
[Releases](https://github.com/dz-vadim/adaptive-wallpapers/releases) page and
extract it anywhere. You get `adaptive-wallpaper.exe` next to a `wallpapers/`
folder (the exe looks for `wallpapers/` beside itself).

```bat
adaptive-wallpaper.exe
adaptive-wallpaper.exe --dry-run
```

Schedule it (no Python required):

```bat
schtasks /create /sc minute /mo 15 /tn AdaptiveWallpaper /tr "C:\path\to\adaptive-wallpaper.exe"
```

> The exe is built with Nuitka (no UPX) but **unsigned**, so SmartScreen or an
> antivirus may warn on first run — choose *More info → Run anyway*. A signed
> build would remove this; it needs a code-signing certificate.

## Option 2 — run the Python script

The `WALLPAPERS` path in the script is relative to the repo, so run it from the
repository root:

```bat
cd <repo>
python scripts\set_wallpaper.py
```

Useful flags (unchanged across platforms):

```bat
python scripts\set_wallpaper.py --dry-run
python scripts\set_wallpaper.py --weather cloudy --time evening
python scripts\set_wallpaper.py --location Kyiv
```

## Schedule it every 15 minutes (Task Scheduler)

Use `pythonw` (not `python`) so no console window pops up each run. Create the
task with `schtasks`:

```bat
schtasks /create /sc minute /mo 15 /tn AdaptiveWallpaper /tr "pythonw <repo>\scripts\set_wallpaper.py"
```

Replace `<repo>` with the absolute path to the cloned repository, e.g.
`C:\Users\you\wallpapers_archive`. The full command would look like:

```bat
schtasks /create /sc minute /mo 15 /tn AdaptiveWallpaper /tr "pythonw C:\Users\you\wallpapers_archive\scripts\set_wallpaper.py"
```

To remove the task later:

```bat
schtasks /delete /tn AdaptiveWallpaper /f
```

## Caveat

There is **no smooth crossfade** on Windows. The KDE Plasma plugin provides a
fade transition on Linux; on Windows the wallpaper change is **instant**.
