# Contrato para la interacción por voz.
# Reemplaza System.Speech (síntesis y reconocimiento de comandos) de ProjectionScreenActivity2.cs.
from abc import abstractmethod
from typing import Callable

from contracts.plugin_base import PluginBase


class ISpeechProvider(PluginBase):
    # Síntesis de voz y reconocimiento de comandos.

    @abstractmethod
    def speak(self, text: str) -> None:
        # Lee el texto en voz alta sin bloquear (SpeakAsync).
        pass

    @abstractmethod
    def stop_speaking(self) -> None:
        # Cancela la lectura en curso (SpeakAsyncCancelAll).
        pass

    @abstractmethod
    def start_listening(self, commands: list[str], on_command: Callable[[str], None]) -> bool:
        # Escucha el micrófono y llama on_command(comando) cuando reconoce uno de la lista.
        pass

    @abstractmethod
    def stop_listening(self) -> None:
        # Detiene el reconocimiento de comandos.
        pass
