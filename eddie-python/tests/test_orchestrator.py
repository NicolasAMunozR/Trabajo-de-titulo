"""
tests/test_orchestrator.py
============================
Tests unitarios del OrchestratorCore y PluginLoader.

Cobertura objetivo: ≥ 80% (requisito del informe de seminario)

Cómo ejecutar:
  Desde la carpeta eddie-python/:
  ..\\eddie-python-venv\\Scripts\\pytest tests/test_orchestrator.py -v --cov=orchestrator --cov-report=term-missing
"""
import sys
import os
import json
import tempfile
import pytest

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contracts.plugin_base import PluginBase
from orchestrator.plugin_loader import PluginLoader
from orchestrator.orchestrator_core import OrchestratorCore


# ─────────────────────────────────────────────────────────────────
# FIXTURES: Plugins de prueba
# ─────────────────────────────────────────────────────────────────

class _PluginOK(PluginBase):
    """Plugin simple que funciona correctamente."""
    @property
    def name(self): return "TestPluginOK"
    def initialize(self, config): return True
    def execute(self): return {'status': 'ok', 'value': 42}
    def release(self): pass

class _PluginInitFail(PluginBase):
    """Plugin que falla en initialize() retornando False."""
    @property
    def name(self): return "TestPluginInitFail"
    def initialize(self, config): return False
    def execute(self): return {}
    def release(self): pass

class _PluginInitException(PluginBase):
    """Plugin que lanza excepción en initialize()."""
    @property
    def name(self): return "TestPluginInitException"
    def initialize(self, config): raise RuntimeError("Error forzado en initialize")
    def execute(self): return {}
    def release(self): pass

class _PluginExecuteException(PluginBase):
    """Plugin que lanza excepción en execute()."""
    @property
    def name(self): return "TestPluginExecuteException"
    def initialize(self, config): return True
    def execute(self): raise ValueError("Error forzado en execute")
    def release(self): pass

class _PluginReleaseException(PluginBase):
    """Plugin que lanza excepción en release()."""
    @property
    def name(self): return "TestPluginReleaseException"
    def initialize(self, config): return True
    def execute(self): return {'status': 'ok'}
    def release(self): raise RuntimeError("Error forzado en release")


def make_config(plugins: list) -> str:
    """Crea un archivo plugins.json temporal con los plugins dados."""
    tmp = tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False, encoding='utf-8'
    )
    json.dump({'plugins': plugins}, tmp, ensure_ascii=False)
    tmp.close()
    return tmp.name


# ─────────────────────────────────────────────────────────────────
# TESTS: PluginLoader
# ─────────────────────────────────────────────────────────────────

class TestPluginLoader:

    def test_load_valid_plugin(self):
        """Carga un plugin válido que hereda de PluginBase."""
        loader = PluginLoader()
        # Registramos el plugin en el módulo actual para que importlib lo encuentre
        import tests.test_orchestrator as _self_module
        _self_module.TempPlugin = _PluginOK
        
        plugin = loader.load_plugin('tests.test_orchestrator.TempPlugin', {})
        assert plugin is not None
        assert plugin.name == "TestPluginOK"

    def test_load_invalid_module(self):
        """Retorna None si el módulo no existe."""
        loader = PluginLoader()
        plugin = loader.load_plugin('modulo.que.no.existe.Clase', {})
        assert plugin is None

    def test_load_invalid_class_in_valid_module(self):
        """Retorna None si la clase no existe en el módulo."""
        loader = PluginLoader()
        plugin = loader.load_plugin('contracts.plugin_base.ClaseQueNoExiste', {})
        assert plugin is None

    def test_load_class_not_subclass_of_plugin_base(self):
        """Retorna None si la clase no hereda de PluginBase."""
        loader = PluginLoader()
        # str no es subclase de PluginBase
        plugin = loader.load_plugin('builtins.str', {})
        assert plugin is None

    def test_load_all_enabled_plugins(self):
        """Carga solo los plugins habilitados (enabled=true)."""
        import tests.test_orchestrator as _self_module
        _self_module.PluginEnabled = _PluginOK
        _self_module.PluginDisabled = _PluginOK

        loader = PluginLoader()
        config = [
            {'name': 'P1', 'class': 'tests.test_orchestrator.PluginEnabled', 'enabled': True, 'config': {}},
            {'name': 'P2', 'class': 'tests.test_orchestrator.PluginDisabled', 'enabled': False, 'config': {}},
        ]
        plugins = loader.load_all(config)
        assert len(plugins) == 1

    def test_load_all_empty_config(self):
        """Retorna lista vacía si no hay plugins en config."""
        loader = PluginLoader()
        plugins = loader.load_all([])
        assert plugins == []

    def test_load_all_missing_class_key(self):
        """Omite plugins sin 'class' definido."""
        loader = PluginLoader()
        config = [{'name': 'SinClase', 'enabled': True, 'config': {}}]
        plugins = loader.load_all(config)
        assert plugins == []


