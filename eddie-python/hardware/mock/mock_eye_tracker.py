"""
hardware/mock/mock_eye_tracker.py
=====================================
Mock del Eye Tracker para desarrollo y testing sin hardware físico.

Genera coordenadas de gaze simuladas con distribución normal,
permitiendo validar el sistema sin necesitar GazePoint o TheEyeTribe.
"""
import time
import random
import math
from contracts.i_eye_tracker import IEyeTracker, GazePoint


class MockEyeTracker(IEyeTracker):
    """
    Simulador del eye tracker para desarrollo y tests.

    Genera coordenadas de gaze con ruido gaussiano alrededor de
    un punto de fijación simulado, imitando el comportamiento
    real de un tracker con fijaciones y sacadas.
    """

    @property
    def name(self) -> str:
        return "MockEyeTracker"

    def initialize(self, config: dict) -> bool:
        self._noise_std = config.get('noise_std', 0.02)
        self._fixation_duration = config.get('fixation_duration_s', 0.3)
        self._current_fixation_x = 0.5
        self._current_fixation_y = 0.5
        self._fixation_start = time.time()
        self._last_call_time = time.time()
        self._initialized = True
        return True

    def execute(self) -> dict:
        gaze = self.get_gaze_point()
        return {
            'gaze_x': gaze.x if gaze else None,
            'gaze_y': gaze.y if gaze else None,
            'is_fixation': gaze.is_fixation if gaze else False,
            'latency_ms': self.get_latency_ms()
        }

    def release(self) -> None:
        self._initialized = False

    def get_gaze_point(self) -> GazePoint:
        now = time.time()
        start = time.perf_counter()

        # Simular sacada cada fixation_duration segundos
        if now - self._fixation_start > self._fixation_duration:
            self._current_fixation_x = random.uniform(0.1, 0.9)
            self._current_fixation_y = random.uniform(0.1, 0.9)
            self._fixation_start = now

        # Agregar ruido gaussiano alrededor del punto de fijación
        x = random.gauss(self._current_fixation_x, self._noise_std)
        y = random.gauss(self._current_fixation_y, self._noise_std)
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))

        elapsed_ms = (time.perf_counter() - start) * 1000
        self._last_latency_ms = elapsed_ms

        return GazePoint(
            x=x,
            y=y,
            timestamp=now,
            is_fixation=(now - self._fixation_start < self._fixation_duration * 0.8)
        )

    def is_connected(self) -> bool:
        return self._initialized

    def get_latency_ms(self) -> float:
        return getattr(self, '_last_latency_ms', 0.0)
