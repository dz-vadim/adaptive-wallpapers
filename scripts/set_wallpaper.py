#!/usr/bin/env python3
"""
Ставить шпалеру робочого столу (KDE Plasma) відповідно до поточних
сезону, часу доби й погоди.

Файл обирається як wallpapers/NN_<season>_<time>_<weather>.png.

Запуск (з кореня проєкту):
    .venv/bin/python scripts/set_wallpaper.py            # авто: сезон+час+погода
    .venv/bin/python scripts/set_wallpaper.py --dry-run  # лише показати вибір
    .venv/bin/python scripts/set_wallpaper.py --weather cloudy --time evening
    .venv/bin/python scripts/set_wallpaper.py --location Kyiv

Погода — wttr.in (без ключа, місто за IP або --location).
"""
import argparse
import datetime as _dt
import json
import random
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scenes import NUMBER, SEASONS, TIMES_OF_DAY, WEATHER, numbered  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WALLPAPERS = ROOT / "wallpapers"

# Місяць → сезон (північна півкуля).
MONTH_SEASON = {12: "winter", 1: "winter", 2: "winter",
                3: "spring", 4: "spring", 5: "spring",
                6: "summer", 7: "summer", 8: "summer",
                9: "autumn", 10: "autumn", 11: "autumn"}

# Година → час доби (межі можна підправити).
def hour_to_time(h: int) -> str:
    if 6 <= h < 11:  return "morning"
    if 11 <= h < 17: return "day"
    if 17 <= h < 21: return "evening"
    return "night"

# wttr.in weatherCode → наша погода. Решта кодів (опади/гроза) → rain_snow.
CLEAR_CODES = {113}
CLOUDY_CODES = {116, 119, 122, 143, 248, 260}


def random_weather() -> str:
    """Офлайн-фолбек: випадкова погода з реалістичним ухилом."""
    r = random.random()
    return "clear" if r < 0.50 else ("cloudy" if r < 0.85 else "rain_snow")


def detect_weather(location: str = "") -> str:
    """Поточна погода через wttr.in → clear|cloudy|rain_snow.
    Без мережі — випадкова погода (бо визначити неможливо)."""
    url = f"https://wttr.in/{location}?format=j1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r)
        code = int(data["current_condition"][0]["weatherCode"])
    except Exception as e:
        w = random_weather()
        print(f"⚠️ Погоду не вдалось отримати ({e}); випадково → {w}.")
        return w
    if code in CLEAR_CODES:
        return "clear"
    if code in CLOUDY_CODES:
        return "cloudy"
    return "rain_snow"


def resolve_file(season: str, time: str, weather: str) -> Path | None:
    """Точний файл або найближчий доступний у межах сезону."""
    exact = WALLPAPERS / f"{numbered(f'{season}_{time}_{weather}')}.png"
    if exact.exists():
        return exact
    # 1) той самий сезон+час, інша погода
    for w in ("clear", "cloudy", "rain_snow"):
        f = WALLPAPERS / f"{numbered(f'{season}_{time}_{w}')}.png"
        if f.exists():
            return f
    # 2) той самий сезон, будь-який час/погода (у порядку нумерації)
    for name in sorted(NUMBER, key=lambda n: NUMBER[n]):
        if name.startswith(season + "_"):
            f = WALLPAPERS / f"{numbered(name)}.png"
            if f.exists():
                return f
    return None


def _set_wallpaper_linux(path: Path) -> bool:
    """KDE Plasma: plasma-apply-wallpaperimage."""
    try:
        subprocess.run(["plasma-apply-wallpaperimage", str(path)],
                       check=True, capture_output=True, text=True)
        return True
    except FileNotFoundError:
        print("❌ Немає plasma-apply-wallpaperimage (потрібен KDE Plasma).")
    except subprocess.CalledProcessError as e:
        print(f"❌ plasma-apply-wallpaperimage: {e.stderr.strip() or e}")
    return False


def _set_wallpaper_windows(path: Path) -> bool:
    """Windows: SystemParametersInfoW (потрібен абсолютний шлях)."""
    import ctypes  # windll існує лише на Windows
    SPI_SETDESKWALLPAPER = 20
    SPIF_UPDATEINIFILE_SENDCHANGE = 3  # SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
    abs_path = str(path.resolve())
    try:
        ok = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, abs_path, SPIF_UPDATEINIFILE_SENDCHANGE)
        if ok:
            return True
        print("❌ SystemParametersInfoW повернув 0 (не вдалось встановити).")
    except Exception as e:
        print(f"❌ Windows: не вдалось встановити шпалеру ({e}).")
    return False


def set_wallpaper(path: Path) -> bool:
    """Встановити шпалеру залежно від платформи."""
    if sys.platform.startswith("linux"):
        return _set_wallpaper_linux(path)
    if sys.platform == "win32":
        return _set_wallpaper_windows(path)
    print(f"❌ Платформа '{sys.platform}' не підтримується.")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", choices=list(SEASONS))
    ap.add_argument("--time", choices=list(TIMES_OF_DAY))
    ap.add_argument("--weather", choices=list(WEATHER))
    ap.add_argument("--location", default="", help="місто для wttr.in")
    ap.add_argument("--dry-run", action="store_true",
                    help="лише показати вибір, не ставити")
    args = ap.parse_args()

    now = _dt.datetime.now()
    season = args.season or MONTH_SEASON[now.month]
    time = args.time or hour_to_time(now.hour)
    weather = args.weather or detect_weather(args.location)

    want = f"{season}_{time}_{weather}"
    path = resolve_file(season, time, weather)
    print(f"🕒 {now:%Y-%m-%d %H:%M} → сезон={season}, час={time}, погода={weather}")

    if path is None:
        print(f"⚠️ Немає жодного файлу для сезону '{season}' "
              f"(потрібен {want}.png). Генерація ще не завершена?")
        return 1
    if path.stem.split("_", 1)[1] != want:
        print(f"ℹ️ Точного {want}.png ще нема — беру найближчий: {path.name}")

    if args.dry_run:
        print(f"[dry-run] поставив би: {path.name}")
        return 0

    if set_wallpaper(path):
        print(f"🖼️ Встановлено: {path.name}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
