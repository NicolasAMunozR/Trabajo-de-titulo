# Pruebas de los plugins que reemplazan los módulos C# de EDDIE-2023.
import json
import os

import cv2
import numpy as np
import pymupdf
import pytest

from contracts.i_consistency_provider import Annotation, IConsistencyProvider
from contracts.i_eye_tracker import GazePoint, IEyeTracker
from contracts.i_gesture_plugin import GestureCalibration, IGesturePlugin
from contracts.i_image_processor import IImageProcessor
from contracts.i_web_search_provider import IWebSearchProvider
from hardware.mock_devices import EyeTrackerMock, MockCameraSensor
from orchestrator.device_factory import DeviceFactory
from plugins.consistency_plugin import ConsistencyPlugin
class StaticSensor(MockCameraSensor):
    def __init__(self, frame):
        super().__init__()
        self.frame = frame

    def capture_frame(self):
        self._latest_frame = self.frame
        return self.frame


# ---------------------------------------------------------------- contratos
def _gesture(cls, frame, **config):
    plugin = cls()
    plugin.set_camera_sensor(StaticSensor(frame))
    plugin._camera_sensor.capture_frame()
    assert plugin.initialize({"max_fps": 0, **config})
    plugin.set_recognition_active(True)
    return plugin


def _consistency(pdf, **config):
    plugin = ConsistencyPlugin()
    assert plugin.initialize({"pdf_path": str(pdf), "camera_rotated_180": False, **config})
    return plugin


def test_highlight_roundtrip_and_backup(sample_pdf):
    plugin = _consistency(sample_pdf)
    assert plugin.add_highlight(Annotation(2, 0.1, 0.1, 0.5, 0.15, "highlight", "lectura"))
    annotations = plugin.get_annotations(2)
    assert len(annotations) == 1 and annotations[0].content == "lectura"
    assert annotations[0].x0 == pytest.approx(0.1, abs=0.01)
    assert (sample_pdf.parent / (sample_pdf.name + ".bac")).exists()
    plugin.release()
    with pymupdf.open(sample_pdf) as document:
        assert len(list(document[1].annots())) == 1


def test_search_text_returns_pages(sample_pdf):
    plugin = _consistency(sample_pdf)
    assert plugin.search_text("homografia") == [2]
    assert plugin.search_text("CAPITULO") == [1, 2, 3]


def test_bookmarks_add_list_delete(sample_pdf):
    plugin = _consistency(sample_pdf)
    plugin.add_bookmark("Introducción", 1)
    plugin.add_bookmark("Resultados", 3)
    assert plugin.get_bookmarks() == ["Introducción Pag.1", "Resultados Pag.3"]
    assert plugin.delete_bookmark("Resultados Pag.3")
    assert plugin.get_bookmarks() == ["Introducción Pag.1"]
    assert not plugin.delete_bookmark("No existe Pag.9")


def test_physical_bookmark_sync(sample_pdf, frames):
    plugin = _consistency(sample_pdf)
    assert plugin.sync_bookmark_from_frame(frames["bookmark"], 2)
    assert plugin.get_bookmarks() == ["Marcador físico página 2 Pag.2"]
    assert not plugin.sync_bookmark_from_frame(frames["empty"], 2)


def test_physical_comment_sync_and_delete(sample_pdf, frames):
    plugin = _consistency(sample_pdf)
    assert plugin.sync_comments_from_frame(frames["comment"], 1) == 1
    comments = plugin.get_comments()
    assert len(comments) == 1 and comments[0]["page"] == 1
    assert plugin.delete_comment(comments[0]["content"], 1)
    assert plugin.get_comments() == []


def test_physical_figures_become_digital_figures(sample_pdf, frames):
    plugin = _consistency(sample_pdf)
    assert plugin.sync_figures_from_frame(frames["figures"], 1) == 2
    figures = plugin.get_figures(1, (400, 450))
    assert len(figures["rectangulos"]) + len(figures["circulos"]) == 2
    assert all(0 <= f["x"] <= 400 for f in figures["rectangulos"] + figures["circulos"])


def test_missing_pdf_is_reported_not_crashing():
    plugin = ConsistencyPlugin()
    assert plugin.initialize({})
    with pytest.raises(RuntimeError, match="No hay un PDF cargado"):
        plugin.add_highlight(Annotation(1, 0.1, 0.1, 0.8, 0.2, "highlight"))
    with pytest.raises(RuntimeError):
        plugin.get_bookmarks()


# ---------------------------------------------------------------- LLM Gemini (reemplazo de APIs)
def _llm(url, **extra):
    plugin = LLMSearchPlugin()
    assert plugin.initialize({"base_url": url, "api_key": "test-key", **extra})
    return plugin


def test_device_factory_switches_to_simulated(monkeypatch):
    conf = {"name": "TextCamera", "class": "hardware.camera_sensor.CameraSensorPlugin",
            "simulated_class": "hardware.mock_devices.MockCameraSensor"}
    monkeypatch.setenv("EDDIE_DEVICE_MODE", "real")
    assert DeviceFactory.resolve(conf) == conf["class"]
    monkeypatch.setenv("EDDIE_DEVICE_MODE", "sim")
    assert DeviceFactory.resolve(conf) == conf["simulated_class"]
    assert DeviceFactory.resolve({**conf, "device_mode": "real"}) == conf["class"]


def test_mock_page_scene_is_ready_after_initialize():
    # La hoja simulada se dibuja en initialize(): el primer ciclo ya no tiene un pico de ~20 ms.
    camera = MockCameraSensor()
    camera.initialize({"scene": "page"})
    assert camera._still is not None
    import time
    start = time.perf_counter()
    camera.capture_frame()
    assert (time.perf_counter() - start) * 1000 < 8.3


def test_damaged_pdf_is_rejected_with_a_clear_reason(tmp_path, sample_pdf):
    damaged = tmp_path / "danado.pdf"
    damaged.write_bytes(_as_text_copy(sample_pdf))   # como el caso real
    plugin = ConsistencyPlugin()
    assert plugin.initialize({"pdf_path": str(damaged)})          # el plugin sigue vivo, sin documento
    assert plugin.execute()["document_loaded"] is False
    assert "dañado" in plugin.last_load_error
    assert plugin.load_document(str(sample_pdf))
    assert plugin.load_document(str(damaged)) is False             # el PDF anterior se conserva
    assert plugin.get_page_count() > 0 and plugin.get_page_size()[0] > 0
    assert plugin.load_document(str(tmp_path / "no_existe.pdf")) is False
    assert "No existe" in plugin.last_load_error


def _as_text_copy(pdf_path):
    # Reproduce el daño real: un PDF comprimido copiado como texto UTF-8 (bytes → U+FFFD).
    import pymupdf
    with pymupdf.open(pdf_path) as document:
        data = document.tobytes(deflate=True, garbage=3, use_objstms=1)
    return data.decode("utf-8", "replace").encode("utf-8")