# ─────────────────────────────────────────────────────────────────
# TESTS: OrchestratorCore — initialize()
# ─────────────────────────────────────────────────────────────────

class TestOrchestratorInitialize:

    def test_initialize_with_no_plugins(self):
        """Retorna False si no hay plugins en la configuración."""
        config_path = make_config([])
        orch = OrchestratorCore(config_path)
        result = orch.initialize()
        os.unlink(config_path)
        assert result is False

    def test_initialize_with_missing_config_file(self):
        """Retorna False si el archivo de configuración no existe."""
        orch = OrchestratorCore('archivo_que_no_existe.json')
        result = orch.initialize()
        assert result is False

    def test_initialize_plugin_init_fail_does_not_stop_system(self):
        """Un plugin que retorna False en initialize() no bloquea otros plugins."""
        import tests.test_orchestrator as _m
        _m.PluginOK_For_Init = _PluginOK
        _m.PluginFail_For_Init = _PluginInitFail

        config_path = make_config([
            {'name': 'TestPluginOK', 'class': 'tests.test_orchestrator.PluginOK_For_Init', 'enabled': True, 'config': {}},
            {'name': 'TestPluginInitFail', 'class': 'tests.test_orchestrator.PluginFail_For_Init', 'enabled': True, 'config': {}},
        ])
        orch = OrchestratorCore(config_path)
        result = orch.initialize()
        os.unlink(config_path)

        # El sistema debe inicializarse (al menos 1 plugin OK)
        assert result is True
        # Solo el plugin OK debe estar activo
        assert len(orch.active_plugins) == 1
        assert orch.active_plugins[0].name == "TestPluginOK"

    def test_initialize_plugin_exception_does_not_crash_system(self):
        """Un plugin que lanza excepción en initialize() no crashea el sistema."""
        import tests.test_orchestrator as _m
        _m.PluginOK2 = _PluginOK
        _m.PluginEx = _PluginInitException

        config_path = make_config([
            {'name': 'TestPluginOK', 'class': 'tests.test_orchestrator.PluginOK2', 'enabled': True, 'config': {}},
            {'name': 'TestPluginInitException', 'class': 'tests.test_orchestrator.PluginEx', 'enabled': True, 'config': {}},
        ])
        orch = OrchestratorCore(config_path)
        result = orch.initialize()
        os.unlink(config_path)

        assert result is True
        assert len(orch.active_plugins) == 1


# ─────────────────────────────────────────────────────────────────
# TESTS: OrchestratorCore — execute_cycle()
# ─────────────────────────────────────────────────────────────────

