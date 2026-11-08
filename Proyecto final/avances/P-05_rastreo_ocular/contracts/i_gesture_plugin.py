"""
contracts/i_gesture_plugin.py
================================
Contrato para el módulo de reconocimiento gestual.

Reemplaza:
  - ModuloReconocimientoGestual/GestureRecognitionActivity.cs
  - ColorPenRecognition, HandSkinRecognition, LeapMotionRecognition
  - PluginFramework/IFilter.cs (IPlugin con RunPlugin(VideoCapture))
"""
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from contracts.i_camera_frame_consumer import ICameraFrameConsumer
from contracts.i_camera_sensor import CameraFrame
from contracts.plugin_base import PluginBase


@dataclass
class GestureResult:
    """Resultado de un ciclo de reconocimiento gestual."""
    gesture_name: str   # Nombre del gesto: 'point', 'scroll_up', 'scroll_down', 'none'
    confidence: float   # Confianza [0.0, 1.0]
    position_x: int     # Coordenada X en píxeles (espacio de pantalla)
    position_y: int     # Coordenada Y en píxeles (espacio de pantalla)
    is_click: bool = False  # True si el gesto debe interpretarse como un clic


@dataclass
class GestureCalibration:
    """Transformación lineal sensor → aplicación de GestureRecognitionActivity.cs.

    x_app = |(x_sensor - sensor_start_x) * (app_end_x - app_start_x)
             / (sensor_end_x - sensor_start_x) + app_start_x|
    Solo se aplica en los ejes con transform_x / transform_y activos.
    """
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
    """Rectángulo seleccionado con el gesto (RectangularSelection en C#)."""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    extra: dict = field(default_factory=dict)


class IGesturePlugin(PluginBase, ICameraFrameConsumer):
    """
    Contrato para el módulo de reconocimiento gestual.

    Unifica los distintos plugins gestuales del C# (ColorPen, HandSkin,
    LeapMotion, Mouse) bajo una única interfaz, eliminando el patrón
    IPlugin.RunPlugin(VideoCapture) que tenía acoplamiento a Emgu.CV.
    """

    @abstractmethod
    def detect_gesture(self, frame: CameraFrame) -> GestureResult:
        """
        Analiza un frame y retorna el gesto detectado.

        Args:
            frame: Frame BGR uint8 entregado por ICameraSensor.

        Returns:
            GestureResult: Resultado del reconocimiento.
        """
        pass

    @abstractmethod
    def set_recognition_active(self, active: bool) -> None:
        """Inicia/detiene el reconocimiento (botones Start/Stop Recognition)."""
        pass

    @abstractmethod
    def set_calibration(self, calibration: GestureCalibration) -> None:
        """Aplica la calibración sensor → pantalla configurada por el usuario."""
        pass

    @abstractmethod
    def get_preview_frame(self) -> Optional[CameraFrame]:
        """Último frame anotado por el plugin (imageBox2 en la interfaz)."""
        pass

    @abstractmethod
    def mark_selection_start(self) -> None:
        """Primer clic sobre el área de resaltado (FinalToRectXY)."""
        pass

    @abstractmethod
    def mark_selection_end(self) -> GestureSelection:
        """Fin de la selección (FinalToRectWH); retorna el rectángulo en píxeles de cámara."""
        pass

    @abstractmethod
    def capture_selection(self, selection: Optional[GestureSelection] = None) -> Optional[CameraFrame]:
        """Recorta del frame actual el rectángulo seleccionado (CaptureImage)."""
        pass

    @property
    @abstractmethod
    def auto_cam_capture(self) -> bool:
        """True si el plugin captura imagen automáticamente al soltar el gesto."""
        pass

    @abstractmethod
    def get_error_rate(self) -> float:
        """
        Retorna la tasa de error gestual acumulada en la sesión actual.
        Métrica requerida por el informe de seminario.

        Returns:
            float: Tasa de error [0.0, 1.0] (0 = sin errores).
        """
        pass
