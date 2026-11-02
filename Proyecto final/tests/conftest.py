"""Fixtures compartidas: PDF de prueba, frames sintéticos y un servidor LLM falso."""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import cv2
import numpy as np
import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# QtWebEngine (navegador de videos/imágenes) no corre como root sin esta opción en contenedores de CI.
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")


@pytest.fixture
def sample_pdf(tmp_path) -> Path:
    path = tmp_path / "libro.pdf"
    document = pymupdf.open()
    for number in range(1, 4):
        page = document.new_page()
        page.insert_text((72, 72), f"Capitulo {number}: lectura aumentada")
        page.insert_text((72, 100), "EDDIE proyecta definiciones sobre el papel")
    document[1].insert_text((72, 140), "homografia")
    document.save(path)
    document.close()
    return path


def blank_page(width: int = 640, height: int = 480) -> np.ndarray:
    return np.full((height, width, 3), 245, np.uint8)


@pytest.fixture
def frames() -> dict:
    """Frames de cámara con las marcas físicas que detecta BibliotecaConsistencia."""
    bookmark = blank_page()
    cv2.rectangle(bookmark, (50, 50), (130, 120), (200, 120, 0), -1)        # azul (H≈100)
    comment = blank_page()
    cv2.rectangle(comment, (300, 200), (500, 350), (0, 200, 255), -1)       # nota amarilla/naranja
    figures = blank_page()
    cv2.circle(figures, (200, 240), 60, (200, 0, 220), 4)                   # magenta
    cv2.rectangle(figures, (380, 120), (560, 300), (200, 0, 220), 4)
    highlight = blank_page()
    cv2.putText(highlight, "palabra", (220, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (10, 10, 10), 3)
    cv2.rectangle(highlight, (200, 205), (400, 265), (0, 230, 255), -1)
    cv2.putText(highlight, "palabra", (220, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (10, 10, 10), 3)
    pen = np.full((480, 640, 3), 25, np.uint8)
    cv2.circle(pen, (320, 200), 12, (40, 40, 255), -1)
    return {"bookmark": bookmark, "comment": comment, "figures": figures, "highlight": highlight,
            "empty": blank_page(), "pen": pen, "dark": np.full((480, 640, 3), 25, np.uint8)}


class _FakeLLM(BaseHTTPRequestHandler):
    requests: list = []
    status = 200

    def log_message(self, *args) -> None:
        pass

    def _reply(self, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        _FakeLLM.requests.append({"path": self.path, "headers": dict(self.headers), "body": data})
        if _FakeLLM.status != 200:
            body = json.dumps({"error": {"code": _FakeLLM.status, "message": "fake error"}}).encode()
            self.send_response(_FakeLLM.status)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        text = self._answer(json.dumps(data, ensure_ascii=False))
        self._reply({"candidates": [{"content": {"role": "model", "parts": [{"text": text}]},
                                     "finishReason": "STOP"}]})

    @staticmethod
    def _answer(prompt: str) -> str:
        if "enciclopedia" in prompt:
            return "Primer párrafo sobre el término.\n\nSegundo párrafo con más detalle."
        if "definiciones" in prompt:
            return "(sustantivo) Primera definición.\n(verbo) Segunda definición."
        if "Traduce" in prompt:
            return "augmented reading"
        if "YouTube" in prompt:
            return "lectura aumentada explicación"
        if "imagen" in prompt:
            return "Libro abierto"
        return "respuesta"


@pytest.fixture
def fake_llm():
    _FakeLLM.requests = []
    _FakeLLM.status = 200
    server = HTTPServer(("127.0.0.1", 0), _FakeLLM)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}", _FakeLLM.requests
    server.shutdown()


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtCore import QCoreApplication, Qt
    from PySide6.QtWidgets import QApplication
    from ui.form_builder import apply_light_theme, load_fonts
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication.instance() or QApplication([])
    apply_light_theme(app)
    load_fonts()
    return app
