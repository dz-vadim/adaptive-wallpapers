"""Перевірка й застосування оновлень через GitHub Releases.

- check_latest(): питає latest-реліз, повертає інфо лише якщо версія новіша.
- download(): потоково качає артефакт із прогресом.
- apply_update(): Windows — запускає setup.exe (апгрейд на місці й закриває
  застосунок); Linux (заморожений бінарник) — замінює exe й перезапускається.
  Якщо запущено із сорсів — самооновлення нема (відкриваємо сторінку релізів).
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

from . import __version__
from .log import log
from .paths import is_frozen

REPO = "dz-vadim/adaptive-wallpapers"
_API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{REPO}/releases/latest"


def _parse(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3]) or (0,)


def is_newer(latest: str, current: str = __version__) -> bool:
    return _parse(latest) > _parse(current)


def check_latest(timeout: float = 8.0) -> dict | None:
    """Інфо про новіший реліз або None (немає новішого / помилка / офлайн)."""
    try:
        req = urllib.request.Request(_API, headers={
            "User-Agent": "adaptive-wallpaper",
            "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r)
        tag = (data.get("tag_name") or "").lstrip("v")
        if not tag or not is_newer(tag):
            return None
        assets = {a["name"]: a["browser_download_url"]
                  for a in data.get("assets", [])}
        return {"version": tag,
                "url": data.get("html_url") or RELEASES_URL,
                "assets": assets}
    except Exception as e:                       # офлайн / rate-limit / тощо
        log.info("update check failed: %s", e)
        return None


def asset_url(assets: dict) -> str | None:
    """URL артефакта для самооновлення на поточній платформі."""
    if sys.platform == "win32":
        return assets.get("adaptive-wallpaper-setup.exe")
    if sys.platform.startswith("linux"):
        return assets.get("adaptive-wallpaper")
    return None


def can_self_update(assets: dict) -> bool:
    """Чи можемо оновитись усередині програми (заморожений білд + є артефакт)."""
    return is_frozen() and asset_url(assets) is not None


def download(url: str, dest: Path, progress=None, timeout: float = 30.0) -> None:
    """Потокове завантаження у dest; progress(done, total) — опційний колбек."""
    req = urllib.request.Request(url, headers={"User-Agent": "adaptive-wallpaper"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        with open(dest, "wb") as f:
            while True:
                chunk = r.read(262144)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if progress:
                    progress(done, total)


def apply_update(downloaded: Path) -> list[str] | None:
    """Застосувати завантажене. Повертає команду перезапуску (Linux) або None
    (Windows — інсталятор сам перезапустить; виклику слід завершити застосунок)."""
    if sys.platform == "win32":
        os.startfile(str(downloaded))   # noqa: S606 — запуск інсталятора
        return None
    # Linux: замінити поточний бінарник і перезапуститись
    target = Path(sys.argv[0]).resolve()
    os.chmod(downloaded, 0o755)
    os.replace(downloaded, target)      # downloaded має бути в тій самій теці
    return [str(target)]
