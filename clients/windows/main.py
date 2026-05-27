"""Jarvis masaüstü istemcisi (PyQt6).

Platform-bağımsızdır: macOS, Windows ve Linux'ta çalışır. Jarvis API'sine
(Tailscale üzerinden de olabilir) bağlanır, cihaz anahtarıyla token alır ve
sohbet eder. Ağ işleri ayrı bir thread'de yürür; arayüz bloklanmaz.

Çalıştırma:
    JARVIS_API=http://localhost:8000 JARVIS_DEVICE_KEY=... \
        uv run --extra windows python clients/windows/main.py
"""

from __future__ import annotations

import os
import sys

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from jarvis.client import JarvisClient


class ChatWorker(QObject):
    """Ağ çağrısını arka planda yürüten worker."""

    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, client: JarvisClient, message: str) -> None:
        super().__init__()
        self._client = client
        self._message = message

    def run(self) -> None:
        try:
            result = self._client.chat(self._message)
            self.done.emit(result.get("content", ""))
        except Exception as exc:  # noqa: BLE001 — hatayı arayüze ilet
            self.failed.emit(str(exc))


class ChatWindow(QMainWindow):
    """Basit sohbet penceresi."""

    def __init__(self, client: JarvisClient) -> None:
        super().__init__()
        self._client = client
        self._thread: QThread | None = None
        self.setWindowTitle("J.A.R.V.I.S")
        self.resize(620, 520)

        self._log = QTextEdit(readOnly=True)
        self._input = QLineEdit(placeholderText="Bir şey sorun, efendim…")
        self._send = QPushButton("Gönder")

        row = QHBoxLayout()
        row.addWidget(self._input)
        row.addWidget(self._send)
        layout = QVBoxLayout()
        layout.addWidget(self._log)
        layout.addLayout(row)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self._send.clicked.connect(self._on_send)
        self._input.returnPressed.connect(self._on_send)

    def _append(self, who: str, text: str) -> None:
        self._log.append(f"<b>{who}:</b> {text}")

    def _on_send(self) -> None:
        message = self._input.text().strip()
        if not message or self._thread is not None:
            return
        self._append("Siz", message)
        self._input.clear()
        self._set_busy(True)

        self._thread = QThread()
        self._worker = ChatWorker(self._client, message)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._thread.start()

    def _on_done(self, content: str) -> None:
        self._append("Jarvis", content)
        self._teardown()

    def _on_failed(self, detail: str) -> None:
        self._append("Hata", detail)
        self._teardown()

    def _teardown(self) -> None:
        self._set_busy(False)
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
            self._thread = None

    def _set_busy(self, busy: bool) -> None:
        self._send.setEnabled(not busy)
        self._input.setEnabled(not busy)


def main() -> None:
    """Masaüstü istemcisini başlatır."""
    base_url = os.environ.get("JARVIS_API", "http://localhost:8000")
    device_key = os.environ.get("JARVIS_DEVICE_KEY")
    client = JarvisClient(base_url=base_url, device_key=device_key)

    app = QApplication(sys.argv)
    window = ChatWindow(client)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
