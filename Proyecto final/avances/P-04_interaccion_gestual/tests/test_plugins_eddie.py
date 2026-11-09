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
from plugins.gestures.detectors import ColorPenPlugin, HandSkinPlugin, MousePlugin
from plugins.image_processor_plugin import ImageProcessorPlugin
class StaticSensor(MockCameraSensor):
    def __init__(self, frame):
        super().__init__()
        self.frame = frame

    def capture_frame(self):
        self._latest_frame = self.frame
        return self.frame


# ---------------------------------------------------------------- contratos
def test_highlight_region_is_detected_and_cropped(frames):
    plugin = ImageProcessorPlugin()
    plugin.set_camera_sensor(StaticSensor(frames["highlight"]))
    assert plugin.initialize({"rotate_180": False})
    annotated, box = plugin.detect_highlight_region(frames["highlight"])
    assert box is not None
    x, y, w, h = box
    assert 190 <= x <= 210 and 195 <= y <= 215 and w >= 190 and h >= 50
    assert annotated.shape == frames["highlight"].shape


def test_no_highlight_returns_empty_text(frames):
    plugin = ImageProcessorPlugin()
    plugin.set_camera_sensor(StaticSensor(frames["empty"]))
    plugin.initialize({})
    result = plugin.recognize_highlighted_text()
    assert result["box"] is None and result["text"] == ""


@pytest.mark.skipif(os.system("tesseract --version >/dev/null 2>&1") != 0, reason="Tesseract no instalado")
def test_ocr_reads_highlighted_word(frames):
    plugin = ImageProcessorPlugin()
    plugin.set_camera_sensor(StaticSensor(frames["highlight"]))
    plugin.initialize({"rotate_180": False, "ocr_language": "eng"})
    assert "palabra" in plugin.recognize_highlighted_text()["text"].lower()


@pytest.mark.skipif(os.system("tesseract --version >/dev/null 2>&1") != 0
                    and os.system("tesseract --version >NUL 2>&1") != 0, reason="Tesseract no instalado")
def test_ocr_drops_letter_fragments_cut_by_the_highlight():
    # El resaltado toca letras de las palabras vecinas: no deben aparecer como "1 aumentada e".
    camera = MockCameraSensor()
    camera.initialize({"scene": "page"})
    plugin = ImageProcessorPlugin()
    plugin.set_camera_sensor(camera)
    plugin.initialize({"ocr_language": "spa+eng"})
    result = plugin.recognize_highlighted_text()
    assert result["text"].lower() == "aumentada"
    assert result["upright_crop"] is not None


def test_precision_recall_metric():
    plugin = ImageProcessorPlugin()
    plugin._last_detected_words = ["lectura", "aumentada", "ruido"]
    metrics = plugin.get_precision_recall(["lectura", "aumentada"])
    assert metrics["recall"] == 1.0 and metrics["precision"] == pytest.approx(0.6667, abs=1e-3)


# ---------------------------------------------------------------- gestos
def _gesture(cls, frame, **config):
    plugin = cls()
    plugin.set_camera_sensor(StaticSensor(frame))
    plugin._camera_sensor.capture_frame()
    assert plugin.initialize({"max_fps": 0, **config})
    plugin.set_recognition_active(True)
    return plugin


def test_color_pen_finds_pen_center(frames):
    plugin = _gesture(ColorPenPlugin, frames["pen"])
    out = plugin.execute()
    assert out["gesture"] == "point"
    assert abs(out["sensor_x"] - 320) <= 8 and abs(out["sensor_y"] - 200) <= 8
    assert plugin.get_preview_frame() is not None


def test_color_pen_release_captures_selection(frames):
    plugin = _gesture(ColorPenPlugin, frames["pen"])
    plugin.execute()                                     # lápiz visible → clic abajo
    plugin._camera_sensor.frame = frames["dark"]
    plugin._camera_sensor.capture_frame()
    out = plugin.execute()                               # lápiz desaparece → captura automática
    assert out["selection_captured"] is True
    assert plugin.get_last_capture_jpeg()


def test_calibration_maps_sensor_to_application_coordinates(frames):
    plugin = _gesture(ColorPenPlugin, frames["pen"])
    plugin.set_calibration(GestureCalibration(sensor_start_x=0, sensor_end_x=640, app_start_x=0, app_end_x=1280,
                                              sensor_start_y=0, sensor_end_y=480, app_start_y=0, app_end_y=960,
                                              transform_x=True, transform_y=True))
    out = plugin.execute()
    assert abs(out["position_x"] - 640) <= 16 and abs(out["position_y"] - 400) <= 16


def test_inactive_gesture_plugin_does_no_work(frames):
    plugin = _gesture(HandSkinPlugin, frames["pen"])
    plugin.set_recognition_active(False)
    assert plugin.execute() == {"active": False, "plugin": "Hand Skin Recognition"}


def test_hand_skin_detects_skin_blob():
    frame = np.full((480, 640, 3), 30, np.uint8)
    cv2.ellipse(frame, (320, 260), (90, 130), 0, 0, 360, (120, 160, 220), -1)   # tono piel (BGR)
    plugin = _gesture(HandSkinPlugin, frame)
    assert plugin.execute()["gesture"] == "point"


def test_selection_start_end_rectangle(frames):
    plugin = _gesture(ColorPenPlugin, frames["pen"])
    plugin._final = (100, 50)
    plugin.mark_selection_start()
    plugin._final = (300, 150)
    selection = plugin.mark_selection_end()
    assert (selection.x, selection.y, selection.width, selection.height) == (300, 150, 200, 100)


# ---------------------------------------------------------------- consistencia
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


def test_mock_camera_page_scene_contains_highlight():
    camera = MockCameraSensor()
    camera.initialize({"scene": "page"})
    frame = camera.capture_frame()
    plugin = ImageProcessorPlugin()
    plugin.set_camera_sensor(camera)
    plugin.initialize({})
    assert plugin.detect_highlight_region(frame)[1] is not None


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
