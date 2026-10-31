import json
from pathlib import Path
import sys

import numpy as np
import pytest
from contracts.i_eye_tracker import GazePoint
import pymupdf as fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.i_consistency_provider import Annotation
from contracts.i_camera_sensor import CameraFrame, ICameraSensor
from contracts.i_gesture_plugin import GestureResult
from hardware.camera_sensor import CameraSensorPlugin
from hardware.eye_tracker import EyeTrackerPlugin
import plugins.image_processor_plugin as plugin_module
from plugins.consistency_plugin import ConsistencyPlugin
from plugins.gesture_plugin import GesturePlugin
from plugins.image_processor_plugin import ImageProcessorPlugin
from plugins.web_search_plugin import WebSearchPlugin
from orchestrator.plugin_loader import PluginLoader


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeCameraSensor(ICameraSensor):
    def __init__(self, frame: CameraFrame | None):
        self.frame = frame
        self.latest_frame = None

    @property
    def name(self):
        return "FakeCameraSensor"

    def initialize(self, config):
        return True

    def execute(self):
        self.latest_frame = self.frame
        return {"frame_available": self.latest_frame is not None}

    def capture_frame(self):
        self.latest_frame = self.frame
        return self.latest_frame

    def get_latest_frame(self):
        return self.latest_frame

    def release(self):
        self.latest_frame = None


def test_runtime_plugin_config_does_not_enable_simulation():
    config = json.loads((PROJECT_ROOT / "config" / "plugins.json").read_text())
    assert all("use_mock" not in plugin.get("config", {}) for plugin in config["plugins"])
    eye_tracker = next(plugin for plugin in config["plugins"] if plugin["name"] == "EyeTracker")
    assert eye_tracker["class"] == "hardware.eye_tracker.EyeTrackerPlugin"
    image_processor = next(plugin for plugin in config["plugins"] if plugin["name"] == "ImageProcessor")
    gesture = next(plugin for plugin in config["plugins"] if plugin["name"] == "GesturePlugin")
    assert image_processor["dependencies"]["camera_sensor"] == "CameraSensor"
    assert gesture["dependencies"]["camera_sensor"] == "CameraSensor"
    assert [plugin["name"] for plugin in config["plugins"] if plugin["class"] == "hardware.camera_sensor.CameraSensorPlugin"] == ["CameraSensor"]
    enabled = [plugin for plugin in config["plugins"] if plugin["enabled"]]
    assert len(PluginLoader().load_all(enabled)) == len(enabled)


def test_loader_gives_same_plugin_class_distinct_configured_instance_names():
    loaded = PluginLoader().load_all([
        {
            "name": "CameraSensor",
            "class": "hardware.camera_sensor.CameraSensorPlugin",
            "enabled": True,
        },
        {
            "name": "GestureCameraSensor",
            "class": "hardware.camera_sensor.CameraSensorPlugin",
            "enabled": True,
        },
    ])

    assert [plugin.instance_name for plugin in loaded] == [
        "CameraSensor",
        "GestureCameraSensor",
    ]


def test_image_processor_uses_injected_camera_frame_without_owning_sensor(monkeypatch):
    monkeypatch.setattr(
        "plugins.image_processor_plugin.pytesseract.pytesseract.tesseract_cmd", ""
    )
    monkeypatch.setattr(
        "plugins.image_processor_plugin.pytesseract.get_languages",
        lambda config="": ["eng", "spa"],
    )
    plugin = ImageProcessorPlugin()
    sensor = FakeCameraSensor(np.zeros((32, 32, 3), dtype=np.uint8))
    sensor.capture_frame()
    plugin.set_camera_sensor(sensor)
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    assert plugin.initialize({"tesseract_path": tesseract_path})
    assert plugin_module.pytesseract.pytesseract.tesseract_cmd == tesseract_path
    monkeypatch.setattr(plugin, "detect_text_region", lambda frame: None)
    monkeypatch.setattr(plugin, "preprocess", lambda frame: frame)
    monkeypatch.setattr(plugin, "extract_text_with_regions", lambda frame: {
        "raw_text": "lectura aumentada",
        "text_regions": [{
            "text": "lectura",
            "confidence": 0.95,
            "x": 4,
            "y": 5,
            "width": 12,
            "height": 6,
        }],
    })

    result = plugin.execute()

    assert result["raw_text"] == "lectura aumentada"
    assert result["detected_words"] == ["lectura", "aumentada"]
    assert result["text_regions"][0]["text"] == "lectura"
    assert result["frame_size"] == {"width": 32, "height": 32}
    assert "mock" not in result
    plugin.release()
    assert sensor.get_latest_frame() is not None


