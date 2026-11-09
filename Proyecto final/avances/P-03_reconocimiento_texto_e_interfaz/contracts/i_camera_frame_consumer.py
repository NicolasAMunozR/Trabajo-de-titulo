# Dependencias de contratos de inyección de dependencias para plugins que consumen frames de cámara.
from abc import ABC, abstractmethod

from contracts.i_camera_sensor import ICameraSensor


class ICameraFrameConsumer(ABC):
    # Recibe su fuente de frames desde el orquestador, nunca abre una cámara.

    @abstractmethod
    def set_camera_sensor(self, sensor: ICameraSensor) -> None:
        # Unir la fuente de frames configurada antes de la inicialización del plugin.
        raise NotImplementedError
