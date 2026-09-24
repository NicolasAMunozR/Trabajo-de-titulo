"""
contracts/i_eye_tracker.py
============================
Contrato de interfaz para el módulo de rastreo ocular (Eye Tracking).

Reemplaza:
  - InterfazEyeTracking/IEyeTracking.cs
  - ModuloRastreoOcular/IntermediateClass.cs (AppDomain proxy)
  - PluginEyeTribe, PluginGazeCloud
"""
from abc import abstractmethod
from typing import Optional
from dataclasses import dataclass
from contracts.plugin_base import PluginBase


@dataclass
class GazePoint:
    """Representa un punto de mirada en coordenadas normalizadas [0,1]."""
    x: float       # Coordenada horizontal (0=izquierda, 1=derecha)
    y: float       # Coordenada vertical   (0=arriba, 1=abajo)
    timestamp: float  # Timestamp en segundos (time.time())
    is_fixation: bool = False  # True si se detecta una fijación


class IEyeTracker(PluginBase):
    """
    Contrato para el módulo de rastreo ocular.

    Reemplaza el peligroso patrón AppDomain de IntermediateClass.cs,
    que cargaba los DLLs del eye tracker en dominios de aplicación
    aislados (uno de los 16 errores arquitectónicos críticos).
    """

    @abstractmethod
    def get_gaze_point(self) -> Optional[GazePoint]:
        """
        Obtiene el punto de mirada actual del eye tracker.

        Returns:
            GazePoint | None: Punto de mirada o None si no hay datos válidos.
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Verifica si el dispositivo eye tracker está conectado y operativo.

        Returns:
            bool: True si el dispositivo responde correctamente.
        """
        pass

    @abstractmethod
    def get_latency_ms(self) -> float:
        """
        Retorna la latencia de la última lectura de gaze en milisegundos.
        Requerimiento del seminario: ≤ 8.3 ms para dispositivos 60Hz.

        Returns:
            float: Latencia en milisegundos.
        """
        pass
