"""Fixtures compartidas del avance (las del servidor LLM falso llegan en P-06)."""
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


