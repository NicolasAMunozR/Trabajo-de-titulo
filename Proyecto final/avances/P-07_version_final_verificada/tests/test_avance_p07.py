# Pruebas del avance P-07: los hallazgos de la verificación (H-01, H-02) quedan corregidos.
import importlib.util
import json
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def test_h02_demo_de_consistencia_conserva_todos_los_cambios_en_disco(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("demo_consistencia", ROOT / "demos" / "demo_consistencia.py")
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    monkeypatch.setattr(demo, "OUT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["demo_consistencia.py"])
    assert demo.main() == 0
    report = json.loads((tmp_path / "reporte.json").read_text(encoding="utf-8"))
    assert all(call["ok"] for call in report["calls"])
    with pymupdf.open(tmp_path / "resultado.pdf") as document:
        assert not document.is_repaired
        assert [len(list(page.annots())) for page in document] == [1, 1, 2]
        assert len(document.get_toc()) == 2