def test_ocr_regions_include_word_boxes_and_confidence(monkeypatch):
    plugin = ImageProcessorPlugin()
    plugin._ocr_language = "spa"
    plugin._tesseract_config = ""
    monkeypatch.setattr(
        "plugins.image_processor_plugin.pytesseract.image_to_data",
        lambda *args, **kwargs: {
            "text": ["", "EDDIE"],
            "conf": ["-1", "92"],
            "left": ["0", "20"],
            "top": ["0", "30"],
            "width": ["0", "45"],
            "height": ["0", "12"],
        },
    )

    result = plugin.extract_text_with_regions(np.zeros((64, 64), dtype=np.uint8))

    assert result == {
        "raw_text": "EDDIE",
        "text_regions": [{
            "text": "EDDIE",
            "confidence": pytest.approx(0.92),
            "x": 20,
            "y": 30,
            "width": 45,
            "height": 12,
        }],
    }


def test_image_processor_skips_initialization_when_ocr_language_is_missing(monkeypatch):
    monkeypatch.setattr(
        "plugins.image_processor_plugin.pytesseract.get_languages",
        lambda config="": ["eng"],
    )
    plugin = ImageProcessorPlugin()
    plugin.set_camera_sensor(FakeCameraSensor(np.zeros((32, 32, 3), dtype=np.uint8)))

    assert plugin.initialize({"ocr_language": "spa"}) is False


def test_gesture_plugin_processes_injected_camera_frame(monkeypatch):
    plugin = GesturePlugin()
    sensor = FakeCameraSensor(np.zeros((32, 32, 3), dtype=np.uint8))
    sensor.capture_frame()
    plugin.set_camera_sensor(sensor)
    assert plugin.initialize({})
    monkeypatch.setattr(
        plugin,
        "detect_gesture",
        lambda frame: GestureResult("point", 0.9, 12, 15, True)
    )

    result = plugin.execute()

    assert result["gesture"] == "point"
    assert result["position_x"] == 12
    assert "mock" not in result
    plugin.release()
    assert sensor.get_latest_frame() is not None


def test_camera_sensor_publishes_the_latest_valid_frame(monkeypatch):
    frame = np.zeros((32, 32, 3), dtype=np.uint8)

    class Capture:
        def isOpened(self):
            return True

        def read(self):
            return True, frame

        def release(self):
            pass

    monkeypatch.setattr("hardware.camera_sensor.cv2.VideoCapture", lambda index: Capture())
    sensor = CameraSensorPlugin()
    assert sensor.initialize({"camera_index": 4})
    result = sensor.execute()
    assert result["frame_available"] is True
    assert sensor.get_latest_frame() is frame
    sensor.release()
    assert sensor.get_latest_frame() is None


def test_consistency_plugin_saves_highlight_to_pdf(tmp_path):
    pdf_path = tmp_path / "document.pdf"
    document = fitz.open()
    document.new_page().insert_text((72, 72), "Texto de prueba")
    document.save(pdf_path)
    document.close()

    plugin = ConsistencyPlugin()
    assert plugin.initialize({"pdf_path": str(pdf_path)})
    annotation = Annotation(
        page_number=1,
        x0=0.1,
        y0=0.1,
        x1=0.8,
        y1=0.2,
        annotation_type="highlight",
        content="Texto de prueba"
    )

    assert plugin.add_highlight(annotation)
    assert plugin.execute()["document_loaded"]
    assert len(plugin.get_annotations(1)) == 1
    plugin.release()

    saved_document = fitz.open(pdf_path)
    assert len(list(saved_document[0].annots())) == 1
    saved_document.close()


def test_gaze_and_gesture_click_confirm_mapped_ocr_highlight_in_pdf(tmp_path):
    pdf_path = tmp_path / "calibrated.pdf"
    document = fitz.open()
    document.new_page().insert_text((72, 72), "EDDIE")
    document.save(pdf_path)
    document.close()

    plugin = ConsistencyPlugin()
    assert plugin.initialize({
        "pdf_path": str(pdf_path),
        "spatial_calibration": {
            "camera_page_corners": [
                [0, 0], [1, 0], [1, 1], [0, 1],
            ],
            "gaze_viewport": [0, 0, 1, 1],
        },
    })
    plugin.consume_cycle_results({
        "ImageProcessor": {
            "frame_size": {"width": 100, "height": 100},
            "text_regions": [{
                "text": "EDDIE",
                "confidence": 0.95,
                "x": 20,
                "y": 20,
                "width": 20,
                "height": 10,
            }],
        },
        "EyeTracker": {"gaze": GazePoint(0.3, 0.25, 1.0)},
        "GesturePlugin": {"is_click": True},
    })

    result = plugin.execute()

    assert result["last_sync"]["status"] == "annotated"
    assert result["last_sync"]["text"] == "EDDIE"
    assert result["annotation_count"] == 1
    plugin.release()

    saved_document = fitz.open(pdf_path)
    assert len(list(saved_document[0].annots())) == 1
    annotation = next(saved_document[0].annots())
    assert annotation.info["content"] == "EDDIE"
    saved_document.close()


