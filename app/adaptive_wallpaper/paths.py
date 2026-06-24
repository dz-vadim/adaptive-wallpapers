"""Автовизначення шляхів: тека зі шпалерами, конфіг, дані застосунку.

Працює і при запуску з репозиторію (dev), і зі встановленого пакета, і з
«замороженого» exe (Nuitka/PyInstaller).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from . import __app_id__

_WINDOWS = sys.platform == "win32"
_MACOS = sys.platform == "darwin"


def _frozen() -> bool:
    return getattr(sys, "frozen", False) or "__compiled__" in globals()


def exe_dir() -> Path:
    """Тека поряд із виконуваним файлом (для bundle: exe + wallpapers/)."""
    if _frozen():
        return Path(sys.argv[0]).resolve().parent
    return Path(sys.executable).resolve().parent


def config_dir() -> Path:
    if _WINDOWS:
        base = os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
        return Path(base) / "AdaptiveWallpaper"
    if _MACOS:
        return Path.home() / "Library" / "Application Support" / "AdaptiveWallpaper"
    base = os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")
    return Path(base) / __app_id__


def data_dir() -> Path:
    """Куди інсталятор кладе зображення."""
    if _WINDOWS:
        base = os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")
        return Path(base) / "AdaptiveWallpaper"
    if _MACOS:
        return Path.home() / "Library" / "Application Support" / "AdaptiveWallpaper"
    base = os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
    return Path(base) / __app_id__


def _has_wallpapers(p: Path) -> bool:
    try:
        return p.is_dir() and any(p.glob("[0-9][0-9]_*.png"))
    except OSError:
        return False


def _candidate_dirs(configured: str = "") -> list[Path]:
    """Порядок пошуку теки зі шпалерами (від найвищого пріоритету)."""
    here = Path(__file__).resolve()
    out: list[Path] = []
    if configured:
        out.append(Path(configured).expanduser())
    env = os.environ.get("ADAPTIVE_WALLPAPER_DIR")
    if env:
        out.append(Path(env).expanduser())
    # поряд з exe / у встановлених даних
    out.append(exe_dir() / "wallpapers")
    out.append(data_dir() / "wallpapers")
    # розкладка репозиторію: app/adaptive_wallpaper/paths.py → <repo>/wallpapers
    out.append(here.parents[2] / "wallpapers")
    # поряд із самим пакетом
    out.append(here.parent / "wallpapers")
    return out


def find_wallpapers(configured: str = "") -> Path | None:
    """Перша наявна тека з кадрами NN_*.png, інакше None."""
    for p in _candidate_dirs(configured):
        if _has_wallpapers(p):
            return p.resolve()
    return None
