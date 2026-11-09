# Hallazgos conocidos en P-06 (código previo a la verificación). Se espera que fallen; P-07 los corrige.
import cv2
import numpy as np
import pymupdf
import pytest

from contracts.i_consistency_provider import Annotation


@pytest.mark.xfail(strict=True, reason="Hallazgo H-01: Hand Skin rota siempre 180° la imagen. Corregido en P-07.")
def test_hallazgo_h01_hand_skin_respeta_la_orientacion_de_la_camara():
    from hardware.mock_devices import MockCameraSensor
    from plugins.gestures.detectors import HandSkinPlugin

    class StaticSensor(MockCameraSensor):
        def __init__(self, frame):
            super().__init__()
            self._latest_frame = frame

    frame = np.full((480, 640, 3), 30, np.uint8)
    cv2.ellipse(frame, (140, 110), (60, 80), 0, 0, 360, (120, 160, 220), -1)
    plugin = HandSkinPlugin()
    plugin.set_camera_sensor(StaticSensor(frame))
    assert plugin.initialize({"max_fps": 0, "processing_scale": 1.0})
    plugin.set_recognition_active(True)
    assert plugin.execute()["sensor_y"] < 240


@pytest.mark.xfail(strict=True, reason="Hallazgo H-02: saveIncr() sucesivos dañan el PDF. Corregido en P-07.")
def test_hallazgo_h02_guardados_sucesivos_conservan_todo(sample_pdf, frames):
    from plugins.consistency_plugin import ConsistencyPlugin
    plugin = ConsistencyPlugin()
    assert plugin.initialize({"pdf_path": str(sample_pdf), "camera_rotated_180": False})
    plugin.add_highlight(Annotation(1, 0.1, 0.1, 0.5, 0.15, "highlight", "lectura"))
    plugin.add_bookmark("Introducción", 1)
    plugin.sync_comments_from_frame(frames["comment"], 2)
    plugin.release()
    with pymupdf.open(sample_pdf) as document:
        assert [len(list(page.annots())) for page in document] == [1, 1, 0]
