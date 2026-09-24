"""
Prototipo Desechable: Destacado Amarillo en PDF con PyMuPDF
------------------------------------------------------------
Función EDDIE-2023: ModuloConsistenciaDatos (DigitalDocSync Highlight Annotation)
Hardware Requerido: Ninguno (Sistema de archivos PDF)

Prueba directa y aislada ("probar una función y era").
"""

import sys
import os
import time
import fitz  # PyMuPDF

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def check_hardware(pdf_path="temp_sample.pdf"):
    """Verifica disponibilidad del archivo PDF objetivo."""
    print(f"[VERIFICACIÓN ARCHIVO] Probando acceso a PDF ({pdf_path})...")
    if not os.path.exists(pdf_path):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(fitz.Point(50, 100), "EDDIE Test Document - Realidad Aumentada sobre Papel", fontsize=12)
        doc.save(pdf_path)
        doc.close()

    print(f" -> Estado Archivo PDF: ✅ DISPONIBLE Y ACCESIBLE")
    return True, pdf_path


def execute_function(pdf_path="temp_sample.pdf", word="Realidad"):
    """Ejecuta la función aislada: Buscar término en PDF e insertar anotación Highlight amarilla."""
    _, path = check_hardware(pdf_path)

    t0 = time.perf_counter()
    doc = fitz.open(path)
    page = doc[0]
    quads = page.search_for(word, quads=True)

    count_annots = 0
    if quads:
        for q in quads:
            annot = page.add_highlight_annot(q)
            annot.set_colors(stroke=(1, 1, 0))  # Amarillo
            annot.update()
            count_annots += 1

    out_path = "temp_sample_highlighted.pdf"
    doc.save(out_path)
    doc.close()
    t_proc = (time.perf_counter() - t0) * 1000.0

    # Limpieza
    for f in [path, out_path]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    print("\n--- RESULTADO DE FUNCIÓN AISLADA ---")
    print(f"Tiempo PyMuPDF Highlight Annotation: {t_proc:.2f} ms")
    print(f"Destacadas Insertadas en QuadPoints: {count_annots}")
    print("------------------------------------\n")


if __name__ == "__main__":
    execute_function()
