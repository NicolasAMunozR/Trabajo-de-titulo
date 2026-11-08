"""Manual camera/display calibration for mapping observations onto a PDF page."""
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np


@dataclass(frozen=True)
class SpatialCalibration:
    """Maps normalized camera/page and display/page coordinates."""

    camera_page_corners: tuple[tuple[float, float], ...]
    gaze_viewport: tuple[float, float, float, float]

    @classmethod
    def from_config(cls, config: dict) -> "SpatialCalibration":
        corners = tuple(
            (float(point[0]), float(point[1]))
            for point in config["camera_page_corners"]
        )
        viewport = tuple(float(value) for value in config["gaze_viewport"])
        if len(corners) != 4:
            raise ValueError(
                "camera_page_corners debe contener 4 puntos TL, TR, BR, BL."
            )
        if len(viewport) != 4:
            raise ValueError("gaze_viewport debe ser [x0, y0, x1, y1].")
        if any(not 0 <= value <= 1 for point in corners for value in point):
            raise ValueError("Las esquinas de cámara deben estar normalizadas [0, 1].")
        corner_array = np.asarray(corners, dtype=np.float32)
        if (
            not cv2.isContourConvex(corner_array)
            or cv2.contourArea(corner_array) <= 1e-6
        ):
            raise ValueError(
                "Las esquinas de cámara deben formar una página convexa "
                "en orden TL, TR, BR, BL."
            )
        x0, y0, x1, y1 = viewport
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
            raise ValueError("gaze_viewport debe ser un rectángulo normalizado válido.")
        return cls(corners, viewport)

    def map_camera_rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        frame_width: int,
        frame_height: int,
    ) -> Optional[tuple[float, float, float, float]]:
        """Map an OCR pixel box into normalized PDF-page coordinates."""
        if frame_width <= 0 or frame_height <= 0 or width <= 0 or height <= 0:
            return None
        source = np.asarray(self.camera_page_corners, dtype=np.float32)
        target = np.asarray(
            [[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32
        )
        transform = cv2.getPerspectiveTransform(source, target)
        image_points = np.asarray(
            [
                [x / frame_width, y / frame_height],
                [(x + width) / frame_width, y / frame_height],
                [(x + width) / frame_width, (y + height) / frame_height],
                [x / frame_width, (y + height) / frame_height],
            ],
            dtype=np.float32,
        ).reshape(1, 4, 2)
        page_points = cv2.perspectiveTransform(image_points, transform)[0]
        min_x = max(0.0, float(np.min(page_points[:, 0])))
        min_y = max(0.0, float(np.min(page_points[:, 1])))
        max_x = min(1.0, float(np.max(page_points[:, 0])))
        max_y = min(1.0, float(np.max(page_points[:, 1])))
        if min_x >= max_x or min_y >= max_y:
            return None
        return min_x, min_y, max_x, max_y

    def map_gaze(self, x: float, y: float) -> Optional[tuple[float, float]]:
        """Map normalized display gaze into normalized PDF-page coordinates."""
        x0, y0, x1, y1 = self.gaze_viewport
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            return None
        return (x - x0) / (x1 - x0), (y - y0) / (y1 - y0)
