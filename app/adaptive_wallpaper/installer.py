"""Інсталятор: розпаковує зображення в системну теку, пише дефолтний конфіг
і налаштовує автозапуск. Кросплатформно (Linux .desktop, Windows реєстр,
macOS LaunchAgent). Усе — у профіль користувача, без прав адміністратора.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from . import __app_id__, __app_name__, paths
from . import config as cfg
from .icon import ICON_NAME, png_path, svg_path


def _launch_command() -> list[str]:
    """Команда, якою стартувати застосунок (для автозапуску)."""
    if paths.is_frozen():
        return [str(Path(sys.argv[0]).resolve())]
    return [sys.executable, "-m", "adaptive_wallpaper"]


def _desktop_entry(autostart: bool) -> str:
    cmd = " ".join(_launch_command())
    extra = "X-GNOME-Autostart-enabled=true\n" if autostart else ""
    return ("[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={__app_name__}\n"
            f"Exec={cmd}\n"
            f"Icon={ICON_NAME}\n"
            f"StartupWMClass={ICON_NAME}\n"
            "Categories=Utility;\n"
            "Terminal=false\n" + extra)


def install_icon_linux() -> bool:
    """Покласти кастомну іконку в тему користувача (для Wayland/трея/.desktop).
    Ставимо і PNG (256x256), і SVG (scalable) під однією назвою, та оновлюємо
    кеш іконок — інакше панель/пуск показують стару закешовану іконку."""
    base = Path.home() / ".local" / "share" / "icons" / "hicolor"
    ok = False
    for src, sub, ext in ((png_path(), "256x256", "png"),
                          (svg_path(), "scalable", "svg")):
        if src.exists():
            dest = base / sub / "apps" / f"{ICON_NAME}.{ext}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            ok = True
    _refresh_icon_cache(base)
    return ok


def _refresh_icon_cache(hicolor: Path) -> None:
    """Best-effort оновлення кешу іконок (різні DE — різні утиліти).
    Plasma тримає окремий icon-cache.kcache — без його скидання панель/пуск
    показують стару закешовану іконку."""
    import subprocess
    # оновити mtime теми, щоб кеші помітили зміну
    try:
        (hicolor / "index.theme").touch(exist_ok=True)
    except OSError:
        pass
    # прибрати кеш іконок Plasma
    cache = Path.home() / ".cache"
    for name in ("icon-cache.kcache",):
        (cache / name).unlink(missing_ok=True)
    for cmd in (["gtk-update-icon-cache", "-f", "-t", str(hicolor)],
                ["kbuildsycoca6", "--noincremental"],
                ["kbuildsycoca5", "--noincremental"],
                ["xdg-desktop-menu", "forceupdate"]):
        try:
            subprocess.run(cmd, check=False, capture_output=True, timeout=30)
        except (FileNotFoundError, OSError, subprocess.SubprocessError):
            pass


def install_launcher_linux() -> bool:
    """Створити пункт у меню застосунків (для прив'язки іконки під Wayland)."""
    d = Path.home() / ".local" / "share" / "applications"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{__app_id__}.desktop").write_text(_desktop_entry(autostart=False),
                                             encoding="utf-8")
    return True


# ---------------- автозапуск ----------------
def _autostart_linux(enable: bool) -> bool:
    d = Path.home() / ".config" / "autostart"
    f = d / f"{__app_id__}.desktop"
    if not enable:
        f.unlink(missing_ok=True)
        return True
    d.mkdir(parents=True, exist_ok=True)
    f.write_text(_desktop_entry(autostart=True), encoding="utf-8")
    return True


def _autostart_windows(enable: bool) -> bool:
    import winreg
    run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    name = "AdaptiveWallpaper"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0,
                            winreg.KEY_SET_VALUE) as k:
            if enable:
                parts = _launch_command()
                val = " ".join(f'"{p}"' if " " in p else p for p in parts)
                winreg.SetValueEx(k, name, 0, winreg.REG_SZ, val)
            else:
                try:
                    winreg.DeleteValue(k, name)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False


def _autostart_macos(enable: bool) -> bool:
    d = Path.home() / "Library" / "LaunchAgents"
    f = d / "com.adaptivewallpaper.agent.plist"
    if not enable:
        f.unlink(missing_ok=True)
        return True
    d.mkdir(parents=True, exist_ok=True)
    args = "".join(f"    <string>{p}</string>\n" for p in _launch_command())
    f.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0"><dict>\n'
        '  <key>Label</key><string>com.adaptivewallpaper.agent</string>\n'
        f'  <key>ProgramArguments</key><array>\n{args}  </array>\n'
        '  <key>RunAtLoad</key><true/>\n'
        '</dict></plist>\n',
        encoding="utf-8")
    return True


def set_autostart(enable: bool) -> bool:
    if sys.platform.startswith("linux"):
        return _autostart_linux(enable)
    if sys.platform == "win32":
        return _autostart_windows(enable)
    if sys.platform == "darwin":
        return _autostart_macos(enable)
    return False


# ---------------- розпакування зображень ----------------
def install_wallpapers(source: Path | None = None) -> Path | None:
    """Скопіювати кадри з bundle у data_dir()/wallpapers. Повертає шлях теки."""
    src = Path(source) if source else paths.find_wallpapers()
    if not src or not src.is_dir():
        return None
    dest = paths.data_dir() / "wallpapers"
    if src.resolve() == dest.resolve():
        return dest
    dest.mkdir(parents=True, exist_ok=True)
    for png in src.glob("[0-9][0-9]_*.png"):
        target = dest / png.name
        if not target.exists() or target.stat().st_size != png.stat().st_size:
            shutil.copy2(png, target)
    return dest


# ---------------- повне встановлення ----------------
def install(*, copy_images: bool = True, autostart: bool = True,
            source: Path | None = None) -> dict:
    """Виконати встановлення з базовими налаштуваннями. Повертає звіт."""
    report: dict = {"wallpapers": None, "config": None, "autostart": False,
                    "icon": False}
    folder = None
    if copy_images:
        folder = install_wallpapers(source)
        report["wallpapers"] = str(folder) if folder else None

    # кастомна іконка + пункт меню (під Wayland вікно бере іконку з .desktop)
    if sys.platform.startswith("linux"):
        report["icon"] = install_icon_linux()
        install_launcher_linux()

    conf = cfg.load()
    if folder:
        conf["folder"] = str(folder)
    conf["autostart"] = bool(autostart)
    cfg.save(conf)
    report["config"] = str(cfg.config_path())

    if autostart:
        report["autostart"] = set_autostart(True)
    return report


def uninstall(*, remove_images: bool = False) -> None:
    set_autostart(False)
    conf = cfg.load()
    conf["autostart"] = False
    cfg.save(conf)
    if remove_images:
        shutil.rmtree(paths.data_dir() / "wallpapers", ignore_errors=True)
