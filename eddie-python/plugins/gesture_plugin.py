"""
plugins/gesture_plugin.py
=====================================
Implementación del plugin de reconocimiento gestual.

Reemplaza (C# legacy):
  - ModuloReconocimientoGestual/GestureRecognitionActivity.cs
      → Capture_ImageGrabbed() → capture_frame() + detect_gesture()
      → DetectObject (vía IPlugin.RunPlugin) → find_largest_contour()
      → SensorX/SensorY → GestureResult.position_x/y
      → FinalToRectXY/FinalToRectWH → bounding_rect()
  - ColorPenRecognition, HandSkinRecognition (detección por color/piel)
      → Unificados en detect_gesture() con contornos OpenCV
  - PluginFramework/IPlugin.RunPlugin(VideoCapture)
      → Reemplazado por detect_gesture(frame: ndarray)

Dependencias:
  - opencv-python (cv2): detección por contornos
  - numpy: procesamiento de arrays
"""
import logging
from typing import Optional, Tuple

import cv2
import numpy as np

from contracts.i_camera_sensor import ICameraSensor
from contracts.i_gesture_plugin import IGesturePlugin, GestureResult

logger = logging.getLogger(__name__)


class GesturePlugin(IGesturePlugin):
    """
    Plugin concreto para reconocimiento gestual mediante visión computacional.

    Implementa el ciclo de vida initialize → execute → release.
    Reemplaza GestureRecognitionActivity.cs + IPlugin.RunPlugin() del C# legado,
    eliminando el acoplamiento a Emgu.CV y al patrón IPlugin con VideoCapture.

    Attributes:
        _detection_method (str): Método de detección ('opencv_contours').
        _total_attempts (int): Contador de ciclos execute() llamados.
        _error_count (int): Contador de ciclos con error.
        _camera_sensor: Sensor compartido inyectado por el orquestador.
        _sensor_x (int): Coordenada X del sensor (equiv. C# SensorX).
        _sensor_y (int): Coordenada Y del sensor (equiv. C# SensorY).
        _click_down (bool): Estado del clic (equiv. C# clickDown).
        _initialized (bool): Bandera de ciclo de vida.
    """

    _MIN_CONTOUR_AREA = 5000  # Área mínima en píxeles² para detectar gesto

    def __init__(self) -> None:
        self._camera_sensor: Optional[ICameraSensor] = None
        self._initialized = False

    @property
    def name(self) -> str:
        """Nombre identificador del plugin.

        Returns:
            str: 'GesturePlugin'
        """
        return 'GesturePlugin'

    def initialize(self, config: dict) -> bool:
        """
        Inicializa el plugin usando el sensor inyectado por el orquestador.

        Args:
            config (dict): Parámetros de configuración. Claves relevantes:
                - 'detection_method' (str): Método (default 'opencv_contours').

        Returns:
            bool: True si el sensor está conectado y el plugin está listo.
        """
        if self._camera_sensor is None:
            logger.error("[GesturePlugin] No se inyectó un ICameraSensor.")
            return False
        self._detection_method = config.get('detection_method', 'opencv_contours')
        self._total_attempts = 0
        self._error_count = 0
        # Estado equivalente a C#: sensorX, sensorY, clickDown
        self._sensor_x = 0
        self._sensor_y = 0
        self._click_down = True

        self._initialized = True
        logger.info("[GesturePlugin] Sensor de cámara compartido conectado.")
        return True

    def execute(self) -> dict:
        """
        Ejecuta un ciclo de detección gestual.

        Equivalente a GestureRecognitionActivity.Capture_ImageGrabbed() en C#.
        Captura un frame y aplica detección por contornos.

        Returns:
            dict: Diccionario con claves:
                - 'gesture' (str): Nombre del gesto detectado.
                - 'confidence' (float): Confianza de la detección [0.0, 1.0].
                - 'position_x' (int): Coordenada X (equiv. C# xFinal).
                - 'position_y' (int): Coordenada Y (equiv. C# yFinal).
                - 'is_click' (bool): Si el gesto es un clic.
                - 'error_rate' (float): Tasa de error acumulada.
        """
        self._total_attempts += 1

        try:
            frame = (
                self._camera_sensor.get_latest_frame()
                if self._camera_sensor is not None
                else None
            )
            if frame is None:
                self._error_count += 1
                return {
                    'gesture': 'none',
                    'confidence': 0.0,
                    'position_x': 0,
                    'position_y': 0,
                    'is_click': False,
                    'error_rate': self.get_error_rate(),
                    'error': 'frame_capture_failed'
                }

            result = self.detect_gesture(frame)
            self._sensor_x = result.position_x
            self._sensor_y = result.position_y

            return {
                'gesture': result.gesture_name,
                'confidence': result.confidence,
                'position_x': result.position_x,
                'position_y': result.position_y,
                'is_click': result.is_click,
                'error_rate': self.get_error_rate()
            }

        except Exception as exc:
            self._error_count += 1
            logger.error(f"[GesturePlugin] Error en execute: {exc}")
            return {
                'gesture': 'none',
                'confidence': 0.0,
                'position_x': 0,
                'position_y': 0,
                'is_click': False,
                'error_rate': self.get_error_rate(),
                'error': str(exc)
            }

    def release(self) -> None:
        """
        Libera los recursos del plugin.

        El sensor compartido pertenece al orquestador; este plugin no lo cierra.
        """
        self._initialized = False

    def set_camera_sensor(self, sensor: ICameraSensor) -> None:
        if not isinstance(sensor, ICameraSensor):
            raise TypeError("GesturePlugin requiere una implementación de ICameraSensor.")
        self._camera_sensor = sensor

    def detect_gesture(self, frame: object) -> GestureResult:
        """
        Detecta un gesto en el frame dado usando contornos de OpenCV.

        Equivalente a IPlugin.RunPlugin(VideoCapture) + DetectObject() en C#.
        Busca el contorno más grande; si supera el área mínima, se clasifica
        el gesto como 'point'.

        Args:
            frame: numpy.ndarray con el frame de la cámara en BGR.

        Returns:
            GestureResult: Resultado del reconocimiento.
        """
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (11, 11), 0)
            _, thresh = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                            cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                return GestureResult(gesture_name='none', confidence=0.0,
                                     position_x=0, position_y=0)

            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)

            if area < self._MIN_CONTOUR_AREA:
                return GestureResult(gesture_name='none', confidence=0.0,
                                     position_x=0, position_y=0)

            M = cv2.moments(largest)
            cx = int(M['m10'] / M['m00']) if M['m00'] != 0 else 0
            cy = int(M['m01'] / M['m00']) if M['m00'] != 0 else 0
            confidence = min(1.0, area / (self._MIN_CONTOUR_AREA * 5))

            return GestureResult(
                gesture_name='point',
                confidence=round(confidence, 3),
                position_x=cx,
                position_y=cy,
                is_click=(confidence > 0.8)
            )
        except Exception as exc:
            logger.error(f"[GesturePlugin] Error en detect_gesture: {exc}")
            return GestureResult(gesture_name='none', confidence=0.0,
                                 position_x=0, position_y=0)

    def bounding_rect(self, frame: object) -> Optional[Tuple[int, int, int, int]]:
        """
        Calcula el rectángulo delimitador del contorno principal.

        Equivalente a FinalToRectXY() + FinalToRectWH() de C#.

        Args:
            frame: numpy.ndarray binarizado.

        Returns:
            tuple | None: (x, y, width, height) o None si no hay contorno.
        """
        try:
            contours, _ = cv2.findContours(frame, cv2.RETR_EXTERNAL,
                                            cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return None
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            return (x, y, w, h)
        except Exception as exc:
            logger.warning(f"[GesturePlugin] Advertencia en bounding_rect: {exc}")
            return None

    def get_error_rate(self) -> float:
        """
        Retorna la tasa de error gestual acumulada en la sesión.

        Métrica requerida por el informe de seminario.

        Returns:
            float: Tasa de error [0.0, 1.0] (0.0 = sin errores).
        """
        return self._error_count / max(1, self._total_attempts)
