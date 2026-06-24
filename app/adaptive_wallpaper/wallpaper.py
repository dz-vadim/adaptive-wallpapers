"""Кросплатформне встановлення шпалери робочого столу.

Linux: визначає середовище (KDE/GNOME/Cinnamon/MATE/XFCE/…) і застосовує
відповідний механізм; як крайній фолбек — feh. Windows: SystemParametersInfoW.
macOS: osascript. Усі функції повертають bool успіху й не кидають винятків.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> bool:
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


# ---------------- Windows ----------------
def _set_windows(path: Path) -> bool:
    import ctypes
    SPI_SETDESKWALLPAPER = 20
    SPIF_UPDATE_SENDCHANGE = 3  # UPDATEINIFILE | SENDWININICHANGE
    try:
        ok = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, str(path.resolve()), SPIF_UPDATE_SENDCHANGE)
        return bool(ok)
    except Exception:
        return False


# ---------------- macOS ----------------
def _set_macos(path: Path) -> bool:
    script = (f'tell application "System Events" to set picture of every '
              f'desktop to POSIX file "{path.resolve()}"')
    return _run(["osascript", "-e", script])


# ---------------- Linux ----------------
def _desktop() -> str:
    env = (os.environ.get("XDG_CURRENT_DESKTOP", "") + ":" +
           os.environ.get("XDG_SESSION_DESKTOP", "") + ":" +
           os.environ.get("DESKTOP_SESSION", "")).lower()
    return env


def _set_kde(path: Path) -> bool:
    return _run(["plasma-apply-wallpaperimage", str(path)])


def _set_gnome(path: Path) -> bool:
    uri = path.resolve().as_uri()
    ok = False
    for key in ("picture-uri", "picture-uri-dark"):
        ok = _run(["gsettings", "set", "org.gnome.desktop.background", key, uri]) or ok
    return ok


def _set_cinnamon(path: Path) -> bool:
    uri = path.resolve().as_uri()
    return _run(["gsettings", "set", "org.cinnamon.desktop.background",
                 "picture-uri", uri])


def _set_mate(path: Path) -> bool:
    return _run(["gsettings", "set", "org.mate.background",
                 "picture-filename", str(path.resolve())])


def _set_xfce(path: Path) -> bool:
    """XFCE: пройтись усіма властивостями last-image у backdrop."""
    p = str(path.resolve())
    try:
        listing = subprocess.run(
            ["xfconf-query", "-c", "xfce4-desktop", "-l"],
            check=True, capture_output=True, text=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    props = [ln.strip() for ln in listing.splitlines()
             if ln.strip().endswith("last-image")]
    ok = False
    for prop in props or ["/backdrop/screen0/monitor0/workspace0/last-image"]:
        ok = _run(["xfconf-query", "-c", "xfce4-desktop", "-p", prop,
                   "-s", p]) or ok
    return ok


def _set_feh(path: Path) -> bool:
    if shutil.which("feh"):
        return _run(["feh", "--bg-fill", str(path.resolve())])
    return False


def _set_linux(path: Path) -> bool:
    de = _desktop()
    # порядок: спершу те, що відповідає поточному DE, потім універсальні спроби
    order = []
    if "kde" in de or "plasma" in de:
        order = [_set_kde, _set_gnome, _set_feh]
    elif "gnome" in de or "unity" in de or "budgie" in de:
        order = [_set_gnome, _set_feh]
    elif "cinnamon" in de:
        order = [_set_cinnamon, _set_gnome, _set_feh]
    elif "mate" in de:
        order = [_set_mate, _set_feh]
    elif "xfce" in de:
        order = [_set_xfce, _set_feh]
    elif "lxqt" in de or "lxde" in de or "openbox" in de or "i3" in de:
        order = [_set_feh]
    else:
        # невідоме DE — пробуємо все по черзі
        order = [_set_kde, _set_gnome, _set_cinnamon, _set_mate, _set_xfce, _set_feh]
    return any(fn(path) for fn in order)


def set_wallpaper(path: Path) -> bool:
    """Встановити шпалеру для поточної платформи. True — успіх."""
    path = Path(path)
    if not path.exists():
        return False
    if sys.platform.startswith("linux"):
        return _set_linux(path)
    if sys.platform == "win32":
        return _set_windows(path)
    if sys.platform == "darwin":
        return _set_macos(path)
    return False
