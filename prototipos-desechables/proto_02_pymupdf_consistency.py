"""
Prototipo Desechable #2: Sincronización de Consistencia Físico-Digital en PDFs (PyMuPDF)
---------------------------------------------------------------------------------------
Objetivo: Validar la factibilidad técnica de reemplazar iTextSharp v5.x (C# legacy)
por PyMuPDF (fitz) en Python sin dependencias de DLLs ni vulnerabilidades de licencias.

Operaciones validadas:
  1. Lectura y renderizado de páginas a imágenes (Pixmap).
  2. Búsqueda de términos de texto y extracción de coordenadas de rectángulos y QuadPoints.
  3. Inserción de destacadas amarillas (Highlight Annotations) y notas adhesivas (Text Annotations).
  4. Persistencia de cambios y relectura incremental de anotaciones en el PDF.

Metodología: Figueroa (2025) - Prototipado Aislado de Bajo Costo.
"""

import sys
import os
import time
import argparse
import fitz  # PyMuPDF

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def generate_sample_pdf(pdf_path="sample_augmented_reading.pdf"):
    """Crea un archivo PDF sintético con contenido estructurado para pruebas de consistencia."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 standard

    # Insertar títulos y párrafos
    p1 = fitz.Point(50, 70)
    page.insert_text(p1, "EDDIE: Empowering Digital Paper with Interactive Enhancements", fontsize=14, fontname="helv", color=(0, 0, 0))

    p2 = fitz.Point(50, 120)
    page.insert_text(p2, "El modulo de consistencia fisico-digital mantiene la sincronizacion entre", fontsize=11, fontname="helv", color=(0.2, 0.2, 0.2))

    p3 = fitz.Point(50, 140)
    page.insert_text(p3, "el libro impreso y el archivo PDF digital correspondiente en el equipo.", fontsize=11, fontname="helv", color=(0.2, 0.2, 0.2))

    p4 = fitz.Point(50, 180)
    page.insert_text(p4, "PalabraClaveTarget: Realidad Aumentada y Rastreo Ocular Integrado.", fontsize=11, fontname="helv", color=(0.1, 0.1, 0.5))

    doc.save(pdf_path)
    doc.close()
    return pdf_path


def run_prototype_02(pdf_path=None, test_cycles=5):
    """Ejecuta las pruebas de factibilidad técnica para reemplazo de iTextSharp por PyMuPDF."""
    print("==========================================================")
    print("PROTOTIPO #2: CONSISTENCIA FÍSICO-DIGITAL EN PDFS (PyMuPDF)")
    print("==========================================================")

    created_temp_file = False
    if pdf_path is None or not os.path.exists(pdf_path):
        pdf_path = "temp_prototype_doc.pdf"
        generate_sample_pdf(pdf_path)
        created_temp_file = True
        print(f"Generado PDF Sintético de Evaluación: {pdf_path}")
    else:
        print(f"Usando PDF Real Provisto: {pdf_path}")

    open_latencies = []
    render_latencies = []
    search_latencies = []
    annot_latencies = []
    save_latencies = []

    out_pdf_path = "temp_prototype_doc_annotated.pdf"

    for _ in range(test_cycles):
        # 1. Apertura PDF
        t0 = time.perf_counter()
        doc = fitz.open(pdf_path)
        t_open = (time.perf_counter() - t0) * 1000.0
        open_latencies.append(t_open)

        page = doc[0]

        # 2. Renderizado a Pixmap (imagen)
        t0 = time.perf_counter()
        pix = page.get_pixmap(dpi=150)
        t_render = (time.perf_counter() - t0) * 1000.0
        render_latencies.append(t_render)

        # 3. Búsqueda de texto y extracción de QuadPoints / Rects
        t0 = time.perf_counter()
        quads = page.search_for("PalabraClaveTarget", quads=True)
        t_search = (time.perf_counter() - t0) * 1000.0
        search_latencies.append(t_search)

        # 4. Inserción de anotaciones Highlight y Sticky Note
        t0 = time.perf_counter()
        if quads:
            for q in quads:
                annot = page.add_highlight_annot(q)
                annot.set_colors(stroke=(1, 1, 0))  # Amarillo
                annot.update()
        else:
            # Highlight default box
            rect = fitz.Rect(50, 175, 450, 195)
            annot = page.add_highlight_annot(rect)
            annot.set_colors(stroke=(1, 1, 0))
            annot.update()

        # Nota adhesiva
        note = page.add_text_annot(fitz.Point(460, 175), "Comentario proyectado desde escritorio físico.")
        note.update()

        t_annot = (time.perf_counter() - t0) * 1000.0
        annot_latencies.append(t_annot)

        # 5. Persistencia
        t0 = time.perf_counter()
        doc.save(out_pdf_path, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
        t_save = (time.perf_counter() - t0) * 1000.0
        save_latencies.append(t_save)

        doc.close()

    # Relectura de verificación de anotaciones
    doc_check = fitz.open(out_pdf_path)
    page_check = doc_check[0]
    annots_found = list(page_check.annots())
    count_annots = len(annots_found)
    doc_check.close()

    # Limpieza de archivos temporales
    if created_temp_file and os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception:
            pass
    if os.path.exists(out_pdf_path):
        try:
            os.remove(out_pdf_path)
        except Exception:
            pass

    avg_open = sum(open_latencies) / len(open_latencies)
    avg_render = sum(render_latencies) / len(render_latencies)
    avg_search = sum(search_latencies) / len(search_latencies)
    avg_annot = sum(annot_latencies) / len(annot_latencies)
    avg_save = sum(save_latencies) / len(save_latencies)
    total_avg_ms = avg_open + avg_render + avg_search + avg_annot + avg_save

    print("\n--- Resultados de Rendimiento y Factibilidad ---")
    print(f"Apertura Documento PDF:          {avg_open:.3f} ms")
    print(f"Renderizado de Página (Pixmap): {avg_render:.3f} ms")
    print(f"Búsqueda Texto (QuadPoints):     {avg_search:.3f} ms")
    print(f"Inserción Anotaciones:          {avg_annot:.3f} ms")
    print(f"Guardado de PDF Modificado:     {avg_save:.3f} ms")
    print(f"Latencia Total Pipeline PDF:     {total_avg_ms:.3f} ms")
    print(f"Anotaciones Recuperadas en Relectura: {count_annots}")

    is_feasible = total_avg_ms < 100.0 and count_annots >= 2

    print(f"\nDictamen Factibilidad Técnica: {' FACTIBLE (Aprobado)' if is_feasible else ' NO FACTIBLE'}")
    print("==========================================================\n")

    return {
        "prototype": "Proto 02 - PyMuPDF Consistency",
        "is_feasible": is_feasible,
        "avg_open_ms": round(avg_open, 3),
        "avg_render_ms": round(avg_render, 3),
        "avg_search_ms": round(avg_search, 3),
        "avg_annot_ms": round(avg_annot, 3),
        "avg_save_ms": round(avg_save, 3),
        "total_avg_ms": round(total_avg_ms, 3),
        "annots_recovered": count_annots
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prototipo PyMuPDF PDF")
    parser.add_argument("--pdf", type=str, default=None, help="Ruta de archivo PDF a evaluar")
    args = parser.parse_args()

    run_prototype_02(pdf_path=args.pdf)
