"""Вікно «Про програму» (PyQt6) — професійне, з версією, посиланнями,
подяками авторам оригінального арту та ліцензією."""
from __future__ import annotations

import platform
import sys

from PyQt6.QtCore import QT_VERSION_STR, Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from . import __app_name__, __version__
from .i18n import tr
from .icon import make_icon

_REPO = "https://github.com/dz-vadim/adaptive-wallpapers"


def _link(url: str, text: str) -> str:
    return f'<a href="{url}" style="color:#e3b94f;text-decoration:none;">{text}</a>'


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("About"))
        self.setWindowIcon(make_icon())
        self.setMinimumWidth(440)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 16)
        root.setSpacing(10)

        # шапка: іконка + назва + версія
        head = QHBoxLayout()
        head.setSpacing(14)
        ic = QLabel()
        ic.setPixmap(make_icon().pixmap(64, 64))
        head.addWidget(ic)
        col = QVBoxLayout()
        col.setSpacing(2)
        title = QLabel(__app_name__)
        title.setObjectName("Title")
        ver = QLabel(tr("Version {v}").format(v=__version__))
        ver.setObjectName("Subtitle")
        col.addStretch(1)
        col.addWidget(title)
        col.addWidget(ver)
        col.addStretch(1)
        head.addLayout(col)
        head.addStretch(1)
        root.addLayout(head)

        tagline = QLabel(tr("A living neon coffee-shop wallpaper that follows "
                            "the season, time of day and weather."))
        tagline.setWordWrap(True)
        tagline.setObjectName("Subtitle")
        root.addWidget(tagline)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:palette(mid);")
        root.addWidget(line)

        # посилання + подяки + ліцензія (rich text, клікабельне)
        info = QLabel()
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setOpenExternalLinks(True)
        info.setWordWrap(True)
        info.setText(
            f"<p><b>{tr('Source &amp; releases')}:</b> "
            f"{_link(_REPO, _REPO.replace('https://', ''))}<br>"
            f"<b>{tr('Report an issue')}:</b> "
            f"{_link(_REPO + '/issues', tr('Open an issue'))}</p>"
            f"<p><b>{tr('Artwork')}:</b> "
            f"{_link('https://www.artstation.com/mb0sco', 'Bogdan mB0sco')} &amp; "
            f"{_link('https://www.youtube.com/channel/UCsIg9WMfxjZZvwROleiVsQg', 'STEEZYASFUCK')}"
            f" — {tr('the generated frames are derivative works of their original art.')}</p>"
            f"<p><b>{tr('License')}:</b> MIT</p>"
        )
        root.addWidget(info)

        runtime = QLabel(f"PyQt {QT_VERSION_STR} · Python "
                         f"{sys.version_info.major}.{sys.version_info.minor}."
                         f"{sys.version_info.micro} · {platform.system()}")
        runtime.setObjectName("Subtitle")
        runtime.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(runtime)

        buttons = QDialogButtonBox()
        gh = buttons.addButton(tr("GitHub"), QDialogButtonBox.ButtonRole.ActionRole)
        gh.setObjectName("Primary")
        gh.clicked.connect(lambda: _open(_REPO))
        close = buttons.addButton(tr("Close"), QDialogButtonBox.ButtonRole.RejectRole)
        close.clicked.connect(self.accept)
        root.addWidget(buttons)


def _open(url: str) -> None:
    QDesktopServices.openUrl(QUrl(url))
