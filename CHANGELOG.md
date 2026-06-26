# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project follows
[Semantic Versioning](https://semver.org/).

## [1.3.3]

### Added
- **In-app updates** — an unobtrusive check against GitHub Releases; when a newer
  version exists you get a one-time tray notification and an *Update to vX.Y.Z…*
  item in the menu. One click downloads and installs it (Windows runs the
  `setup.exe`; the Linux binary replaces itself and restarts; from source it
  opens the releases page). Toggle in Settings → *Check for updates*.

## [1.3.2]

### Added
- **About** dialog (tray menu) with version, links, artwork credits, license and
  runtime info.
- File logging to the config dir (`app.log`) for diagnosing silent failures.

### Changed
- Setting the wallpaper and the lock screen now runs off the GUI thread — the
  tray/settings window no longer freezes during `plasma-apply` / `gsettings` /
  PowerShell calls.
- Weather is cached (~25 min) so short update intervals don't hit wttr.in rate
  limits; the lock screen is no longer re-written when the target is unchanged.
- Release CI derives the version from the git tag (no more version drift) and
  smoke-tests the built binary; `pyproject.toml` gains classifiers/URLs.

### Fixed
- macOS wallpaper AppleScript now escapes quotes in the path.
- Linux autostart entry always gets the app icon; glyph icons aren't rewritten
  on every theme change.

## [1.3.1]

### Added
- Theme selector **Auto / Dark / Light**; reference night-blue dark palette.
- Two-column settings layout; dropdown chevrons and checkbox checkmarks.
- English README (`README.en.md`) and a 48-image [GALLERY.md](GALLERY.md).

### Changed
- New neon line-art cup icon matching the reference; identical across all builds.
- Robust **update & uninstall**: Windows installer upgrades in place and closes
  the running app; uninstall removes files, shortcuts, autostart and per-user
  data. Linux `--uninstall` removes the icon/launcher (`--purge` for data too).

### Fixed
- Icon-cache refresh no longer creates an empty `hicolor/index.theme` (which had
  broken icon resolution for other apps).

## [1.3.0]
- Modern themed UI, reactive language switch, single-instance lock, success
  notifications. Windows **setup.exe** (Inno Setup, standalone — fewer AV false
  positives) + portable zip. Windows lock-screen support (WinRT via PowerShell).

## [1.2.0]
- English/Ukrainian UI (i18n) and a custom app icon consistent across builds.

## [1.1.0]
- Cross-platform PyQt6 **tray app** (Linux/GNOME/XFCE/KDE, Windows, macOS) with a
  live preview; CI builds Linux & Windows binaries on every `v*` tag.

## [1.0.0]
- 48 generated wallpapers (season × time × weather) and the KDE Plasma adaptive
  wallpaper plugin.
