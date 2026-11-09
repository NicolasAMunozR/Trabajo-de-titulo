# Hardware real emulado (cámara, GazePoint, EyeTribe) y extensiones del OrchestratorCore.
import json
import socket
import threading
import time

import numpy as np
import pytest

import hardware.camera_sensor as camera_module
from app.settings_store import SettingsStore
from contracts.i_eye_tracker import IEyeTracker
from contracts.i_gesture_plugin import IGesturePlugin
from hardware.camera_sensor import CameraSensorPlugin
from orchestrator.orchestrator_core import OrchestratorCore


class FakeCapture:
    def __init__(self, index, backend=None):
        self.index, self.opened, self.props = index, index >= 0, {}

    def isOpened(self):
        return self.opened

    def set(self, prop, value):
        self.props[prop] = value

    def read(self):
        time.sleep(0.005)
        return True, np.full((48, 64, 3), 7, np.uint8)

    def release(self):
        self.opened = False


@pytest.mark.parametrize("threaded", [True, False])
def test_camera_sensor_publishes_latest_frame(monkeypatch, threaded):
    monkeypatch.setattr(camera_module.cv2, "VideoCapture", FakeCapture)
    sensor = CameraSensorPlugin()
    assert sensor.initialize({"camera_index": 2, "width": 64, "height": 48, "threaded": threaded})
    deadline = time.time() + 2
    while sensor.capture_frame() is None and time.time() < deadline:
        time.sleep(0.01)
    result = sensor.execute()
    assert result["frame_available"] and result["width"] == 64 and sensor.camera_index == 2
    assert sensor.get_latest_frame().shape == (48, 64, 3)
    sensor.release()
    assert sensor.capture_frame() is None


def test_camera_sensor_fails_cleanly_when_camera_missing(monkeypatch):
    monkeypatch.setattr(camera_module.cv2, "VideoCapture", lambda *a: FakeCapture(-1))
    sensor = CameraSensorPlugin()
    assert sensor.initialize({"camera_index": 5}) is False
    assert sensor.execute()["frame_available"] is False


def _serve_once(handler):
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)

    def run():
        conn, _ = server.accept()
        with conn:
            handler(conn)
        server.close()
    threading.Thread(target=run, daemon=True).start()
    return server.getsockname()[1]


def _wait_gaze(tracker, timeout=3.0):
    deadline = time.time() + timeout
    while tracker.get_gaze_point() is None and time.time() < deadline:
        time.sleep(0.02)
    return tracker.get_gaze_point()


@pytest.fixture
def orchestrator(monkeypatch, tmp_path):
    monkeypatch.setenv("EDDIE_DEVICE_MODE", "sim")
    settings = SettingsStore(tmp_path / "s.json")
    orch = OrchestratorCore("config/plugins.json", settings.plugin_overrides())
    assert orch.initialize()
    yield orch
    orch.release()


def test_overrides_and_device_factory_apply_to_declared_plugins(orchestrator):
    sensor = orchestrator.get_plugin("TextCamera")
    assert type(sensor).__name__ == "MockCameraSensor"
    assert orchestrator.get_plugin("GestureCamera").camera_index == 1


def test_settings_store_persists_and_builds_overrides(tmp_path):
    store = SettingsStore(tmp_path / "s.json")
    store["cameraTextIndex"] = 2
    store["deviceMode"] = "sim"
    store.save()
    again = SettingsStore(tmp_path / "s.json")
    overrides = again.plugin_overrides()
    assert overrides["TextCamera"]["config"]["camera_index"] == 2
    assert overrides["TextCamera"]["device_mode"] == "sim"
    with pytest.raises(KeyError):
        again["claveInventada"] = 1
    again.reset()
    assert again["cameraTextIndex"] == 0


