"""Рушій вибору кадру: сезон × час доби × погода → конкретний файл.

Самодостатній (не залежить від scripts/scenes.py), щоб пакет можна було
встановити окремо. Контракт назв/нумерації дзеркалить scenes.py і QML logic.js:
файли звуться NN_<season>_<time>_<weather>.png, де NN — порядковий номер у
переборі seasons × times × weathers (1..48).
"""
from __future__ import annotations

import datetime as _dt
import json
import random
import urllib.request
from pathlib import Path

# --- контракт (дзеркало scenes.py) ---
SEASONS = ["winter", "spring", "summer", "autumn"]
TIMES = ["morning", "day", "evening", "night"]
WEATHERS = ["clear", "cloudy", "rain_snow"]

ALL_NAMES = [f"{s}_{t}_{w}" for s in SEASONS for t in TIMES for w in WEATHERS]
NUMBER = {name: i for i, name in enumerate(ALL_NAMES, 1)}


def numbered(name: str) -> str:
    """`winter_day_clear` → `04_winter_day_clear`."""
    return f"{NUMBER[name]:02d}_{name}"


def all_files() -> list[str]:
    """Усі 48 імен файлів у правильному порядку."""
    return [f"{numbered(n)}.png" for n in ALL_NAMES]


# --- сезон/час за датою ---
MONTH_SEASON = {12: "winter", 1: "winter", 2: "winter",
                3: "spring", 4: "spring", 5: "spring",
                6: "summer", 7: "summer", 8: "summer",
                9: "autumn", 10: "autumn", 11: "autumn"}


def month_to_season(month: int) -> str:
    return MONTH_SEASON[month]


def hour_to_time(hour: int) -> str:
    """Час доби за годиною (фолбек, коли немає даних про сонце)."""
    if 6 <= hour < 11:
        return "morning"
    if 11 <= hour < 17:
        return "day"
    if 17 <= hour < 21:
        return "evening"
    return "night"


def sun_to_time(now_min: int, sunrise_min: int, sunset_min: int) -> str:
    """Час доби за реальним сонцем (хвилини від півночі).

    morning — година навколо сходу; evening — година навколо заходу;
    day — між ними; night — решта.
    """
    if sunrise_min < 0 or sunset_min < 0:
        return hour_to_time(now_min // 60)
    if sunrise_min - 60 <= now_min < sunrise_min + 60:
        return "morning"
    if sunset_min - 60 <= now_min < sunset_min + 60:
        return "evening"
    if sunrise_min + 60 <= now_min < sunset_min - 60:
        return "day"
    return "night"


# --- погода (wttr.in) ---
CLEAR_CODES = {113}
CLOUDY_CODES = {116, 119, 122, 143, 248, 260}


def map_weather_code(code: int) -> str:
    if code in CLEAR_CODES:
        return "clear"
    if code in CLOUDY_CODES:
        return "cloudy"
    return "rain_snow"


def random_weather() -> str:
    """Офлайн-фолбек: випадкова погода з реалістичним ухилом."""
    r = random.random()
    return "clear" if r < 0.50 else ("cloudy" if r < 0.85 else "rain_snow")


def parse_clock(hhmm: str) -> int:
    """'06:21 AM' / '18:05' → хвилини від півночі; -1 якщо не розпарсити."""
    try:
        s = hhmm.strip().upper()
        ampm = None
        if s.endswith("AM") or s.endswith("PM"):
            ampm = s[-2:]
            s = s[:-2].strip()
        h, m = (int(x) for x in s.split(":")[:2])
        if ampm == "PM" and h != 12:
            h += 12
        if ampm == "AM" and h == 12:
            h = 0
        return h * 60 + m
    except Exception:
        return -1


class Conditions:
    """Поточні умови: погода + (опційно) схід/захід сонця у хвилинах."""

    def __init__(self, weather: str, sunrise: int = -1, sunset: int = -1,
                 online: bool = True):
        self.weather = weather
        self.sunrise = sunrise
        self.sunset = sunset
        self.online = online


# Кеш успішних онлайн-умов: щоб короткі інтервали оновлення не довбали
# wttr.in (він агресивно rate-лімітить). Невдачі не кешуємо — повторюємо.
_COND_TTL = 25 * 60
_cond_cache: dict[str, tuple[float, Conditions]] = {}


def fetch_conditions(location: str = "", timeout: float = 10.0) -> Conditions:
    """Погода + астрономія через wttr.in (кеш ~25 хв). Без мережі — випадкова."""
    import time
    hit = _cond_cache.get(location)
    if hit and time.monotonic() - hit[0] < _COND_TTL:
        return hit[1]
    url = f"https://wttr.in/{location}?format=j1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r)
        code = int(data["current_condition"][0]["weatherCode"])
        astro = data["weather"][0]["astronomy"][0]
        cond = Conditions(map_weather_code(code),
                          parse_clock(astro["sunrise"]),
                          parse_clock(astro["sunset"]),
                          online=True)
        _cond_cache[location] = (time.monotonic(), cond)
        return cond
    except Exception:
        return Conditions(random_weather(), online=False)


# --- вибір файлу ---
def resolve_file(folder: Path, season: str, time: str, weather: str) -> Path | None:
    """Точний файл або найближчий доступний у межах сезону."""
    folder = Path(folder)
    exact = folder / f"{numbered(f'{season}_{time}_{weather}')}.png"
    if exact.exists():
        return exact
    # 1) той самий сезон+час, інша погода
    for w in WEATHERS:
        f = folder / f"{numbered(f'{season}_{time}_{w}')}.png"
        if f.exists():
            return f
    # 2) той самий сезон, будь-який час/погода (у порядку нумерації)
    for name in ALL_NAMES:
        if name.startswith(season + "_"):
            f = folder / f"{numbered(name)}.png"
            if f.exists():
                return f
    # 3) хоч щось
    for name in ALL_NAMES:
        f = folder / f"{numbered(name)}.png"
        if f.exists():
            return f
    return None


def choose(folder: Path, *, season: str = "auto", time: str = "auto",
           weather: str = "auto", location: str = "",
           now: _dt.datetime | None = None) -> tuple[Path | None, str, dict]:
    """Підібрати файл за поточними/заданими умовами.

    Повертає (path|None, ім'я-сцени, інфо-дикт для логів/тултіпа).
    Будь-яке поле може бути 'auto' (визначити) або конкретним значенням.
    """
    now = now or _dt.datetime.now()
    cond = None
    if weather == "auto" or time == "auto":
        cond = fetch_conditions(location)

    s = season if season in SEASONS else month_to_season(now.month)
    if time in TIMES:
        t = time
    elif cond is not None:
        t = sun_to_time(now.hour * 60 + now.minute, cond.sunrise, cond.sunset)
    else:
        t = hour_to_time(now.hour)
    w = weather if weather in WEATHERS else (cond.weather if cond else random_weather())

    path = resolve_file(folder, s, t, w)
    info = {"season": s, "time": t, "weather": w,
            "online": (cond.online if cond else None)}
    return path, f"{s}_{t}_{w}", info
