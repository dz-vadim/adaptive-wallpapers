"""Кастомна іконка застосунку — однакова в усіх білдах.

Канонічне джерело — вбудований PNG (вантажиться завжди, без QtSvg-плагіна),
тож рантайм-іконка ідентична на Linux/Windows/із сорсів. SVG — як альтернатива,
мальована філіжанка — останній фолбек (якщо асети раптом відсутні).

PyQt6 імпортується ЛІНИВО (всередині make_icon) — щоб CLI (`--once`/`--version`)
та інсталятор не тягнули GUI-бібліотеки (libEGL тощо) на headless-системах.
"""
from __future__ import annotations

from pathlib import Path

ICON_NAME = "adaptive-wallpaper"
_ASSETS = Path(__file__).resolve().parent / "assets"
_PNG = _ASSETS / f"{ICON_NAME}.png"
_SVG = _ASSETS / f"{ICON_NAME}.svg"


def png_path() -> Path:
    return _PNG


def svg_path() -> Path:
    return _SVG


def _drawn():
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#122430"))
    p.setPen(QPen(QColor("#ecdf92"), 2))
    p.drawRoundedRect(6, 6, 52, 52, 12, 12)
    p.drawLine(24, 18, 40, 18)
    p.drawLine(22, 24, 42, 24)
    p.drawLine(24, 24, 27, 50)
    p.drawLine(40, 24, 37, 50)
    p.drawLine(27, 50, 37, 50)
    p.end()
    return QIcon(pm)


def make_icon():
    from PyQt6.QtGui import QIcon
    for f in (_PNG, _SVG):                  # PNG спершу — без залежності від QtSvg
        if f.exists():
            ic = QIcon(str(f))
            if not ic.isNull():
                return ic
    return _drawn()
