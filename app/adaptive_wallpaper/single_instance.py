"""Один екземпляр застосунку на користувача (QLocalServer).

Якщо застосунок уже працює — другий запуск надсилає сигнал «показати
налаштування» першому й одразу завершується, тож кількох трей-іконок/процесів
не буде.
"""
from __future__ import annotations

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

_KEY = "adaptive-wallpaper.single-instance"


def already_running(timeout_ms: int = 300) -> bool:
    """True, якщо інший екземпляр уже слухає (і ми йому сигналимо «show»)."""
    sock = QLocalSocket()
    sock.connectToServer(_KEY)
    if sock.waitForConnected(timeout_ms):
        sock.write(b"show")
        sock.waitForBytesWritten(timeout_ms)
        sock.disconnectFromServer()
        return True
    return False


class InstanceServer(QObject):
    """Слухає підключення других запусків; емітить activated на «show»."""

    activated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._srv = QLocalServer(self)
        self._srv.newConnection.connect(self._on_conn)
        # Спершу пробуємо просто слухати; лише якщо сокет зайнятий «мертвим»
        # екземпляром (already_running() уже підтвердив, що живого немає) —
        # прибираємо його й слухаємо знову. Не чіпаємо живий перший екземпляр.
        if not self._srv.listen(_KEY):
            QLocalServer.removeServer(_KEY)
            self._srv.listen(_KEY)

    def _on_conn(self):
        c = self._srv.nextPendingConnection()
        if c is None:
            return

        def handle():
            c.readAll()                    # прочитати й відкинути payload
            c.disconnectFromServer()
            QTimer.singleShot(0, self.activated.emit)  # поза callback сокета

        c.readyRead.connect(handle)
        c.disconnected.connect(c.deleteLater)
