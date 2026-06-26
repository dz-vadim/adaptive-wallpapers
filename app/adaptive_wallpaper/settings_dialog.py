"""Вікно налаштувань (PyQt6): сучасний тематичний вигляд, реактивна мова,
авто-застосування з підтвердженням."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from . import engine, paths, style
from .i18n import set_language, tr
from .icon import make_icon

_WEATHER = [("Auto (live)", "auto"), ("Clear", "clear"),
            ("Cloudy", "cloudy"), ("Rain / Snow", "rain_snow")]
_SEASON = [("Auto (by date)", "auto"), ("Winter", "winter"), ("Spring", "spring"),
           ("Summer", "summer"), ("Autumn", "autumn")]
_TIME = [("Auto (sun-based)", "auto"), ("Morning", "morning"), ("Day", "day"),
         ("Evening", "evening"), ("Night", "night")]
_MODE = [("Adaptive (season · time · weather)", "adaptive"),
         ("Carousel (cycle all images)", "carousel")]
_LOCK = [("Keep original (restore pre-app)", "skip"),
         ("Mirror desktop wallpaper", "mirror"),
         ("Pick from library", "library")]
_LANG = [("Automatic", "auto"), ("English", "en"), ("Українська", "uk")]
_THEME = [("Auto (system)", "auto"), ("Dark", "dark"), ("Light", "light")]


class SettingsDialog(QDialog):
    """Редагує копію конфіга. on_apply(cfg) застосовує негайно;
    on_language(lang) (опц.) — щоб застосунок реактивно перемалював меню."""

    def __init__(self, cfg: dict, on_apply, on_language=None, parent=None):
        super().__init__(parent)
        self._cfg = dict(cfg)
        self._on_apply = on_apply
        self._on_language = on_language
        self._building = True
        self._tr_labels: list[tuple[QLabel, str]] = []
        self._tr_combos: list[tuple[QComboBox, list]] = []

        self.setWindowIcon(make_icon())
        self.setMinimumWidth(780)

        # авто-застосування з дебаунсом (реактивність)
        self._applyTimer = QTimer(self)
        self._applyTimer.setSingleShot(True)
        self._applyTimer.setInterval(450)
        self._applyTimer.timeout.connect(self._apply)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 14)
        root.setSpacing(12)
        root.addWidget(self._header())

        # дві колонки замість одного довгого стовпця
        cols = QHBoxLayout()
        cols.setSpacing(12)
        left = QVBoxLayout()
        left.setSpacing(12)
        left.addWidget(self._general_card())
        left.addWidget(self._adaptive_card())
        left.addStretch(1)
        right = QVBoxLayout()
        right.setSpacing(12)
        right.addWidget(self._preview_card())
        right.addWidget(self._lock_card())
        right.addStretch(1)
        cols.addLayout(left, 1)
        cols.addLayout(right, 1)
        root.addLayout(cols)
        root.addLayout(self._footer())

        self._building = False
        self._toggle_mode()
        self._toggle_lock()
        self._refresh_preview()

    # ---------- будівельні блоки ----------
    def _card(self, title_key: str) -> tuple[QFrame, QFormLayout]:
        frame = QFrame()
        frame.setObjectName("Card")
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(14, 10, 14, 12)
        if title_key:
            t = QLabel(tr(title_key))
            t.setObjectName("Section")
            self._tr_labels.append((t, title_key))
            outer.addWidget(t)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)
        outer.addLayout(form)
        return frame, form

    def _row(self, form: QFormLayout, key: str, field) -> QLabel:
        lbl = QLabel(tr(key))
        self._tr_labels.append((lbl, key))
        form.addRow(lbl, field)
        return lbl

    def _combo(self, pairs, value: str, on_change=None) -> QComboBox:
        c = QComboBox()
        for text, val in pairs:
            c.addItem(tr(text), val)
        c.setCurrentIndex(max(0, c.findData(value)))
        self._tr_combos.append((c, pairs))
        if on_change:
            c.currentIndexChanged.connect(on_change)
        c.currentIndexChanged.connect(self._schedule_apply)
        return c

    def _header(self) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(2, 0, 2, 2)
        ic = QLabel()
        ic.setPixmap(make_icon().pixmap(44, 44))
        h.addWidget(ic)
        col = QVBoxLayout()
        col.setSpacing(0)
        self.titleLbl = QLabel("Adaptive Coffee Wallpaper")
        self.titleLbl.setObjectName("Title")
        self.subLbl = QLabel(tr("Wallpaper by season, time and weather"))
        self.subLbl.setObjectName("Subtitle")
        self._tr_labels.append((self.subLbl, "Wallpaper by season, time and weather"))
        col.addWidget(self.titleLbl)
        col.addWidget(self.subLbl)
        h.addLayout(col)
        h.addStretch(1)
        return w

    def _general_card(self) -> QFrame:
        frame, form = self._card("General")
        self.modeBox = self._combo(_MODE, self._cfg["mode"], self._toggle_mode)
        self._row(form, "Mode:", self.modeBox)

        folderRow = QHBoxLayout()
        self.folderEdit = QLineEdit(self._cfg.get("folder", ""))
        found = paths.find_wallpapers(self._cfg.get("folder", ""))
        self.folderEdit.setPlaceholderText(
            f"auto: {found}" if found else tr("auto-detect (none found yet)"))
        self.folderEdit.editingFinished.connect(self._schedule_apply)
        self.folderEdit.textChanged.connect(self._refresh_preview)
        self.browseBtn = QPushButton(tr("Browse…"))
        self.browseBtn.clicked.connect(self._browse)
        folderRow.addWidget(self.folderEdit)
        folderRow.addWidget(self.browseBtn)
        fw = QWidget()
        fw.setLayout(folderRow)
        self._row(form, "Folder:", fw)

        self.themeBox = self._combo(_THEME, self._cfg.get("theme", "auto"),
                                    self._on_theme_change)
        self._row(form, "Theme:", self.themeBox)

        self.langBox = self._combo(_LANG, self._cfg.get("language", "auto"),
                                   self._on_lang_change)
        self._row(form, "Language:", self.langBox)
        return frame

    def _adaptive_card(self) -> QFrame:
        frame, form = self._card("Adaptive")
        self.locationEdit = QLineEdit(self._cfg.get("location", ""))
        self.locationEdit.setPlaceholderText(tr("blank = auto by IP"))
        self.locationEdit.editingFinished.connect(self._schedule_apply)
        self.locLbl = self._row(form, "Weather location:", self.locationEdit)

        self.intervalSpin = QSpinBox()
        self.intervalSpin.setRange(1, 240)
        self.intervalSpin.setValue(int(self._cfg.get("interval_minutes", 20)))
        self.intervalSpin.valueChanged.connect(self._schedule_apply)
        self.intLbl = self._row(form, "Update every (min):", self.intervalSpin)

        self.carouselSpin = QSpinBox()
        self.carouselSpin.setRange(1, 1440)
        self.carouselSpin.setValue(int(self._cfg.get("carousel_minutes", 30)))
        self.carouselSpin.valueChanged.connect(self._schedule_apply)
        self.carLbl = self._row(form, "Carousel change (min):", self.carouselSpin)

        self.weatherBox = self._combo(_WEATHER, self._cfg.get("weather", "auto"),
                                      self._refresh_preview)
        self.seasonBox = self._combo(_SEASON, self._cfg.get("season", "auto"),
                                     self._refresh_preview)
        self.timeBox = self._combo(_TIME, self._cfg.get("time", "auto"),
                                   self._refresh_preview)
        self.wLbl = self._row(form, "Weather:", self.weatherBox)
        self.sLbl = self._row(form, "Season:", self.seasonBox)
        self.tLbl = self._row(form, "Time of day:", self.timeBox)
        return frame

    def _lock_card(self) -> QFrame:
        frame, form = self._card("Lock screen")
        self.lockBox = self._combo(_LOCK, self._cfg.get("lock_mode", "skip"),
                                   self._toggle_lock)
        self._row(form, "Lock screen:", self.lockBox)
        self.lockFileBox = QComboBox()
        for fn in engine.all_files():
            self.lockFileBox.addItem(fn, fn)
        self.lockFileBox.setCurrentIndex(
            max(0, self.lockFileBox.findData(self._cfg.get("lock_file", ""))))
        self.lockFileBox.currentIndexChanged.connect(self._schedule_apply)
        self._row(form, "Lock image:", self.lockFileBox)

        self.autostartChk = QCheckBox(tr("Run at login"))
        self.autostartChk.setChecked(bool(self._cfg.get("autostart", False)))
        self.autostartChk.toggled.connect(self._schedule_apply)
        self._tr_labels.append((self.autostartChk, "Run at login"))
        form.addRow("", self.autostartChk)
        return frame

    def _preview_card(self) -> QFrame:
        frame, _ = self._card("Now showing")
        lay = frame.layout()
        self.preview = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.preview.setObjectName("Preview")
        self.preview.setFixedSize(300, 169)
        self.previewName = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.previewName.setObjectName("Subtitle")
        lay.addWidget(self.preview, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.previewName)
        return frame

    def _footer(self) -> QHBoxLayout:
        h = QHBoxLayout()
        self.statusLbl = QLabel("")
        self.statusLbl.setObjectName("Subtitle")
        h.addWidget(self.statusLbl)
        h.addStretch(1)
        self.applyBtn = QPushButton(tr("Apply"))
        self.applyBtn.setObjectName("Primary")
        self.applyBtn.clicked.connect(self._apply)
        self.closeBtn = QPushButton(tr("Close"))
        self.closeBtn.clicked.connect(self.accept)
        h.addWidget(self.applyBtn)
        h.addWidget(self.closeBtn)
        return h

    # ---------- логіка ----------
    def _schedule_apply(self):
        if not self._building:
            self._applyTimer.start()

    def _toggle_lock(self):
        self.lockFileBox.setEnabled(self.lockBox.currentData() == "library")

    def _toggle_mode(self):
        carousel = self.modeBox.currentData() == "carousel"
        for w in (self.locationEdit, self.intervalSpin, self.weatherBox,
                  self.seasonBox, self.timeBox, self.locLbl, self.intLbl,
                  self.wLbl, self.sLbl, self.tLbl):
            w.setVisible(not carousel)
        for w in (self.carouselSpin, self.carLbl):
            w.setVisible(carousel)
        self._refresh_preview()

    def _on_lang_change(self):
        # реактивно: одразу перемкнути мову інтерфейсу
        set_language(self._effective_lang(self.langBox.currentData()))
        self._retranslate()
        if self._on_language:
            self._on_language(self.langBox.currentData())

    def _on_theme_change(self):
        # реактивно: одразу перемалювати тему всього застосунку
        style.set_pref(self.themeBox.currentData())
        app = QApplication.instance()
        if app is not None:
            style.apply_theme(app)
        self._refresh_preview()

    @staticmethod
    def _effective_lang(lang: str) -> str:
        from .i18n import detect
        return detect() if lang == "auto" else lang

    def _retranslate(self):
        self.setWindowTitle(tr("Adaptive Coffee Wallpaper — Settings"))
        for lbl, key in self._tr_labels:
            lbl.setText(tr(key))
        for combo, pairs in self._tr_combos:
            data = combo.currentData()
            combo.blockSignals(True)
            for i, (text, _val) in enumerate(pairs):
                combo.setItemText(i, tr(text))
            combo.setCurrentIndex(max(0, combo.findData(data)))
            combo.blockSignals(False)
        self.browseBtn.setText(tr("Browse…"))
        self.applyBtn.setText(tr("Apply"))
        self.closeBtn.setText(tr("Close"))
        self.locationEdit.setPlaceholderText(tr("blank = auto by IP"))
        self._refresh_preview()

    def _browse(self):
        start = self.folderEdit.text() or str(paths.find_wallpapers() or Path.home())
        d = QFileDialog.getExistingDirectory(self, tr("Choose wallpapers folder"), start)
        if d:
            self.folderEdit.setText(d)
            self._schedule_apply()

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
            "lock_mode": self.lockBox.currentData(),
            "lock_file": self.lockFileBox.currentData() or "",
            "language": self.langBox.currentData(),
            "theme": self.themeBox.currentData(),
        }

    def _refresh_preview(self):
        if self._building:
            return
        folder = paths.find_wallpapers(self.folderEdit.text().strip())
        if not folder:
            self.preview.setText(tr("no wallpapers found"))
            self.previewName.setText("")
            return
        import datetime as _dt
        now = _dt.datetime.now()
        season = self.seasonBox.currentData()
        time = self.timeBox.currentData()
        weather = self.weatherBox.currentData()
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
            self.preview.setText(tr("no matching file"))
            self.previewName.setText("")

    def _apply(self):
        self._applyTimer.stop()
        self._cfg = self._collect()
        self._on_apply(dict(self._cfg))
        import datetime as _dt
        self.statusLbl.setText(f"✓ {tr('Applied')}  {_dt.datetime.now():%H:%M:%S}")
        self._refresh_preview()

    def result_config(self) -> dict:
        return self._collect()
