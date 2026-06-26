"""Трей-застосунок: фонова зміна шпалери + меню + налаштування (PyQt6)."""
from __future__ import annotations

import time
from pathlib import Path

from PyQt6.QtCore import QLocale, QObject, QRunnable, QThreadPool, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
)

from . import (
    __app_name__,
    __version__,
    engine,
    installer,
    lockscreen,
    paths,
    single_instance,
    style,
)
from . import config as cfg
from . import wallpaper as wp
from .i18n import detect, set_language, tr
from .icon import ICON_NAME, make_icon
from .log import log
from .settings_dialog import SettingsDialog


def _apply_language(lang: str) -> None:
    """Застосувати мову; 'auto' → за локаллю системи (env LANG, далі Qt)."""
    if lang == "auto":
        lang = detect()   # за змінними локалі (LANG/LC_*)
        if lang == "en" and QLocale.system().name().startswith("uk"):
            lang = "uk"   # запасний сигнал (напр. мова UI у Windows)
    set_language(lang)


_NO_LOCK = object()   # сентинел: не чіпати екран блокування цього разу


class _Signals(QObject):
    picked = pyqtSignal(object, str, dict)                 # (path|None, name, info)
    # (path, name, ok, lock_changed, lock_backup, suffix)
    applied = pyqtSignal(object, str, bool, bool, object, str)
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
            self.sig.picked.emit(path, name, info)
        except Exception as e:  # ніколи не валимо потік
            log.exception("pick failed")
            self.sig.failed.emit(str(e))


class _ApplyTask(QRunnable):
    """Встановлення шпалери (+ екран блокування) у фоновому потоці, щоб не
    блокувати GUI на subprocess (plasma-apply / gsettings / PowerShell)."""

    def __init__(self, path: Path, name: str, target, conf: dict,
                 suffix: str, sig: _Signals):
        super().__init__()
        self.path, self.name, self.target = path, name, target
        self.conf, self.suffix, self.sig = conf, suffix, sig

    def run(self):
        try:
            ok = wp.set_wallpaper(self.path)
            changed = False
            if ok and self.target is not _NO_LOCK:
                changed = lockscreen.manage_lock(self.conf, self.target)
            self.sig.applied.emit(self.path, self.name, ok, changed,
                                  self.conf.get("lock_backup"), self.suffix)
        except Exception as e:
            log.exception("apply failed")
            self.sig.failed.emit(str(e))


