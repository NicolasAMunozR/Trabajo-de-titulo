"""
orchestrator/orchestrator_core.py
=====================================
Núcleo orquestador del sistema EDDIE Python.

Gestiona el ciclo de vida completo de todos los plugins:
  initialize() → loop: execute() → release()

Características clave vs. el legacy C# (ProjectionScreenActivity2.cs):
  - Un bloque centralizado de manejo de excepciones (vs. bloques dispersos)
  - Aislamiento de fallos: un plugin que falla NO detiene los demás
  - Medición de latencia por ciclo (objetivo: ≤ 8.3 ms para 60Hz)
  - Logging estructurado en cada evento del ciclo de vida
"""
import json
import logging
import time
from pathlib import Path
from typing import Optional
from contracts.i_camera_frame_consumer import ICameraFrameConsumer
from contracts.i_camera_sensor import ICameraSensor
from contracts.i_cycle_result_consumer import ICycleResultConsumer
from contracts.plugin_base import PluginBase
from orchestrator.plugin_loader import PluginLoader

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Latencia máxima objetivo (8.3 ms = 1/120 segundos, conservador para 60Hz)
MAX_LATENCY_MS = 8.3


class OrchestratorCore:
    """
    Orquestador central del sistema EDDIE Python.

    Coordina el ciclo de vida de todos los plugins declarados
    en el archivo de configuración config/plugins.json.

    Uso básico:
        orch = OrchestratorCore('config/plugins.json')
        orch.initialize()
        orch.run(max_cycles=100)  # o run() para loop infinito
        orch.release()
    """

    def __init__(self, config_path: str = 'config/plugins.json'):
        """
        Args:
            config_path (str): Ruta al archivo JSON de configuración de plugins.
        """
        self.config_path = Path(config_path)
        self._plugins: list[PluginBase] = []
        self._loader = PluginLoader()
        self._is_running = False
        self._cycle_count = 0
        self._latency_history: list[float] = []
        self._last_cycle_metrics: dict[str, dict] = {}
        self._initialization_report: dict[str, dict] = {}

    # ─────────────────────────────────────────────
    # CICLO DE VIDA
    # ─────────────────────────────────────────────

    def initialize(self) -> bool:
        """
        Fase 1: Lee la configuración y carga + inicializa todos los plugins.

        Comportamiento ante fallos:
          - Si un plugin falla su initialize(), se registra el error pero
            el sistema CONTINÚA cargando los demás plugins.
          - Si NINGÚN plugin se inicializa, retorna False.

        Returns:
            bool: True si al menos un plugin se inicializó correctamente.
        """
        logger.info("=" * 60)
        logger.info("EDDIE Python - OrchestratorCore inicializando...")
        logger.info("=" * 60)

        # Leer configuración
        plugins_config = self._load_config()
        if plugins_config is None:
            logger.error(f"No se pudo leer la configuración desde: {self.config_path}")
            return False

        # Cargar plugins (instanciar clases dinámicamente)
        raw_plugins = self._loader.load_all(plugins_config)

        plugins_by_name = {plugin.instance_name: plugin for plugin in raw_plugins}
        loaded_names = set(plugins_by_name)
        config_by_name = {
            plugin_conf.get("name"): plugin_conf
            for plugin_conf in plugins_config
        }
        for plugin_conf in plugins_config:
            plugin_name = plugin_conf.get("name", "UnknownPlugin")
            if not plugin_conf.get("enabled", True):
                self._initialization_report[plugin_name] = {
                    "status": "disabled",
                    "error": None,
                }
            elif plugin_name not in loaded_names:
                self._initialization_report[plugin_name] = {
                    "status": "load_failed",
                    "error": "El plugin no se pudo cargar; revisa el log del PluginLoader.",
                }
            else:
                self._initialization_report[plugin_name] = {
                    "status": "pending",
                    "error": None,
                }
        initialization_state: dict[str, str] = {}

        def initialize_plugin(plugin_name: str) -> bool:
            plugin = plugins_by_name.get(plugin_name)
            plugin_conf = config_by_name.get(plugin_name)
            if plugin is None or plugin_conf is None:
                logger.error("Dependencia de plugin no disponible: %s", plugin_name)
                self._initialization_report.setdefault(plugin_name, {
                    "status": "dependency_unavailable",
                    "error": "No se encontró entre los plugins cargados.",
                })
                return False

            state = initialization_state.get(plugin_name)
            if state == "initialized":
                return True
            if state == "failed":
                return False
            if state == "initializing":
                logger.error("Dependencia circular detectada en el plugin %s.", plugin_name)
                initialization_state[plugin_name] = "failed"
                self._initialization_report[plugin_name] = {
                    "status": "initialization_failed",
                    "error": "Dependencia circular detectada.",
                }
                return False
            initialization_state[plugin_name] = "initializing"

            sensor_name = plugin_conf.get("dependencies", {}).get("camera_sensor")
            if sensor_name:
                sensor = plugins_by_name.get(sensor_name)
                if not isinstance(sensor, ICameraSensor):
                    logger.error(
                        "[%s] requiere '%s' como ICameraSensor; dependencia ausente o incompatible.",
                        plugin_name,
                        sensor_name,
                    )
                    initialization_state[plugin_name] = "failed"
                    self._initialization_report[plugin_name] = {
                        "status": "dependency_failed",
                        "error": f"'{sensor_name}' no implementa ICameraSensor.",
                    }
                    return False
                if not isinstance(plugin, ICameraFrameConsumer):
                    logger.error(
                        "[%s] declara un sensor, pero no implementa ICameraFrameConsumer.",
                        plugin_name,
                    )
                    initialization_state[plugin_name] = "failed"
                    self._initialization_report[plugin_name] = {
                        "status": "dependency_failed",
                        "error": "No implementa ICameraFrameConsumer.",
                    }
                    return False
                if not initialize_plugin(sensor_name):
                    logger.error("[%s] omitido porque el sensor %s no está disponible.",
                                 plugin_name, sensor_name)
                    initialization_state[plugin_name] = "failed"
                    self._initialization_report[plugin_name] = {
                        "status": "dependency_failed",
                        "error": f"El sensor '{sensor_name}' no se inicializó.",
                    }
                    return False
                plugin.set_camera_sensor(sensor)

            try:
                logger.info("Inicializando plugin: [%s]", plugin.instance_name)
                success = plugin.initialize(plugin_conf.get("config", {}))
                if not success:
                    logger.warning("[%s] initialize() retornó False — plugin omitido.",
                                   plugin_name)
                    initialization_state[plugin_name] = "failed"
                    self._initialization_report[plugin_name] = {
                        "status": "initialization_failed",
                        "error": "initialize() retornó False.",
                    }
                    return False
                self._plugins.append(plugin)
                plugin._initialized = True
                initialization_state[plugin_name] = "initialized"
                self._initialization_report[plugin_name] = {
                    "status": "initialized",
                    "error": None,
                }
                logger.info(                "  ✓ [%s] inicializado correctamente", plugin_name)
                return True
            except Exception as exc:
                logger.error(
                    "  ✗ [%s] lanzó excepción en initialize(): %s — plugin omitido",
                    plugin_name,
                    exc,
                )
                initialization_state[plugin_name] = "failed"
                self._initialization_report[plugin_name] = {
                    "status": "initialization_failed",
                    "error": str(exc),
                }
                return False

        for plugin in raw_plugins:
            initialize_plugin(plugin.instance_name)

        initialized_count = len(self._plugins)
        logger.info(f"Inicialización completa: {initialized_count}/{len(raw_plugins)} plugins activos")

        return initialized_count > 0

    def execute_cycle(self) -> dict:
        """
        Fase 2: Ejecuta UN ciclo del sistema (llama execute() en cada plugin).

        Mide la latencia total del ciclo y registra advertencia si supera 8.3 ms.

        Returns:
            dict: {plugin_name: resultado_execute()} para cada plugin.
                  Si un plugin falla, su entrada tiene {'error': str(excepción)}.
        """
        cycle_start = time.perf_counter()
        results = {}
        metrics = {}

        cycle_plugins = [
            plugin for plugin in self._plugins
            if not isinstance(plugin, ICycleResultConsumer)
        ] + [
            plugin for plugin in self._plugins
            if isinstance(plugin, ICycleResultConsumer)
        ]
        for plugin in cycle_plugins:
            plugin_start = time.perf_counter()
            status = "ok"
            try:
                if isinstance(plugin, ICycleResultConsumer):
                    plugin.consume_cycle_results(dict(results))
                result = plugin.execute()
                results[plugin.instance_name] = result
                if isinstance(result, dict) and result.get("error"):
                    status = "error"
            except Exception as e:
                # AISLAMIENTO DE FALLOS: un plugin que falla en execute()
                # no detiene la ejecución de los demás plugins.
                logger.error(f"[{plugin.instance_name}] excepción en execute(): {e}")
                results[plugin.instance_name] = {'error': str(e)}
                status = "error"
            finally:
                plugin_ms = (time.perf_counter() - plugin_start) * 1000
                metrics[plugin.instance_name] = {
                    "status": status,
                    "latency_ms": round(plugin_ms, 3),
                }
                if plugin_ms > MAX_LATENCY_MS:
                    logger.warning(
                        f"[{plugin.instance_name}] latencia alta: {plugin_ms:.2f} ms "
                        f"(objetivo: ≤ {MAX_LATENCY_MS} ms)"
                    )

        # Latencia total del ciclo
        total_ms = (time.perf_counter() - cycle_start) * 1000
        self._last_cycle_metrics = metrics
        self._latency_history.append(total_ms)
        self._cycle_count += 1

        if self._cycle_count % 100 == 0:  # Log cada 100 ciclos
            avg_ms = sum(self._latency_history[-100:]) / min(100, len(self._latency_history))
            logger.info(f"Ciclo #{self._cycle_count} | Latencia promedio (últimos 100): {avg_ms:.2f} ms")

        return results

    def run(self, max_cycles: Optional[int] = None) -> None:
        """
        Loop principal del sistema.

        Args:
            max_cycles (int | None): Número máximo de ciclos a ejecutar.
                                     None = loop infinito hasta KeyboardInterrupt.
        """
        self._is_running = True
        logger.info(f"Loop principal iniciado. Max ciclos: {max_cycles or 'infinito'}")

        try:
            cycle = 0
            while self._is_running:
                self.execute_cycle()
                cycle += 1

                if max_cycles is not None and cycle >= max_cycles:
                    logger.info(f"Se alcanzó el máximo de {max_cycles} ciclos.")
                    break

        except KeyboardInterrupt:
            logger.info("Interrupción del usuario (Ctrl+C). Deteniendo el sistema...")
        finally:
            self._is_running = False

    def release(self) -> None:
        """
        Fase 3: Libera recursos de todos los plugins en orden inverso.

        Si un plugin falla en release(), el error se registra pero
        el sistema continúa liberando los demás plugins.
        """
        logger.info("Liberando recursos del sistema...")

        # Orden inverso al de inicialización (como un stack LIFO)
        for plugin in reversed(self._plugins):
            try:
                plugin.release()
                logger.info(f"  ✓ [{plugin.instance_name}] recursos liberados")
            except Exception as e:
                logger.error(f"  ✗ [{plugin.instance_name}] excepción en release(): {e}")

        self._plugins.clear()
        logger.info("OrchestratorCore terminado correctamente.")
        self._print_latency_summary()

    # ─────────────────────────────────────────────
    # MÉTODOS AUXILIARES
    # ─────────────────────────────────────────────

    def _load_config(self) -> Optional[list]:
        """Lee el archivo plugins.json y retorna la lista de plugins."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('plugins', [])
        except FileNotFoundError:
            logger.error(f"Archivo de configuración no encontrado: {self.config_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear {self.config_path}: {e}")
            return None

    def _print_latency_summary(self) -> None:
        """Imprime resumen de métricas de latencia de la sesión."""
        if not self._latency_history:
            return
        avg = sum(self._latency_history) / len(self._latency_history)
        max_lat = max(self._latency_history)
        min_lat = min(self._latency_history)
        logger.info(
            f"\n{'='*50}\n"
            f"  RESUMEN DE LATENCIA ({self._cycle_count} ciclos)\n"
            f"  Promedio: {avg:.2f} ms\n"
            f"  Máxima:   {max_lat:.2f} ms\n"
            f"  Mínima:   {min_lat:.2f} ms\n"
            f"  Objetivo: ≤ {MAX_LATENCY_MS} ms\n"
            f"{'='*50}"
        )

    @property
    def active_plugins(self) -> list:
        """Retorna la lista de plugins actualmente activos."""
        return list(self._plugins)

    @property
    def cycle_count(self) -> int:
        """Retorna el número total de ciclos ejecutados."""
        return self._cycle_count

    @property
    def last_cycle_metrics(self) -> dict[str, dict]:
        """Per-plugin execution status and duration for the most recent cycle."""
        return {name: dict(metric) for name, metric in self._last_cycle_metrics.items()}

    @property
    def initialization_report(self) -> dict[str, dict]:
        """Configured plugin load and initialization outcomes."""
        return {
            name: dict(result)
            for name, result in self._initialization_report.items()
        }
