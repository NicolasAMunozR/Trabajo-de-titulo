"""
plugins/image_processor_plugin.py
=====================================
Implementación del plugin de procesamiento de imágenes y OCR.

Reemplaza (C# legacy):
  - ModuloProcesamientoImagenes/OCRProcess.cs
      → OCRProcess.TransformImage() → extract_text()
  - ModuloProcesamientoImagenes/ColorRecognition.cs
      → ColorRecognition.Recognition() → capture_frame() + preprocess()
      → ColorRecognition.DetectTxt() → detect_text_region()
      → ColorRecognition.DetectObject() → find_largest_contour()
  - ModuloProcesamientoImagenes/CameraActivity.cs
      → CameraActivity → VideoCapture lifecycle (initialize/release)

Dependencias:
  - opencv-python (cv2): captura y preprocesamiento de frames
  - pytesseract: motor OCR (requiere Tesseract instalado)
  - numpy: manejo de matrices de imagen
"""
import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pytesseract

from contracts.i_camera_sensor import ICameraSensor
from contracts.i_image_processor import IImageProcessor

logger = logging.getLogger(__name__)


class ImageProcessorPlugin(IImageProcessor):
    """
    Plugin concreto para captura de cámara y OCR.

    Implementa el ciclo de vida initialize → execute → release.
    Reemplaza la funcionalidad de OCRProcess.cs y ColorRecognition.cs del
    sistema legado C#, eliminando la dependencia de Emgu.CV y Tesseract.NET.

    Attributes:
        _ocr_language (str): Idioma de Tesseract (ej. 'spa', 'eng').
        _min_confidence (float): Umbral de confianza para palabras.
        _threshold (int): Umbral binario para binarización (equiv. C# Threshold=1).
        _erode_iterations (int): Iteraciones de erosión (equiv. C# ErodeIterations=1).
        _dilate_iterations (int): Iteraciones de dilatación (equiv. C# DilateIterations=7).
        _camera_sensor: Sensor compartido inyectado por el orquestador.
        _last_detected_words (list[str]): Palabras detectadas en el último ciclo.
        _initialized (bool): Bandera de estado del ciclo de vida.
    """

    # Constantes equivalentes a las del C# ColorRecognition.cs
    _THRESHOLD = 1
    _ERODE_ITERATIONS = 1
    _DILATE_ITERATIONS = 7
    _MIN_CONTOUR_AREA = 500  # área mínima en píxeles² para considerar región de texto

    def __init__(self) -> None:
        self._camera_sensor: Optional[ICameraSensor] = None
        self._initialized = False

    @property
    def name(self) -> str:
        """Nombre identificador del plugin.

        Returns:
            str: 'ImageProcessor'
        """
        return 'ImageProcessor'

    def initialize(self, config: dict) -> bool:
        """
        Inicializa el procesador sin adquirir directamente el sensor.

        Args:
            config (dict): Parámetros de configuración. Claves relevantes:
                - 'ocr_language' (str): Idioma Tesseract (default 'spa').
                - 'min_confidence' (float): Umbral de confianza (default 0.6).
                - 'tesseract_path' (str): Ruta opcional al ejecutable Tesseract.

        Returns:
            bool: True si existe un sensor inyectado y el procesador está listo.
        """
        if self._camera_sensor is None:
            logger.error("[ImageProcessor] No se inyectó un ICameraSensor.")
            return False
        self._ocr_language = config.get('ocr_language', 'spa')
        self._min_confidence = config.get('min_confidence', 0.6)
        self._tesseract_config = ''
        tesseract_path = config.get('tesseract_path')
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        tessdata_dir = config.get('tessdata_dir')
        if tessdata_dir:
            tessdata_path = Path(tessdata_dir).expanduser()
            if not tessdata_path.is_dir():
                logger.error(
                    "[ImageProcessor] La carpeta tessdata no existe: %s",
                    tessdata_path,
                )
                return False
            self._tesseract_config = f'--tessdata-dir "{tessdata_path.as_posix()}"'

        try:
            available_languages = pytesseract.get_languages(
                config=self._tesseract_config
            )
        except pytesseract.TesseractNotFoundError as exc:
            logger.error(
                "[ImageProcessor] No se pudo ejecutar Tesseract. Revisa "
                "tesseract_path o PATH: %s",
                exc,
            )
            return False
        except pytesseract.TesseractError as exc:
            logger.error("[ImageProcessor] No se pudo consultar Tesseract: %s", exc)
            return False
        if self._ocr_language not in available_languages:
            logger.error(
                "[ImageProcessor] El idioma OCR '%s' no está instalado. "
                "Instala %s.traineddata en tessdata o configura tessdata_dir.",
                self._ocr_language,
                self._ocr_language,
            )
            return False

        self._last_detected_words: list[str] = []
        self._initialized = True
        logger.info("[ImageProcessor] Sensor de cámara compartido conectado.")
        return True

    def execute(self) -> dict:
        """
        Ejecuta un ciclo de captura y OCR.

        Equivalente al flujo principal de ColorRecognition.Recognition() +
        OCRProcess.TransformImage() en el C# legado.

        Returns:
            dict: Diccionario con claves:
                - 'detected_words' (list[str]): Palabras detectadas.
                - 'raw_text' (str): Texto crudo del OCR.
                - 'word_count' (int): Número de palabras detectadas.
                - 'region_found' (bool): True si se detectó una región de texto.
        """
        try:
            frame = (
                self._camera_sensor.get_latest_frame()
                if self._camera_sensor is not None
                else None
            )
            if frame is None:
                return {'detected_words': [], 'raw_text': '', 'word_count': 0,
                        'region_found': False, 'error': 'frame_capture_failed'}

            # Detectar región de texto (equivale a ColorRecognition.DetectTxt)
            region = self.detect_text_region(frame)
            processed = self.preprocess(frame)
            ocr_result = self.extract_text_with_regions(processed)
            raw_text = ocr_result["raw_text"]
            words = [w.strip() for w in raw_text.split() if w.strip()]
            self._last_detected_words = words

            return {
                'detected_words': words,
                'raw_text': raw_text,
                'text_regions': ocr_result["text_regions"],
                'frame_size': {
                    "width": int(frame.shape[1]),
                    "height": int(frame.shape[0]),
                },
                'word_count': len(words),
                'region_found': region is not None
            }
        except Exception as exc:
            logger.error(f"[ImageProcessor] Error en execute: {exc}")
            return {'detected_words': [], 'raw_text': '', 'word_count': 0,
                    'region_found': False, 'error': str(exc)}

    def release(self) -> None:
        """
        Libera los recursos del plugin.

        El sensor compartido pertenece al orquestador; este plugin no lo cierra.
        """
        self._initialized = False

    def set_camera_sensor(self, sensor: ICameraSensor) -> None:
        if not isinstance(sensor, ICameraSensor):
            raise TypeError("ImageProcessor requiere una implementación de ICameraSensor.")
        self._camera_sensor = sensor

    def preprocess(self, frame: object) -> object:
        """
        Aplica preprocesamiento al frame para mejorar el reconocimiento OCR.

        Equivalente al pipeline de ColorRecognition.DetectTxt():
          1. Convertir a escala de grises (CvtColor Bgr2Gray)
          2. Binarización con umbral Otsu (Threshold Binary)
          3. Erosión para eliminar ruido (Erode)
          4. Dilatación para recuperar forma (Dilate)

        Args:
            frame: numpy.ndarray con el frame original en BGR.

        Returns:
            numpy.ndarray: Frame preprocesado listo para OCR.
        """
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255,
                                      cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            kernel = np.ones((3, 3), np.uint8)
            eroded = cv2.erode(binary, kernel,
                               iterations=self._ERODE_ITERATIONS)
            dilated = cv2.dilate(eroded, kernel,
                                 iterations=self._DILATE_ITERATIONS)
            return dilated
        except Exception as exc:
            raise RuntimeError(f"No se pudo preprocesar el frame de cámara: {exc}") from exc

    def detect_text_region(self, frame: object) -> Optional[object]:
        """
        Detecta la región principal de texto en el frame usando contornos.

        Equivalente a ColorRecognition.DetectObject() + DetectTxt() en C#.
        Encuentra el contorno más grande (que se asume es la región de texto)
        y retorna el recorte de esa región.

        Args:
            frame: numpy.ndarray con el frame original en BGR.

        Returns:
            numpy.ndarray | None: Región de texto recortada, o None si no
            se detecta ninguna región con área suficiente.
        """
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255,
                                      cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                            cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return None

            # Seleccionar el contorno más grande (equiv. C# chosen = maxArea)
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)

            if area < self._MIN_CONTOUR_AREA:
                return None

            # Bounding rectangle (equiv. C# BoundingRectangle + ROI)
            x, y, w, h = cv2.boundingRect(largest)
            cropped = frame[y:y+h, x:x+w]
            return cropped

        except Exception as exc:
            raise RuntimeError(f"No se pudo detectar la región de texto: {exc}") from exc

    def find_largest_contour(self, frame: object):
        """
        Encuentra el contorno más grande en un frame binarizado.

        Equivalente al bucle de selección de contorno en
        ColorRecognition.DetectObject() del C# legado.

        Args:
            frame: numpy.ndarray binarizado (escala de grises).

        Returns:
            tuple | None: (contorno, área, cx, cy) del contorno más grande,
            o None si no hay contornos suficientes.
        """
        try:
            contours, _ = cv2.findContours(frame, cv2.RETR_EXTERNAL,
                                            cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return None

            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)

            M = cv2.moments(largest)
            cx = int(M['m10'] / M['m00']) if M['m00'] != 0 else 0
            cy = int(M['m01'] / M['m00']) if M['m00'] != 0 else 0

            return (largest, area, cx, cy)
        except Exception as exc:
            logger.warning(f"[ImageProcessor] Advertencia en find_largest_contour: {exc}")
            return None

    def extract_text(self, frame: object) -> str:
        """
        Aplica OCR al frame preprocesado y retorna el texto detectado.

        Equivalente a OCRProcess.TransformImage(Bitmap img) en C#.
        En C# se usaba TesseractEngine; aquí se usa pytesseract (wrapper Python).

        Args:
            frame: numpy.ndarray preprocesado (idealmente binarizado).

        Returns:
            str: Texto extraído por Tesseract, o cadena vacía si falla.
        """
        try:
            text = pytesseract.image_to_string(
                frame,
                lang=self._ocr_language,
                config=self._tesseract_config,
            )
            return text.strip()
        except Exception as exc:
            raise RuntimeError(f"Falló el motor OCR de Tesseract: {exc}") from exc

    def extract_text_with_regions(self, frame: object) -> dict:
        """Run OCR once and retain per-word boxes for calibrated PDF mapping."""
        try:
            data = pytesseract.image_to_data(
                frame,
                lang=self._ocr_language,
                config=self._tesseract_config,
                output_type=pytesseract.Output.DICT,
            )
        except Exception as exc:
            raise RuntimeError(f"Falló el motor OCR de Tesseract: {exc}") from exc

        regions = []
        words = []
        for index, raw_word in enumerate(data["text"]):
            word = raw_word.strip()
            if not word:
                continue
            try:
                confidence = float(data["conf"][index]) / 100.0
                x, y = int(data["left"][index]), int(data["top"][index])
                width = int(data["width"][index])
                height = int(data["height"][index])
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise RuntimeError("Tesseract devolvió cajas OCR incompletas.") from exc
            if confidence < 0 or width <= 0 or height <= 0:
                continue
            words.append(word)
            regions.append({
                "text": word,
                "confidence": min(confidence, 1.0),
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            })
        return {"raw_text": " ".join(words), "text_regions": regions}

    def get_precision_recall(self, expected_words: list[str]) -> dict:
        """
        Calcula precisión, recall y F1 del OCR contra palabras esperadas.

        Métrica requerida por el informe de seminario: validar con mínimo
        10 palabras esperadas. Normaliza a minúsculas antes de comparar.

        Args:
            expected_words (list[str]): Lista de palabras que se espera encontrar.

        Returns:
            dict: Diccionario con claves:
                - 'precision' (float): TP / (TP + FP), rango [0.0, 1.0].
                - 'recall' (float): TP / (TP + FN), rango [0.0, 1.0].
                - 'f1' (float): Media armónica de precision y recall.
                - 'detected_count' (int): Palabras detectadas en último ciclo.
                - 'expected_count' (int): Palabras esperadas recibidas.
        """
        detected_set = set(w.lower() for w in self._last_detected_words)
        expected_set = set(w.lower() for w in expected_words)

        if not expected_set and not detected_set:
            return {'precision': 1.0, 'recall': 1.0, 'f1': 1.0,
                    'detected_count': 0, 'expected_count': 0}
        if not expected_set:
            return {'precision': 0.0, 'recall': 1.0, 'f1': 0.0,
                    'detected_count': len(detected_set), 'expected_count': 0}
        if not detected_set:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0,
                    'detected_count': 0, 'expected_count': len(expected_set)}

        tp = len(detected_set & expected_set)
        precision = tp / len(detected_set) if detected_set else 0.0
        recall = tp / len(expected_set) if expected_set else 0.0
        f1 = (2 * precision * recall / (precision + recall)
               if (precision + recall) > 0 else 0.0)

        return {
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1': round(f1, 4),
            'detected_count': len(detected_set),
            'expected_count': len(expected_set)
        }
