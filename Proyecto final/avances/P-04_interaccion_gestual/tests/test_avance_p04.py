# Pruebas del avance P-04: los tres plug-ins gestuales comparten la cámara gestual declarada.
import cv2
import numpy as np
import pytest

from contracts.i_gesture_plugin import IGesturePlugin
from orchestrator.orchestrator_core import OrchestratorCore


@pytest.fixture
def orch(monkeypatch):
    monkeypatch.setenv("EDDIE_DEVICE_MODE", "sim")
    core = OrchestratorCore("config/plugins.json")
    assert core.initialize()
    yield core
    core.release()


def test_plugins_gestuales_declarados_aparecen_por_contrato(orch):
    names = [p["name"] for p in orch.declared_plugins(IGesturePlugin)]
    assert names == ["ColorPenRecognition", "HandSkinRecognition", "MouseRecognition"]
    assert len(orch.get_plugins_by_contract(IGesturePlugin)) == 3


def test_reiniciar_la_camara_gestual_reconecta_los_plugins(orch):
    old = orch.get_plugin("GestureCamera")
    assert orch.restart_plugin("GestureCamera", {"camera_index": 3})
    new = orch.get_plugin("GestureCamera")
    assert new is not old and new.camera_index == 3
    for name in ("ColorPenRecognition", "HandSkinRecognition", "MouseRecognition"):
        assert orch.get_plugin(name)._camera_sensor is new


def test_lapiz_simulado_mueve_las_coordenadas_del_sensor(orch):
    import time
    pen = orch.get_plugin("ColorPenRecognition")
    pen.set_recognition_active(True)
    seen = set()
    for _ in range(30):
        out = orch.execute_cycle()["ColorPenRecognition"]
        if out.get("processed"):
            seen.add((out["sensor_x"], out["sensor_y"]))
        time.sleep(0.07)
    assert len(seen) >= 3                                              # el lápiz se mueve en la escena


@pytest.mark.xfail(strict=True, reason="Hallazgo H-01: Hand Skin rota siempre 180° la imagen (herencia del C#), "
                                       "así la vista de calibración sale al revés con una cámara normal. "
                                       "Corregido en P-07.")
def test_hallazgo_h01_hand_skin_respeta_la_orientacion_de_la_camara():
    from hardware.mock_devices import MockCameraSensor
    from plugins.gestures.detectors import HandSkinPlugin

    class StaticSensor(MockCameraSensor):
        def __init__(self, frame):
            super().__init__()
            self._latest_frame = frame

    frame = np.full((480, 640, 3), 30, np.uint8)
    cv2.ellipse(frame, (140, 110), (60, 80), 0, 0, 360, (120, 160, 220), -1)      # mano arriba a la izquierda
    plugin = HandSkinPlugin()
    plugin.set_camera_sensor(StaticSensor(frame))
    assert plugin.initialize({"max_fps": 0, "processing_scale": 1.0})
    plugin.set_recognition_active(True)
    out = plugin.execute()
    assert out["sensor_y"] < 240                                                  # debería seguir arriba
