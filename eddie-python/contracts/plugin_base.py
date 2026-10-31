"""
contracts/plugin_base.py
========================
Contrato base para todos los plugins del sistema EDDIE Python.

Reemplaza la interfaz IPlugin fragmentada del legacy C# (IFilter.cs,
InterfacesModuloWeb, InterfacesModuloConsistencia) unificándola en
una única clase abstracta con ciclo de vida estandarizado.

Ciclo de vida obligatorio:
    initialize() → execute() → release()
"""
from abc import ABC, abstractmethod
from typing import Any


class PluginBase(ABC):
    """
    Clase base abstracta para todos los plugins EDDIE.

    Todo plugin que se registre en el OrchestratorCore DEBE heredar
    de esta clase e implementar los tres métodos del ciclo de vida.
    """

    @abstractmethod
    def initialize(self, config: dict) -> bool:
        """
        Inicializa el plugin con su configuración.

        Se llama una única vez al arrancar el sistema. Si falla,
        el OrchestratorCore lo registra pero NO detiene el sistema.

        Args:
            config (dict): Parámetros de configuración leídos
                           del archivo plugins.json para este plugin.

        Returns:
            bool: True si la inicialización fue exitosa, False si falló.

        Raises:
            Exception: Cualquier excepción es capturada por el orquestador.
        """
        pass

    @abstractmethod
    def execute(self) -> dict:
        """
        Ejecuta un ciclo del plugin.

        Se llama en cada iteración del loop principal del orquestador.
        Debe ser lo más rápido posible (objetivo: ≤ 8.3 ms para 60 Hz).

        Returns:
            dict: Datos producidos por el plugin en este ciclo.
                  El formato depende de cada plugin.

        Raises:
            Exception: Cualquier excepción es capturada por el orquestador;
                       no debe propagarse para no detener otros plugins.
        """
        pass

    @abstractmethod
    def release(self) -> None:
        """
        Libera todos los recursos del plugin.

        Se llama en orden inverso al de inicialización al cerrar el sistema.
        Debe garantizar que cámaras, sockets y archivos queden cerrados.

        Raises:
            Exception: Capturada por el orquestador; se intenta release
                       de todos los plugins aunque alguno falle.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Nombre del tipo de plugin.

        Returns:
            str: Nombre del tipo, ej: 'ImageProcessorPlugin'.
        """
        pass

    def set_instance_name(self, name: str) -> None:
        """Assigns the unique identifier declared for this plugin instance."""
        self._instance_name = name

    @property
    def instance_name(self) -> str:
        """Returns the configured instance identifier, or the type name."""
        return getattr(self, "_instance_name", self.name)

    @property
    def is_initialized(self) -> bool:
        """
        Indica si el plugin fue inicializado exitosamente.

        Returns:
            bool: True si initialize() retornó True.
        """
        return getattr(self, '_initialized', False)
