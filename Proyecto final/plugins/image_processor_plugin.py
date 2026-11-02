"""
plugins/image_processor_plugin.py
=================================
Reconocimiento de texto resaltado (IImageProcessor).

Porta a OpenCV/pytesseract:
  - ModuloProcesamientoImagenes/ColorRecognition.cs  → detect_highlight_region()
      Segmenta los píxeles del resaltado proyectado (BGR (0,0,120)…(125,255,255)),
      erosiona 1 vez, dilata 7 veces, toma el contorno de mayor área, su envolvente
      convexa y su rectángulo, que se dibuja en rojo sobre el frame (imageBox1).
  - ModuloProcesamientoImagenes/OCRProcess.cs        → extract_text()
      Rota 180° (la cámara del montaje está invertida) y aplica Tesseract.

El OCR es costoso, por lo que NO se ejecuta en cada ciclo: execute() solo informa el
estado y la interfaz lo pide bajo demanda con OrchestratorCore.invoke(), igual que el
C# lo hacía al terminar un resaltado (ButtonAction → CaptureTxt).
"""
import logging
import shutil
import sys
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from contracts.i_camera_sensor import CameraFrame, ICameraSensor
from contracts.i_image_processor import IImageProcessor

logger = logging.getLogger(__name__)

try:
    import pytesseract
except ImportError:                      # pragma: no cover - se informa en initialize()
    pytesseract = None

_WINDOWS_TESSERACT = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)


