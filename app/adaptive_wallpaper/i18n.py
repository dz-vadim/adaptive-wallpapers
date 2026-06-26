"""Легка локалізація без зовнішніх .ts/.qm — словник + tr().

Підтримує англійську (джерело) та українську. Мова: 'auto' (за локаллю
системи), 'en' або 'uk'. Рядки-джерела англійською передаються в tr(); для
української береться переклад зі словника, інакше — оригінал.
"""
from __future__ import annotations

import os

LANGUAGES = ["auto", "en", "uk"]
_current = "en"

# Англійський рядок-джерело → українська. Шаблони з {..} перекладаються до
# .format(): tr("No file for {name}.").format(name=...).
_UK = {
    # --- вікно налаштувань ---
    "Adaptive Coffee Wallpaper — Settings": "Adaptive Coffee Wallpaper — Налаштування",
    "Mode:": "Режим:",
    "Adaptive (season · time · weather)": "Адаптивний (сезон · час · погода)",
    "Carousel (cycle all images)": "Карусель (циклічно всі кадри)",
    "Wallpapers folder:": "Тека зі шпалерами:",
    "Folder:": "Тека:",
    "Browse…": "Огляд…",
    "auto-detect (none found yet)": "автовизначення (поки не знайдено)",
    "Choose wallpapers folder": "Оберіть теку зі шпалерами",
    "Weather location:": "Локація погоди:",
    "blank = auto by IP": "порожньо = авто за IP",
    "Update every (min):": "Оновлювати кожні (хв):",
    "Carousel change (min):": "Зміна каруселі (хв):",
    "Weather:": "Погода:",
    "Auto (live)": "Авто (наживо)",
    "Clear": "Ясно",
    "Cloudy": "Хмарно",
    "Rain / Snow": "Дощ / Сніг",
    "Season:": "Сезон:",
    "Auto (by date)": "Авто (за датою)",
    "Winter": "Зима",
    "Spring": "Весна",
    "Summer": "Літо",
    "Autumn": "Осінь",
    "Time of day:": "Час доби:",
    "Auto (sun-based)": "Авто (за сонцем)",
    "Morning": "Ранок",
    "Day": "День",
    "Evening": "Вечір",
    "Night": "Ніч",
    "Lock screen:": "Екран блокування:",
    "Keep original (restore pre-app)": "Зберегти оригінал (відновити до програми)",
    "Mirror desktop wallpaper": "Дзеркалити шпалеру робочого столу",
    "Pick from library": "Обрати з бібліотеки",
    "Lock image:": "Зображення блокування:",
    "Run at login": "Запуск при вході",
    "Language:": "Мова:",
    "Automatic": "Автоматично",
    "Theme:": "Тема:",
    "Auto (system)": "Авто (за системою)",
    "Dark": "Темна",
    "Light": "Світла",
    "Language change applies after reopening this window.":
        "Зміна мови застосується після повторного відкриття вікна.",
    "no wallpapers found": "шпалер не знайдено",
    "no matching file": "немає відповідного файлу",
    "Apply now": "Застосувати",
    "Apply": "Застосувати",
    "Close": "Закрити",
    "Settings applied": "Налаштування застосовано",
    "Applied": "Застосовано",
    "Wallpaper by season, time and weather":
        "Шпалери за сезоном, часом і погодою",
    "General": "Загальне",
    "Adaptive": "Адаптивно",
    "Carousel": "Карусель",
    "Lock screen": "Екран блокування",
    "Now showing": "Зараз показано",
    # --- трей-меню ---
    "Update now": "Оновити зараз",
    "Settings…": "Налаштування…",
    "Copy wallpapers to system…": "Скопіювати шпалери в систему…",
    "About": "Про програму",
    "Quit": "Вийти",
    # --- вікно «Про програму» ---
    "Version {v}": "Версія {v}",
    "A living neon coffee-shop wallpaper that follows "
    "the season, time of day and weather.":
        "Жива шпалера «неонова кав'ярня», що йде за сезоном, часом доби й погодою.",
    "Source &amp; releases": "Код і релізи",
    "Report an issue": "Повідомити про проблему",
    "Open an issue": "Відкрити issue",
    "Artwork": "Оригінальний арт",
    "the generated frames are derivative works of their original art.":
        "згенеровані кадри — похідні від їхнього оригінального арту.",
    "License": "Ліцензія",
    "GitHub": "GitHub",
    # --- сповіщення/повідомлення ---
    "No wallpapers found — set the folder in Settings.":
        "Шпалер не знайдено — вкажіть теку в Налаштуваннях.",
    "No wallpapers found in folder.": "У теці немає шпалер.",
    "No file for {name}.": "Немає файлу для {name}.",
    "Could not set the wallpaper on this desktop.":
        "Не вдалось встановити шпалеру на цьому робочому столі.",
    "Update failed: {msg}": "Помилка оновлення: {msg}",
    "Wallpapers copied to:\n{dest}\n\nConfig: {config}":
        "Шпалери скопійовано в:\n{dest}\n\nКонфіг: {config}",
    "Could not find wallpapers to copy. Put the 48 PNGs next to the app "
    "or pick the folder in Settings.":
        "Не знайдено шпалер для копіювання. Поклади 48 PNG поряд із програмою "
        "або обери теку в Налаштуваннях.",
}


def detect() -> str:
    """Мова за змінними локалі середовища (фолбек 'en')."""
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        v = os.environ.get(var, "")
        if v[:2].lower() == "uk":
            return "uk"
    return "en"


def set_language(lang: str) -> None:
    global _current
    if lang == "auto":
        _current = detect()
    else:
        _current = lang if lang in ("en", "uk") else "en"


def current() -> str:
    return _current


def tr(s: str) -> str:
    if _current == "uk":
        return _UK.get(s, s)
    return s
