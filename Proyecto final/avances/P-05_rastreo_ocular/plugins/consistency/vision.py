# Detección de marcas físicas en el papel (lado físico → digital).
# Porta los filtros HSV de BibliotecaConsistencia: marcador azul, notas amarillas y figuras magenta.
import math
from dataclasses import dataclass

import cv2
import numpy as np


def _hsv_mask(frame: np.ndarray, hue: tuple[int, int], value: tuple[int, int], sat_min: int) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    hue_mask = cv2.inRange(h, hue[0], hue[1])
    val_mask = cv2.inRange(v, value[0], value[1])
    _, sat_mask = cv2.threshold(s, sat_min, 255, cv2.THRESH_BINARY)
    return cv2.bitwise_and(cv2.bitwise_and(hue_mask, val_mask), sat_mask)


def _smooth_threshold(mask: np.ndarray, level: int) -> np.ndarray:
    # SmoothGaussian(5) + ThresholdBinary(level) del C#.
    blurred = cv2.GaussianBlur(mask, (5, 5), 0)
    _, binary = cv2.threshold(blurred, level, 255, cv2.THRESH_BINARY)
    return binary


def _rect(width: int, height: int) -> np.ndarray:
    return cv2.getStructuringElement(cv2.MORPH_RECT, (width, height))


def detect_bookmark(frame: np.ndarray, min_area: float = 1000) -> bool:
    mask = _hsv_mask(frame, (90, 120), (100, 255), 10)
    mask = cv2.erode(mask, _rect(3, 2), iterations=1)
    mask = cv2.dilate(mask, _rect(3, 2), iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, _rect(3, 3), iterations=2, borderType=cv2.BORDER_REFLECT)
    contours, _ = cv2.findContours(_smooth_threshold(mask, 230), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return any(cv2.contourArea(c) > min_area for c in contours)


def detect_comments(frame: np.ndarray, min_area: float = 15000) -> list[tuple[int, int, int, int]]:
    # Notas adhesivas: contornos de 4 vértices sobre un filtro de tono amarillo/naranjo.
    mask = _hsv_mask(frame, (0, 30), (100, 255), 10)
    mask = cv2.erode(mask, _rect(3, 2), iterations=3)
    mask = cv2.dilate(mask, _rect(3, 2), iterations=4)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, _rect(3, 3), iterations=5, borderType=cv2.BORDER_REFLECT)
    contours, _ = cv2.findContours(_smooth_threshold(mask, 230), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for contour in contours:
        if cv2.contourArea(contour) <= min_area:
            continue
        approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True), True)
        if len(approx) == 4:
            boxes.append(tuple(int(v) for v in cv2.boundingRect(approx)))
    return boxes


@dataclass
class Figure:
    kind: str                       # 'rect' | 'ellipse'
    x: float
    y: float
    width: float
    height: float


def detect_figures(frame: np.ndarray, min_area: float = 1000) -> list[Figure]:
    # Clasifica figuras dibujadas en rosado/magenta: triángulo→rect, 4 vértices→rect/elipse, ≥5→elipse.
    mask = _hsv_mask(frame, (150, 255), (100, 255), 20)
    mask = cv2.erode(mask, _rect(3, 2), iterations=2)
    mask = cv2.dilate(mask, _rect(3, 3), iterations=3, borderType=cv2.BORDER_REPLICATE)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, _rect(3, 3), iterations=5, borderType=cv2.BORDER_REFLECT)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, _rect(3, 3), iterations=1, borderType=cv2.BORDER_REFLECT)
    contours, _ = cv2.findContours(_smooth_threshold(mask, 20), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    figures = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area <= min_area:
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        (cx, cy), (rw, rh), _ = cv2.minAreaRect(contour)
        ellipse = Figure("ellipse", cx - rw / 2, cy - rh / 2, rw, rh)
        x, y, w, h = cv2.boundingRect(approx)
        rect = Figure("rect", x, y, w, h)
        if len(approx) == 3:
            figures.append(rect)
        elif len(approx) == 4:
            bx, by, bw, bh = cv2.boundingRect(contour)
            aspect = bw / bh if bh else 0
            circularity = 4 * math.pi * area / (perimeter ** 2) if perimeter else 0
            if circularity > 0.69 and not 0.8 <= aspect <= 1.0:
                figures.append(ellipse)
            else:
                figures.append(rect)
        elif len(approx) >= 5:
            figures.append(ellipse)
    return figures
