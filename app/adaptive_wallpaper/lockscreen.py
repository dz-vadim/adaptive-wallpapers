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


def _kreadconfig() -> str | None:
    for exe in ("kreadconfig6", "kreadconfig5"):
        if shutil.which(exe):
            return exe
    return None


_KDE_IMG_GROUPS = ("Greeter", "Wallpaper", "org.kde.image", "General")


def _get_kde() -> dict | None:
    """Поточні plugin+image екрана блокування (для бекапу). None — не KDE."""
    kr = _kreadconfig()
    if not kr:
        return None

    def read(groups: tuple[str, ...], key: str) -> str:
        cmd = [kr, "--file", "kscreenlockerrc"]
        for g in groups:
            cmd += ["--group", g]
        cmd += ["--key", key]
        try:
            return subprocess.run(cmd, check=True, capture_output=True,
                                  text=True).stdout.strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            return ""

    return {"plugin": read(("Greeter",), "WallpaperPlugin"),
            "image": read(_KDE_IMG_GROUPS, "Image")}


def _write_kde(groups: tuple[str, ...], key: str, value: str | None) -> bool:
    kw = _kwriteconfig()
    if not kw:
        return False
    cmd = [kw, "--file", "kscreenlockerrc"]
    for g in groups:
        cmd += ["--group", g]
    cmd += ["--key", key]
    cmd += ["--delete"] if value is None else [value]
    return _run(cmd)


def _restore_kde(backup: dict) -> bool | None:
    """Повернути plugin+image з бекапу (порожнє → видалити ключ = дефолт)."""
    if _kwriteconfig() is None:
        return None
    plugin = backup.get("plugin") or None
    image = backup.get("image") or None
    ok = _write_kde(("Greeter",), "WallpaperPlugin", plugin)
    ok = _write_kde(_KDE_IMG_GROUPS, "Image", image) and ok
    return ok


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


# ---------------- бекап/відновлення (режим «keep original») ----------------
def _capture() -> dict | None:
    """Знімок поточного екрана блокування (щоб потім відновити). None —
    платформа не дає надійно прочитати поточне значення."""
    if sys.platform.startswith("linux"):
        de = _desktop()
        if "kde" in de or "plasma" in de:
            return _get_kde()
        if shutil.which("gsettings") and ("gnome" in de or "unity" in de
                                          or "cinnamon" in de or "budgie" in de):
            try:
                v = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.screensaver",
                     "picture-uri"], check=True, capture_output=True,
                    text=True).stdout.strip().strip("'\"")
                return {"gnome_uri": v}
            except (FileNotFoundError, subprocess.CalledProcessError):
                return None
    return None  # Windows/macOS: поточне зображення надійно не прочитати


def _restore(backup: dict) -> bool | None:
    if not backup:
        return None
    if "plugin" in backup or "image" in backup:
        return _restore_kde(backup)
    if "gnome_uri" in backup:
        return _run(["gsettings", "set", "org.gnome.desktop.screensaver",
                     "picture-uri", backup["gnome_uri"]])
    return None


def manage_lock(conf: dict, target: Path | None) -> bool:
    """Застосувати політику екрана блокування. Повертає True, якщо conf
    змінився (бекап захоплено/скинуто) — викликач має зберегти конфіг.

    - mirror/library: один раз запам'ятати оригінал, далі ставити target.
    - skip («keep original»): якщо програма керувала — відновити оригінал.
    """
    mode = conf.get("lock_mode", "skip")
    changed = False
    if mode in ("mirror", "library"):
        if not conf.get("lock_backup"):
            cap = _capture()
            if cap is not None:
                conf["lock_backup"] = cap
                changed = True
        if target and Path(target).exists():
            set_lockscreen(Path(target))
    else:  # skip = зберегти/відновити той, що був до програми
        if conf.get("lock_backup"):
            _restore(conf["lock_backup"])
            conf["lock_backup"] = None
            changed = True
    return changed
