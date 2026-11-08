"""Pruebas de los plugins que reemplazan los módulos C# de EDDIE-2023."""
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
from hardware.eye_tracker import EyeTrackerPlugin
from hardware.mock_devices import EyeTrackerMock, MockCameraSensor
from orchestrator.device_factory import DeviceFactory
from plugins.consistency_plugin import ConsistencyPlugin
from plugins.gaze_session_plugin import GazeSessionPlugin
from plugins.gestures.detectors import ColorPenPlugin, HandSkinPlugin, MousePlugin
from plugins.image_processor_plugin import ImageProcessorPlugin
from plugins.llm_search_plugin import LLMSearchPlugin
from plugins.speech_plugin import SpeechPlugin


class StaticSensor(MockCameraSensor):
    def __init__(self, frame):
        super().__init__()
        self.frame = frame

    def capture_frame(self):
        self._latest_frame = self.frame
        return self.frame


# ---------------------------------------------------------------- contratos
def test_every_plugin_implements_its_single_contract():
    assert issubclass(ImageProcessorPlugin, IImageProcessor)
    assert all(issubclass(c, IGesturePlugin) for c in (ColorPenPlugin, HandSkinPlugin, MousePlugin))
    assert issubclass(ConsistencyPlugin, IConsistencyProvider)
    assert issubclass(EyeTrackerPlugin, IEyeTracker) and issubclass(EyeTrackerMock, IEyeTracker)
    assert issubclass(LLMSearchPlugin, IWebSearchProvider)


# ---------------------------------------------------------------- OCR / ColorRecognition
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
    """El resaltado toca letras de las palabras vecinas: no deben aparecer como "1 aumentada e"."""
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


def _skin_frame_top_left() -> np.ndarray:
    frame = np.full((480, 640, 3), 30, np.uint8)
    cv2.ellipse(frame, (140, 110), (60, 80), 0, 0, 360, (120, 160, 220), -1)   # mano arriba a la izquierda
    cv2.rectangle(frame, (590, 440), (610, 460), (255, 0, 0), -1)              # marca azul abajo a la derecha
    return frame


@pytest.mark.parametrize("cls", [HandSkinPlugin, ColorPenPlugin])
def test_gesture_preview_keeps_camera_orientation_by_default(cls):
    """Regresión: la vista de calibración de Hand Skin salía rotada 180° respecto de la cámara."""
    frame = _skin_frame_top_left()
    cv2.circle(frame, (140, 110), 10, (40, 40, 255), -1)            # punta luminosa para Color Pen
    plugin = _gesture(cls, frame, processing_scale=1.0)
    out = plugin.execute()
    assert out["gesture"] == "point"
    assert out["sensor_x"] < 320 and out["sensor_y"] < 240          # sigue arriba a la izquierda
    preview = plugin.get_preview_frame()
    assert preview.shape == frame.shape
    assert preview[450, 600].tolist() == [255, 0, 0]                 # la marca sigue abajo a la derecha


def test_rotate_180_is_optional_and_shared_by_preview_coordinates_and_capture():
    frame = _skin_frame_top_left()
    plugin = _gesture(HandSkinPlugin, frame, processing_scale=1.0, rotate_180=True)
    out = plugin.execute()
    assert out["sensor_x"] > 320 and out["sensor_y"] > 240          # cámara montada invertida
    assert plugin.get_preview_frame()[480 - 1 - 450, 640 - 1 - 600].tolist() == [255, 0, 0]
    crop = plugin.capture_selection()
    assert crop.shape == frame.shape and crop[480 - 1 - 450, 640 - 1 - 600].tolist() == [255, 0, 0]
    plugin.set_rotate_180(False)
    plugin._last_processed = 0
    assert plugin.execute()["sensor_y"] < 240


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


