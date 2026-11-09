# Cargador dinámico de plugins para el OrchestratorCore.
# Reemplaza los tres mecanismos de reflexión del C# por uno solo: importlib.import_module().
import importlib
import logging
from typing import Optional
from contracts.plugin_base import PluginBase

logger = logging.getLogger(__name__)


class PluginLoader:
    # Cargador de plugins mediante importlib.
    # Se instancia dinámicamente cualquier clase que herede de PluginBase, usando 'modulo.submodulo.NombreClase'.

    def load_plugin(self, class_path: str, config: dict) -> Optional[PluginBase]:
        # Carga e instancia un plugin dado su class_path ('paquete.modulo.Clase').
        # Devuelve el plugin instanciado o None si falló la carga.
        try:
            # Separar módulo y clase
            module_path, class_name = class_path.rsplit('.', 1)
            
            # Importar el módulo dinámicamente (equivale a Assembly.LoadFrom en C#)
            module = importlib.import_module(module_path)
            
            # Obtener la clase
            plugin_class = getattr(module, class_name)
            
            # Verificar que hereda de PluginBase (safety check)
            if not issubclass(plugin_class, PluginBase):
                logger.error(
                    f"La clase '{class_name}' no hereda de PluginBase. "
                    f"Plugin rechazado: {class_path}"
                )
                return None
            
            # Instanciar el plugin
            plugin_instance = plugin_class()
            logger.info(f"Plugin cargado exitosamente: {class_name} desde {module_path}")
            return plugin_instance
            
        except ImportError as e:
            logger.error(f"No se pudo importar el módulo para '{class_path}': {e}")
            return None
        except AttributeError as e:
            logger.error(f"Clase '{class_path}' no encontrada en el módulo: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al cargar plugin '{class_path}': {e}")
            return None

    def load_all(self, plugins_config: list) -> list:
        # Dado un listado de configuraciones de plugins, intenta cargar e instanciar cada plugin habilitado.
        loaded_plugins = []
        
        for plugin_conf in plugins_config:
            name = plugin_conf.get('name', 'UnknownPlugin')
            class_path = plugin_conf.get('class', '')
            enabled = plugin_conf.get('enabled', True)
            config = plugin_conf.get('config', {})
            
            if not enabled:
                logger.info(f"Plugin '{name}' desactivado en configuración — omitido.")
                continue
            
            if not class_path:
                logger.warning(f"Plugin '{name}' no tiene 'class' definido — omitido.")
                continue
            
            plugin = self.load_plugin(class_path, config)
            if plugin is not None:
                plugin.set_instance_name(name)
                loaded_plugins.append(plugin)
            else:
                logger.warning(
                    f"Plugin '{name}' no pudo ser cargado. "
                    f"El sistema continúa con los demás plugins."
                )
        
        logger.info(
            f"Carga completada: {len(loaded_plugins)}/{len(plugins_config)} "
            f"plugins cargados exitosamente."
        )
        return loaded_plugins
