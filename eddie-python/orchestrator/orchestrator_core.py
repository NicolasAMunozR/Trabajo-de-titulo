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

        # Inicializar cada plugin con su configuración individual
        for i, plugin_conf in enumerate(plugins_config):
            # Buscar el plugin correspondiente en la lista cargada
            plugin = next(
                (p for p in raw_plugins if p.name == plugin_conf.get('name', '')),
                None
            )
            if plugin is None:
                continue

            plugin_config = plugin_conf.get('config', {})
            try:
                logger.info(f"Inicializando plugin: [{plugin.name}]")
                success = plugin.initialize(plugin_config)
                if success:
                    self._plugins.append(plugin)
                    # Marcar como inicializado internamente
                    plugin._initialized = True
                    logger.info(f"  ✓ [{plugin.name}] inicializado correctamente")
                else:
                    logger.warning(f"  ✗ [{plugin.name}] initialize() retornó False — plugin omitido")
            except Exception as e:
                # AISLAMIENTO DE FALLOS: capturamos la excepción del plugin,
                # registramos el error, y continuamos con el siguiente.
                logger.error(
                    f"  ✗ [{plugin.name}] lanzó excepción en initialize(): {e} — plugin omitido"
                )

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

        for plugin in self._plugins:
            plugin_start = time.perf_counter()
            try:
                result = plugin.execute()
                results[plugin.name] = result
            except Exception as e:
                # AISLAMIENTO DE FALLOS: un plugin que falla en execute()
                # no detiene la ejecución de los demás plugins.
                logger.error(f"[{plugin.name}] excepción en execute(): {e}")
                results[plugin.name] = {'error': str(e)}
            finally:
                plugin_ms = (time.perf_counter() - plugin_start) * 1000
                if plugin_ms > MAX_LATENCY_MS:
                    logger.warning(
                        f"[{plugin.name}] latencia alta: {plugin_ms:.2f} ms "
                        f"(objetivo: ≤ {MAX_LATENCY_MS} ms)"
                    )

        # Latencia total del ciclo
        total_ms = (time.perf_counter() - cycle_start) * 1000
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
                logger.info(f"  ✓ [{plugin.name}] recursos liberados")
            except Exception as e:
                logger.error(f"  ✗ [{plugin.name}] excepción en release(): {e}")

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
