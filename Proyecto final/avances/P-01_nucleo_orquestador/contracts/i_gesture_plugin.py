# Contrato para el módulo de reconocimiento gestual.
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from contracts.i_camera_frame_consumer import ICameraFrameConsumer
from contracts.i_camera_sensor import CameraFrame
from contracts.plugin_base import PluginBase

@dataclass
class GestureResult:
    # Resultado de un ciclo de reconocimiento gestual.
    gesture_name: str   # Nombre del gesto: 'point', 'scroll_up', 'scroll_down', 'none'
    confidence: float   # Confianza [0.0, 1.0]
    position_x: int     # Coordenada X en píxeles (espacio de pantalla)
    position_y: int     # Coordenada Y en píxeles (espacio de pantalla)
    is_click: bool = False  # True si el gesto debe interpretarse como un clic


@dataclass
class GestureCalibration:
    # Coordenadas de calibración del sensor y de la aplicación (pantalla).
    # Se usan para mapear las coordenadas del sensor a las coordenadas de la aplicación.
    sensor_start_x: float = 0
    sensor_end_x: float = 0
    app_start_x: float = 0
    app_end_x: float = 0
    sensor_start_y: float = 0
    sensor_end_y: float = 0
    app_start_y: float = 0
    app_end_y: float = 0
    transform_x: bool = False
    transform_y: bool = False
    mouse_control: bool = False   # checkbox "Recognition on": mueve el cursor del sistema


@dataclass
class GestureSelection:
    # Rectángulo en coordenadas de cámara (píxeles) que representa la selección del usuario.
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    extra: dict = field(default_factory=dict)


class IGesturePlugin(PluginBase, ICameraFrameConsumer):
    # Recibe su fuente de frames desde el orquestador, nunca abre una cámara.
    # Devuelve un resultado de reconocimiento gestual o None si no hay gesto válido.
    @abstractmethod
    def detect_gesture(self, frame: CameraFrame) -> GestureResult:
        # Devuelve el resultado del reconocimiento gestual para el frame dado, o None si no se detecta un gesto válido.
        pass

    @abstractmethod
    def set_recognition_active(self, active: bool) -> None:
        # Inicia o detiene el reconocimiento gestual. Cuando está activo, el plugin procesa los frames entrantes y genera resultados de gestos.
        pass

    @abstractmethod
    def set_calibration(self, calibration: GestureCalibration) -> None:
        # La calibración se aplica a las coordenadas de los gestos detectados.
        pass

    @abstractmethod
    def get_preview_frame(self) -> Optional[CameraFrame]:
        # Devuelve el último frame procesado por el plugin para previsualización, o None si no hay frame disponible.
        pass

    @abstractmethod
    def mark_selection_start(self) -> None:
        # Marca el inicio de la selección gestual (StartToRectXY). El plugin debe registrar la posición inicial del gesto.
        pass

    @abstractmethod
    def mark_selection_end(self) -> GestureSelection:
        # Marca el final de la selección gestual (EndToRectWH). El plugin debe calcular el rectángulo de selección basado en la posición inicial y final del gesto, y devolverlo.
        pass

    @abstractmethod
    def capture_selection(self, selection: Optional[GestureSelection] = None) -> Optional[CameraFrame]:
        # Recorta del frame actual el rectángulo seleccionado (CaptureImage). Si no se proporciona un rectángulo, utiliza la selección marcada por mark_selection_start/end. Devuelve el frame recortado o None si no hay selección válida.
        pass

    @property
    @abstractmethod
    def auto_cam_capture(self) -> bool:
        # Devuelve true si el plugin captura automáticamente la imagen al soltar el gesto, o False si requiere un comando explícito de captura.
        pass

    @abstractmethod
    def get_error_rate(self) -> float:
        # Devuelve la tasa de error gestual acumulada en la sesión actual.
        pass
