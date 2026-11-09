# Sesión de rastreo ocular (reemplaza IntermediateClass.cs).
# En cada ciclo mueve el cursor si "Mouse Control" está activo, guarda la mirada en CSV y la publica para la retícula.
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO

from contracts.i_cycle_result_consumer import ICycleResultConsumer
from contracts.plugin_base import PluginBase
from hardware.os_mouse import os_mouse

logger = logging.getLogger(__name__)


class GazeSessionPlugin(PluginBase, ICycleResultConsumer):
    def __init__(self) -> None:
        self._tracker_name: Optional[str] = None
        self._mouse_control = False
        self._csv: Optional[TextIO] = None
        self._csv_path: Optional[Path] = None
        self._screen = (1920, 1080)
        self._screen_origin = (0, 0)
        self._last_gaze = None
        self._last_screen_point: Optional[tuple[int, int]] = None
        self._click_register = 0
        self._samples = 0
        self._last_timestamp = None
        self._initialized = False

    @property
    def name(self) -> str:
        return "GazeSession"

    def initialize(self, config: dict) -> bool:
        self._screen = (int(config.get("screen_width", 1920)), int(config.get("screen_height", 1080)))
        self._initialized = True
        return True

    def configure_session(self, tracker_name: Optional[str], mouse_control: bool, save_data: bool,
                          save_route: str = "", file_name: str = "",
                          screen: Optional[tuple[int, int, int, int]] = None) -> Optional[str]:
        # Equivalente a IntermediateClass.InitializeClass(). Retorna la ruta del CSV, si aplica.
        self.close_session()
        self._tracker_name = tracker_name
        self._mouse_control = mouse_control
        if screen is not None:
            self._screen_origin = (screen[0], screen[1])
            self._screen = (screen[2], screen[3])
        if save_data:
            directory = Path(save_route or ".")
            directory.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            self._csv_path = directory / f"{file_name or 'eyetracking'} - {stamp}.csv"
            self._csv = self._csv_path.open("w", encoding="utf-8", newline="")
            return str(self._csv_path)
        return None

    def close_session(self) -> None:
        if self._csv is not None:
            self._csv.close()
            self._csv = None
        self._tracker_name = None
        self._mouse_control = False
        self._last_screen_point = None

    def register_click(self) -> None:
        # Un botón activado por permanencia de la mirada marca el clic en el CSV.
        self._click_register = 1

    def consume_cycle_results(self, results: dict[str, dict]) -> None:
        if not self._tracker_name:
            return
        gaze = results.get(self._tracker_name, {}).get("gaze")
        if gaze is None or gaze.timestamp == self._last_timestamp:
            return
        self._last_timestamp = gaze.timestamp
        self._last_gaze = gaze
        x = int(self._screen_origin[0] + gaze.x * self._screen[0])
        y = int(self._screen_origin[1] + gaze.y * self._screen[1])
        self._last_screen_point = (x, y)
        self._samples += 1
        if self._csv is not None:
            self._csv.write(f"{x}, {y}, {gaze.timestamp},{self._click_register}\n")
            self._csv.flush()
        self._click_register = 0
        if self._mouse_control and os_mouse().available:
            os_mouse().move(x, y)

    def execute(self) -> dict:
        return {
            "tracker": self._tracker_name,
            "screen_point": self._last_screen_point,
            "gaze": self._last_gaze,
            "mouse_control": self._mouse_control,
            "saving": self._csv is not None,
            "samples": self._samples,
        }

    @property
    def screen_point(self) -> Optional[tuple[int, int]]:
        return self._last_screen_point

    @property
    def mouse_control(self) -> bool:
        return self._mouse_control

    def release(self) -> None:
        self.close_session()
        self._initialized = False
