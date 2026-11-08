"""
orchestrator/device_factory.py
==============================
Capa de abstracción de hardware (DeviceFactory).

Cada plugin de hardware declarado en plugins.json puede indicar una implementación
simulada con la clave "simulated_class". DeviceFactory decide cuál cargar:

    EDDIE_DEVICE_MODE=real   → clase real (cámara física, eye tracker físico)   [por defecto]
    EDDIE_DEVICE_MODE=sim    → clase simulada (MockCameraSensor, EyeTrackerMock, ...)

También se puede forzar por plugin con "device_mode": "sim" | "real" en su entrada
(o en los ajustes del usuario). Esto permite validar el sistema completo sin el
montaje físico del laboratorio y distinguir una falla de sensor de una señal
experimental (sección 3.1 del informe).
"""
import logging
import os

logger = logging.getLogger(__name__)

ENV_VAR = "EDDIE_DEVICE_MODE"
VALID_MODES = ("real", "sim")


class DeviceFactory:
    """Resuelve la clase concreta de cada dispositivo según el modo real/simulado."""

    @staticmethod
    def global_mode() -> str:
        mode = os.environ.get(ENV_VAR, "real").strip().lower()
        if mode not in VALID_MODES:
            logger.warning("%s=%s no es válido; se usa 'real'.", ENV_VAR, mode)
            return "real"
        return mode

    @classmethod
    def resolve(cls, plugin_conf: dict) -> str:
        """Retorna el class_path que debe cargarse para esta entrada de plugins.json."""
        class_path = plugin_conf.get("class", "")
        simulated = plugin_conf.get("simulated_class")
        if not simulated:
            return class_path
        mode = plugin_conf.get("device_mode") or plugin_conf.get("config", {}).get("device_mode") or cls.global_mode()
        if mode == "sim":
            logger.info("DeviceFactory: '%s' usará la implementación simulada %s",
                        plugin_conf.get("name"), simulated)
            return simulated
        return class_path
