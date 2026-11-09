# Contrato para la interacción por voz.
from abc import abstractmethod
from typing import Callable
from contracts.plugin_base import PluginBase

class ISpeechProvider(PluginBase):
    # Recibe su fuente de audio desde el orquestador, nunca abre un micrófono.
    @abstractmethod
    def speak(self, text: str) -> None:
        # Devuelve inmediatamente y la lectura ocurre en segundo plano.
        pass

    @abstractmethod
    def stop_speaking(self) -> None:
        # Devuelve inmediatamente y la lectura se detiene en segundo plano.
        pass

    @abstractmethod
    def start_listening(self, commands: list[str], on_command: Callable[[str], None]) -> bool:
        # Devuelve True si el reconocimiento de comandos se inició correctamente, False si no se pudo iniciar.
        pass

    @abstractmethod
    def stop_listening(self) -> None:
        # Devuelve inmediatamente y el reconocimiento se detiene en segundo plano.
        pass
