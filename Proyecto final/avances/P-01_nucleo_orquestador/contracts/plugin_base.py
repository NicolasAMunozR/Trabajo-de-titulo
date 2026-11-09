# Clase base abstracta para todos los plugins EDDIE.
# Todo plugin que se registre en el OrchestratorCore debe heredar
from abc import ABC, abstractmethod
from typing import Any


class PluginBase(ABC):
    # Recibe su fuente de datos desde el orquestador, nunca abre un micrófono, cámara ni navegador.
    @abstractmethod
    def initialize(self, config: dict) -> bool:
        # Devuelve True si la inicialización fue exitosa, False si falló.
        pass

    @abstractmethod
    def execute(self) -> dict:
        # Devuelve un diccionario con los datos producidos por el plugin en este ciclo.
        pass

    @abstractmethod
    def release(self) -> None:
        # Libera todos los recursos del plugin, como cámaras, sockets y archivos.
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        # Devuelve el nombre del tipo de plugin, que es el mismo para todas las instancias de ese tipo.
        pass

    def set_instance_name(self, name: str) -> None:
        # Asigna el identificador único declarado para esta instancia de plugin.
        self._instance_name = name

    @property
    def instance_name(self) -> str:
        # Devuelve el identificador único configurado para esta instancia de plugin, o el nombre del tipo de plugin si no se configuró un identificador.
        return getattr(self, "_instance_name", self.name)

    @property
    def is_initialized(self) -> bool:
        # Devuelve True si initialize() retornó True.
        return getattr(self, '_initialized', False)
