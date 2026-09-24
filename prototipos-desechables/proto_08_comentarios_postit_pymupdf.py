"""
Prototipo Desechable: Notas Adhesivas / Post-It en PDF con PyMuPDF
------------------------------------------------------------------
Función EDDIE-2023: ConsistencyLibraryCommentsDP (Sticky Notes / Post-It)
Hardware Requerido: Ninguno (Sistema de archivos PDF)

Prueba directa y aislada ("probar una función y era").
"""

import sys
import os
import time
import fitz  # PyMuPDF

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def check_hardware(pdf_path="temp_comment_sample.pdf"):
    """Verifica disponibilidad del archivo PDF objetivo."""
    print(f"[VERIFICACIÓN ARCHIVO] Probando acceso a PDF ({pdf_path})...")
    if not os.path.exists(pdf_path):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(fitz.Point(50, 100), "Documento de Lectura Aumentada para Notas Adhesivas", fontsize=12)
        doc.save(pdf_path)
        doc.close()

    print(f" -> Estado Archivo PDF: ✅ DISPONIBLE Y ACCESIBLE")
    return True, pdf_path


def execute_function(pdf_path="temp_comment_sample.pdf", text_note="Nota proyectada desde escritorio físico"):
    """Ejecuta la función aislada: Insertar una nota de texto adhesiva (Post-it) en el PDF."""
    _, path = check_hardware(pdf_path)

    t0 = time.perf_counter()
    doc = fitz.open(path)
    page = doc[0]

    point = fitz.Point(400, 100)
    note = page.add_text_annot(point, text_note)
    note.update()

    out_path = "temp_comment_sample_annotated.pdf"
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
    print(f"Tiempo PyMuPDF Post-It Text Annotation: {t_proc:.2f} ms")
    print(f"Nota Adhesiva Estampada en Coordenadas:  (400, 100)")
    print(f"Contenido de la Nota:                    \"{text_note}\"")
    print("------------------------------------\n")


if __name__ == "__main__":
    execute_function()
