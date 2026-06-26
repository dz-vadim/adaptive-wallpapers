"""Логування у файл (config_dir/app.log) — щоб тихі помилки (не той DE,
відсутній gsettings/PowerShell тощо) можна було діагностувати з баг-репорту."""
from __future__ import annotations

import logging

from .paths import config_dir


def _setup() -> logging.Logger:
    logger = logging.getLogger("adaptive_wallpaper")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    try:
        d = config_dir()
        d.mkdir(parents=True, exist_ok=True)
        h = logging.FileHandler(d / "app.log", encoding="utf-8")
        h.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(h)
    except OSError:
        logger.addHandler(logging.NullHandler())
    return logger


log = _setup()
