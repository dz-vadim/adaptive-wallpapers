"""Кастомна іконка застосунку — однакова в усіх білдах.

Канонічне джерело — вбудований PNG (вантажиться завжди, без QtSvg-плагіна),
тож рантайм-іконка ідентична на Linux/Windows/із сорсів. SVG — як альтернатива,
мальована філіжанка — останній фолбек (якщо асети раптом відсутні).
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

ICON_NAME = "adaptive-wallpaper"
_ASSETS = Path(__file__).resolve().parent / "assets"
_PNG = _ASSETS / f"{ICON_NAME}.png"
_SVG = _ASSETS / f"{ICON_NAME}.svg"


def png_path() -> Path:
    return _PNG


def svg_path() -> Path:
    return _SVG


def _drawn() -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#1b2233"))
    p.setPen(QPen(QColor("#ff5fae"), 3))
    p.drawRoundedRect(5, 5, 54, 54, 14, 14)            # неоновий фон
    p.setBrush(QColor("#6f4e37"))
    p.setPen(QPen(QColor("#3e2b20"), 3))
    p.drawRoundedRect(16, 26, 28, 24, 6, 6)            # чашка
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(42, 28, 16, 18, -90 * 16, 180 * 16)      # вушко
    p.setPen(QPen(QColor("#cfe3ff"), 3))
    p.drawLine(24, 14, 24, 21)
    p.drawLine(32, 14, 32, 21)                          # пара
    p.end()
    return QIcon(pm)


def make_icon() -> QIcon:
    for f in (_PNG, _SVG):                  # PNG спершу — без залежності від QtSvg
        if f.exists():
            ic = QIcon(str(f))
            if not ic.isNull():
                return ic
    return _drawn()
