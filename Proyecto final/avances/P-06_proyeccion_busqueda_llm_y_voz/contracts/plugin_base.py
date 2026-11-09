# Contrato base para todos los plugins del sistema EDDIE Python.
# Ciclo de vida obligatorio: initialize() → execute() → release()
from abc import ABC, abstractmethod
from typing import Any


class PluginBase(ABC):
    # Clase base abstracta para todos los plugins EDDIE.
    # Todo plugin que se registre en el OrchestratorCore debe heredar de esta clase.

    @abstractmethod
    def initialize(self, config: dict) -> bool:
        # Inicializa el plugin con su configuración de plugins.json.
        # Devuelve True si la inicialización fue exitosa, False si falló.
        pass

    @abstractmethod
    def execute(self) -> dict:
        # Ejecuta un ciclo del plugin (objetivo ≤ 8,3 ms).
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
        # Devuelve el identificador configurado para esta instancia, o el nombre del tipo de plugin.
        return getattr(self, "_instance_name", self.name)

    @property
    def is_initialized(self) -> bool:
        # Devuelve True si initialize() retornó True.
        return getattr(self, '_initialized', False)
