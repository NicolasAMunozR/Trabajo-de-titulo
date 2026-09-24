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
from typing import Optional
from dataclasses import dataclass
from contracts.plugin_base import PluginBase


@dataclass
class GestureResult:
    """Resultado de un ciclo de reconocimiento gestual."""
    gesture_name: str   # Nombre del gesto: 'point', 'scroll_up', 'scroll_down', 'none'
    confidence: float   # Confianza [0.0, 1.0]
    position_x: int     # Coordenada X en píxeles (espacio de pantalla)
    position_y: int     # Coordenada Y en píxeles (espacio de pantalla)
    is_click: bool = False  # True si el gesto debe interpretarse como un clic


class IGesturePlugin(PluginBase):
    """
    Contrato para el módulo de reconocimiento gestual.

    Unifica los distintos plugins gestuales del C# (ColorPen, HandSkin,
    LeapMotion, Mouse) bajo una única interfaz, eliminando el patrón
    IPlugin.RunPlugin(VideoCapture) que tenía acoplamiento a Emgu.CV.
    """

    @abstractmethod
    def detect_gesture(self, frame: object) -> GestureResult:
        """
        Analiza un frame y retorna el gesto detectado.

        Args:
            frame: numpy.ndarray con el frame de la cámara de gestos.

        Returns:
            GestureResult: Resultado del reconocimiento.
        """
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
