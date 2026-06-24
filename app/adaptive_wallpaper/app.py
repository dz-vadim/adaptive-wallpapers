"""Трей-застосунок: фонова зміна шпалери + меню + налаштування (PyQt6)."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)

from . import __app_name__, __version__, engine, installer, lockscreen, paths
from . import config as cfg
from . import wallpaper as wp
from .settings_dialog import SettingsDialog


def _make_icon() -> QIcon:
    """Іконка теми, інакше намальована філіжанка кави."""
    themed = QIcon.fromTheme("preferences-desktop-wallpaper")
    if not themed.isNull():
        return themed
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#6f4e37"))
    p.setPen(QPen(QColor("#3e2b20"), 3))
    p.drawRoundedRect(14, 22, 28, 26, 6, 6)          # чашка
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(40, 26, 16, 18, -90 * 16, 180 * 16)     # вушко
    p.setPen(QPen(QColor("#d9c7a3"), 3))
    p.drawLine(22, 12, 22, 19)
    p.drawLine(30, 12, 30, 19)                        # пара
    p.end()
    return QIcon(pm)


class _Signals(QObject):
    done = pyqtSignal(object, str, dict)   # (path|None, scene_name, info)
    failed = pyqtSignal(str)


class _PickTask(QRunnable):
    """Підбір кадру (з мережею) у фоновому потоці."""

    def __init__(self, folder: Path, conf: dict, sig: _Signals):
        super().__init__()
        self.folder, self.conf, self.sig = folder, conf, sig

    def run(self):
        try:
            path, name, info = engine.choose(
                self.folder,
                season=self.conf.get("season", "auto"),
                time=self.conf.get("time", "auto"),
                weather=self.conf.get("weather", "auto"),
                location=self.conf.get("location", ""))
            self.sig.done.emit(path, name, info)
        except Exception as e:  # ніколи не валимо потік
            self.sig.failed.emit(str(e))


class Controller(QObject):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.cfg = cfg.load()
        self.pool = QThreadPool.globalInstance()
        self.sig = _Signals()
        self.sig.done.connect(self._on_picked)
        self.sig.failed.connect(lambda m: self._notify(f"Update failed: {m}"))
        self._carousel_pos = 0

        self.icon = _make_icon()
        self.tray = QSystemTrayIcon(self.icon)
        self.tray.setToolTip(__app_name__)
        self.tray.activated.connect(self._on_activated)
        self._build_menu()
        self.tray.show()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.apply)
        self._reschedule()
        QTimer.singleShot(300, self.apply)   # перший раз — невдовзі після старту

    # ---- меню ----
    def _build_menu(self):
        m = QMenu()
        self.statusAct = m.addAction("Adaptive Coffee Wallpaper")
        self.statusAct.setEnabled(False)
        m.addSeparator()
        m.addAction("Update now", self.apply)
        m.addAction("Settings…", self.open_settings)
        m.addSeparator()
        self.autostartAct = QAction("Run at login", self, checkable=True)
        self.autostartAct.setChecked(bool(self.cfg.get("autostart", False)))
        self.autostartAct.triggered.connect(self._toggle_autostart)
        m.addAction(self.autostartAct)
        m.addAction("Copy wallpapers to system…", self._do_install)
        m.addSeparator()
        m.addAction("Quit", self.app.quit)
        self.tray.setContextMenu(m)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.open_settings()

    # ---- цикл застосування ----
    def _folder(self) -> Path | None:
        return paths.find_wallpapers(self.cfg.get("folder", ""))

    def _reschedule(self):
        carousel = self.cfg.get("mode") == "carousel"
        mins = self.cfg.get("carousel_minutes" if carousel else "interval_minutes", 20)
        self.timer.start(max(1, int(mins)) * 60_000)

    def apply(self):
        folder = self._folder()
        if not folder:
            self._notify("No wallpapers found — set the folder in Settings.")
            return
        if self.cfg.get("mode") == "carousel":
            self._carousel_step(folder)
        else:
            self.pool.start(_PickTask(folder, self.cfg, self.sig))

    def _carousel_step(self, folder: Path):
        files = [folder / n for n in engine.all_files() if (folder / n).exists()]
        if not files:
            self._notify("No wallpapers found in folder.")
            return
        self._carousel_pos %= len(files)
        path = files[self._carousel_pos]
        self._carousel_pos += 1
        self._set(path, path.stem)

    def _on_picked(self, path, name, info):
        if path is None:
            self._notify(f"No file for {name}.")
            return
        online = "" if info.get("online") else "  (offline guess)"
        self._set(Path(path), name, suffix=online)

    def _set(self, path: Path, name: str, suffix: str = ""):
        ok = wp.set_wallpaper(path)
        if ok:
            self.tray.setToolTip(f"{__app_name__}\n{path.name}{suffix}")
            self._apply_lock(path)
        else:
            self._notify("Could not set the wallpaper on this desktop.")

    def _apply_lock(self, desktop_path: Path):
        """Екран блокування за обраним режимом (best-effort).

        skip = «keep original» (відновити те, що було до програми);
        mirror = поточна шпалера; library = закріплений кадр.
        """
        mode = self.cfg.get("lock_mode", "skip")
        if mode == "mirror":
            target = desktop_path
        elif mode == "library":
            folder = self._folder()
            name = self.cfg.get("lock_file", "")
            target = (folder / name) if (folder and name) else None
        else:
            target = None
        if lockscreen.manage_lock(self.cfg, target):
            cfg.save(self.cfg)

    def _notify(self, msg: str):
        self.tray.setToolTip(f"{__app_name__}\n{msg}")
        if QSystemTrayIcon.supportsMessages():
            self.tray.showMessage(__app_name__, msg, self.icon, 4000)

    # ---- налаштування ----
    def open_settings(self):
        dlg = SettingsDialog(self.cfg, self._apply_settings)
        dlg.exec()
        self._apply_settings(dlg.result_config())

    def _apply_settings(self, new: dict):
        autostart_changed = new.get("autostart") != self.cfg.get("autostart")
        self.cfg.update(new)
        cfg.save(self.cfg)
        self.autostartAct.setChecked(bool(self.cfg.get("autostart")))
        if autostart_changed:
            installer.set_autostart(bool(self.cfg.get("autostart")))
        self._carousel_pos = 0
        self._reschedule()
        self.apply()

    def _toggle_autostart(self, checked: bool):
        self.cfg["autostart"] = checked
        cfg.save(self.cfg)
        installer.set_autostart(checked)

    def _do_install(self):
        report = installer.install(copy_images=True,
                                   autostart=self.cfg.get("autostart", False))
        dest = report.get("wallpapers")
        if dest:
            self.cfg["folder"] = dest
            cfg.save(self.cfg)
            QMessageBox.information(
                None, __app_name__,
                f"Wallpapers copied to:\n{dest}\n\nConfig: {report['config']}")
        else:
            QMessageBox.warning(
                None, __app_name__,
                "Could not find wallpapers to copy. Put the 48 PNGs next to the "
                "app or pick the folder in Settings.")


def run_gui() -> int:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setQuitOnLastWindowClosed(False)   # закриття вікна не завершує застосунок
    if not QSystemTrayIcon.isSystemTrayAvailable():
        # без трея — хоч раз поставимо шпалеру й вийдемо
        folder = paths.find_wallpapers(cfg.load().get("folder", ""))
        if folder:
            conf = cfg.load()
            path, _name, _info = engine.choose(
                folder, season=conf.get("season", "auto"),
                time=conf.get("time", "auto"), weather=conf.get("weather", "auto"),
                location=conf.get("location", ""))
            if path:
                wp.set_wallpaper(path)
        return 0
    app._controller = Controller(app)   # зберегти посилання, щоб трей не зник
    return app.exec()
