"""
demos/demo_consistencia.py — Avance P-02
========================================
Demuestra el módulo de consistencia papel ↔ PDF integrado como plugin, invocado a
través del OrchestratorCore (OrchestratorCore.invoke), sin interfaz ni cámara real.

1. Genera un PDF de 3 páginas (o usa --pdf ruta).
2. Genera tres "fotos" sintéticas de la hoja física: marcador azul, nota adhesiva
   amarilla y figuras magenta (los colores que usaba BibliotecaConsistencia).
3. Llama a los métodos del contrato IConsistencyProvider por el orquestador y guarda:
   - evidencias/consistencia/resultado.pdf     (PDF con lo sincronizado)
   - evidencias/consistencia/pagina_N.png      (render de cada página)
   - evidencias/consistencia/frame_*.png       (frames de entrada)
   - evidencias/consistencia/reporte.json      (resultado y latencia de cada llamada, y lo que
                                                quedó realmente guardado en el PDF al reabrirlo)

Uso:  python demos/demo_consistencia.py  [--pdf libro.pdf]
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import cv2                      # noqa: E402
import numpy as np              # noqa: E402
import pymupdf                  # noqa: E402

from contracts.i_consistency_provider import Annotation   # noqa: E402
from orchestrator.orchestrator_core import OrchestratorCore  # noqa: E402

OUT = ROOT / "evidencias" / "consistencia"


def sample_pdf(path: Path) -> None:
    document = pymupdf.open()
    for number in range(1, 4):
        page = document.new_page()
        page.insert_text((72, 72), f"Capitulo {number}: lectura aumentada", fontsize=16)
        page.insert_text((72, 110), "EDDIE proyecta definiciones sobre el papel.")
        page.insert_text((72, 130), "El lector resalta, marca y comenta el libro fisico.")
    document[1].insert_text((72, 170), "homografia")
    document.save(path)
    document.close()


def page_frame() -> np.ndarray:
    return np.full((480, 640, 3), 245, np.uint8)


def frames() -> dict:
    bookmark = page_frame()
    cv2.rectangle(bookmark, (50, 50), (130, 120), (200, 120, 0), -1)          # banderilla azul
    comment = page_frame()
    cv2.rectangle(comment, (300, 200), (500, 350), (0, 200, 255), -1)         # post-it amarillo
    figures = page_frame()
    cv2.circle(figures, (200, 240), 60, (200, 0, 220), 4)                     # figuras magenta
    cv2.rectangle(figures, (380, 120), (560, 300), (200, 0, 220), 4)
    return {"marcador": bookmark, "comentario": comment, "figuras": figures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", help="PDF propio (se copia; el original no se modifica)")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    pdf = OUT / "resultado.pdf"
    if args.pdf:
        shutil.copy(args.pdf, pdf)
    else:
        sample_pdf(pdf)

    os.environ.setdefault("EDDIE_DEVICE_MODE", "sim")
    orch = OrchestratorCore("config/plugins.json",
                            {"ConsistencyProvider": {"config": {"pdf_path": str(pdf), "camera_rotated_180": False}}})
    orch.initialize()
    report = {"initialization": orch.initialization_report, "calls": []}

    def call(method, *a):
        result = orch.invoke("ConsistencyProvider", method, *a)
        value = result.value
        if isinstance(value, np.ndarray):
            value = f"ndarray{list(value.shape)}"
        report["calls"].append({"method": method, "ok": result.ok, "error": result.error,
                                "latency_ms": round(result.latency_ms, 3), "value": value})
        return result

    call("search_text", "homografia")
    call("add_highlight", Annotation(1, 0.1, 0.08, 0.6, 0.12, "highlight", "lectura aumentada"))
    call("add_bookmark", "Introducción", 1)
    for name, frame in frames().items():
        cv2.imwrite(str(OUT / f"frame_{name}.png"), frame)
    call("sync_bookmark_from_frame", frames()["marcador"], 2)
    call("sync_comments_from_frame", frames()["comentario"], 2)
    call("sync_figures_from_frame", frames()["figuras"], 3)
    call("get_bookmarks")
    call("get_comments")
    call("get_figures", 3, (400, 450))
    call("search_text", "")                                             # entrada inválida: no debe romper nada
    for page in (1, 2, 3):
        image = orch.invoke("ConsistencyProvider", "render_page", page, 612, 792)
        if image.ok:
            cv2.imwrite(str(OUT / f"pagina_{page}.png"), image.value)
    orch.release()
    with pymupdf.open(pdf) as document:                                # ¿qué quedó realmente guardado?
        report["persistencia"] = {"anotaciones_por_pagina": [len(list(page.annots())) for page in document],
                                  "marcadores": document.get_toc(), "pdf_reparado_al_abrir": document.is_repaired,
                                  "esperado": {"anotaciones_por_pagina": [1, 1, 2], "marcadores": 2}}
    (OUT / "reporte.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    ok = sum(c["ok"] for c in report["calls"])
    print(f"{ok}/{len(report['calls'])} llamadas correctas. Resultados en {OUT}")
    print("Guardado en disco:", report["persistencia"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
