"""
plugins/demo_plugins.py  (solo avance P-01)
==========================================
Plugins mínimos para validar el núcleo antes de migrar los módulos reales de EDDIE.

  FrameStatisticsPlugin  Consume la cámara declarada como dependencia (ICameraFrameConsumer)
                         y calcula el brillo medio del frame. Valida la inyección de
                         dependencias sensor → consumidor sin que el plugin abra la cámara.
  CycleSummaryPlugin     Implementa ICycleResultConsumer: recibe lo que produjeron los demás
                         plugins en el mismo ciclo. Valida el orden de ejecución del ciclo.
  FaultInjectionPlugin   Lanza una excepción cada N ciclos. Valida el aislamiento de fallos:
                         el resto de los plugins debe seguir ejecutándose.

Ninguno de estos plugins existe en EDDIE-2023; se usan como "plugins de prueba" del
núcleo, igual que el primer prototipo de Figueroa Contreras (2025) usó plugins básicos
de mouse/teclado para validar la arquitectura de MO.
"""
from typing import Optional

import numpy as np

from contracts.i_camera_frame_consumer import ICameraFrameConsumer
from contracts.i_camera_sensor import ICameraSensor
from contracts.i_cycle_result_consumer import ICycleResultConsumer
from contracts.plugin_base import PluginBase


class FrameStatisticsPlugin(PluginBase, ICameraFrameConsumer):
    """Lee el último frame del sensor inyectado y reporta tamaño y brillo medio."""

    def __init__(self) -> None:
        self._sensor: Optional[ICameraSensor] = None
        self._frames = 0

    @property
    def name(self) -> str:
        return "FrameStatisticsPlugin"

    def set_camera_sensor(self, sensor: ICameraSensor) -> None:
        self._sensor = sensor

    def initialize(self, config: dict) -> bool:
        return self._sensor is not None

    def execute(self) -> dict:
        frame = self._sensor.get_latest_frame() if self._sensor else None
        if frame is None:
            return {"frame": False}
        self._frames += 1
        return {"frame": True, "shape": list(frame.shape), "mean_intensity": round(float(np.mean(frame)), 2),
                "frames_processed": self._frames}

    def release(self) -> None:
        self._sensor = None


class CycleSummaryPlugin(PluginBase, ICycleResultConsumer):
    """Resume, al final de cada ciclo, qué plugins produjeron resultados y cuáles fallaron."""

    def __init__(self) -> None:
        self._seen: dict[str, dict] = {}

    @property
    def name(self) -> str:
        return "CycleSummaryPlugin"

    def initialize(self, config: dict) -> bool:
        return True

    def consume_cycle_results(self, results: dict[str, dict]) -> None:
        self._seen = results

    def execute(self) -> dict:
        failed = sorted(name for name, out in self._seen.items() if isinstance(out, dict) and out.get("error"))
        return {"plugins_before_me": sorted(self._seen), "failed_this_cycle": failed}

    def release(self) -> None:
        self._seen = {}


class FaultInjectionPlugin(PluginBase):
    """Falla de forma controlada cada `fail_every` ciclos (prueba de aislamiento de fallos)."""

    def __init__(self) -> None:
        self._every = 10
        self._count = 0

    @property
    def name(self) -> str:
        return "FaultInjectionPlugin"

    def initialize(self, config: dict) -> bool:
        self._every = max(1, int(config.get("fail_every", 10)))
        return True

    def execute(self) -> dict:
        self._count += 1
        if self._count % self._every == 0:
            raise RuntimeError(f"Falla inyectada en el ciclo {self._count}")
        return {"cycle": self._count}

    def release(self) -> None:
        self._count = 0
