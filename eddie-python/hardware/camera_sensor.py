"""OpenCV adapter implementing the shared camera sensor contract."""
import logging
from typing import Optional

import cv2
import numpy as np

from contracts.i_camera_sensor import CameraFrame, ICameraSensor

logger = logging.getLogger(__name__)


class CameraSensorPlugin(ICameraSensor):
    """Owns one physical camera and publishes one frame per orchestrator cycle."""

    def __init__(self) -> None:
        self._camera_index = 0
        self._capture: Optional[cv2.VideoCapture] = None
        self._latest_frame: Optional[CameraFrame] = None
        self._initialized = False

    @property
    def name(self) -> str:
        return "CameraSensor"

    def initialize(self, config: dict) -> bool:
        self._camera_index = int(config.get("camera_index", 0))
        self._latest_frame = None
        self._capture = cv2.VideoCapture(self._camera_index)
        if not self._capture.isOpened():
            logger.error("No se pudo abrir la cámara %s.", self._camera_index)
            self._capture.release()
            self._capture = None
            return False
        self._initialized = True
        logger.info("Sensor de cámara %s inicializado.", self._camera_index)
        return True

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
        success, frame = self._capture.read()
        if not success or frame is None:
            self._latest_frame = None
            return None
        if (
            not isinstance(frame, np.ndarray)
            or frame.dtype != np.uint8
            or frame.ndim != 3
            or frame.shape[2] != 3
            or frame.size == 0
        ):
            self._latest_frame = None
            raise ValueError("La cámara debe producir un frame BGR uint8 no vacío (HxWx3).")
        self._latest_frame = frame
        return frame

    def get_latest_frame(self) -> Optional[CameraFrame]:
        return self._latest_frame

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._latest_frame = None
        self._initialized = False