class Controller(QObject):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.cfg = cfg.load()
        self.pool = QThreadPool.globalInstance()
        self.sig = _Signals()
        self.sig.picked.connect(self._on_picked)
        self.sig.applied.connect(self._on_applied)
        self._last_lock = None       # ключ останнього застосованого lock (анти-churn)
        self.sig.failed.connect(
            lambda m: self._notify(tr("Update failed: {msg}").format(msg=m)))
        self._carousel_pos = 0
        self._last_apply_note = 0.0
        self._dlg = None
        _apply_language(self.cfg.get("language", "auto"))

        self.icon = make_icon()
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
        self.statusAct = m.addAction(__app_name__)
        self.statusAct.setEnabled(False)
        m.addSeparator()
        m.addAction(tr("Update now"), self.apply)
        m.addAction(tr("Settings…"), self.open_settings)
        m.addSeparator()
        self.autostartAct = m.addAction(tr("Run at login"))
        self.autostartAct.setCheckable(True)
        self.autostartAct.setChecked(bool(self.cfg.get("autostart", False)))
        self.autostartAct.triggered.connect(self._toggle_autostart)
        m.addAction(tr("Copy wallpapers to system…"), self._do_install)
        m.addSeparator()
        m.addAction(tr("About"), self.open_about)
        m.addAction(tr("Quit"), self.app.quit)
        self.tray.setContextMenu(m)

    def open_about(self):
        from .about_dialog import AboutDialog
        dlg = AboutDialog()
        dlg.exec()

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
            self._notify(tr("No wallpapers found — set the folder in Settings."))
            return
        if self.cfg.get("mode") == "carousel":
            self._carousel_step(folder)
        else:
            # знімок конфіга — воркер-потік не має читати спільний self.cfg,
            # який змінює GUI-потік
            self.pool.start(_PickTask(folder, dict(self.cfg), self.sig))

    def _carousel_step(self, folder: Path):
        files = [folder / n for n in engine.all_files() if (folder / n).exists()]
        if not files:
            self._notify(tr("No wallpapers found in folder."))
            return
        self._carousel_pos %= len(files)
        path = files[self._carousel_pos]
        self._carousel_pos += 1
        self._start_apply(path, path.stem)

    def _on_picked(self, path, name, info):
        if path is None:
            self._notify(tr("No file for {name}.").format(name=name))
            return
        # суфікс лише коли погоду реально не вдалось отримати (online is False);
        # None = детермінований вибір без мережі (ручні значення)
        suffix = "  (offline guess)" if info.get("online") is False else ""
        self._start_apply(Path(path), name, suffix)

    def _lock_target(self, desktop_path: Path):
        """Ціль для екрана блокування: mirror=шпалера, library=кадр, skip=None."""
        mode = self.cfg.get("lock_mode", "skip")
        if mode == "mirror":
            return desktop_path
        if mode == "library":
            folder = self._folder()
            name = self.cfg.get("lock_file", "")
            return (folder / name) if (folder and name) else None
        return None

    def _start_apply(self, path: Path, name: str, suffix: str = ""):
        """Запустити встановлення шпалери+lock у воркері (GUI не блокується)."""
        target = self._lock_target(path)
        # анти-churn: не переписувати екран блокування, якщо ціль не змінилась
        key = str(target) if target else f"skip:{bool(self.cfg.get('lock_backup'))}"
        if key == self._last_lock:
            target = _NO_LOCK
        else:
            self._last_lock = key
        self.pool.start(_ApplyTask(path, name, target, dict(self.cfg),
                                   suffix, self.sig))

    def _on_applied(self, path, name, ok, lock_changed, lock_backup, suffix):
        if not ok:
            self._notify(tr("Could not set the wallpaper on this desktop."))
            return
        self.tray.setToolTip(f"{__app_name__}\n{Path(path).name}{suffix}")
        if lock_changed:
            self.cfg["lock_backup"] = lock_backup
            cfg.save(self.cfg)

    def _notify(self, msg: str):
        self.tray.setToolTip(f"{__app_name__}\n{msg}")
        if QSystemTrayIcon.supportsMessages():
            self.tray.showMessage(__app_name__, msg, self.icon, 4000)

    # ---- налаштування ----
    def open_settings(self):
        if getattr(self, "_dlg", None) is not None:
            self._dlg.raise_()
            self._dlg.activateWindow()
            return
        self._dlg = SettingsDialog(self.cfg, self._apply_settings, self._on_language)
        self._dlg.finished.connect(self._on_dialog_closed)
        self._dlg.show()
        self._dlg.raise_()
        self._dlg.activateWindow()

    def _on_dialog_closed(self, _result):
        self._dlg = None

    def _on_language(self, lang: str):
        """Реактивна зміна мови з діалогу: одразу перемалювати меню."""
        _apply_language(lang)
        self._build_menu()

    def _apply_settings(self, new: dict):
        changed = any(new.get(k) != self.cfg.get(k) for k in new)
        if not changed:
            return
        autostart_changed = new.get("autostart") != self.cfg.get("autostart")
        lang_changed = new.get("language") != self.cfg.get("language")
        theme_changed = new.get("theme") != self.cfg.get("theme")
        self.cfg.update(new)
        cfg.save(self.cfg)
        if lang_changed:
            _apply_language(self.cfg.get("language", "auto"))
            self._build_menu()        # перебудувати меню новою мовою
        if theme_changed:
            style.set_pref(self.cfg.get("theme", "auto"))
            style.apply_theme(self.app)
        self.autostartAct.setChecked(bool(self.cfg.get("autostart")))
        if autostart_changed:
            installer.set_autostart(bool(self.cfg.get("autostart")))
        self._carousel_pos = 0
        self._last_lock = None       # нові налаштування → застосувати lock наново
        self._reschedule()
        self.apply()
        # ненав'язливе підтвердження (з тротлінгом, щоб не спамити)
        now = time.monotonic()
        if QSystemTrayIcon.supportsMessages() and now - self._last_apply_note > 2.0:
            self._last_apply_note = now
            self.tray.showMessage(__app_name__, tr("Settings applied"),
                                  self.icon, 2500)

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
                tr("Wallpapers copied to:\n{dest}\n\nConfig: {config}").format(
                    dest=dest, config=report["config"]))
        else:
            QMessageBox.warning(
                None, __app_name__,
                tr("Could not find wallpapers to copy. Put the 48 PNGs next to "
                   "the app or pick the folder in Settings."))


def run_gui() -> int:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    # Прив'язка до .desktop (під Wayland вікно бере іконку звідти).
    app.setDesktopFileName(ICON_NAME)
    app.setWindowIcon(make_icon())         # іконка у заголовку вікон / панелі
    app.setQuitOnLastWindowClosed(False)   # закриття вікна не завершує застосунок
    style.set_pref(cfg.load().get("theme", "auto"))
    style.apply_theme(app)                 # тема за вибором/системою

    # один екземпляр: другий запуск показує налаштування першому й виходить
    if single_instance.already_running():
        return 0

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

    server = single_instance.InstanceServer()
    ctrl = Controller(app)
    server.activated.connect(ctrl.open_settings)   # другий запуск → показати вікно
    app._instance_server = server
    app._controller = ctrl              # зберегти посилання, щоб трей не зник
    return app.exec()
