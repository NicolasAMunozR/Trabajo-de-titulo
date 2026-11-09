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
from hardware.eye_tracker import EyeTrackerPlugin
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


def test_gazepoint_backend_reads_open_gaze_api():
    received = []

    def handler(conn):
        data, deadline = "", time.time() + 2
        while "ENABLE_SEND_DATA" not in data and time.time() < deadline:   # los comandos pueden llegar separados
            data += conn.recv(1024).decode()
        received.append(data)
        conn.sendall(b'<ACK ID="ENABLE_SEND_DATA" STATE="1" />\r\n<REC FPOGX="0.40" FPOGY="0.60" FPOGV="1" />\r\n')
        time.sleep(0.5)
    port = _serve_once(handler)
    tracker = EyeTrackerPlugin()
    assert tracker.initialize({"backend": "gazepoint", "gazepoint_port": port})
    gaze = _wait_gaze(tracker)
    assert (gaze.x, gaze.y) == (0.40, 0.60) and tracker.execute()["backend"] == "gazepoint"
    assert "ENABLE_SEND_POG_FIX" in received[0]
    tracker.release()


def test_eyetribe_backend_reads_push_frames():
    def handler(conn):
        conn.recv(1024)
        frame = {"category": "tracker", "statuscode": 200,
                 "values": {"frame": {"smoothed": {"x": 960, "y": 270}, "fix": True}}}
        conn.sendall((json.dumps(frame) + "\n").encode())
        time.sleep(0.5)
    port = _serve_once(handler)
    tracker = EyeTrackerPlugin()
    assert tracker.initialize({"backend": "eyetribe", "eyetribe_port": port, "screen_width": 1920,
                               "screen_height": 1080})
    gaze = _wait_gaze(tracker)
    assert gaze.x == pytest.approx(0.5) and gaze.y == pytest.approx(0.25) and gaze.is_fixation
    tracker.release()


def test_eye_tracker_without_device_fails_initialization():
    tracker = EyeTrackerPlugin()
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        free_port = probe.getsockname()[1]
    assert tracker.initialize({"backend": "gazepoint", "gazepoint_port": free_port,
                               "connection_timeout_s": 0.3}) is False
    with pytest.raises(ValueError):
        tracker.initialize({"backend": "desconocido"})


# ---------------------------------------------------------------- OrchestratorCore (extensiones)
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


def test_contract_queries_list_declared_plugins(orchestrator):
    gestures = [p["name"] for p in orchestrator.declared_plugins(IGesturePlugin)]
    assert gestures == ["ColorPenRecognition", "HandSkinRecognition", "MouseRecognition"]
    trackers = orchestrator.declared_plugins(IEyeTracker)
    assert {t["name"] for t in trackers} >= {"EyeTracker-GazePoint", "EyeTrackerMock"}
    assert all(t["status"] == "disabled" for t in trackers)
    assert len(orchestrator.get_plugins_by_contract(IGesturePlugin)) == 3


def test_invoke_isolates_failures(orchestrator):
    ok = orchestrator.invoke("ConsistencyProvider", "search_text", "x")
    assert not ok.ok and "PDF" in ok.error
    missing = orchestrator.invoke("NoExiste", "execute")
    assert not missing.ok
    good = orchestrator.invoke("GazeSession", "execute")
    assert good.ok and good.latency_ms >= 0


def test_restart_rebinds_consumers_and_stop_removes_plugin(orchestrator):
    old_sensor = orchestrator.get_plugin("GestureCamera")
    assert orchestrator.restart_plugin("GestureCamera", {"camera_index": 3})
    new_sensor = orchestrator.get_plugin("GestureCamera")
    assert new_sensor is not old_sensor and new_sensor.camera_index == 3
    assert orchestrator.get_plugin("ColorPenRecognition")._camera_sensor is new_sensor
    assert orchestrator.restart_plugin("EyeTrackerMock")
    assert orchestrator.get_plugin("EyeTrackerMock") is not None
    orchestrator.stop_plugin("EyeTrackerMock")
    assert orchestrator.get_plugin("EyeTrackerMock") is None
    assert not orchestrator.restart_plugin("NoDeclarado")


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


def test_gazecloud_server_receives_browser_samples():
    websocket = pytest.importorskip("websocket")
    pytest.importorskip("websockets")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    tracker = EyeTrackerPlugin()
    assert tracker.initialize({"backend": "gazecloud", "gazecloud_port": port})
    client = websocket.create_connection(f"ws://127.0.0.1:{port}")
    client.send("OK")
    client.send(f"960,540,{int(time.time() * 1000)}")
    gaze = _wait_gaze(tracker)
    assert gaze.x == pytest.approx(0.5) and tracker.get_latency_ms() >= 0
    client.close()
    tracker.release()


def test_restarting_a_failed_sensor_revives_its_consumers(monkeypatch, tmp_path):
    monkeypatch.setenv("EDDIE_DEVICE_MODE", "sim")
    orch = OrchestratorCore("config/plugins.json", {"GestureCamera": {"config": {"source": "no-existe.mp4"}}})
    orch.initialize()
    assert orch.get_plugin("GestureCamera") is None and orch.get_plugin("ColorPenRecognition") is None
    assert orch.restart_plugin("GestureCamera", {"source": ""})
    assert orch.get_plugin("ColorPenRecognition") is not None
    orch.release()
