# Detectores gestuales portados desde los plugins C#: ColorPenPlugin, HandSkinPlugin y MousePlugin.
# Se declaran en config/plugins.json; ya no se cargan con Assembly.LoadFrom.
import math

import cv2
import numpy as np

from contracts.i_camera_sensor import CameraFrame
from hardware.os_mouse import os_mouse
from plugins.gestures.base import CalibratedGesturePlugin, Detection, write_multiline


class ColorPenPlugin(CalibratedGesturePlugin):
    # Lápiz de color/luminoso: segmenta BGR (0,0,230)…(255,255,255), erosión 1, dilatación 7.

    DISPLAY_NAME = "Color Pen Recognition"
    AUTO_CLICK = True
    AUTO_CAM_CAPTURE = True

    def configure(self, config: dict) -> None:
        self._lower = np.array(config.get("lower_bgr", (0, 0, 230)), np.uint8)
        self._upper = np.array(config.get("upper_bgr", (255, 255, 255)), np.uint8)
        self._erode = int(config.get("erode_iterations", 1))
        self._dilate = max(1, round(int(config.get("dilate_iterations", 7)) * self._scale))
        self._min_area = float(config.get("min_area", 0))

    def _detect(self, frame: CameraFrame) -> Detection:
        mask = cv2.inRange(frame, self._lower, self._upper)
        mask = cv2.erode(mask, None, iterations=self._erode)
        mask = cv2.dilate(mask, None, iterations=self._dilate)
        display = frame.copy()
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return Detection(display, self._sensor, False)
        chosen = max(contours, key=cv2.contourArea)
        if cv2.contourArea(chosen) < self._min_area:
            return Detection(display, self._sensor, False)
        x, y, w, h = cv2.boundingRect(cv2.convexHull(chosen))
        cv2.rectangle(display, (x, y), (x + w, y + h), (0, 0, 255), 1)
        center = (x + w // 2, y + h // 2)
        full = (int(center[0] / self._scale), int(center[1] / self._scale))
        write_multiline(display, ["Centro", f"Posicion: {full[0]}, {full[1]}"],
                        (center[0] + 30, center[1]))
        cv2.circle(display, center, 2, (0, 100, 0), 4)
        return Detection(display, center, True)


class HandSkinPlugin(CalibratedGesturePlugin):
    # Mano por color de piel (YCrCb) con conteo de defectos de convexidad para el clic.

    DISPLAY_NAME = "Hand Skin Recognition"
    AUTO_CLICK = False
    AUTO_CAM_CAPTURE = False

    def configure(self, config: dict) -> None:
        self._ycc_min = np.array(config.get("ycrcb_min", (0, 131, 80)), np.uint8)
        self._ycc_max = np.array(config.get("ycrcb_max", (255, 185, 135)), np.uint8)
        self._rotate = bool(config.get("rotate_180", True))
        self._detect_click = False
        self._repeat = 0
        k12, k6 = max(2, round(12 * self._scale)), max(2, round(6 * self._scale))
        self._erode_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k12, k12))
        self._dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k6, k6))

    def _skin(self, frame: np.ndarray) -> np.ndarray:
        skin = cv2.inRange(cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb), self._ycc_min, self._ycc_max)
        skin = cv2.erode(skin, self._erode_kernel, iterations=1, borderType=cv2.BORDER_REFLECT)
        return cv2.dilate(skin, self._dilate_kernel, iterations=2, borderType=cv2.BORDER_REFLECT)

    def _detect(self, frame: CameraFrame) -> Detection:
        if self._rotate:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        display = frame.copy()
        contours, _ = cv2.findContours(self._skin(frame), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return Detection(display, self._sensor, False, self._detect_click)
        chosen = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(chosen)
        bx, by, bw, bh = cv2.boundingRect(chosen)
        cv2.polylines(display, [chosen], True, (0, 0, 255))
        cv2.rectangle(display, (bx, by), (bx + bw, by + bh), (0, 0, 255))
        write_multiline(display, [f"Area: {area}", f"Position: {bx + bw // 2}, {by + bh // 2}"],
                        (bx + bw + 5, by + bh // 2))
        hull_idx = cv2.convexHull(chosen, returnPoints=False)
        detect_gesture = hull_idx is not None and len(hull_idx) > 3
        hull_pts = cv2.convexHull(chosen)
        x, y, w, h = cv2.boundingRect(hull_pts)
        cv2.rectangle(display, (x, y), (x + w, y + h), (0, 0, 255))
        center = (x + w // 2, y + h // 2)
        try:
            defects = cv2.convexityDefects(chosen, hull_idx) if detect_gesture else None
        except cv2.error:
            defects = None
        if defects is None:
            return Detection(display, self._sensor, detect_gesture, self._detect_click)
        fingers = 0
        tip = (math.inf, math.inf)
        for start_idx, end_idx, far_idx, _ in defects.reshape(-1, 4):   # OpenCV 4 (N,1,4) y 5 (N,4)
            start, end, far = (tuple(int(v) for v in chosen[i][0]) for i in (start_idx, end_idx, far_idx))
            cv2.circle(display, end, 3, (0, 255, 255))
            cv2.circle(display, start, 3, (255, 255, 0))
            if end[1] < tip[1]:
                tip = end
            if math.dist(center, far) < h * 0.3:
                cv2.circle(display, far, 10, (255, 0, 0), 4)
                fingers += 1
            cv2.line(display, start, end, (0, 255, 255))
        self._repeat = self._repeat + 1 if fingers >= 4 else 0
        if self._repeat == 3:                     # mano abierta 3 cuadros seguidos alterna el clic
            self._repeat = 0
            self._detect_click = not self._detect_click
        sensor = (int(tip[0]), int(tip[1])) if tip[0] != math.inf else self._sensor
        cv2.circle(display, sensor, 20, (255, 0, 255), 2)
        return Detection(display, sensor, detect_gesture, self._detect_click)


class MousePlugin(CalibratedGesturePlugin):
    # El cursor del sistema actúa como sensor (MouseRecognition.dll).

    DISPLAY_NAME = "Mouse Recognition"
    AUTO_CLICK = True
    AUTO_CAM_CAPTURE = True
    SCALABLE = False          # el centro viene del cursor (coordenadas de pantalla)

    def _detect(self, frame: CameraFrame) -> Detection:
        display = frame.copy()
        for point, color in (((300, 300), (0, 0, 255)), ((600, 600), (0, 0, 255)), ((960, 720), (255, 0, 0))):
            cv2.circle(display, point, 10, color, 8)
        x, y = os_mouse().position()
        return Detection(display, (int(x), int(y)), True)
