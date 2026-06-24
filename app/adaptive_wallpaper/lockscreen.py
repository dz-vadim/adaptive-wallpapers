"""Встановлення зображення екрана блокування (best-effort, кросплатформно).

Повертає True (успіх), False (спроба була, але не вдалось) або None
(платформа/середовище не підтримує — мовчки пропускаємо, бо «якщо можливо»).

- KDE Plasma: пишемо kscreenlockerrc (плагін org.kde.image) — надійно.
- GNOME: org.gnome.desktop.screensaver picture-uri — best-effort (на нових
  версіях GNOME екран блокування може ігнорувати це).
- Windows: WinRT LockScreen.SetImageFileAsync (потрібен пакет `winsdk`).
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


# ---------------- KDE ----------------
def _kwriteconfig() -> str | None:
    for exe in ("kwriteconfig6", "kwriteconfig5"):
        if shutil.which(exe):
            return exe
    return None


def _set_kde(path: Path) -> bool | None:
    kw = _kwriteconfig()
    if not kw:
        return None
    p = str(path.resolve())
    ok = _run([kw, "--file", "kscreenlockerrc",
               "--group", "Greeter", "--key", "WallpaperPlugin", "org.kde.image"])
    ok = _run([kw, "--file", "kscreenlockerrc",
               "--group", "Greeter", "--group", "Wallpaper",
               "--group", "org.kde.image", "--group", "General",
               "--key", "Image", p]) and ok
    return ok


# ---------------- GNOME ----------------
def _set_gnome(path: Path) -> bool | None:
    if not shutil.which("gsettings"):
        return None
    uri = path.resolve().as_uri()
    return _run(["gsettings", "set", "org.gnome.desktop.screensaver",
                 "picture-uri", uri])


def _desktop() -> str:
    return (os.environ.get("XDG_CURRENT_DESKTOP", "") + ":" +
            os.environ.get("XDG_SESSION_DESKTOP", "") + ":" +
            os.environ.get("DESKTOP_SESSION", "")).lower()


def _set_linux(path: Path) -> bool | None:
    de = _desktop()
    if "kde" in de or "plasma" in de:
        r = _set_kde(path)
        return r if r is not None else _set_gnome(path)
    if "gnome" in de or "unity" in de or "cinnamon" in de or "budgie" in de:
        return _set_gnome(path)
    # невідоме DE: спробуємо KDE, потім GNOME
    r = _set_kde(path)
    return r if r else _set_gnome(path)


# ---------------- Windows ----------------
def _set_windows(path: Path) -> bool | None:
    try:
        import asyncio

        from winsdk.windows.storage import StorageFile
        from winsdk.windows.system.userprofile import LockScreen
    except Exception:
        return None  # без winsdk — не підтримуємо

    async def _go():
        f = await StorageFile.get_file_from_path_async(str(path.resolve()))
        await LockScreen.set_image_file_async(f)

    try:
        asyncio.run(_go())
        return True
    except Exception:
        return False


def set_lockscreen(path: Path) -> bool | None:
    path = Path(path)
    if not path.exists():
        return False
    if sys.platform.startswith("linux"):
        return _set_linux(path)
    if sys.platform == "win32":
        return _set_windows(path)
    return None  # macOS: окремого API для екрана блокування немає
