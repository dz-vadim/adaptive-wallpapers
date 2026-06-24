"""Вікно налаштувань (PyQt6)."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from . import engine, paths

_WEATHER = [("Auto (live)", "auto"), ("Clear", "clear"),
            ("Cloudy", "cloudy"), ("Rain / Snow", "rain_snow")]
_SEASON = [("Auto (by date)", "auto"), ("Winter", "winter"), ("Spring", "spring"),
           ("Summer", "summer"), ("Autumn", "autumn")]
_TIME = [("Auto (sun-based)", "auto"), ("Morning", "morning"), ("Day", "day"),
         ("Evening", "evening"), ("Night", "night")]
_MODE = [("Adaptive (season · time · weather)", "adaptive"),
         ("Carousel (cycle all images)", "carousel")]


def _combo(pairs: list[tuple[str, str]], value: str) -> QComboBox:
    c = QComboBox()
    for text, val in pairs:
        c.addItem(text, val)
    i = c.findData(value)
    c.setCurrentIndex(max(0, i))
    return c


class SettingsDialog(QDialog):
    """Редагує копію конфіга; on_apply(cfg) застосовує зміни негайно."""

    def __init__(self, cfg: dict, on_apply, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adaptive Coffee Wallpaper — Settings")
        self.setMinimumWidth(440)
        self._cfg = dict(cfg)
        self._on_apply = on_apply

        form = QFormLayout()
        self.modeBox = _combo(_MODE, self._cfg["mode"])
        self.modeBox.currentIndexChanged.connect(self._toggle_mode)
        form.addRow("Mode:", self.modeBox)

        folderRow = QHBoxLayout()
        self.folderEdit = QLineEdit(self._cfg.get("folder", ""))
        found = paths.find_wallpapers(self._cfg.get("folder", ""))
        self.folderEdit.setPlaceholderText(
            f"auto: {found}" if found else "auto-detect (none found yet)")
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        folderRow.addWidget(self.folderEdit)
        folderRow.addWidget(browse)
        fw = QWidget()
        fw.setLayout(folderRow)
        form.addRow("Wallpapers folder:", fw)

        self.locationEdit = QLineEdit(self._cfg.get("location", ""))
        self.locationEdit.setPlaceholderText("blank = auto by IP")
        form.addRow("Weather location:", self.locationEdit)

        self.intervalSpin = QSpinBox()
        self.intervalSpin.setRange(1, 240)
        self.intervalSpin.setValue(int(self._cfg.get("interval_minutes", 20)))
        form.addRow("Update every (min):", self.intervalSpin)

        self.carouselSpin = QSpinBox()
        self.carouselSpin.setRange(1, 1440)
        self.carouselSpin.setValue(int(self._cfg.get("carousel_minutes", 30)))
        form.addRow("Carousel change (min):", self.carouselSpin)

        self.weatherBox = _combo(_WEATHER, self._cfg.get("weather", "auto"))
        self.seasonBox = _combo(_SEASON, self._cfg.get("season", "auto"))
        self.timeBox = _combo(_TIME, self._cfg.get("time", "auto"))
        form.addRow("Weather:", self.weatherBox)
        form.addRow("Season:", self.seasonBox)
        form.addRow("Time of day:", self.timeBox)

        self.autostartChk = QCheckBox("Run at login")
        self.autostartChk.setChecked(bool(self._cfg.get("autostart", False)))
        form.addRow("", self.autostartChk)

        # прев'ю
        self.preview = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.preview.setFixedSize(288, 162)
        self.preview.setStyleSheet("border:1px solid palette(mid);")
        self.previewName = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.previewName.setStyleSheet("color:palette(mid);")

        buttons = QDialogButtonBox()
        applyBtn = buttons.addButton("Apply now",
                                     QDialogButtonBox.ButtonRole.ApplyRole)
        buttons.addButton(QDialogButtonBox.StandardButton.Close)
        applyBtn.clicked.connect(self._apply)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Close).clicked.connect(
            self.accept)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.previewName)
        root.addWidget(buttons)

        for w in (self.weatherBox, self.seasonBox, self.timeBox):
            w.currentIndexChanged.connect(self._refresh_preview)
        self.folderEdit.textChanged.connect(self._refresh_preview)
        self._toggle_mode()
        self._refresh_preview()

    # ---- helpers ----
    def _toggle_mode(self):
        carousel = self.modeBox.currentData() == "carousel"
        self.intervalSpin.setEnabled(not carousel)
        for w in (self.weatherBox, self.seasonBox, self.timeBox,
                  self.locationEdit):
            w.setEnabled(not carousel)
        self.carouselSpin.setEnabled(carousel)
        self._refresh_preview()

    def _browse(self):
        start = self.folderEdit.text() or str(paths.find_wallpapers() or Path.home())
        d = QFileDialog.getExistingDirectory(self, "Choose wallpapers folder", start)
        if d:
            self.folderEdit.setText(d)

    def _collect(self) -> dict:
        return {
            "mode": self.modeBox.currentData(),
            "folder": self.folderEdit.text().strip(),
            "location": self.locationEdit.text().strip(),
            "interval_minutes": self.intervalSpin.value(),
            "carousel_minutes": self.carouselSpin.value(),
            "weather": self.weatherBox.currentData(),
            "season": self.seasonBox.currentData(),
            "time": self.timeBox.currentData(),
            "autostart": self.autostartChk.isChecked(),
        }

    def _refresh_preview(self):
        folder = paths.find_wallpapers(self.folderEdit.text().strip())
        if not folder:
            self.preview.setText("no wallpapers found")
            self.previewName.setText("")
            return
        # без мережі для прев'ю: лише локальна евразистика (sezon за датою, час за годиною)
        season = self.seasonBox.currentData()
        time = self.timeBox.currentData()
        weather = self.weatherBox.currentData()
        import datetime as _dt
        now = _dt.datetime.now()
        s = season if season != "auto" else engine.month_to_season(now.month)
        t = time if time != "auto" else engine.hour_to_time(now.hour)
        w = weather if weather != "auto" else "clear"
        path = engine.resolve_file(folder, s, t, w)
        if path and path.exists():
            pm = QPixmap(str(path)).scaled(
                self.preview.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            self.preview.setPixmap(pm)
            self.previewName.setText(path.name)
        else:
            self.preview.setText("no matching file")
            self.previewName.setText("")

    def _apply(self):
        self._cfg = self._collect()
        self._on_apply(dict(self._cfg))
        self._refresh_preview()

    def result_config(self) -> dict:
        return self._collect()
