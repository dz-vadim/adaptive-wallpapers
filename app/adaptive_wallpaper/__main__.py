"""Точка входу.

  adaptive-wallpaper            # трей-застосунок (фонова зміна)
  adaptive-wallpaper --once     # поставити одну шпалеру й вийти (для планувальника)
  adaptive-wallpaper --install  # розпакувати зображення + автозапуск + дефолт-конфіг
  adaptive-wallpaper --uninstall
"""
from __future__ import annotations

import argparse
import sys

from . import __app_name__, __version__, engine, installer, paths
from . import config as cfg
from . import wallpaper as wp


def _once(args) -> int:
    conf = cfg.load()
    folder = paths.find_wallpapers(args.folder or conf.get("folder", ""))
    if not folder:
        print("❌ Не знайдено теки зі шпалерами. Вкажіть --folder або --install.")
        return 1
    path, name, info = engine.choose(
        folder,
        season=args.season or conf.get("season", "auto"),
        time=args.time or conf.get("time", "auto"),
        weather=args.weather or conf.get("weather", "auto"),
        location=args.location or conf.get("location", ""))
    tag = "online" if info.get("online") else "offline-guess"
    print(f"🕒 {name}  [{tag}] → {path.name if path else '—'}")
    if path is None:
        return 1
    if args.dry_run:
        print(f"[dry-run] поставив би: {path.name}")
        return 0
    if wp.set_wallpaper(path):
        print(f"🖼️ Встановлено: {path.name}")
        return 0
    print("❌ Не вдалось встановити шпалеру на цьому робочому столі.")
    return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="adaptive-wallpaper", description=__app_name__)
    ap.add_argument("--version", action="version",
                    version=f"{__app_name__} {__version__}")
    ap.add_argument("--once", action="store_true",
                    help="поставити одну шпалеру й вийти (для планувальника)")
    ap.add_argument("--dry-run", action="store_true", help="лише показати вибір")
    ap.add_argument("--install", action="store_true",
                    help="розпакувати зображення, автозапуск, дефолтний конфіг")
    ap.add_argument("--no-autostart", action="store_true",
                    help="з --install: не додавати в автозапуск")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--folder", default="", help="тека зі шпалерами")
    ap.add_argument("--location", default="", help="місто для wttr.in")
    ap.add_argument("--season", choices=engine.SEASONS)
    ap.add_argument("--time", choices=engine.TIMES)
    ap.add_argument("--weather", choices=engine.WEATHERS)
    args = ap.parse_args(argv)

    if args.uninstall:
        installer.uninstall()
        print("✅ Автозапуск вимкнено.")
        return 0
    if args.install:
        rep = installer.install(copy_images=True, autostart=not args.no_autostart)
        print(f"✅ Зображення: {rep['wallpapers']}")
        print(f"✅ Конфіг: {rep['config']}")
        print(f"✅ Автозапуск: {'увімкнено' if rep['autostart'] else 'ні'}")
        return _once(args)
    if args.once or args.dry_run:
        return _once(args)

    # за замовчуванням — GUI-трей
    try:
        from .app import run_gui
    except ImportError as e:
        print(f"❌ GUI недоступний ({e}). Спробуйте --once для разового запуску.")
        return 2
    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
