# Interacción por voz (ISpeechProvider): síntesis con pyttsx3 y reconocimiento con SpeechRecognition.
# Si falta alguna librería se informa en initialize() y el resto de EDDIE sigue funcionando.
import logging
import queue
import threading
import unicodedata
from typing import Callable, Optional

from contracts.i_speech_provider import ISpeechProvider

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


class SpeechPlugin(ISpeechProvider):
    def __init__(self) -> None:
        self._speech_queue: "queue.Queue[Optional[str]]" = queue.Queue()
        self._tts_thread: Optional[threading.Thread] = None
        self._engine = None
        self._tts_available = False
        self._listening = threading.Event()
        self._listener: Optional[threading.Thread] = None
        self._recognizer_engine = "google"
        self._language = "es-ES"
        self._chunk_seconds = 3.0
        self._initialized = False

    @property
    def name(self) -> str:
        return "SpeechProvider"

    def initialize(self, config: dict) -> bool:
        self._recognizer_engine = config.get("recognizer", "google")
        self._language = config.get("language", "es-ES")
        self._chunk_seconds = float(config.get("chunk_seconds", 3.0))
        self._rate = int(config.get("rate", 165))
        self._tts_thread = threading.Thread(target=self._tts_loop, name="EDDIE-tts", daemon=True)
        self._tts_thread.start()
        self._initialized = True
        return True

    def execute(self) -> dict:
        return {"tts_available": self._tts_available, "listening": self._listening.is_set()}

    def release(self) -> None:
        self.stop_listening()
        self._speech_queue.put(None)
        if self._tts_thread is not None:
            self._tts_thread.join(timeout=2)
        self._initialized = False

    # ------------------------------------------------------------------ síntesis
    def _tts_loop(self) -> None:
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self._rate)
            for voice in self._engine.getProperty("voices"):
                tag = f"{voice.name} {voice.id}".lower()
                if "spanish" in tag or "español" in tag or "es-" in tag or "helena" in tag or "sabina" in tag:
                    self._engine.setProperty("voice", voice.id)
                    break
            self._tts_available = True
        except Exception as exc:
            logger.error("[SpeechProvider] Síntesis de voz no disponible: %s", exc)
            self._tts_available = False
        while True:
            text = self._speech_queue.get()
            if text is None:
                break
            if self._tts_available and text.strip():
                try:
                    self._engine.say(text)
                    self._engine.runAndWait()
                except Exception as exc:
                    logger.error("[SpeechProvider] Error al leer en voz alta: %s", exc)

    def speak(self, text: str) -> None:
        if not self._tts_available:
            raise RuntimeError("La síntesis de voz no está disponible (instale pyttsx3).")
        self._speech_queue.put(text)

    def stop_speaking(self) -> None:
        while not self._speech_queue.empty():
            try:
                self._speech_queue.get_nowait()
            except queue.Empty:
                break
        if self._engine is not None:
            try:
                self._engine.stop()
            except Exception:
                pass

    # ------------------------------------------------------------------ reconocimiento
    def start_listening(self, commands: list[str], on_command: Callable[[str], None]) -> bool:
        try:
            import numpy  # noqa: F401
            import sounddevice  # noqa: F401
            import speech_recognition  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("No hay reconocedor de voz instalado (pip install SpeechRecognition "
                               f"sounddevice): {exc}") from exc
        self.stop_listening()
        self._listening.set()
        self._listener = threading.Thread(target=self._listen_loop, args=(commands, on_command),
                                          name="EDDIE-stt", daemon=True)
        self._listener.start()
        return True

    def stop_listening(self) -> None:
        self._listening.clear()
        if self._listener is not None:
            self._listener.join(timeout=self._chunk_seconds + 1)
            self._listener = None

    def match_command(self, text: str, commands: list[str]) -> Optional[str]:
        heard = _normalize(text)
        for command in commands:
            if all(word in heard for word in _normalize(command).split()):
                return command
        return None

    def _listen_loop(self, commands: list[str], on_command: Callable[[str], None]) -> None:
        import numpy as np
        import sounddevice as sd
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        rate = 16000
        while self._listening.is_set():
            try:
                audio = sd.rec(int(self._chunk_seconds * rate), samplerate=rate, channels=1, dtype="int16")
                sd.wait()
                if np.abs(audio).mean() < 150:              # silencio
                    continue
                data = sr.AudioData(audio.tobytes(), rate, 2)
                if self._recognizer_engine == "whisper":
                    text = recognizer.recognize_whisper(data, language="spanish")
                elif self._recognizer_engine == "vosk":
                    text = recognizer.recognize_vosk(data)
                else:
                    text = recognizer.recognize_google(data, language=self._language)
            except Exception as exc:                       # UnknownValueError, sin red, etc.
                logger.debug("[SpeechProvider] Sin reconocimiento: %s", exc)
                continue
            command = self.match_command(text, commands)
            if command:
                logger.info("[SpeechProvider] Comando reconocido: %s", command)
                on_command(command)
