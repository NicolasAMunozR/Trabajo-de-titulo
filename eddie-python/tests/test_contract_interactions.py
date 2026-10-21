"""Deterministic interaction checks for the non-web plugin contracts."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.i_camera_sensor import CameraFrame, ICameraSensor
from contracts.i_consistency_provider import Annotation
from contracts.i_eye_tracker import GazePoint, IEyeTracker
from contracts.i_gesture_plugin import GestureResult
from contracts.i_image_processor import IImageProcessor
from hardware.eye_tracker import EyeTrackerPlugin
from plugins.consistency_plugin import ConsistencyPlugin
from plugins.gesture_plugin import GesturePlugin
from plugins.image_processor_plugin import ImageProcessorPlugin


class FakeCameraSensor(ICameraSensor):
    def __init__(self, frame: CameraFrame | None) -> None:
        self._frame = frame
        self._latest_frame: CameraFrame | None = None
        self._initialized = False

    @property
    def name(self) -> str:
        return "TestCameraSensor"

    def initialize(self, config: dict) -> bool:
        self._initialized = True
        return True

    def execute(self) -> dict:
        frame = self.capture_frame()
        return {"frame_available": frame is not None}

    def capture_frame(self) -> CameraFrame | None:
        self._latest_frame = self._frame
        return self._frame

    def get_latest_frame(self) -> CameraFrame | None:
        return self._latest_frame

    def release(self) -> None:
        self._initialized = False


def _trace_event(
    trace_file: Path,
    event: str,
    input_id: str,
    output: str,
    trace_started: float,
    event_started: float,
    status: str = "OK",
    error: str | None = None,
) -> None:
    record = {
        "timestamp_s": round(time.perf_counter() - trace_started, 6),
        "event": event,
        "input": input_id,
        "output": output,
        "status": status,
        "latency_ms": round((time.perf_counter() - event_started) * 1000, 3),
    }
    if error is not None:
        record["error"] = error
    with trace_file.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def test_camera_frame_contract_matches_image_and_gesture_inputs(tmp_path, monkeypatch):
    frame = np.zeros((48, 64, 3), dtype=np.uint8)
    sensor = FakeCameraSensor(frame)
    assert sensor.initialize({})
    trace_file = tmp_path / "contract-trace.jsonl"
    trace_started = time.perf_counter()

    event_started = time.perf_counter()
    captured = sensor.capture_frame()
    assert captured is frame
    _trace_event(
        trace_file, "sensor.capture_frame", "sensor-test-01", "frame-test-01",
        trace_started, event_started
    )

    image_processor = ImageProcessorPlugin()
    event_started = time.perf_counter()
    processed = image_processor.preprocess(captured)
    assert processed.shape == frame.shape[:2]
    _trace_event(
        trace_file, "image_processor.preprocess", "frame-test-01", "frame-gray-uint8",
        trace_started, event_started
    )
    monkeypatch.setattr(image_processor, "extract_text", lambda image: "texto de prueba")
    event_started = time.perf_counter()
    recognized_text = image_processor.extract_text(processed)
    assert recognized_text == "texto de prueba"
    _trace_event(
        trace_file, "image_processor.extract_text", "frame-gray-uint8", "text-test-01",
        trace_started, event_started
    )

    gesture_plugin = GesturePlugin()
    event_started = time.perf_counter()
    result = gesture_plugin.detect_gesture(captured)
    assert isinstance(result, GestureResult)
    assert 0.0 <= result.confidence <= 1.0
    _trace_event(
        trace_file, "gesture.detect_gesture", "frame-test-01", "GestureResult",
        trace_started, event_started
    )

    tracker = EyeTrackerPlugin()
    tracker._store_message('{"values":{"frame":{"avg":{"x":960,"y":540}}}}')
    event_started = time.perf_counter()
    gaze = tracker.get_gaze_point()
    assert isinstance(gaze, GazePoint)
    assert 0.0 <= gaze.x <= 1.0 and 0.0 <= gaze.y <= 1.0
    _trace_event(
        trace_file, "eye_tracker.get_gaze_point", "tracker-protocol-sample",
        "GazePoint-normalized", trace_started, event_started
    )

    import pymupdf as fitz

    pdf_path = tmp_path / "trace.pdf"
    document = fitz.open()
    document.new_page().insert_text((72, 72), "Texto de prueba")
    document.save(pdf_path)
    document.close()
    consistency = ConsistencyPlugin()
    assert consistency.initialize({"pdf_path": str(pdf_path)})
    annotation = Annotation(1, 0.1, 0.1, 0.8, 0.2, "highlight", "traza controlada")
    event_started = time.perf_counter()
    assert consistency.add_highlight(annotation)
    _trace_event(
        trace_file, "consistency.add_highlight", "annotation-test-01",
        "pdf-page-1", trace_started, event_started
    )
    assert consistency.get_annotations(1) == [annotation]
    consistency.release()

    events = [json.loads(line) for line in trace_file.read_text(encoding="utf-8").splitlines()]
    assert [event["event"] for event in events] == [
        "sensor.capture_frame",
        "image_processor.preprocess",
        "image_processor.extract_text",
        "gesture.detect_gesture",
        "eye_tracker.get_gaze_point",
        "consistency.add_highlight",
    ]
    assert all(
        {"timestamp_s", "input", "output", "status", "latency_ms"} <= event.keys()
        and event["status"] == "OK"
        and event["latency_ms"] >= 0
        for event in events
    )
    sensor.release()


def test_camera_sensor_returns_none_when_no_sample_exists(tmp_path):
    sensor = FakeCameraSensor(None)
    assert sensor.initialize({})
    trace_file = tmp_path / "sensor-no-sample-trace.jsonl"
    trace_started = time.perf_counter()
    event_started = time.perf_counter()
    assert sensor.capture_frame() is None
    _trace_event(
        trace_file, "sensor.capture_frame", "sensor-test-no-sample", "none",
        trace_started, event_started, status="ERROR", error="no_frame_available"
    )
    record = json.loads(trace_file.read_text(encoding="utf-8").splitlines()[-1])
    assert record["status"] == "ERROR"
    assert record["error"] == "no_frame_available"
    sensor.release()


def test_consistency_contract_exposes_missing_pdf_and_unimplemented_sync():
    plugin = ConsistencyPlugin()
    assert plugin.initialize({})
    annotation = Annotation(1, 0.1, 0.1, 0.8, 0.2, "highlight")
    with pytest.raises(RuntimeError, match="No hay un PDF cargado"):
        plugin.add_highlight(annotation)
    with pytest.raises(NotImplementedError):
        plugin.sync_physical_to_digital(np.zeros((8, 8, 3), dtype=np.uint8), 1)
    plugin.release()


def test_sensor_contract_requires_lifecycle_and_capture_methods():
    with pytest.raises(TypeError):
        ICameraSensor()


def test_image_and_gesture_contracts_accept_camera_frame_types():
    assert issubclass(ImageProcessorPlugin, IImageProcessor)
    assert issubclass(GesturePlugin, ICameraSensor) is False
    assert issubclass(FakeCameraSensor, ICameraSensor)
    assert issubclass(EyeTrackerPlugin, IEyeTracker)