def test_successive_saves_keep_every_annotation_on_disk(sample_pdf, frames):
    """Regresión H-02: con saveIncr() el segundo guardado dañaba el PDF y se perdían los cambios previos."""
    plugin = _consistency(sample_pdf)
    assert plugin.add_highlight(Annotation(1, 0.1, 0.1, 0.5, 0.15, "highlight", "lectura"))
    plugin.add_bookmark("Introducción", 1)
    assert plugin.sync_comments_from_frame(frames["comment"], 2) == 1
    assert plugin.sync_figures_from_frame(frames["figures"], 3) == 2
    plugin.release()
    with pymupdf.open(sample_pdf) as document:
        assert not document.is_repaired
        assert [len(list(page.annots())) for page in document] == [1, 1, 2]
        assert document.get_toc() == [[1, "Introducción", 1]]


def test_locked_pdf_reports_a_clear_error_and_keeps_working(sample_pdf, monkeypatch):
    """Si el PDF está bloqueado por otro programa (Windows), se informa y el plugin sigue utilizable."""
    from pathlib import Path
    plugin = _consistency(sample_pdf)

    def locked(self, target):
        raise PermissionError("archivo en uso")

    monkeypatch.setattr(Path, "replace", locked)
    monkeypatch.setattr("plugins.consistency_plugin.time.sleep", lambda s: None)
    with pytest.raises(RuntimeError, match="otro programa"):
        plugin.add_bookmark("Introducción", 1)
    monkeypatch.undo()
    assert plugin.get_bookmarks() == []                       # el estado coincide con el archivo en disco
    plugin.add_bookmark("Introducción", 1)
    assert plugin.get_bookmarks() == ["Introducción Pag.1"]
    assert not (sample_pdf.parent / (sample_pdf.name + ".tmp")).exists()


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


def test_gemini_answers_every_service(fake_llm):
    url, requests = fake_llm
    plugin = _llm(url)
    assert "Segundo párrafo" in plugin.search_encyclopedia("lectura").content
    assert len(plugin.search_definition("leer").content.splitlines()) == 2
    assert plugin.translate_text("lectura aumentada", "en").content == "augmented reading"
    video = plugin.search_video("lectura")
    assert video.url.startswith("https://m.youtube.com/results?search_query=")
    image = plugin.search_image(b"\xff\xd8fakejpeg")
    assert image.content == "Libro abierto" and "ecosia" in image.url
    assert all(r["path"] == "/v1beta/models/gemini-2.5-flash:generateContent" for r in requests)
    headers = {k.lower(): v for k, v in requests[0]["headers"].items()}
    assert headers["x-goog-api-key"] == "test-key"
    body = requests[-1]["body"]
    assert body["generationConfig"]["thinkingConfig"]["thinkingBudget"] == 0
    assert body["contents"][0]["parts"][0]["inline_data"]["mime_type"] == "image/jpeg"
    assert "EDDIE" in body["systemInstruction"]["parts"][0]["text"]


def test_gemini_rate_limit_and_errors_are_readable(fake_llm):
    url, _ = fake_llm
    plugin = _llm(url, retries=0)
    from tests.conftest import _FakeLLM
    _FakeLLM.status = 429
    with pytest.raises(RuntimeError, match="límite de la capa gratuita"):
        plugin.search_definition("palabra")
    _FakeLLM.status = 500
    with pytest.raises(RuntimeError, match="HTTP 500"):
        plugin.search_definition("palabra")
    assert plugin.execute()["last_error"]


def test_llm_requires_term_and_reports_unreachable_server():
    plugin = _llm("http://127.0.0.1:9")
    with pytest.raises(ValueError):
        plugin.search_definition("   ")
    with pytest.raises(RuntimeError, match="No se pudo contactar"):
        plugin.search_definition("palabra")


