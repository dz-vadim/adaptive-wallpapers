# Building the desktop app

The app is a normal Python/PyQt6 package; you can run it from source or compile
a single self-contained binary. CI builds Linux and Windows binaries on every
`v*` tag (see [.github/workflows/release.yml](../.github/workflows/release.yml));
the steps below are the same thing locally.

## Run from source

```bash
cd app
python -m pip install PyQt6
python -m adaptive_wallpaper          # tray app
python -m adaptive_wallpaper --once   # set once and exit
```

## Build a binary (Nuitka)

[Nuitka](https://nuitka.net/) compiles Python to C — the result is a real
native binary, which triggers fewer antivirus false positives than
self-extracting bundlers. No UPX (it's an AV trigger too).

```bash
cd app
python -m pip install nuitka PyQt6

# Linux — onefile binary
python -m nuitka --onefile --assume-yes-for-downloads \
  --enable-plugin=pyqt6 --include-package-data=adaptive_wallpaper \
  --linux-icon=adaptive_wallpaper/assets/adaptive-wallpaper.png \
  --output-dir=../dist --output-filename=adaptive-wallpaper run.py
```

On Linux you need `patchelf` (Nuitka can download it with
`--assume-yes-for-downloads`) and the runtime needs `libxcb-cursor0`.

### Windows — standalone + installer

On Windows the release uses a Nuitka **standalone** folder (not onefile — a
self-extracting onefile triggers more antivirus false positives) wrapped in an
**Inno Setup** installer:

```powershell
cd app
python -m nuitka --standalone --assume-yes-for-downloads `
  --enable-plugin=pyqt6 --include-package-data=adaptive_wallpaper `
  --windows-icon-from-ico=adaptive_wallpaper/assets/adaptive-wallpaper.ico `
  --windows-console-mode=disable `
  --output-dir=../dist --output-filename=adaptive-wallpaper.exe run.py

# then compile the installer (Inno Setup 6)
iscc /DMyAppVersion=1.3.1 ..\windows\installer.iss   # → dist\adaptive-wallpaper-setup.exe
```

`--include-package-data` bundles the icon assets; the binary doesn't embed the
48 PNGs — the installer copies a `wallpapers/` folder next to the exe (the app
auto-detects it).

## Build with PyInstaller (alternative)

```bash
cd app
python -m pip install pyinstaller PyQt6
pyinstaller --onefile --windowed --name adaptive-wallpaper run.py
```

PyInstaller is faster to build but more prone to AV false positives than Nuitka.
