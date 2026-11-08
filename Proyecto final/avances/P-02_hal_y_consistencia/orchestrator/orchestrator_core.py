"""
Núcleo orquestador del sistema EDDIE Python (Nucleo que gestiona el ciclo de vida de los plugins Inicializar → ejecutar → liberar).
Un bloque centralizado de manejo de excepciones.
Aislamiento de fallos: un plugin que falla NO detiene los demás.
Medición de latencia por ciclo (objetivo: ≤ 8.3 ms para 60Hz (Ya que es una medida estandar de latencia de 120Hz, se toma un margen conservador para 60Hz)).
Logging estructurado en cada evento del ciclo de vida 
"""
# Importaciones de librerías
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from contracts.i_camera_frame_consumer import ICameraFrameConsumer
from contracts.i_camera_sensor import ICameraSensor
from contracts.i_cycle_result_consumer import ICycleResultConsumer
from contracts.plugin_base import PluginBase
from orchestrator.device_factory import DeviceFactory
from orchestrator.plugin_loader import PluginLoader

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)
# Crear un logger específico para este módulo (Objeto que maneja los mensajes de log)
logger = logging.getLogger(__name__)

# Latencia máxima objetivo (8.3 ms = 1/120 segundos, conservador para 60Hz)
MAX_LATENCY_MS = 8.3


@dataclass
class InvocationResult:
    """Resultado de una llamada bajo demanda a un plugin (OrchestratorCore.invoke)."""
    ok: bool
    value: Any
    error: Optional[str]
    latency_ms: float

