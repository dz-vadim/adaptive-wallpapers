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

# Linux
python -m nuitka --onefile --assume-yes-for-downloads \
  --enable-plugin=pyqt6 \
  --output-dir=../dist --output-filename=adaptive-wallpaper run.py

# Windows (PowerShell) — note --windows-console-mode=disable for a GUI app
python -m nuitka --onefile --assume-yes-for-downloads `
  --enable-plugin=pyqt6 --windows-console-mode=disable `
  --output-dir=../dist --output-filename=adaptive-wallpaper.exe run.py
```

On Linux you need `patchelf` (Nuitka can download it with
`--assume-yes-for-downloads`) and the runtime needs `libxcb-cursor0`.

The binary doesn't embed the 48 PNGs — ship a `wallpapers/` folder next to it,
or let the user pick a folder. The release bundles do both: binary + wallpapers
in one archive.

## Build with PyInstaller (alternative)

```bash
cd app
python -m pip install pyinstaller PyQt6
pyinstaller --onefile --windowed --name adaptive-wallpaper run.py
```

PyInstaller is faster to build but more prone to AV false positives than Nuitka.
