# Dispositivos simulados para DeviceFactory (EDDIE_DEVICE_MODE=sim).
# MockCameraSensor genera una escena sintética y EyeTrackerMock usa el cursor como mirada.
# Todos los resultados incluyen "simulated": True para distinguirlos de los reales.
import logging
import math
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from contracts.i_camera_sensor import CameraFrame, ICameraSensor
from contracts.i_eye_tracker import GazePoint, IEyeTracker

logger = logging.getLogger(__name__)

_PAGE_LINES = [
    "EDDIE: Empowering Digital Paper",
    "with Interactive Enhancements.",
    "La lectura aumentada enriquece el",
    "material impreso con definiciones,",
    "traducciones y contenido digital.",
    "El lector resalta una palabra y",
    "el sistema la reconoce con OCR.",
]


def _page_scene(width: int, height: int, t: float, highlight: bool) -> np.ndarray:
    frame = np.full((height, width, 3), 235, np.uint8)
    margin = int(width * 0.08)
    cv2.rectangle(frame, (margin, int(height * 0.06)), (width - margin, int(height * 0.94)),
                  (250, 250, 250), -1)
    scale = width / 640 * 0.75
    line_h = int(height / (len(_PAGE_LINES) + 3))
    for index, line in enumerate(_PAGE_LINES):
        y = int(height * 0.18) + index * line_h
        if highlight and index == 2:
            (tw, th), _ = cv2.getTextSize("aumentada", cv2.FONT_HERSHEY_SIMPLEX, scale, 2)
            x0 = margin + 20 + cv2.getTextSize("La lectura ", cv2.FONT_HERSHEY_SIMPLEX, scale, 2)[0][0]
            cv2.rectangle(frame, (x0 - 6, y - th - 8), (x0 + tw + 6, y + 10), (0, 230, 255), -1)
        cv2.putText(frame, line, (margin + 20, y), cv2.FONT_HERSHEY_SIMPLEX, scale, (20, 20, 20), 2,
                    cv2.LINE_AA)
    # La cámara del montaje original está invertida (OCRProcess rota 180°)
    return cv2.rotate(frame, cv2.ROTATE_180)


def _pen_scene(width: int, height: int, t: float) -> np.ndarray:
    frame = np.full((height, width, 3), 25, np.uint8)
    cx = int(width / 2 + width * 0.3 * math.cos(t * 0.8))
    cy = int(height / 2 + height * 0.3 * math.sin(t * 1.1))
    visible = (int(t) % 6) != 5           # el lápiz "desaparece" 1 s de cada 6 (suelta el clic)
    if visible:
        cv2.circle(frame, (cx, cy), max(8, width // 60), (40, 40, 255), -1)
    return frame


class MockCameraSensor(ICameraSensor):
    # Cámara simulada que cumple el mismo contrato ICameraSensor.

    def __init__(self) -> None:
        self._latest_frame: Optional[CameraFrame] = None
        self._capture: Optional[cv2.VideoCapture] = None
        self._still: Optional[np.ndarray] = None
        self._scene = "page"
        self._size = (640, 480)
        self._t0 = time.time()
        self._camera_index = 0
        self._initialized = False

    @property
    def name(self) -> str:
        return "MockCameraSensor"

    def initialize(self, config: dict) -> bool:
        self._size = (int(config.get("width", 640)), int(config.get("height", 480)))
        self._scene = config.get("scene", "page")
        self._camera_index = int(config.get("camera_index", 0))
        source = config.get("source")
        if source:
            path = Path(source)
            if not path.exists():
                logger.error("MockCameraSensor: no existe la fuente %s", path)
                return False
            if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp"):
                self._still = cv2.resize(cv2.imread(str(path)), self._size)
            else:
                self._capture = cv2.VideoCapture(str(path))
        self._t0 = time.time()
        if self._still is None and self._capture is None and self._scene != "pen":
            # La hoja simulada es estática: se dibuja aquí y no en el primer ciclo
            # (antes ese primer ciclo tardaba ~20 ms y superaba el umbral de 8,3 ms).
            self._still = _page_scene(self._size[0], self._size[1], 0.0, highlight=True)
        self._initialized = True
        return True

    def execute(self) -> dict:
        frame = self.capture_frame()
        return {
            "sensor": self.instance_name,
            "frame_available": frame is not None,
            "width": self._size[0],
            "height": self._size[1],
            "simulated": True,
        }

    def capture_frame(self) -> Optional[CameraFrame]:
        width, height = self._size
        t = time.time() - self._t0
        if self._still is not None:
            frame = self._still.copy()
        elif self._capture is not None:
            ok, frame = self._capture.read()
            if not ok:
                self._capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self._capture.read()
            if not ok:
                frame = None
        elif self._scene == "pen":
            frame = _pen_scene(width, height, t)
        else:                                             # la hoja es estática: se dibuja una vez
            self._still = _page_scene(width, height, t, highlight=True)
            frame = self._still.copy()
        self._latest_frame = frame
        return frame

    def get_latest_frame(self) -> Optional[CameraFrame]:
        return self._latest_frame

    @property
    def camera_index(self) -> int:
        return self._camera_index

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._latest_frame = None
        self._initialized = False


class EyeTrackerMock(IEyeTracker):
    # Mirada simulada: cursor del sistema (F09) o trayectoria sintética de lectura.

    def __init__(self) -> None:
        self._gaze: Optional[GazePoint] = None
        self._screen = (1920, 1080)
        self._source = "mouse"
        self._t0 = time.time()
        self._initialized = False

    @property
    def name(self) -> str:
        return "EyeTrackerMock"

    def initialize(self, config: dict) -> bool:
        self._screen = (int(config.get("screen_width", 1920)), int(config.get("screen_height", 1080)))
        self._source = config.get("source", "mouse")
        self._t0 = time.time()
        self._initialized = True
        return True

    def execute(self) -> dict:
        now = time.time()
        x = y = None
        if self._source == "mouse":
            from hardware.os_mouse import os_mouse
            mouse = os_mouse()
            if mouse.available:
                px, py = mouse.position()
                x, y = px / self._screen[0], py / self._screen[1]
        if x is None:
            t = now - self._t0
            x = 0.2 + 0.6 * ((t * 0.25) % 1.0)              # barrido de lectura izquierda→derecha
            y = 0.2 + 0.08 * (int(t * 0.25) % 8)
        x, y = min(max(x, 0.0), 1.0), min(max(y, 0.0), 1.0)
        self._gaze = GazePoint(x=x, y=y, timestamp=now, is_fixation=True)
        return {"backend": "mock", "connected": True, "gaze": self._gaze, "latency_ms": 0.0,
                "simulated": True}

    def get_gaze_point(self) -> Optional[GazePoint]:
        return self._gaze

    def is_connected(self) -> bool:
        return self._initialized

    def get_latency_ms(self) -> float:
        return 0.0

    def release(self) -> None:
        self._initialized = False
