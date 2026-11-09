# Pruebas del avance P-01: el núcleo carga, ejecuta y libera plugins con un único mecanismo.
import statistics

import pytest

from orchestrator.orchestrator_core import MAX_LATENCY_MS, OrchestratorCore


@pytest.fixture
def orch():
    core = OrchestratorCore("config/plugins.json")
    assert core.initialize()
    yield core
    core.release()


def test_configuracion_del_avance_carga_todo_y_reporta_la_clase_faltante(orch):
    report = orch.initialization_report
    for name in ("TextCamera", "FrameStatistics", "EyeTrackerMock", "FaultInjection", "CycleSummary"):
        assert report[name]["status"] == "initialized", name
    assert report["PluginInexistente"]["status"] == "load_failed"     # E38/E50: el resto sigue funcionando


def test_sensor_se_inyecta_en_el_consumidor_sin_que_este_abra_la_camara(orch):
    out = orch.execute_cycle()
    assert out["TextCamera"]["frame_available"] is True
    assert out["FrameStatistics"]["frame"] is True and out["FrameStatistics"]["shape"] == [480, 640, 3]


def test_falla_inyectada_queda_aislada_y_los_demas_plugins_siguen(orch):
    failures = []
    for _ in range(20):
        out = orch.execute_cycle()
        assert out["FrameStatistics"]["frame"] is True                 # nunca se interrumpe
        if out["FaultInjection"].get("error"):
            failures.append(orch.cycle_count)
            assert "FaultInjection" in out["CycleSummary"]["failed_this_cycle"]
    assert failures == [10, 20]
    assert orch.last_cycle_metrics["FaultInjection"]["status"] == "error"


def test_consumidor_de_resultados_se_ejecuta_al_final_del_ciclo(orch):
    out = orch.execute_cycle()
    assert set(out["CycleSummary"]["plugins_before_me"]) == {"TextCamera", "FrameStatistics", "EyeTrackerMock",
                                                             "FaultInjection"}


def test_latencia_por_plugin_bajo_el_presupuesto_de_8_3_ms(orch):
    samples: dict[str, list[float]] = {}
    for _ in range(100):
        orch.execute_cycle()
        for name, metric in orch.last_cycle_metrics.items():
            samples.setdefault(name, []).append(metric["latency_ms"])
    for name, values in samples.items():
        assert statistics.quantiles(values, n=20)[18] <= MAX_LATENCY_MS, name      # p95


CONTRACTS = {
    "contracts.i_camera_sensor": "ICameraSensor",
    "contracts.i_image_processor": "IImageProcessor",
    "contracts.i_gesture_plugin": "IGesturePlugin",
    "contracts.i_eye_tracker": "IEyeTracker",
    "contracts.i_consistency_provider": "IConsistencyProvider",
    "contracts.i_web_search_provider": "IWebSearchProvider",
    "contracts.i_speech_provider": "ISpeechProvider",
}


@pytest.mark.parametrize("module, name", CONTRACTS.items())
def test_cada_contrato_extiende_plugin_base_y_no_se_puede_instanciar(module, name):
    # Diseño (OE2): todos los módulos heredados se integran por un contrato sobre PluginBase.
    import importlib
    from contracts.plugin_base import PluginBase
    contract = getattr(importlib.import_module(module), name)
    assert issubclass(contract, PluginBase)
    assert {"initialize", "execute", "release", "name"} <= set(dir(contract))
    assert contract.__abstractmethods__                       # define operaciones propias del módulo
    with pytest.raises(TypeError):
        contract()