class ImageProcessorPlugin(IImageProcessor):
    """Detecta el texto resaltado sobre el papel y lo transforma en texto con OCR."""

    # Constantes de ColorRecognition.cs
    _ERODE_ITERATIONS = 1
    _DILATE_ITERATIONS = 7
    _LOWER_BGR = (0, 0, 120)
    _UPPER_BGR = (125, 255, 255)

    def __init__(self) -> None:
        self._camera_sensor: Optional[ICameraSensor] = None
        self._ocr_language = "eng"
        self._tesseract_config = ""
        self._rotate_180 = True
        self._ocr_available = False
        self._last_detected_words: list[str] = []
        self._last_result: dict = {}
        self._initialized = False

    @property
    def name(self) -> str:
        return "ImageProcessor"

    # ------------------------------------------------------------------ ciclo de vida
    def initialize(self, config: dict) -> bool:
        if self._camera_sensor is None:
            logger.error("[ImageProcessor] No se inyectó un ICameraSensor.")
            return False
        self._ocr_language = config.get("ocr_language", "spa+eng")
        self._rotate_180 = bool(config.get("rotate_180", True))
        lower = config.get("highlight_lower_bgr", self._LOWER_BGR)
        upper = config.get("highlight_upper_bgr", self._UPPER_BGR)
        self._lower = np.array(lower, np.uint8)
        self._upper = np.array(upper, np.uint8)
        self._min_area = float(config.get("min_region_area", 150))
        self._ocr_available = self._configure_tesseract(config)
        if not self._ocr_available:
            # El plugin sigue activo: la detección del resaltado funciona sin OCR y la
            # interfaz informa que Tesseract no está instalado (antes la app se cerraba).
            logger.warning("[ImageProcessor] OCR deshabilitado; solo se detectarán regiones.")
        self._initialized = True
        return True

    def _configure_tesseract(self, config: dict) -> bool:
        if pytesseract is None:
            logger.error("[ImageProcessor] pytesseract no está instalado.")
            return False
        path = config.get("tesseract_path") or shutil.which("tesseract")
        if not path and sys.platform == "win32":
            path = next((p for p in _WINDOWS_TESSERACT if Path(p).exists()), None)
        if path:
            pytesseract.pytesseract.tesseract_cmd = path
        tessdata_dir = config.get("tessdata_dir")
        if tessdata_dir:
            self._tesseract_config = f'--tessdata-dir "{Path(tessdata_dir).expanduser().as_posix()}"'
        try:
            available = set(pytesseract.get_languages(config=self._tesseract_config))
        except Exception as exc:
            logger.error("[ImageProcessor] No se pudo ejecutar Tesseract: %s", exc)
            return False
        wanted = [lang for lang in self._ocr_language.split("+") if lang in available]
        if not wanted:
            fallback = "eng" if "eng" in available else next(iter(available - {"osd"}), None)
            if fallback is None:
                logger.error("[ImageProcessor] Tesseract no tiene idiomas instalados.")
                return False
            logger.warning("[ImageProcessor] Idioma '%s' no instalado; se usa '%s'.",
                           self._ocr_language, fallback)
            wanted = [fallback]
        self._ocr_language = "+".join(wanted)
        return True

    def execute(self) -> dict:
        frame = self._camera_sensor.get_latest_frame() if self._camera_sensor else None
        return {
            "frame_available": frame is not None,
            "ocr_available": self._ocr_available,
            "last_text": self._last_result.get("text", ""),
        }

    def release(self) -> None:
        self._initialized = False

    def set_camera_sensor(self, sensor: ICameraSensor) -> None:
        if not isinstance(sensor, ICameraSensor):
            raise TypeError("ImageProcessor requiere una implementación de ICameraSensor.")
        self._camera_sensor = sensor

    @property
    def ocr_available(self) -> bool:
        return self._ocr_available

    # ------------------------------------------------------------------ visión
    def detect_highlight_region(self, frame: CameraFrame) -> tuple[np.ndarray, Optional[tuple]]:
        """ColorRecognition.DetectTxt + DetectObject. Retorna (frame anotado, caja | None)."""
        mask = cv2.inRange(frame, self._lower, self._upper)
        already_red = cv2.inRange(frame, np.array((0, 0, 255), np.uint8), np.array((0, 0, 255), np.uint8))
        mask = cv2.bitwise_and(mask, cv2.bitwise_not(already_red))
        mask = cv2.erode(mask, None, iterations=self._ERODE_ITERATIONS)
        mask = cv2.dilate(mask, None, iterations=self._DILATE_ITERATIONS)
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        annotated = frame.copy()
        if not contours:
            return annotated, None
        chosen = max(contours, key=cv2.contourArea)
        if cv2.contourArea(chosen) < self._min_area:
            return annotated, None
        hull = cv2.convexHull(chosen)
        x, y, w, h = cv2.boundingRect(hull)
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 255), 1)
        return annotated, (int(x), int(y), int(w), int(h))

    def preprocess(self, frame: CameraFrame) -> np.ndarray:
        """Escala de grises + Otsu para mejorar el OCR del recorte."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
        if gray.shape[0] < 60:                       # recortes pequeños: Tesseract necesita ~30 px de alto
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    def extract_text(self, frame: np.ndarray) -> str:
        if not self._ocr_available:
            raise RuntimeError("Tesseract OCR no está instalado o no se encontró.")
        text = pytesseract.image_to_string(frame, lang=self._ocr_language,
                                           config=f"{self._tesseract_config} --psm 6".strip())
        words = [w for w in text.split() if w.strip()]
        self._last_detected_words = words
        return text.strip()

    def extract_text_with_regions(self, frame: np.ndarray) -> dict:
        if not self._ocr_available:
            raise RuntimeError("Tesseract OCR no está instalado o no se encontró.")
        data = pytesseract.image_to_data(frame, lang=self._ocr_language, config=self._tesseract_config,
                                         output_type=pytesseract.Output.DICT)
        regions, words = [], []
        for index, raw_word in enumerate(data["text"]):
            word = raw_word.strip()
            if not word:
                continue
            confidence = float(data["conf"][index]) / 100.0
            width, height = int(data["width"][index]), int(data["height"][index])
            if confidence < 0 or width <= 0 or height <= 0:
                continue
            words.append(word)
            regions.append({"text": word, "confidence": min(confidence, 1.0),
                            "x": int(data["left"][index]), "y": int(data["top"][index]),
                            "width": width, "height": height})
        self._last_detected_words = words
        return {"raw_text": " ".join(words), "text_regions": regions}

    def recognize_highlighted_text(self, frame: Optional[CameraFrame] = None) -> dict:
        """Flujo completo de 'resaltar y reconocer' (CaptureTxt + OCRProcess.TransformImage)."""
        if frame is None:
            frame = self._camera_sensor.capture_frame() if self._camera_sensor else None
        if frame is None:
            raise RuntimeError("La cámara de reconocimiento de texto no entrega imágenes.")
        annotated, box = self.detect_highlight_region(frame)
        crop = None
        text = ""
        if box is not None:
            x, y, w, h = box
            crop = frame[y:y + h, x:x + w].copy()
            ocr_input = cv2.rotate(crop, cv2.ROTATE_180) if self._rotate_180 else crop
            if self._ocr_available:
                text = self.extract_text(self.preprocess(ocr_input))
        self._last_result = {"text": text, "annotated": annotated, "crop": crop, "box": box}
        return dict(self._last_result)

    def get_precision_recall(self, expected_words: list[str]) -> dict:
        detected_set = {w.lower() for w in self._last_detected_words}
        expected_set = {w.lower() for w in expected_words}
        if not expected_set and not detected_set:
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "detected_count": 0, "expected_count": 0}
        tp = len(detected_set & expected_set)
        precision = tp / len(detected_set) if detected_set else 0.0
        recall = tp / len(expected_set) if expected_set else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
                "detected_count": len(detected_set), "expected_count": len(expected_set)}
