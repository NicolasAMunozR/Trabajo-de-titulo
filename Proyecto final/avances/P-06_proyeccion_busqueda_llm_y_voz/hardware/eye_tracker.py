# Adaptadores de eye tracker: GazeCloud (WebSocket), TheEyeTribe (TCP 6555) y GazePoint (TCP 4242).
# Un único plugin IEyeTracker con varios backends reemplaza los DLLs y el AppDomain del C#.
import json
import logging
import re
import socket
import threading
import time
from typing import Optional

import websocket

from contracts.i_eye_tracker import GazePoint, IEyeTracker

logger = logging.getLogger(__name__)

_GAZEPOINT_ATTR = re.compile(r'(\w+)="([^"]*)"')


class _ServerHandle:
    # Adapta el servidor WebSocket a la interfaz close() de las conexiones.

    def __init__(self, server) -> None:
        self._server = server

    def close(self) -> None:
        self._server.shutdown()


class EyeTrackerPlugin(IEyeTracker):
    # Lee muestras reales de mirada desde el servicio del tracker configurado.

    BACKENDS = ("gazecloud", "gazecloud_client", "eyetribe", "gazepoint")

    def __init__(self) -> None:
        self._connection = None
        self._backend = ""
        self._reader: Optional[threading.Thread] = None
        self._heartbeat: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._gaze: Optional[GazePoint] = None
        self._latency_ms = -1.0
        self._samples = 0
        self._screen_width = 1920
        self._screen_height = 1080
        self._initialized = False

    @property
    def name(self) -> str:
        return "EyeTracker"

    # ------------------------------------------------------------------ ciclo de vida
    def initialize(self, config: dict) -> bool:
        self.release()
        backend = config.get("backend", "auto")
        if backend != "auto" and backend not in self.BACKENDS:
            raise ValueError(f"Backend de eye tracker no válido: {backend}")

        self._screen_width = int(config.get("screen_width", 1920))
        self._screen_height = int(config.get("screen_height", 1080))
        timeout = float(config.get("connection_timeout_s", 2.0))
        self._stop.clear()

        candidates = ("gazepoint", "eyetribe", "gazecloud_client") if backend == "auto" else (backend,)
        for candidate in candidates:
            try:
                if candidate == "gazecloud":
                    self._start_gazecloud_server(config.get("gazecloud_host", "127.0.0.1"),
                                                 int(config.get("gazecloud_port", 3000)))
                    reader = None                                  # el servidor ya tiene su hilo
                elif candidate == "gazecloud_client":
                    self._connect_gazecloud(config.get("gazecloud_url", "ws://127.0.0.1:3000"), timeout)
                    reader = self._read_samples
                elif candidate == "eyetribe":
                    self._connect_eyetribe(config.get("eyetribe_host", "127.0.0.1"),
                                           int(config.get("eyetribe_port", 6555)), timeout)
                    reader = self._read_samples
                else:
                    self._connect_gazepoint(config.get("gazepoint_host", "127.0.0.1"),
                                            int(config.get("gazepoint_port", 4242)), timeout)
                    reader = self._read_samples
                self._backend = candidate
                if reader is not None:
                    self._reader = threading.Thread(target=reader, name=f"EDDIE-{candidate}-reader",
                                                    daemon=True)
                    self._reader.start()
                self._initialized = True
                logger.info("Eye tracker conectado mediante %s.", candidate)
                return True
            except (OSError, websocket.WebSocketException, RuntimeError) as exc:
                logger.info("No se pudo conectar al backend %s: %s", candidate, exc)

        logger.error("No se encontró un eye tracker real. Inicie GazePoint Control, "
                     "EyeTribe Server o GazeCloud.")
        return False

    def execute(self) -> dict:
        gaze = self.get_gaze_point()
        return {
            "backend": self._backend,
            "connected": self.is_connected(),
            "gaze": gaze,
            "latency_ms": self.get_latency_ms(),
            "samples": self._samples,
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
        for thread in (self._reader, self._heartbeat):
            if thread is not None:
                thread.join(timeout=1.5)
        self._reader = None
        self._heartbeat = None
        self._initialized = False
        self._backend = ""

    # ------------------------------------------------------------------ contrato
    def get_gaze_point(self) -> Optional[GazePoint]:
        with self._lock:
            return self._gaze

    def is_connected(self) -> bool:
        return self._initialized and not self._stop.is_set()

    def get_latency_ms(self) -> float:
        with self._lock:
            return self._latency_ms

    # ------------------------------------------------------------------ conexiones
    def _connect_gazecloud(self, url: str, timeout: float) -> None:
        self._connection = websocket.create_connection(url, timeout=timeout)
        self._connection.settimeout(1.0)

    def _start_gazecloud_server(self, host: str, port: int) -> None:
        # Servidor WebSocket como PluginGazeCloud.cs (127.0.0.1:3000); el navegador envía "x,y,timestamp".
        try:
            from websockets.sync.server import serve  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Instale 'websockets' (>=12) para usar GazeCloud.") from exc

        def handler(connection) -> None:
            for message in connection:
                if self._stop.is_set():
                    break
                if message != "OK":
                    self._store_message(message)

        server = serve(handler, host, port)                 # lanza OSError si el puerto está ocupado
        self._connection = _ServerHandle(server)
        self._reader = threading.Thread(target=server.serve_forever, name="EDDIE-gazecloud-server",
                                        daemon=True)
        self._reader.start()

    def _connect_eyetribe(self, host: str, port: int, timeout: float) -> None:
        connection = socket.create_connection((host, port), timeout=timeout)
        connection.settimeout(1.0)
        connection.sendall(
            b'{"category":"tracker","request":"set","values":{"push":true,"version":1}}\n'
        )
        self._connection = connection

        def heartbeat():                       # EyeTribe Server corta la conexión sin heartbeat
            while not self._stop.wait(2.0):
                try:
                    connection.sendall(b'{"category":"heartbeat","request":null}\n')
                except OSError:
                    break
        self._heartbeat = threading.Thread(target=heartbeat, name="EDDIE-eyetribe-heartbeat", daemon=True)
        self._heartbeat.start()

    def _connect_gazepoint(self, host: str, port: int, timeout: float) -> None:
        connection = socket.create_connection((host, port), timeout=timeout)
        connection.settimeout(1.0)
        for command in ("ENABLE_SEND_TIME", "ENABLE_SEND_POG_FIX", "ENABLE_SEND_DATA"):
            connection.sendall(f'<SET ID="{command}" STATE="1" />\r\n'.encode())
        self._connection = connection

    def _read_samples(self) -> None:
        connection = self._connection
        buffer = ""
        while not self._stop.is_set() and connection is not None:
            try:
                if self._backend in ("eyetribe", "gazepoint"):
                    chunk = connection.recv(4096)
                    if not chunk:
                        break
                    buffer += chunk.decode("utf-8", "ignore")
                    *lines, buffer = re.split(r"\r?\n", buffer)
                    for line in lines:
                        if line.strip():
                            self._store_message(line)
                else:
                    self._store_message(connection.recv())
            except (socket.timeout, websocket.WebSocketTimeoutException):
                continue
            except (OSError, websocket.WebSocketException) as exc:
                if not self._stop.is_set():
                    logger.warning("Conexión del eye tracker interrumpida: %s", exc)
                break
        self._stop.set()

    # ------------------------------------------------------------------ parsing
    def _store_message(self, message: object) -> None:
        text = message.decode("utf-8", "ignore") if isinstance(message, bytes) else str(message)
        text = text.strip()
        if text.startswith("<"):
            self._store_gazepoint(text)
            return
        payload = None
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            parts = [p.strip().strip('"') for p in text.split(",")]
            if len(parts) >= 2:                             # Formato GazeCloud "x,y,timestamp"
                try:
                    payload = {"x": float(parts[0]), "y": float(parts[1])}
                    if len(parts) >= 3 and parts[2]:
                        payload["timestamp"] = float(parts[2])
                except ValueError:
                    payload = None
        if payload is None:
            logger.debug("Se descartó un mensaje no reconocido del eye tracker.")
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
        source_timestamp = self._find_timestamp(payload)
        self._commit(x, y, source_timestamp, bool(self._find_key(payload, "fix")))

    def _store_gazepoint(self, text: str) -> None:
        if not text.startswith("<REC"):
            return
        attrs = dict(_GAZEPOINT_ATTR.findall(text))
        try:
            x, y = float(attrs["FPOGX"]), float(attrs["FPOGY"])
        except (KeyError, ValueError):
            return
        if attrs.get("FPOGV", "1") != "1" or not (0 <= x <= 1 and 0 <= y <= 1):
            return
        self._commit(x, y, None, True)

    def _commit(self, x: float, y: float, source_timestamp: Optional[float], fixation: bool) -> None:
        now = time.time()
        if source_timestamp is not None and source_timestamp > 1e12:
            source_timestamp /= 1000
        latency = (
            (now - source_timestamp) * 1000
            if source_timestamp is not None and 0 <= now - source_timestamp <= 60
            else -1.0
        )
        point = GazePoint(x=x, y=y, timestamp=source_timestamp if latency >= 0 else now,
                          is_fixation=fixation)
        with self._lock:
            self._gaze = point
            self._latency_ms = latency
            self._samples += 1

    @classmethod
    def _find_key(cls, value: object, key: str) -> object:
        if isinstance(value, dict):
            if key in value:
                return value[key]
            for nested in value.values():
                found = cls._find_key(nested, key)
                if found is not None:
                    return found
        return None

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
            if isinstance(value.get("smoothed"), dict):          # EyeTribe: SmoothedCoordinates
                found = cls._find_coordinates(value["smoothed"])
                if found is not None and found != (0.0, 0.0):
                    return found
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
