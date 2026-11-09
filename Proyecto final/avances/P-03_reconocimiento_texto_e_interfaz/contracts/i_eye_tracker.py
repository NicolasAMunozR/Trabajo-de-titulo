# Contrato para el módulo de rastreo ocular (Eye Tracking).
# Reemplaza IEyeTracking.cs, IntermediateClass.cs (AppDomain) y los plugins EyeTribe y GazeCloud.
from abc import abstractmethod
from typing import Optional
from dataclasses import dataclass
from contracts.plugin_base import PluginBase


@dataclass
class GazePoint:
    # Representa un punto de mirada en coordenadas normalizadas [0,1].
    x: float       # Coordenada horizontal (0=izquierda, 1=derecha)
    y: float       # Coordenada vertical   (0=arriba, 1=abajo)
    timestamp: float  # Timestamp en segundos (time.time())
    is_fixation: bool = False  # True si se detecta una fijación


class IEyeTracker(PluginBase):
    # Contrato para el módulo de rastreo ocular.
    # Reemplaza el patrón AppDomain de IntermediateClass.cs, uno de los 16 errores arquitectónicos críticos.

    @abstractmethod
    def get_gaze_point(self) -> Optional[GazePoint]:
        # Devuelve el punto de mirada actual del eye tracker, o None si no hay datos válidos.
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        # Devuelve True si el dispositivo eye tracker está conectado y operativo.
        pass

    @abstractmethod
    def get_latency_ms(self) -> float:
        # Devuelve la latencia de la última lectura de gaze en milisegundos (-1.0 si no se puede calcular).
        pass
