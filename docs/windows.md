# Windows setup

On Windows 10/11 the recommended way is the **GUI app** — a system-tray program
that picks a wallpaper from the `wallpapers/` folder by season, time of day and
weather and sets it via the Win32 API. Install it from the `setup.exe` below;
running the raw Python scripts is only for development.

## Option 1 — installer (recommended, no Python needed)

Grab **adaptive-wallpaper-setup.exe** from the
[Releases](https://github.com/dz-vadim/adaptive-wallpapers/releases) page and run
it. The installer (Inno Setup, per-user, **no admin**) sets up the GUI tray app,
shortcuts, an optional *Run at login* task, and unpacks all 48 wallpapers next to
the program. Launch it and a coffee-cup icon appears in the system tray.

Prefer no install? Take **adaptive-wallpaper-windows-portable.zip** — a folder
with `adaptive-wallpaper.exe` next to `wallpapers/`; just run the exe.

> Builds are **unsigned**, so SmartScreen may warn on first run — choose
> *More info → Run anyway*. The app ships as a Nuitka **standalone** folder
> wrapped in an installer (not a self-extracting onefile), which causes far
> fewer antivirus false positives. The only full fix is a code-signing
> certificate.

The lock-screen option works on Windows too (via the built-in WinRT API through
PowerShell — no extra dependency).

**Updating:** just run a newer `adaptive-wallpaper-setup.exe` — it upgrades the
existing install in place (closing the app first if it's running). **Uninstall:**
via *Settings → Apps* or the Start-menu uninstaller; it removes the program,
shortcuts, the autostart entry and the per-user config/wallpapers it created.

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
