"""Оформлення: палітра з оригінального референсу (глибокий синьо-зелений +
золотий неон COFFEE), що підлаштовується під СИСТЕМНУ тему (темну чи світлу).
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette

# Акцент — золото неонової вивіски COFFEE (трохи глибше для світлої теми).
ACCENT_DARK = "#e3b94f"
ACCENT_LIGHT = "#bd8a1f"

# Темна палітра — нічні сині тони оригіналу (#112233 / #1a324a / #2d4d64),
# тепле золото неону COFFEE як акцент.
_DARK = {
    "accent": ACCENT_DARK, "accent_hi": "#f0cf72", "on_accent": "#101a2b",
    "bg": "#0f1c30", "panel": "#182a44", "border": "#2d4866",
    "text": "#e8e3d4", "muted": "#8ea2bd", "preview": "#0a1626",
}
# Світла палітра (той самий синьо-зелений як текст, нейтральне тло)
_LIGHT = {
    "accent": ACCENT_LIGHT, "accent_hi": "#d6a430", "on_accent": "#ffffff",
    "bg": "#eef1f3", "panel": "#ffffff", "border": "#cdd5da",
    "text": "#17252f", "muted": "#5d6b75", "preview": "#dfe4e7",
}


def is_dark(app) -> bool:
    try:
        return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        return app.palette().color(QPalette.ColorRole.Window).lightness() < 128


def _vars(app) -> dict:
    return _DARK if is_dark(app) else _LIGHT


def _qss(v: dict) -> str:
    return f"""
QWidget {{ color: {v['text']}; font-size: 13px; }}
QDialog, QMenu {{ background: {v['bg']}; }}
QLabel#Title {{ font-size: 17px; font-weight: 600; color: {v['text']}; }}
QLabel#Subtitle {{ color: {v['muted']}; }}
QLabel#Section {{ color: {v['accent']}; font-weight: 600; padding-top: 4px; }}
QLabel#Preview {{ border-radius: 8px; background: {v['preview']}; }}
QFrame#Card {{
    background: {v['panel']};
    border: 1px solid {v['border']};
    border-radius: 12px;
}}
QComboBox, QSpinBox, QLineEdit {{
    background: {v['bg']};
    border: 1px solid {v['border']};
    border-radius: 8px;
    padding: 5px 8px;
    min-height: 20px;
    selection-background-color: {v['accent']};
    selection-color: {v['on_accent']};
}}
QComboBox:hover, QSpinBox:hover, QLineEdit:hover {{ border-color: {v['accent']}; }}
QComboBox:focus, QSpinBox:focus, QLineEdit:focus {{ border-color: {v['accent']}; }}
QComboBox::drop-down {{
    subcontrol-origin: padding; subcontrol-position: center right;
    border: none; width: 22px;
}}
QComboBox::down-arrow {{ width: 10px; height: 10px; }}
QComboBox QAbstractItemView {{
    background: {v['panel']};
    border: 1px solid {v['border']};
    border-radius: 8px;
    selection-background-color: {v['accent']};
    selection-color: {v['on_accent']};
    outline: none;
    padding: 4px;
}}

/* QSpinBox: безрамкові заокруглені степери (а не квадрати в полі) */
QSpinBox {{ padding-right: 22px; }}
QSpinBox::up-button, QSpinBox::down-button {{
    subcontrol-origin: border;
    width: 20px;
    border: none;
    background: transparent;
    margin: 1px;
}}
QSpinBox::up-button {{ subcontrol-position: top right; border-top-right-radius: 7px; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 7px; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {v['accent']};
}}
QSpinBox::up-arrow, QSpinBox::down-arrow {{ width: 9px; height: 9px; }}

QPushButton {{
    background: {v['panel']};
    border: 1px solid {v['border']};
    border-radius: 8px;
    padding: 6px 14px;
    min-height: 18px;
}}
QPushButton:hover {{ border-color: {v['accent']}; }}
QPushButton:pressed {{ background: {v['border']}; }}
QPushButton#Primary {{
    background: {v['accent']}; color: {v['on_accent']};
    border: none; font-weight: 600;
}}
QPushButton#Primary:hover {{ background: {v['accent_hi']}; }}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 1px solid {v['border']}; border-radius: 5px;
    background: {v['bg']};
}}
QCheckBox::indicator:hover {{ border-color: {v['accent']}; }}
QCheckBox::indicator:checked {{ background: {v['accent']}; border-color: {v['accent']}; }}
QMenu::item {{ padding: 6px 22px; }}
QMenu::item:selected {{ background: {v['accent']}; color: {v['on_accent']}; }}
QMenu::item:disabled {{ color: {v['muted']}; }}
QMenu::separator {{ height: 1px; background: {v['border']}; margin: 4px 8px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {v['border']}; border-radius: 5px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {v['accent']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QToolTip {{
    background: {v['panel']}; color: {v['text']};
    border: 1px solid {v['accent']}; border-radius: 6px; padding: 4px;
}}
"""


def apply_theme(app) -> None:
    v = _vars(app)
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(v["bg"]))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(v["text"]))
    pal.setColor(QPalette.ColorRole.Base, QColor(v["bg"]))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(v["panel"]))
    pal.setColor(QPalette.ColorRole.Text, QColor(v["text"]))
    pal.setColor(QPalette.ColorRole.Button, QColor(v["panel"]))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(v["text"]))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(v["accent"]))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(v["on_accent"]))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(v["panel"]))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(v["text"]))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(v["muted"]))
    app.setPalette(pal)
    app.setStyleSheet(_qss(v))

    # реактивність: перемалювати при зміні системної теми (один раз під'єднати)
    if not getattr(app, "_acw_theme_hook", False):
        app._acw_theme_hook = True
        try:
            app.styleHints().colorSchemeChanged.connect(lambda *_: apply_theme(app))
        except Exception:
            pass
