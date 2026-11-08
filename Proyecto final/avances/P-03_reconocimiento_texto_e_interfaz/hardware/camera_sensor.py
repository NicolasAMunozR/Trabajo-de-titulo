"""OpenCV adapter implementing the shared camera sensor contract.

Reemplaza la captura de Emgu.CV (VideoCapture + evento ImageGrabbed) del C#.
Un hilo de captura lee la cámara continuamente; capture_frame() solo toma el
último frame disponible, de modo que un ciclo del orquestador nunca queda
bloqueado esperando a la cámara (presupuesto ≤ 8,3 ms por ciclo).
"""
import logging
import sys
import threading
import time
from typing import Optional

import cv2
import numpy as np

from contracts.i_camera_sensor import CameraFrame, ICameraSensor

logger = logging.getLogger(__name__)

_BACKENDS = {
    "auto": cv2.CAP_ANY,
    "dshow": getattr(cv2, "CAP_DSHOW", cv2.CAP_ANY),
    "msmf": getattr(cv2, "CAP_MSMF", cv2.CAP_ANY),
    "v4l2": getattr(cv2, "CAP_V4L2", cv2.CAP_ANY),
}


def _validate(frame: object) -> CameraFrame:
    if (
        not isinstance(frame, np.ndarray)
        or frame.dtype != np.uint8
        or frame.ndim != 3
        or frame.shape[2] != 3
        or frame.size == 0
    ):
        raise ValueError("La cámara debe producir un frame BGR uint8 no vacío (HxWx3).")
    return frame


class CameraSensorPlugin(ICameraSensor):
    """Owns one physical camera and publishes one frame per orchestrator cycle."""

    def __init__(self) -> None:
        self._camera_index = 0
        self._capture: Optional[cv2.VideoCapture] = None
        self._latest_frame: Optional[CameraFrame] = None
        self._grabbed_frame: Optional[CameraFrame] = None
        self._frame_counter = 0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._threaded = True
        self._initialized = False

    @property
    def name(self) -> str:
        return "CameraSensor"

    def initialize(self, config: dict) -> bool:
        self._camera_index = int(config.get("camera_index", 0))
        default_backend = "dshow" if sys.platform == "win32" else "auto"
        backend = _BACKENDS.get(str(config.get("backend", default_backend)).lower(), cv2.CAP_ANY)
        self._threaded = bool(config.get("threaded", True))
        self._latest_frame = None
        self._capture = cv2.VideoCapture(self._camera_index, backend)
        if not self._capture.isOpened():
            logger.error("No se pudo abrir la cámara %s.", self._camera_index)
            self._capture.release()
            self._capture = None
            return False
        width, height = config.get("width"), config.get("height")
        if width and height:                                   # numericUpDownResX/Y del C#
            self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
            self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, float(height))
        if config.get("fps"):
            self._capture.set(cv2.CAP_PROP_FPS, float(config["fps"]))
        if self._threaded:
            self._stop.clear()
            self._thread = threading.Thread(target=self._grab_loop, name=f"EDDIE-cam{self._camera_index}",
                                            daemon=True)
            self._thread.start()
        self._initialized = True
        logger.info("Sensor de cámara %s inicializado.", self._camera_index)
        return True

    def _grab_loop(self) -> None:
        failures = 0
        while not self._stop.is_set() and self._capture is not None:
            success, frame = self._capture.read()
            if not success or frame is None:
                failures += 1
                if failures > 100:
                    logger.error("La cámara %s dejó de entregar frames.", self._camera_index)
                    failures = 0
                time.sleep(0.01)
                continue
            failures = 0
            with self._lock:
                self._grabbed_frame = frame
                self._frame_counter += 1

    def execute(self) -> dict:
        frame = self.capture_frame()
        if frame is None:
            return {
                "sensor": self.instance_name,
                "camera_index": self._camera_index,
                "frame_available": False,
                "error": "frame_capture_failed",
            }
        return {
            "sensor": self.instance_name,
            "camera_index": self._camera_index,
            "frame_available": True,
            "width": int(frame.shape[1]),
            "height": int(frame.shape[0]),
            "channels": int(frame.shape[2]),
        }

    def capture_frame(self) -> Optional[CameraFrame]:
        if self._capture is None:
            self._latest_frame = None
            return None
        if self._threaded:
            with self._lock:
                frame = self._grabbed_frame
        else:
            success, frame = self._capture.read()
            if not success:
                frame = None
        if frame is None:
            self._latest_frame = None
            return None
        try:
            self._latest_frame = _validate(frame)
        except ValueError:
            self._latest_frame = None
            raise
        return self._latest_frame

    def get_latest_frame(self) -> Optional[CameraFrame]:
        return self._latest_frame

    @property
    def camera_index(self) -> int:
        return self._camera_index

    def release(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._latest_frame = None
        self._grabbed_frame = None
        self._initialized = False
