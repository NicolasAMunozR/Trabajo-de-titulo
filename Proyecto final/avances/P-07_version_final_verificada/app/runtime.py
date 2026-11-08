"""
Puente entre el OrchestratorCore y la interfaz visual.
Un QTimer ejecuta orchestrator.execute_cycle() (por defecto 30 Hz) en el hilo de la interfaz; los sensores capturan en hilos propios, así un ciclo no se bloquea.
Las acciones bajo demanda (OCR, LLM, PDF, voz) se ejecutan con run_async() en un QThreadPool mediante OrchestratorCore.invoke(), y el resultado vuelve a la interfaz por señal. Esto reemplaza los Thread/LoadingBox ad hoc del C#.
Cada invocación queda en la traza JSONL (logs/) para la evaluación próxima.
"""
import logging
from pathlib import Path
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal

from app.settings_store import SettingsStore
from orchestrator.execution_trace import ExecutionTrace
from orchestrator.orchestrator_core import InvocationResult, OrchestratorCore

logger = logging.getLogger(__name__)

# Clase auxiliar para emitir señales desde hilos de trabajo
class _Signals(QObject):
    done = Signal(object, object)          # (callback, resultado de invocación)

# Clase auxiliar para ejecutar invocaciones en un hilo de trabajo
class _Job(QRunnable):
    # Constructor de la tarea de invocación
    def __init__(self, runtime: "EddieRuntime", plugin: str, method: str, args: tuple, kwargs: dict,
                 callback: Optional[Callable[[InvocationResult], None]]) -> None:
        super().__init__()
        self._runtime, self._plugin, self._method = runtime, plugin, method
        self._args, self._kwargs, self._callback = args, kwargs, callback
    # Ejecuta la invocación y emite la señal de resultado
    def run(self) -> None:
        result = self._runtime.invoke(self._plugin, self._method, *self._args, **self._kwargs)
        self._runtime._signals.done.emit(self._callback, result)

# Clase principal que conecta la interfaz con el OrchestratorCore
class EddieRuntime(QObject):
    cycle = Signal(dict)                    # resultados de cada ciclo del orquestador
    started = Signal(dict)                  # reporte de inicialización

    def __init__(self, settings: SettingsStore, config_path: str = "config/plugins.json",
                 cycle_hz: float = 30.0, trace_dir: str | Path = "logs") -> None:
        super().__init__()
        self.settings = settings
        self.config_path = config_path
        self.orchestrator = OrchestratorCore(config_path, settings.plugin_overrides())
        self.latest: dict[str, Any] = {}
        self._timer = QTimer(self)
        self._timer.setInterval(max(1, int(1000 / cycle_hz)))
        self._timer.timeout.connect(self._tick)
        self._pool = QThreadPool.globalInstance()
        self._signals = _Signals()
        self._signals.done.connect(self._deliver)
        self._trace: Optional[ExecutionTrace] = None
        try:
            self._trace = ExecutionTrace(trace_dir)
        except OSError as exc:
            logger.warning("No se pudo crear la traza de ejecución: %s", exc)
        self._running = False

    # ciclo de vida
    def start(self) -> bool:
        ok = self.orchestrator.initialize()
        report = self.orchestrator.initialization_report
        if self._trace:
            self._trace.record("initialization", report=report)
        self._running = True
        self._timer.start()
        self.started.emit(report)
        return ok

    def stop(self) -> None:
        if not self._running:
            return
        self._timer.stop()
        self.orchestrator.release()
        if self._trace:
            self._trace.close()
        self._running = False

    def _tick(self) -> None:
        self.latest = self.orchestrator.execute_cycle()
        self.cycle.emit(self.latest)

    # ------------------------------------------------------------------ acceso a plugins
    def plugin(self, name: str):
        return self.orchestrator.get_plugin(name)

    def plugins_for(self, contract: type) -> list[dict]:
        return self.orchestrator.declared_plugins(contract)

    def restart(self, name: str, config: Optional[dict] = None) -> bool:
        ok = self.orchestrator.restart_plugin(name, config)
        if self._trace:
            self._trace.record("plugin_restart", plugin=name, ok=ok, config=config or {})
        return ok

    def invoke(self, plugin: str, method: str, *args, **kwargs) -> InvocationResult:
        result = self.orchestrator.invoke(plugin, method, *args, **kwargs)
        if self._trace:
            self._trace.record("invoke", plugin=plugin, method=method, ok=result.ok,
                               error=result.error, latency_ms=result.latency_ms)
        return result

    def run_async(self, plugin: str, method: str, *args,
                  callback: Optional[Callable[[InvocationResult], None]] = None, **kwargs) -> None:
        self._pool.start(_Job(self, plugin, method, args, kwargs, callback))

    @staticmethod
    def _deliver(callback, result) -> None:
        if callback is not None:
            callback(result)

    def wait_for_jobs(self, msecs: int = 30000) -> None:
        self._pool.waitForDone(msecs)