# Clase principal del orquestador (gestiona el ciclo de vida de los plugins)
class OrchestratorCore:
    """
    Coordina el ciclo de vida de todos los plugins declarados en el archivo de configuración config/plugins.json.
    """
    # Definición del constructor de la clase OrchestratorCore
    def __init__(self, config_path: str = 'config/plugins.json', config_overrides: Optional[dict] = None):
        """
        Inicializa el núcleo del orquestador con la ruta al archivo de configuración de plugins.
        config_path (str): Ruta al archivo JSON de configuración de plugins.
        config_overrides (dict | None): Ajustes del usuario que se superponen a plugins.json
            sin modificar el archivo, con forma {nombre_plugin: {"enabled": bool, "config": {...}}}.
            Reemplaza a los Properties.Settings del C# legado (índice de cámara, resolución, etc.).
        """
        self.config_path = Path(config_path)                # Ruta al archivo de configuración de plugins
        self._config_overrides: dict = dict(config_overrides or {})  # Ajustes de usuario superpuestos a plugins.json
        self._plugins_config: list[dict] = []               # Configuración efectiva (plugins.json + overrides) usada en initialize()
        self._plugins: list[PluginBase] = []                # Lista de instancias de plugins cargados e inicializados
        self._loader = PluginLoader()                       # Instancia del cargador de plugins (PluginLoader)
        self._is_running = False                            # Bandera para indicar si el loop principal está activo
        self._cycle_count = 0                               # Contador de ciclos ejecutados
        self._latency_history: list[float] = []             # Lista de latencias de ciclos ejecutados (en milisegundos)
        self._last_cycle_metrics: dict[str, dict] = {}      # Diccionario con métricas del último ciclo ejecutado (por plugin)
        self._initialization_report: dict[str, dict] = {}   # Diccionario con resultados de carga e inicialización de plugins (por plugin)

    # Definición de los métodos principales del ciclo de vida del orquestador: initialize(), execute_cycle(), run(), release()
    def initialize(self) -> bool:
        """
        Lee la configuración y carga más inicializa todos los plugins.
        - Si un plugin falla su initialize(), se registra el error pero el sistema continúa cargando los demás plugins.
        - Si ningún plugin se inicializa, retorna False.
        Retorna un bool: True si al menos un plugin se inicializó correctamente.
        """
        plugins_config = self._load_config()                                            # Lee la configuración de plugins desde el archivo JSON
        if plugins_config is None:                                                      # No se pudo leer la configuración
            logger.error(f"No se pudo leer la configuración desde: {self.config_path}")
            return False
        plugins_config = self._apply_overrides(plugins_config)                          # Superpone los ajustes de usuario a la configuración declarada
        self._plugins_config = plugins_config

        raw_plugins = self._loader.load_all(plugins_config)                             # Carga todas las clases de plugins desde los módulos especificados en la configuración

        plugins_by_name = {plugin.instance_name: plugin for plugin in raw_plugins}      # Diccionario de plugins cargados, indexado por su nombre de instancia
        loaded_names = set(plugins_by_name)                                             # Conjunto de nombres de plugins cargados exitosamente
        config_by_name = {                                                             
            plugin_conf.get("name"): plugin_conf                                    
            for plugin_conf in plugins_config                            
        }
        for plugin_conf in plugins_config:                               
            plugin_name = plugin_conf.get("name", "UnknownPlugin")       # Obtiene el nombre del plugin desde la configuración (o "UnknownPlugin" si no está definido)
            if not plugin_conf.get("enabled", True):                     # Verifica si el plugin está habilitado
                self._initialization_report[plugin_name] = {             # Registra el estado del plugin como "disabled" en el informe de inicialización
                    "status": "disabled",
                    "error": None,
                }
            elif plugin_name not in loaded_names:                        # Verifica si el plugin no se cargó correctamente 
                self._initialization_report[plugin_name] = {                                    
                    "status": "load_failed",
                    "error": "El plugin no se pudo cargar; revisa el log del PluginLoader.",
                }
            else:
                self._initialization_report[plugin_name] = {             # Registra el estado del plugin como "pending" en el informe de inicialización
                    "status": "pending",
                    "error": None,
                }
        initialization_state: dict[str, str] = {}               # Diccionario para rastrear el estado de inicialización de cada plugin: "pending", "initializing", "initialized"

        # Función recursiva para inicializar un plugin y sus dependencias
        def initialize_plugin(plugin_name: str) -> bool:        
            plugin = plugins_by_name.get(plugin_name)           # Obtiene la instancia del plugin desde el diccionario de plugins cargados
            plugin_conf = config_by_name.get(plugin_name)       # Obtiene la configuración del plugin desde el diccionario de configuraciones
            if plugin is None or plugin_conf is None:           # Verifica si el plugin o su configuración no están disponibles 
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
                initialization_state[plugin_name] = "failed"    # Marca el estado del plugin como "failed" para evitar reintentos
                self._initialization_report[plugin_name] = {
                    "status": "initialization_failed",
                    "error": "Dependencia circular detectada.",
                }
                return False
            initialization_state[plugin_name] = "initializing"  # Marca el estado del plugin como "initializing" para evitar reentradas y detectar dependencias circulares

            sensor_name = plugin_conf.get("dependencies", {}).get("camera_sensor")      # Obtiene el nombre del sensor de cámara requerido por el plugin desde la configuración (si existe)
            if sensor_name:                                         # Si el plugin declara un sensor de cámara como dependencia, se verifica que el sensor esté disponible y sea compatible
                sensor = plugins_by_name.get(sensor_name)           
                if not isinstance(sensor, ICameraSensor):           
                    logger.error(
                        "%s requiere '%s' como ICameraSensor; dependencia ausente o incompatible.",
                        plugin_name,            # Nombre del plugin que requiere el sensor
                        sensor_name,            # Nombre del sensor declarado como dependencia
                    )
                    initialization_state[plugin_name] = "failed"    # Marca el estado del plugin como "failed" para indicar que no se pudo inicializar debido a la dependencia fallida
                    self._initialization_report[plugin_name] = {    # Indica que la dependencia no implementa ICameraSensor
                        "status": "dependency_failed",
                        "error": f"'{sensor_name}' no implementa ICameraSensor.",
                    }
                    return False
                if not isinstance(plugin, ICameraFrameConsumer):    # Si no se verifica, no puede consumir frames del sensor
                    logger.error(
                        "%s declara un sensor, pero no implementa ICameraFrameConsumer.",
                        plugin_name,            # Nombre del plugin que declara un sensor pero no implementa la interfaz requerida
                    )
                    initialization_state[plugin_name] = "failed"    # Marca el estado del plugin como "failed" para indicar la falta de implementación de la interfaz requerida
                    self._initialization_report[plugin_name] = {    # Registra el estado del plugin como "dependency_failed"
                        "status": "dependency_failed",
                        "error": "No implementa ICameraFrameConsumer.",
                    }
                    return False
                if not initialize_plugin(sensor_name):              # Inicializa recursivamente el sensor de cámara antes de inicializar el plugin que depende de él.
                    logger.error(
                        "%s omitido porque el sensor %s no está disponible.",
                        plugin_name,            # Nombre del plugin que depende del sensor
                        sensor_name             # Nombre del sensor que falló en inicialización
                    ) 
                    initialization_state[plugin_name] = "failed"    # Marca el estado del plugin como "failed" para indicar que no se pudo inicializar debido a la dependencia fallida
                    self._initialization_report[plugin_name] = {    # Registra el estado del plugin como "dependency_failed" 
                        "status": "dependency_failed",
                        "error": f"El sensor '{sensor_name}' no se inicializó.",
                    }
                    return False
                plugin.set_camera_sensor(sensor)        # Asocia el sensor de cámara al plugin que lo requiere, permitiendo que el plugin consuma frames del sensor durante su ejecución.

            # Inicializa el plugin llamando a su método initialize() con la configuración específica del plugin.
            try:
                logger.info("Inicializando plugin: %s", plugin.instance_name)         # Registra un mensaje de información indicando que se está inicializando el plugin con su nombre de instancia
                success = plugin.initialize(plugin_conf.get("config", {}))            # Llama al método initialize() del plugin, pasando la configuración específica del plugin como argumento.
                if not success:             
                    logger.warning(
                        "%s initialize() retornó False — plugin omitido.",
                        plugin_name         # Nombre del plugin que falló en inicialización
                    )
                    initialization_state[plugin_name] = "failed"            # Marca el estado del plugin como "failed" para indicar que no se pudo inicializar 
                    self._initialization_report[plugin_name] = {            # Registra el estado del plugin como "initialization_failed"
                        "status": "initialization_failed",
                        "error": "initialize() retornó False.",
                    }
                    return False
                self._plugins.append(plugin)                        # Agrega el plugin a la lista de plugins activos del orquestador, indicando que estará disponible para ejecutar ciclos.                                
                plugin._initialized = True                          
                initialization_state[plugin_name] = "initialized"  
                self._initialization_report[plugin_name] = {        
                    "status": "initialized",
                    "error": None,
                }
                logger.info(
                    "%s inicializado correctamente", 
                    plugin_name             # Nombre del plugin que se inicializó correctamente
                )
                return True
            except Exception as exc:        # Captura cualquier excepción que ocurra durante la inicialización del plugin
                logger.error(
                    "%s lanzó excepción en initialize(): %s, plugin omitido",
                    plugin_name,            # Nombre del plugin que lanzó la excepción durante la inicialización
                    exc,                    # Mensaje de la excepción capturada
                )
                initialization_state[plugin_name] = "failed"        # Marca el estado del plugin como "failed" 
                self._initialization_report[plugin_name] = {        # Registra el estado del plugin como "initialization_failed"
                    "status": "initialization_failed",
                    "error": str(exc),
                }
                return False
        for plugin in raw_plugins:                     
            initialize_plugin(plugin.instance_name)     # Llama a la función recursiva initialize_plugin() pasando el nombre de instancia del plugin actual para iniciar su proceso.

        initialized_count = len(self._plugins)          # Cuenta el número de plugins que se inicializaron correctamente.
        logger.info(                                    
            f"Inicialización completa: {initialized_count}/{len(raw_plugins)} plugins activos")
        return initialized_count > 0                    # Retorna True si al menos un plugin se inicializó correctamente , o False si ningún plugin se inicializó correctamente.

    # Definición del método execute_cycle() que ejecuta un ciclo completo del sistema llamando al método execute() de cada plugin activo y midiendo la latencia total del ciclo.
    def execute_cycle(self) -> dict:
        """
        Ejecuta un ciclo del sistema (llama execute() en cada plugin).
        Mide la latencia total del ciclo y registra advertencia si supera 8.3 ms.
        Retorna un dict: {plugin_name: resultado_execute()} para cada plugin.
        """
        cycle_start = time.perf_counter()     # Marca el tiempo de inicio del ciclo para medir la latencia total del ciclo
        results = {}                          # Diccionario para almacenar los resultados de ejecución de cada plugin
        metrics = {}                          # Diccionario para almacenar métricas de ejecución de cada plugin, incluyendo el estado y la latencia en milisegundos 

        cycle_plugins = [                     # Ordena los plugins para que los que implementan ICycleResultConsumer se ejecuten al final del ciclo, permitiendo que consuman los resultados de los demás plugins.
            plugin for plugin in self._plugins
            if not isinstance(plugin, ICycleResultConsumer)     # Filtra los plugins que no implementan ICycleResultConsumer, es decir, aquellos que no consumen resultados de otros plugins.
        ] + [
            plugin for plugin in self._plugins
            if isinstance(plugin, ICycleResultConsumer)         # Filtra los plugins que implementan ICycleResultConsumer
        ]
        for plugin in cycle_plugins:
            plugin_start = time.perf_counter()         # Marca el tiempo de inicio de la ejecución del plugin para medir su latencia individual
            status = "ok"
            try:
                if isinstance(plugin, ICycleResultConsumer):          # Si el plugin implementa ICycleResultConsumer, se le pasan los resultados de los demás plugins del ciclo actual para que pueda consumirlos.
                    plugin.consume_cycle_results(dict(results))       # Pasa una copia de los resultados actuales a consume_cycle_results()
                result = plugin.execute()
                results[plugin.instance_name] = result                # Almacena el resultado de la ejecución del plugin en el diccionario results
                if isinstance(result, dict) and result.get("error"):
                    status = "error"
            except Exception as e:          # Aislamiento de fallos: un plugin que falla en execute(), no detiene la ejecución de los demás plugins.
                logger.error(f"[{plugin.instance_name}] excepción en execute(): {e}")
                results[plugin.instance_name] = {'error': str(e)}
                status = "error"
            finally:                        # Calcula la latencia del plugin y registra advertencia si supera MAX_LATENCY_MS
                plugin_ms = (time.perf_counter() - plugin_start) * 1000         # Convierte la latencia del plugin a milisegundos
                metrics[plugin.instance_name] = {                               # Almacena las métricas del plugin en el diccionario metrics, incluyendo el estado y la latencia en milisegundos
                    "status": status,
                    "latency_ms": round(plugin_ms, 3),
                }
                if plugin_ms > MAX_LATENCY_MS:          # Si la latencia del plugin supera el objetivo de latencia máxima, se registra una advertencia en el log indicando que el plugin tiene alta latencia.
                    logger.warning(
                        f"{plugin.instance_name} latencia alta: {plugin_ms:.2f} ms "
                        f"(objetivo: ≤ {MAX_LATENCY_MS} ms)"
                    )

        # Latencia total del ciclo
        total_ms = (time.perf_counter() - cycle_start) * 1000
        self._last_cycle_metrics = metrics                      # Almacena las métricas del último ciclo ejecutado en el atributo _last_cycle_metrics
        self._latency_history.append(total_ms)                  # Almacena la latencia total del ciclo en la lista _latency_history para su posterior análisis y resumen de métricas
        self._cycle_count += 1                                  

        if self._cycle_count % 100 == 0:  # Log cada 100 ciclos
            avg_ms = sum(self._latency_history[-100:]) / min(100, len(self._latency_history))
            logger.info(f"Ciclo #{self._cycle_count}, Latencia promedio (últimos 100): {avg_ms:.2f} ms")

        return results

    # Definición del método run() que ejecuta el loop principal del sistema, llamando a execute_cycle() en cada iteración y controlando la cantidad máxima de ciclos a ejecutar.
    def run(self, max_cycles: Optional[int] = None) -> None:
        self._is_running = True           # Bandera para indicar que el loop principal está activo
        logger.info(
            f"Loop principal iniciado. Max ciclos: {max_cycles or 'infinito'}"
        )
        try:
            cycle = 0
            while self._is_running:        # Loop principal que ejecuta ciclos hasta que se alcance el máximo de ciclos o se interrumpa manualmente (Ctrl+C)
                self.execute_cycle()
                cycle += 1

                if max_cycles is not None and cycle >= max_cycles:
                    logger.info(
                        f"Se alcanzó el máximo de {max_cycles} ciclos."
                    )
                    break
        except KeyboardInterrupt:
            logger.info(
                "Interrupción del usuario (Ctrl+C). Deteniendo el sistema..."
            )
        finally:
            self._is_running = False       # Bandera para indicar que el loop principal ha terminado 

    # Definición del método release() que libera los recursos de todos los plugins en orden inverso al de inicialización, registrando errores si algún plugin falla en release().
    def release(self) -> None:
        """
        Libera recursos de todos los plugins en orden inverso.
        Si un plugin falla en release(), el error se registra pero el sistema continúa liberando los demás plugins.
        """
        logger.info(
            "Liberando recursos del sistema..."
        )
        # Orden inverso al de inicialización
        for plugin in reversed(self._plugins):
            try:
                plugin.release()
                logger.info(
                    f"{plugin.instance_name} recursos liberados"
                )
            except Exception as e:
                logger.error(
                    f"{plugin.instance_name} excepción en release(): {e}"
                )
        self._plugins.clear()
        logger.info("OrchestratorCore terminado correctamente.")
        self._print_latency_summary()

    # Definición del método _load_config() que lee el archivo de configuración plugins.json y retorna la lista de plugins configurados.
    def _load_config(self) -> Optional[list]:
        """Lee el archivo plugins.json y retorna la lista de plugins."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('plugins', [])
        except FileNotFoundError:
            logger.error(
                f"Archivo de configuración no encontrado: {self.config_path}"
            )
            return None
        except json.JSONDecodeError as e:
            logger.error(
                f"Error al parsear {self.config_path}: {e}"
            )
            return None

    # Definición del método _print_latency_summary() que imprime un resumen de métricas de latencia de la sesión, incluyendo promedio, máximo y mínimo.
    def _print_latency_summary(self) -> None:
        """Imprime resumen de métricas de latencia de la sesión."""
        if not self._latency_history:
            return
        avg = sum(self._latency_history) / len(self._latency_history)
        max_lat = max(self._latency_history)
        min_lat = min(self._latency_history)
        logger.info(
            f"\n\n"
            f"Resumen de Latencia ({self._cycle_count} ciclos)\n"
            f"Promedio: {avg:.2f} ms\n"
            f"Máxima:   {max_lat:.2f} ms\n"
            f"Mínima:   {min_lat:.2f} ms\n"
            f"Objetivo: ≤ {MAX_LATENCY_MS} ms\n"
        )

    # ------------------------------------------------------------------
    # Extensiones para la aplicación interactiva (interfaz EDDIE)
    # ------------------------------------------------------------------
    def _apply_overrides(self, plugins_config: list) -> list:
        """Combina plugins.json con los ajustes de usuario sin mutar el archivo original."""
        merged = []
        for plugin_conf in plugins_config:
            conf = dict(plugin_conf)
            override = self._config_overrides.get(conf.get("name"), {})
            if "enabled" in override:
                conf["enabled"] = bool(override["enabled"])
            if "device_mode" in override:
                conf["device_mode"] = override["device_mode"]
            conf["config"] = {**conf.get("config", {}), **override.get("config", {})}
            conf["class"] = DeviceFactory.resolve(conf)                 # Capa HAL: real o simulado
            merged.append(conf)
        return merged

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Retorna el plugin activo con ese nombre de instancia, o None."""
        return next((p for p in self._plugins if p.instance_name == name), None)

    def get_plugins_by_contract(self, contract: type) -> list[PluginBase]:
        """Retorna los plugins activos que implementan un contrato (IEyeTracker, IGesturePlugin, ...)."""
        return [p for p in self._plugins if isinstance(p, contract)]

    def declared_plugins(self, contract: Optional[type] = None) -> list[dict]:
        """Lista las entradas de plugins.json (activas o no) con su estado de inicialización.

        Permite que la interfaz muestre los plugins disponibles por categoría (equivalente a
        los combobox que en C# se llenaban recorriendo carpetas de DLLs).
        """
        declared = []
        for conf in self._plugins_config:
            name = conf.get("name")
            plugin = self.get_plugin(name)
            if contract is not None and not (plugin is not None and isinstance(plugin, contract)):
                if plugin is not None or not self._class_implements(conf.get("class", ""), contract):
                    continue
            report = self._initialization_report.get(name, {})
            declared.append({
                "name": name,
                "label": conf.get("label", name),
                "status": report.get("status", "unknown"),
                "error": report.get("error"),
                "config": dict(conf.get("config", {})),
            })
        return declared

    @staticmethod
    def _class_implements(class_path: str, contract: type) -> bool:
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            return issubclass(getattr(module, class_name), contract)
        except Exception:
            return False

    def invoke(self, plugin_name: str, method: str, *args, **kwargs) -> "InvocationResult":
        """Llama un método de servicio de un plugin bajo el manejo centralizado de excepciones.

        Las acciones bajo demanda de la interfaz (OCR de un resaltado, consulta al LLM,
        sincronización con el PDF) no ocurren en cada ciclo; pasan por aquí para que una
        falla quede aislada, registrada y medida igual que en execute_cycle().
        """
        plugin = self.get_plugin(plugin_name)
        if plugin is None:
            error = f"El plugin '{plugin_name}' no está activo."
            logger.error(error)
            return InvocationResult(False, None, error, 0.0)
        start = time.perf_counter()
        try:
            value = getattr(plugin, method)(*args, **kwargs)
            latency = (time.perf_counter() - start) * 1000
            return InvocationResult(True, value, None, round(latency, 3))
        except Exception as exc:   # Aislamiento de fallos: la excepción no llega a la interfaz
            latency = (time.perf_counter() - start) * 1000
            logger.error("[%s] excepción en %s(): %s", plugin_name, method, exc)
            return InvocationResult(False, None, str(exc), round(latency, 3))

    def restart_plugin(self, name: str, config: Optional[dict] = None) -> bool:
        """Libera y vuelve a inicializar un plugin con nueva configuración (p. ej. otra cámara).

        Los plugins que consumen frames de un sensor reiniciado se vuelven a enlazar a la
        nueva instancia.
        """
        conf = next((c for c in self._plugins_config if c.get("name") == name), None)
        if conf is None:
            logger.error("No existe el plugin declarado '%s'.", name)
            return False
        if config is not None:
            conf["config"] = {**conf.get("config", {}), **config}
            self._config_overrides.setdefault(name, {}).setdefault("config", {}).update(config)
        old = self.get_plugin(name)
        position = len(self._plugins)
        if old is not None:
            position = self._plugins.index(old)
            try:
                old.release()
            except Exception as exc:
                logger.error("%s excepción en release(): %s", name, exc)
            self._plugins.remove(old)
        new_plugin = self._loader.load_plugin(conf.get("class", ""), conf.get("config", {}))
        if new_plugin is None:
            self._initialization_report[name] = {"status": "load_failed", "error": "No se pudo cargar."}
            return False
        new_plugin.set_instance_name(name)
        sensor_name = conf.get("dependencies", {}).get("camera_sensor")
        if sensor_name:
            sensor = self.get_plugin(sensor_name)
            if not isinstance(sensor, ICameraSensor) or not isinstance(new_plugin, ICameraFrameConsumer):
                self._initialization_report[name] = {"status": "dependency_failed",
                                                     "error": f"'{sensor_name}' no disponible."}
                return False
            new_plugin.set_camera_sensor(sensor)
        try:
            ok = new_plugin.initialize(conf.get("config", {}))
        except Exception as exc:
            logger.error("%s lanzó excepción en initialize(): %s", name, exc)
            self._initialization_report[name] = {"status": "initialization_failed", "error": str(exc)}
            return False
        if not ok:
            self._initialization_report[name] = {"status": "initialization_failed",
                                                 "error": "initialize() retornó False."}
            return False
        new_plugin._initialized = True
        self._plugins.insert(position, new_plugin)
        self._initialization_report[name] = {"status": "initialized", "error": None}
        if isinstance(new_plugin, ICameraSensor):           # Re-enlaza consumidores del sensor reiniciado
            for other in self._plugins:
                other_conf = next((c for c in self._plugins_config if c.get("name") == other.instance_name), {})
                if other_conf.get("dependencies", {}).get("camera_sensor") == name and isinstance(other, ICameraFrameConsumer):
                    other.set_camera_sensor(new_plugin)
            for dependent in self._plugins_config:                # consumidores que fallaron por falta de sensor
                dep_name = dependent.get("name")
                if (dependent.get("dependencies", {}).get("camera_sensor") == name
                        and dependent.get("enabled", True) and self.get_plugin(dep_name) is None):
                    self.restart_plugin(dep_name)
        logger.info("%s reiniciado correctamente", name)
        return True

    def stop_plugin(self, name: str) -> None:
        """Libera un plugin activo y lo retira del ciclo (p. ej. desconectar un eye tracker)."""
        plugin = self.get_plugin(name)
        if plugin is None:
            return
        try:
            plugin.release()
        except Exception as exc:
            logger.error("%s excepción en release(): %s", name, exc)
        self._plugins.remove(plugin)
        self._initialization_report[name] = {"status": "stopped", "error": None}

    # Definición de propiedades para exponer información del estado del orquestador y métricas de ejecución.
    @property
    def active_plugins(self) -> list:
        return list(self._plugins)

    # Definición de propiedad cycle_count que retorna el número total de ciclos ejecutados por el orquestador.
    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    # Definición de propiedad last_cycle_metrics que retorna un diccionario con métricas de ejecución del último ciclo, incluyendo estado y latencia por plugin.
    @property
    def last_cycle_metrics(self) -> dict[str, dict]:
        return {name: dict(metric) for name, metric in self._last_cycle_metrics.items()}

    # Definición de propiedad initialization_report que retorna un diccionario con los resultados de carga e inicialización de cada plugin, incluyendo estado y errores si los hubo.
    @property
    def initialization_report(self) -> dict[str, dict]:
        return {
            name: dict(result)
            for name, result in self._initialization_report.items()
        }