def test_gemini_key_from_secrets_file_or_missing(monkeypatch, tmp_path):
    from plugins import llm_search_plugin as module
    monkeypatch.delenv("EDDIE_TEST_KEY", raising=False)
    monkeypatch.setattr(module, "SECRETS_FILE", tmp_path / "secrets.json")
    assert LLMSearchPlugin().initialize({"api_key_env": "EDDIE_TEST_KEY"}) is False
    (tmp_path / "secrets.json").write_text('{"EDDIE_TEST_KEY": "abc"}', encoding="utf-8")
    plugin = LLMSearchPlugin()
    assert plugin.initialize({"api_key_env": "EDDIE_TEST_KEY"}) and plugin._api_key == "abc"


# ---------------------------------------------------------------- eye tracking
def test_eye_tracker_parses_all_protocols():
    tracker = EyeTrackerPlugin()
    tracker._store_message('<REC TIME="1.2" FPOGX="0.25" FPOGY="0.75" FPOGV="1" />')     # GazePoint
    gaze = tracker.get_gaze_point()
    assert (gaze.x, gaze.y, gaze.is_fixation) == (0.25, 0.75, True)
    tracker._store_message("960,540,1700000000000")                                     # GazeCloud
    assert tracker.get_gaze_point().x == pytest.approx(0.5)
    tracker._store_message(json.dumps({"values": {"frame": {"avg": {"x": 10, "y": 10},
                                                            "smoothed": {"x": 480, "y": 270}}}}))   # EyeTribe
    assert tracker.get_gaze_point().x == pytest.approx(0.25)
    tracker._store_message('<REC FPOGX="0.5" FPOGY="0.5" FPOGV="0" />')                  # muestra inválida
    assert tracker.get_gaze_point().x == pytest.approx(0.25)


def test_gaze_session_writes_csv(tmp_path):
    session = GazeSessionPlugin()
    session.initialize({})
    csv = session.configure_session("Tracker", False, True, str(tmp_path), "sesion", (0, 0, 1000, 500))
    session.consume_cycle_results({"Tracker": {"gaze": GazePoint(0.5, 0.5, 123.0)}})
    session.register_click()
    session.consume_cycle_results({"Tracker": {"gaze": GazePoint(0.1, 0.2, 124.0)}})
    session.release()
    lines = open(csv, encoding="utf-8").read().splitlines()
    assert lines == ["500, 250, 123.0,0", "100, 100, 124.0,1"]


# ---------------------------------------------------------------- HAL / voz
def test_device_factory_switches_to_simulated(monkeypatch):
    conf = {"name": "TextCamera", "class": "hardware.camera_sensor.CameraSensorPlugin",
            "simulated_class": "hardware.mock_devices.MockCameraSensor"}
    monkeypatch.setenv("EDDIE_DEVICE_MODE", "real")
    assert DeviceFactory.resolve(conf) == conf["class"]
    monkeypatch.setenv("EDDIE_DEVICE_MODE", "sim")
    assert DeviceFactory.resolve(conf) == conf["simulated_class"]
    assert DeviceFactory.resolve({**conf, "device_mode": "real"}) == conf["class"]


def test_mock_page_scene_is_ready_after_initialize():
    """La hoja simulada se dibuja en initialize(): el primer ciclo ya no tiene un pico de ~20 ms."""
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


def test_voice_command_matching_ignores_accents():
    speech = SpeechPlugin()
    commands = ["Buscar Definición", "Cerrar Video"]
    assert speech.match_command("buscar definicion por favor", commands) == "Buscar Definición"
    assert speech.match_command("hola", commands) is None


# ---------------------------------------------------------------- PDF dañado (caso real: bytes binarios
# reemplazados por U+FFFD al copiar el archivo como texto → PyMuPDF lo "repara" con 0 páginas)
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
    """Reproduce el daño real: un PDF comprimido copiado como texto UTF-8 (bytes → U+FFFD)."""
    import pymupdf
    with pymupdf.open(pdf_path) as document:
        data = document.tobytes(deflate=True, garbage=3, use_objstms=1)
    return data.decode("utf-8", "replace").encode("utf-8")
