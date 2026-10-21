"""Eye tracker adapters for GazeCloud WebSocket and EyeTribe TCP devices."""
import json
import logging
import socket
import threading
import time
from typing import Optional

import websocket

from contracts.i_eye_tracker import GazePoint, IEyeTracker

logger = logging.getLogger(__name__)


class EyeTrackerPlugin(IEyeTracker):
    """Reads real gaze samples from a configured tracker service."""

    def __init__(self) -> None:
        self._connection = None
        self._backend = ""
        self._reader: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._gaze: Optional[GazePoint] = None
        self._latency_ms = -1.0
        self._screen_width = 1920
        self._screen_height = 1080
        self._initialized = False

    @property
    def name(self) -> str:
        return "EyeTracker"

    def initialize(self, config: dict) -> bool:
        self.release()
        backend = config.get("backend", "auto")
        if backend not in {"auto", "gazecloud", "eyetribe"}:
            raise ValueError(f"Backend de eye tracker no válido: {backend}")

        self._screen_width = int(config.get("screen_width", 1920))
        self._screen_height = int(config.get("screen_height", 1080))
        timeout = float(config.get("connection_timeout_s", 2.0))
        self._stop.clear()

        candidates = ("gazecloud", "eyetribe") if backend == "auto" else (backend,)
        for candidate in candidates:
            try:
                if candidate == "gazecloud":
                    self._connect_gazecloud(
                        config.get("gazecloud_url", "ws://127.0.0.1:3000"), timeout
                    )
                else:
                    self._connect_eyetribe(
                        config.get("eyetribe_host", "127.0.0.1"),
                        int(config.get("eyetribe_port", 6555)),
                        timeout
                    )
                self._backend = candidate
                self._reader = threading.Thread(
                    target=self._read_samples,
                    name=f"EDDIE-{candidate}-reader",
                    daemon=True
                )
                self._reader.start()
                self._initialized = True
                logger.info("Eye tracker conectado mediante %s.", candidate)
                return True
            except (OSError, websocket.WebSocketException) as exc:
                logger.info("No se pudo conectar al backend %s: %s", candidate, exc)

        logger.error(
            "No se encontró un eye tracker real. Inicie GazeCloud o conecte EyeTribe."
        )
        return False

    def execute(self) -> dict:
        gaze = self.get_gaze_point()
        return {
            "backend": self._backend,
            "connected": self.is_connected(),
            "gaze": gaze,
            "latency_ms": self.get_latency_ms()
        }

    def release(self) -> None:
        self._stop.set()
        connection = self._connection
        self._connection = None
        if connection is not None:
            try:
                connection.close()
            except (OSError, websocket.WebSocketException):
                logger.debug("Error al cerrar la conexión del eye tracker.", exc_info=True)
        if self._reader is not None:
            self._reader.join(timeout=1.5)
            self._reader = None
        self._initialized = False
        self._backend = ""

    def get_gaze_point(self) -> Optional[GazePoint]:
        with self._lock:
            return self._gaze

    def is_connected(self) -> bool:
        return self._initialized and not self._stop.is_set()

    def get_latency_ms(self) -> float:
        with self._lock:
            return self._latency_ms

    def _connect_gazecloud(self, url: str, timeout: float) -> None:
        self._connection = websocket.create_connection(url, timeout=timeout)
        self._connection.settimeout(1.0)

    def _connect_eyetribe(self, host: str, port: int, timeout: float) -> None:
        connection = socket.create_connection((host, port), timeout=timeout)
        connection.settimeout(1.0)
        connection.sendall(
            b'{"category":"tracker","request":"set","values":{"push":true}}\n'
        )
        self._connection = connection

    def _read_samples(self) -> None:
        connection = self._connection
        while not self._stop.is_set():
            try:
                if self._backend == "eyetribe":
                    message = connection.recv(4096)
                    if not message:
                        break
                else:
                    message = connection.recv()
                self._store_message(message)
            except (socket.timeout, websocket.WebSocketTimeoutException):
                continue
            except (OSError, websocket.WebSocketException) as exc:
                if not self._stop.is_set():
                    logger.warning("Conexión del eye tracker interrumpida: %s", exc)
                break
        self._stop.set()

    def _store_message(self, message: object) -> None:
        try:
            payload = json.loads(
                message.decode("utf-8") if isinstance(message, bytes) else str(message)
            )
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.debug("Se descartó un mensaje no JSON del eye tracker.")
            return

        coordinates = self._find_coordinates(payload)
        if coordinates is None:
            return
        x, y = coordinates
        if x > 1 or y > 1:
            x /= self._screen_width
            y /= self._screen_height
        if not (0 <= x <= 1 and 0 <= y <= 1):
            logger.debug("Se descartó un punto de mirada fuera de pantalla.")
            return

        now = time.time()
        source_timestamp = self._find_timestamp(payload)
        if source_timestamp is not None and source_timestamp > 1e12:
            source_timestamp /= 1000
        latency = (
            (now - source_timestamp) * 1000
            if source_timestamp is not None and 0 <= now - source_timestamp <= 60
            else -1.0
        )
        point = GazePoint(
            x=x,
            y=y,
            timestamp=source_timestamp if latency >= 0 else now
        )
        with self._lock:
            self._gaze = point
            self._latency_ms = latency

    @classmethod
    def _find_timestamp(cls, value: object) -> Optional[float]:
        if isinstance(value, dict):
            for key in ("timestamp", "ts"):
                if key in value:
                    try:
                        return float(value[key])
                    except (TypeError, ValueError):
                        pass
            for nested in value.values():
                timestamp = cls._find_timestamp(nested)
                if timestamp is not None:
                    return timestamp
        elif isinstance(value, list):
            for item in value:
                timestamp = cls._find_timestamp(item)
                if timestamp is not None:
                    return timestamp
        return None

    @classmethod
    def _find_coordinates(cls, value: object) -> Optional[tuple[float, float]]:
        if isinstance(value, dict):
            x_keys = ("x", "X", "x_coordinate", "X_Coordinate", "FPOGX")
            y_keys = ("y", "Y", "y_coordinate", "Y_Coordinate", "FPOGY")
            x = next((value[key] for key in x_keys if key in value), None)
            y = next((value[key] for key in y_keys if key in value), None)
            if x is not None and y is not None:
                try:
                    return float(x), float(y)
                except (TypeError, ValueError):
                    return None
            for nested in value.values():
                found = cls._find_coordinates(nested)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for item in value:
                found = cls._find_coordinates(item)
                if found is not None:
                    return found
        return None
