# Comparte los contratos de sensores de cámara y otros adaptadores de sensores que producen frames.
from abc import abstractmethod
from typing import Optional, TypeAlias
import numpy as np
from numpy.typing import NDArray
from contracts.plugin_base import PluginBase

ImageArray: TypeAlias = NDArray[np.uint8]
CameraFrame: TypeAlias = ImageArray

class ICameraSensor(PluginBase):
    # Recibe su fuente de frames desde el orquestador, nunca abre una cámara.
    # Devuelve un frame de cámara o None si no hay frame disponible.
    @abstractmethod
    def capture_frame(self) -> Optional[CameraFrame]:
        # Captura un frame y lo hace la última muestra disponible.
        raise NotImplementedError

    @abstractmethod
    def get_latest_frame(self) -> Optional[CameraFrame]:
        # Devuelve el frame capturado durante el ciclo actual del orquestador.
        raise NotImplementedError
