"""Конфіг застосунку — простий JSON у теці налаштувань користувача."""
from __future__ import annotations

import json
from pathlib import Path

from .paths import config_dir

DEFAULTS = {
    "mode": "adaptive",          # adaptive | carousel
    "folder": "",                # порожньо = автовизначення (paths.find_wallpapers)
    "location": "",              # місто для wttr.in; порожньо = за IP
    "interval_minutes": 20,      # adaptive: як часто перевіряти умови
    "carousel_minutes": 30,      # carousel: як часто міняти кадр
    "weather": "auto",           # auto | clear | cloudy | rain_snow
    "season": "auto",            # auto | winter | spring | summer | autumn
    "time": "auto",              # auto | morning | day | evening | night
    "autostart": False,          # тримаємо синхронно з реальним станом автозапуску
    "lock_mode": "skip",         # екран блокування: skip(keep) | mirror | library
    "lock_file": "",             # для lock_mode=library: ім'я кадру з бібліотеки
    "lock_backup": None,         # знімок оригіналу до керування (для відновлення)
    "language": "auto",          # мова інтерфейсу: auto | en | uk
    "theme": "auto",             # тема: auto (за системою) | dark | light
    "check_updates": True,       # ненав'язлива перевірка нових версій
    "last_notified_version": "", # щоб не сповіщати про ту саму версію повторно
}


def config_path() -> Path:
    return config_dir() / "config.json"


def load() -> dict:
    cfg = dict(DEFAULTS)
    p = config_path()
    try:
        if p.exists():
            cfg.update(json.loads(p.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return cfg


def save(cfg: dict) -> None:
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.part")
    tmp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)