class TestOrchestratorExecute:

    def _make_orch_with_plugins(self, plugin_classes):
        """Helper: crea un orquestador con plugins ya inicializados."""
        import tests.test_orchestrator as _m
        config_entries = []
        for i, cls in enumerate(plugin_classes):
            attr_name = f'_AutoPlugin_{i}'
            setattr(_m, attr_name, cls)
            config_entries.append({
                'name': cls().name,
                'class': f'tests.test_orchestrator.{attr_name}',
                'enabled': True,
                'config': {}
            })
        config_path = make_config(config_entries)
        orch = OrchestratorCore(config_path)
        orch.initialize()
        os.unlink(config_path)
        return orch

    def test_execute_returns_dict_per_plugin(self):
        """execute_cycle() retorna un dict con clave por cada plugin."""
        orch = self._make_orch_with_plugins([_PluginOK])
        results = orch.execute_cycle()
        assert isinstance(results, dict)
        assert 'TestPluginOK' in results

    def test_execute_plugin_exception_isolation(self):
        """Un plugin que crashea en execute() no detiene los demás."""
        orch = self._make_orch_with_plugins([_PluginOK, _PluginExecuteException])
        results = orch.execute_cycle()

        # El plugin OK debe tener resultado correcto
        assert results['TestPluginOK'] == {'status': 'ok', 'value': 42}
        # El plugin que crashea debe tener error registrado
        assert 'error' in results['TestPluginExecuteException']

    def test_execute_increments_cycle_count(self):
        """execute_cycle() incrementa el contador de ciclos."""
        orch = self._make_orch_with_plugins([_PluginOK])
        assert orch.cycle_count == 0
        orch.execute_cycle()
        assert orch.cycle_count == 1
        orch.execute_cycle()
        assert orch.cycle_count == 2

    def test_execute_latency_recorded(self):
        """La latencia de cada ciclo queda registrada en el historial."""
        orch = self._make_orch_with_plugins([_PluginOK])
        orch.execute_cycle()
        orch.execute_cycle()
        assert len(orch._latency_history) == 2
        assert all(ms >= 0 for ms in orch._latency_history)


# ─────────────────────────────────────────────────────────────────
# TESTS: OrchestratorCore — release()
# ─────────────────────────────────────────────────────────────────

class TestOrchestratorRelease:

    def test_release_clears_plugins(self):
        """release() vacía la lista de plugins activos."""
        import tests.test_orchestrator as _m
        _m._PluginForRelease = _PluginOK
        config_path = make_config([
            {'name': 'TestPluginOK', 'class': 'tests.test_orchestrator._PluginForRelease', 'enabled': True, 'config': {}}
        ])
        orch = OrchestratorCore(config_path)
        orch.initialize()
        os.unlink(config_path)

        assert len(orch.active_plugins) == 1
        orch.release()
        assert len(orch.active_plugins) == 0

    def test_release_exception_does_not_stop_others(self):
        """Una excepción en release() de un plugin no detiene los demás."""
        import tests.test_orchestrator as _m
        _m._PluginOKr = _PluginOK
        _m._PluginREx = _PluginReleaseException

        config_path = make_config([
            {'name': 'TestPluginOK', 'class': 'tests.test_orchestrator._PluginOKr', 'enabled': True, 'config': {}},
            {'name': 'TestPluginReleaseException', 'class': 'tests.test_orchestrator._PluginREx', 'enabled': True, 'config': {}},
        ])
        orch = OrchestratorCore(config_path)
        orch.initialize()
        os.unlink(config_path)

        # No debe lanzar excepción al llamar release()
        try:
            orch.release()
            released_ok = True
        except Exception:
            released_ok = False

        assert released_ok is True
        assert len(orch.active_plugins) == 0


# ─────────────────────────────────────────────────────────────────
# TESTS: PluginBase — contrato
# ─────────────────────────────────────────────────────────────────

class TestPluginBase:

    def test_plugin_base_cannot_be_instantiated(self):
        """PluginBase es abstracta y no puede instanciarse directamente."""
        with pytest.raises(TypeError):
            PluginBase()

    def test_plugin_is_initialized_property(self):
        """is_initialized retorna el valor de _initialized."""
        plugin = _PluginOK()
        assert plugin.is_initialized is False
        plugin._initialized = True
        assert plugin.is_initialized is True

    def test_plugin_name_property(self):
        """La propiedad name debe retornar string no vacío."""
        plugin = _PluginOK()
        assert isinstance(plugin.name, str)
        assert len(plugin.name) > 0
