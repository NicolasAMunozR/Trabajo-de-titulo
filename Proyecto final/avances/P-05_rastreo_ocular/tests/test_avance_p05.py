"""Pruebas del avance P-05: eye trackers bajo IEyeTracker y registro de la sesión de mirada."""
import pytest

from contracts.i_eye_tracker import IEyeTracker
from orchestrator.orchestrator_core import OrchestratorCore


@pytest.fixture
def orch(monkeypatch):
    monkeypatch.setenv("EDDIE_DEVICE_MODE", "sim")
    core = OrchestratorCore("config/plugins.json", {"EyeTrackerMock": {"enabled": True,
                                                                       "config": {"source": "synthetic"}}})
    assert core.initialize()
    yield core
    core.release()


def test_eye_trackers_declarados_se_listan_por_contrato(orch):
    names = {p["name"] for p in orch.declared_plugins(IEyeTracker)}
    assert names >= {"EyeTracker-GazePoint", "EyeTracker-EyeTribe", "EyeTracker-GazeCloud", "EyeTrackerMock"}


def test_la_mirada_simulada_llega_a_la_sesion_en_el_mismo_ciclo(orch):
    out = orch.execute_cycle()
    gaze = out["EyeTrackerMock"]["gaze"]
    assert 0 <= gaze.x <= 1 and 0 <= gaze.y <= 1 and out["EyeTrackerMock"]["simulated"] is True
    assert "GazeSession" in out
