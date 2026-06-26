# Contributing

Thanks for your interest! This repo has three parts:

| Part | Path | Stack |
|------|------|-------|
| Desktop app | [`app/`](app/) | Python 3.10+, PyQt6 |
| KDE Plasma plugin | [`plasma-plugin/`](plasma-plugin/) | QML |
| Wallpaper generation | [`scripts/`](scripts/) | Python, Gemini API |

> Note: the GitHub repo is `adaptive-wallpapers` (plural) while the Python
> package / binary / app-id is `adaptive-wallpaper` (singular). That split is
> intentional — don't "fix" it, it would break links and the single-instance key.

## Dev setup (app)

```bash
cd app
python -m pip install PyQt6 ruff
python -m adaptive_wallpaper            # run the tray app
python -m adaptive_wallpaper --once     # set once and exit
```

## Before opening a PR

```bash
ruff check app/ scripts/                # lint (CI runs this)
python -m py_compile app/adaptive_wallpaper/*.py scripts/*.py
```

- Keep the existing style; user-facing strings in the app go through `tr()` in
  [`i18n.py`](app/adaptive_wallpaper/i18n.py) (add both EN source and the UA
  translation).
- The app icon lives in [`assets/`](app/adaptive_wallpaper/assets/); PNG/ICO are
  generated from the SVG.

## Building binaries

See [docs/build.md](docs/build.md) (Nuitka standalone + Inno Setup on Windows).

## Releasing

CI builds and publishes binaries on a version tag. The build derives the version
from the tag, so just bump [`CHANGELOG.md`](CHANGELOG.md) and push:

```bash
git tag vX.Y.Z && git push origin vX.Y.Z
```
