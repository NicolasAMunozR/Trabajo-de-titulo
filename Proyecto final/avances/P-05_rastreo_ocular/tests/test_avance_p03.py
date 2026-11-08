"""Pruebas del avance P-03: reconocimiento de texto resaltado (IImageProcessor) sobre la cámara declarada."""
import os

import pytest

from orchestrator.orchestrator_core import OrchestratorCore


@pytest.fixture
def orch(monkeypatch):
    monkeypatch.setenv("EDDIE_DEVICE_MODE", "sim")
    core = OrchestratorCore("config/plugins.json")
    assert core.initialize()
    yield core
    core.release()


def test_image_processor_recibe_la_camara_de_texto(orch):
    assert orch.initialization_report["ImageProcessor"]["status"] == "initialized"
    assert orch.get_plugin("ImageProcessor")._camera_sensor is orch.get_plugin("TextCamera")


def test_resaltado_de_la_hoja_simulada_se_detecta_por_invocacion(orch):
    orch.execute_cycle()
    result = orch.invoke("ImageProcessor", "recognize_highlighted_text")
    assert result.ok and result.value["box"] is not None


@pytest.mark.skipif(os.system("tesseract --version >/dev/null 2>&1") != 0
                    and os.system("tesseract --version >NUL 2>&1") != 0, reason="Tesseract no instalado")
def test_ocr_lee_la_palabra_resaltada_de_la_hoja_simulada(orch):
    orch.execute_cycle()
    text = orch.invoke("ImageProcessor", "recognize_highlighted_text").value["text"].lower()
    assert "aumentada" in text
