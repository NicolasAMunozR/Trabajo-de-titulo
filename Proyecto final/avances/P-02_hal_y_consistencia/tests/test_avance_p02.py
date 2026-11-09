# Pruebas del avance P-02: DeviceFactory (real/simulado), invocación aislada y consistencia como plugin.
import importlib.util
import json
import sys
from pathlib import Path

import pymupdf
import pytest

from orchestrator.orchestrator_core import OrchestratorCore

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def orch(monkeypatch):
    monkeypatch.setenv("EDDIE_DEVICE_MODE", "sim")
    core = OrchestratorCore("config/plugins.json")
    assert core.initialize()
    yield core
    core.release()


def test_device_factory_usa_la_camara_simulada_sin_cambiar_codigo(orch):
    assert type(orch.get_plugin("TextCamera")).__name__ == "MockCameraSensor"
    assert orch.initialization_report["ConsistencyProvider"]["status"] == "initialized"


def test_invoke_aisla_los_errores_del_plugin(orch):
    result = orch.invoke("ConsistencyProvider", "search_text", "x")
    assert not result.ok and "PDF" in result.error                   # sin PDF: error legible, no excepción
    assert not orch.invoke("NoExiste", "execute").ok
    assert orch.invoke("TextCamera", "execute").ok


def test_restart_reemplaza_el_sensor_en_caliente(orch):
    old = orch.get_plugin("TextCamera")
    assert orch.restart_plugin("TextCamera", {"camera_index": 3})
    assert orch.get_plugin("TextCamera") is not old and orch.get_plugin("TextCamera").camera_index == 3
    orch.stop_plugin("TextCamera")
    assert orch.get_plugin("TextCamera") is None


def _run_demo(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("demo_consistencia", ROOT / "demos" / "demo_consistencia.py")
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    monkeypatch.setattr(demo, "OUT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["demo_consistencia.py"])
    assert demo.main() == 0
    return json.loads((tmp_path / "reporte.json").read_text(encoding="utf-8"))


def test_demo_de_consistencia_invoca_todo_el_contrato_por_el_orquestador(tmp_path, monkeypatch):
    report = _run_demo(tmp_path, monkeypatch)
    assert all(call["ok"] for call in report["calls"])
    values = {call["method"]: call["value"] for call in report["calls"]}
    assert values["sync_bookmark_from_frame"] is True
    assert values["sync_comments_from_frame"] == 1 and values["sync_figures_from_frame"] == 2
    assert (tmp_path / "pagina_1.png").exists()


@pytest.mark.xfail(strict=True, reason="Hallazgo H-02: con PyMuPDF 2.x, desde el segundo saveIncr() el PDF queda "
                                       "dañado y se pierden los cambios anteriores. Corregido en P-07.")
def test_hallazgo_h02_el_pdf_guardado_conserva_todos_los_cambios(tmp_path, monkeypatch):
    _run_demo(tmp_path, monkeypatch)
    with pymupdf.open(tmp_path / "resultado.pdf") as document:
        assert not document.is_repaired
        assert [len(list(page.annots())) for page in document] == [1, 1, 2]
        assert len(document.get_toc()) == 2