def test_gesture_click_is_edge_triggered_to_avoid_duplicate_highlights(tmp_path):
    pdf_path = tmp_path / "edge-triggered.pdf"
    document = fitz.open()
    document.new_page()
    document.save(pdf_path)
    document.close()

    plugin = ConsistencyPlugin()
    assert plugin.initialize({
        "pdf_path": str(pdf_path),
        "spatial_calibration": {
            "camera_page_corners": [[0, 0], [1, 0], [1, 1], [0, 1]],
            "gaze_viewport": [0, 0, 1, 1],
        },
    })
    cycle_results = {
        "ImageProcessor": {
            "frame_size": {"width": 100, "height": 100},
            "text_regions": [{
                "text": "uno", "confidence": 0.9,
                "x": 20, "y": 20, "width": 20, "height": 10,
            }],
        },
        "EyeTracker": {"gaze": GazePoint(0.3, 0.25, 1.0)},
        "GesturePlugin": {"is_click": True},
    }
    plugin.consume_cycle_results(cycle_results)
    plugin.consume_cycle_results(cycle_results)

    assert plugin.execute()["annotation_count"] == 1
    plugin.release()


def test_consistency_plugin_rejects_annotations_without_pdf():
    plugin = ConsistencyPlugin()
    assert plugin.initialize({})
    annotation = Annotation(1, 0.1, 0.1, 0.5, 0.2, "highlight")
    with pytest.raises(RuntimeError, match="No hay un PDF cargado"):
        plugin.add_highlight(annotation)


def test_consistency_plugin_does_not_claim_physical_sync_is_implemented():
    plugin = ConsistencyPlugin()
    plugin.initialize({})
    with pytest.raises(NotImplementedError, match="no está implementada"):
        plugin.sync_physical_to_digital(np.zeros((2, 2, 3)), 1)


def test_eye_tracker_parses_and_normalizes_real_device_coordinates():
    plugin = EyeTrackerPlugin()
    plugin._store_message('{"values":{"frame":{"avg":{"x":960,"y":540}}}}')

    point = plugin.get_gaze_point()

    assert point is not None
    assert point.x == pytest.approx(0.5)
    assert point.y == pytest.approx(0.5)


def test_web_search_encyclopedia_uses_live_wikipedia_api(monkeypatch):
    plugin = WebSearchPlugin()
    plugin.initialize({"language": "es"})
    responses = iter([
        {"query": {"search": [{"pageid": 42, "title": "Lectura aumentada"}]}},
        {"query": {"pages": {"42": {
            "title": "Lectura aumentada",
            "extract": "Información real consultada en Wikipedia."
        }}}}
    ])
    monkeypatch.setattr(plugin, "_get_json", lambda url, params: next(responses))

    result = plugin.search_encyclopedia("lectura aumentada")

    assert result.content == "Información real consultada en Wikipedia."
    assert result.url.endswith("/wiki/Lectura_aumentada")


def test_web_search_requires_real_credentials_for_paid_apis():
    plugin = WebSearchPlugin()
    plugin.initialize({})
    with pytest.raises(RuntimeError, match="GOOGLE_VISION_API_KEY"):
        plugin.search_image(b"image bytes")
    with pytest.raises(RuntimeError, match="YOUTUBE_API_KEY"):
        plugin.search_video("lectura aumentada")


def test_translation_uses_service_response_without_local_substitution(monkeypatch):
    plugin = WebSearchPlugin()
    plugin.initialize({"language": "es"})
    monkeypatch.setattr(
        plugin,
        "_get_json",
        lambda url, params: {
            "responseData": {"translatedText": "augmented reading"}
        }
    )

    result = plugin.translate_text("lectura aumentada", "en")

    assert result.content == "augmented reading"
    assert result.source == "translation"
