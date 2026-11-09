# Lógica común de GestureRecognitionActivity.cs para todos los detectores gestuales.
# Aplica la calibración, mueve el cursor, maneja el clic y la captura automática; cada detector implementa _detect().
# La rotación de 180° ("rotate_180") es opcional y se aplica una sola vez al frame.
import logging
import time
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from contracts.i_camera_sensor import CameraFrame, ICameraSensor
from contracts.i_gesture_plugin import (GestureCalibration, GestureResult, GestureSelection,
                                        IGesturePlugin)
from hardware.os_mouse import os_mouse

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    # Salida de un detector (equivale a IPlugin.RunPlugin + Center/DetectGesture/DetectClick).
    annotated: np.ndarray
    center: tuple[int, int]
    detect_gesture: bool
    detect_click: bool = False


class CalibratedGesturePlugin(IGesturePlugin):
    # Base de los plugins gestuales: calibración, clic y captura.

    AUTO_CLICK = False
    AUTO_CAM_CAPTURE = False
    DISPLAY_NAME = "Gesture"
    SCALABLE = True          # el detector trabaja en coordenadas de imagen (se puede reducir)

    def __init__(self) -> None:
        self._camera_sensor: Optional[ICameraSensor] = None
        self._calibration = GestureCalibration()
        self._active = False
        self._preview: Optional[CameraFrame] = None
        self._last_frame: Optional[CameraFrame] = None
        self._sensor = (0, 0)
        self._final = (0, 0)
        self._click_down = True
        self._resp = (0, 0)
        self._selection = GestureSelection()
        self._last_capture: Optional[CameraFrame] = None
        self._capture_seq = 0
        self._attempts = 0
        self._errors = 0
        self._min_interval = 0.0
        self._scale = 1.0
        self._last_processed = 0.0
        self._rotate_180 = False
        self._initialized = False

    # ------------------------------------------------------------------ contrato base
    @property
    def name(self) -> str:
        return self.DISPLAY_NAME

    @property
    def auto_cam_capture(self) -> bool:
        return self.AUTO_CAM_CAPTURE

    def set_camera_sensor(self, sensor: ICameraSensor) -> None:
        if not isinstance(sensor, ICameraSensor):
            raise TypeError(f"{self.name} requiere una implementación de ICameraSensor.")
        self._camera_sensor = sensor

    def initialize(self, config: dict) -> bool:
        if self._camera_sensor is None:
            logger.error("[%s] No se inyectó un ICameraSensor.", self.name)
            return False
        fps = float(config.get("max_fps", 15))          # el C# capturaba a 5 FPS (CapProp.Fps)
        self._min_interval = 1.0 / fps if fps > 0 else 0.0
        # Reducir la imagen antes de detectar mantiene el ciclo bajo el presupuesto de 8,3 ms.
        self._scale = float(config.get("processing_scale", 0.5)) if self.SCALABLE else 1.0
        self._active = bool(config.get("start_active", False))
        self._rotate_180 = bool(config.get("rotate_180", False))
        self.configure(config)
        self._initialized = True
        return True

    def configure(self, config: dict) -> None:
        # Hook para parámetros propios del detector.
        pass

    def release(self) -> None:
        self._active = False
        self._initialized = False

    def set_recognition_active(self, active: bool) -> None:
        self._active = bool(active)
        if not active:
            self._preview = None

    @property
    def recognition_active(self) -> bool:
        return self._active

    def set_calibration(self, calibration: GestureCalibration) -> None:
        self._calibration = calibration

    def get_preview_frame(self) -> Optional[CameraFrame]:
        return self._preview

    # ------------------------------------------------------------------ orientación
    def set_rotate_180(self, enabled: bool) -> None:
        # Casilla "Rotate 180°" de Gesture recognition (solo si la cámara está montada invertida).
        self._rotate_180 = bool(enabled)

    @property
    def rotate_180(self) -> bool:
        return self._rotate_180

    def _orient(self, frame: Optional[CameraFrame]) -> Optional[CameraFrame]:
        if frame is None or not self._rotate_180:
            return frame
        return cv2.rotate(frame, cv2.ROTATE_180)

    def get_error_rate(self) -> float:
        return self._errors / max(1, self._attempts)

    # ------------------------------------------------------------------ ciclo
    def execute(self) -> dict:
        if not self._active:
            return {"active": False, "plugin": self.name}
        now = time.perf_counter()
        if now - self._last_processed < self._min_interval:
            return self._result(processed=False)
        frame = self._orient(self._camera_sensor.get_latest_frame()) if self._camera_sensor else None
        if frame is None:
            self._attempts += 1
            self._errors += 1
            return {"active": True, "plugin": self.name, "error": "frame_capture_failed"}
        self._last_processed = now
        self._attempts += 1
        self._last_frame = frame
        try:
            if self._scale != 1.0:
                small = cv2.resize(frame, None, fx=self._scale, fy=self._scale, interpolation=cv2.INTER_AREA)
                detection = self._detect(small)
                detection.center = (int(detection.center[0] / self._scale),
                                    int(detection.center[1] / self._scale))
            else:
                detection = self._detect(frame)
        except Exception:
            self._errors += 1
            raise
        self._preview = detection.annotated
        self._sensor = detection.center
        captured = self._update_state(detection)
        return self._result(processed=True, detection=detection, captured=captured)

    def _result(self, processed: bool, detection: Optional[Detection] = None, captured: bool = False) -> dict:
        return {
            "active": True,
            "plugin": self.name,
            "processed": processed,
            "sensor_x": int(self._sensor[0]),
            "sensor_y": int(self._sensor[1]),
            "position_x": int(self._final[0]),
            "position_y": int(self._final[1]),
            "gesture": "point" if detection and detection.detect_gesture else "none",
            "is_click": not self._click_down if not self.AUTO_CLICK else self._click_down,
            "selection_captured": captured,
            "capture_seq": self._capture_seq,
            "error_rate": self.get_error_rate(),
        }

    def _map(self, center: tuple[int, int]) -> tuple[int, int]:
        c = self._calibration
        x, y = center
        if c.transform_x and c.sensor_end_x != c.sensor_start_x:
            x = abs((x - c.sensor_start_x) * ((c.app_end_x - c.app_start_x) / (c.sensor_end_x - c.sensor_start_x))
                    + c.app_start_x)
        if c.transform_y and c.sensor_end_y != c.sensor_start_y:
            y = abs((y - c.sensor_start_y) * ((c.app_end_y - c.app_start_y) / (c.sensor_end_y - c.sensor_start_y))
                    + c.app_start_y)
        return int(x), int(y)

    def _update_state(self, detection: Detection) -> bool:
        # Máquina de estados de Capture_ImageGrabbed (clic automático / detectado).
        mouse = os_mouse()
        control = self._calibration.mouse_control and mouse.available
        captured = False
        if detection.detect_gesture:
            self._final = self._map(detection.center)
            if control:
                mouse.move(*self._final)
            if not self._click_down and self.AUTO_CLICK:
                if control:
                    mouse.left_down()
                self._click_down = True
                self._resp = detection.center
            if not self.AUTO_CLICK:
                if detection.detect_click and self._click_down:
                    if control:
                        mouse.left_down()
                    self._click_down = False
                if not detection.detect_click and not self._click_down:
                    if control:
                        mouse.left_up()
                    self._click_down = True
        elif self._click_down and self.AUTO_CLICK:
            if control:
                mouse.left_up()
            if self.AUTO_CAM_CAPTURE:
                cx, cy = detection.center
                self._selection = GestureSelection(cx, cy, abs(self._resp[0] - cx), abs(self._resp[1] - cy))
                captured = self.capture_selection(self._selection) is not None
            self._click_down = False
        return captured

    # ------------------------------------------------------------------ selección
    def mark_selection_start(self) -> None:
        self._selection = GestureSelection(self._final[0], self._final[1], 0, 0)

    def mark_selection_end(self) -> GestureSelection:
        s = self._selection
        self._selection = GestureSelection(self._final[0], self._final[1],
                                           abs(s.x - self._final[0]), abs(s.y - self._final[1]))
        return self._selection

    def capture_selection(self, selection: Optional[GestureSelection] = None) -> Optional[CameraFrame]:
        # cropColorFrame: recorta la selección; si es inválida usa el frame completo.
        frame = self._last_frame
        if frame is None and self._camera_sensor is not None:
            frame = self._orient(self._camera_sensor.get_latest_frame())
        if frame is None:
            return None
        s = selection or self._selection
        if s.width > 0 and s.height > 0 and s.x < frame.shape[1]:
            crop = frame[max(0, s.y):s.y + s.height, max(0, s.x):s.x + s.width].copy()
        else:
            crop = frame.copy()
        if crop.size == 0:
            crop = frame.copy()
        self._last_capture = crop
        self._capture_seq += 1
        return crop

    def get_last_capture(self) -> Optional[CameraFrame]:
        return self._last_capture

    def get_last_capture_jpeg(self) -> Optional[bytes]:
        if self._last_capture is None:
            return None
        ok, buffer = cv2.imencode(".jpg", self._last_capture)
        return buffer.tobytes() if ok else None

    def detect_gesture(self, frame: CameraFrame) -> GestureResult:
        detection = self._detect(self._orient(frame))
        x, y = self._map(detection.center)
        return GestureResult(
            gesture_name="point" if detection.detect_gesture else "none",
            confidence=1.0 if detection.detect_gesture else 0.0,
            position_x=x, position_y=y, is_click=detection.detect_click,
        )

    @abstractmethod
    def _detect(self, frame: CameraFrame) -> Detection:
        # Detector específico: retorna frame anotado, centro y estado del gesto.
        pass


def write_multiline(frame: np.ndarray, lines: list[str], origin: tuple[int, int]) -> None:
    for index, line in enumerate(lines):
        cv2.putText(frame, line, (origin[0], origin[1] + index * 10), cv2.FONT_HERSHEY_PLAIN, 0.8,
                    (0, 0, 255), 1)
