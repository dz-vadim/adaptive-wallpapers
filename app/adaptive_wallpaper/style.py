"""Тематичне оформлення: темна «кавова» палітра + QSS (сучасний вигляд)."""
from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette

ACCENT = "#e0a96d"        # тепла амбра (кава з молоком)
ACCENT_DK = "#c98a4e"
BG = "#211912"            # темне кавове тло
BG2 = "#2b211a"           # панелі/поля
TEXT = "#f1e7d6"          # кремовий текст
MUTED = "#a8957f"

_QSS = f"""
QWidget {{
    color: {TEXT};
    font-size: 13px;
}}
QDialog, QMenu {{
    background: {BG};
}}
QLabel#Title {{
    font-size: 17px;
    font-weight: 600;
    color: {TEXT};
}}
QLabel#Subtitle {{
    color: {MUTED};
}}
QLabel#Section {{
    color: {ACCENT};
    font-weight: 600;
    padding-top: 6px;
}}
QFrame#Card {{
    background: {BG2};
    border: 1px solid #3a2c20;
    border-radius: 12px;
}}
QComboBox, QSpinBox, QLineEdit {{
    background: {BG};
    border: 1px solid #4a3829;
    border-radius: 8px;
    padding: 5px 8px;
    selection-background-color: {ACCENT};
    selection-color: #2a1d12;
}}
QComboBox:hover, QSpinBox:hover, QLineEdit:hover {{
    border-color: {ACCENT_DK};
}}
QComboBox:focus, QSpinBox:focus, QLineEdit:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: {BG2};
    border: 1px solid #4a3829;
    selection-background-color: {ACCENT};
    selection-color: #2a1d12;
    outline: none;
}}
QPushButton {{
    background: {BG2};
    border: 1px solid #4a3829;
    border-radius: 8px;
    padding: 6px 14px;
}}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton:pressed {{ background: #34271d; }}
QPushButton#Primary {{
    background: {ACCENT};
    color: #2a1d12;
    border: none;
    font-weight: 600;
}}
QPushButton#Primary:hover {{ background: #ecb87f; }}
QPushButton#Primary:pressed {{ background: {ACCENT_DK}; }}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 1px solid #4a3829; border-radius: 5px;
    background: {BG};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT}; border-color: {ACCENT};
}}
QMenu::item {{ padding: 6px 22px; }}
QMenu::item:selected {{ background: {ACCENT}; color: #2a1d12; }}
QMenu::separator {{ height: 1px; background: #3a2c20; margin: 4px 8px; }}
QToolTip {{
    background: {BG2}; color: {TEXT};
    border: 1px solid {ACCENT_DK}; border-radius: 6px; padding: 4px;
}}
"""


def apply_theme(app) -> None:
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(BG))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    pal.setColor(QPalette.ColorRole.Base, QColor(BG))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(BG2))
    pal.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    pal.setColor(QPalette.ColorRole.Button, QColor(BG2))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#2a1d12"))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(BG2))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(MUTED))
    app.setPalette(pal)
    app.setStyleSheet(_QSS)
