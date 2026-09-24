"""
prototypes/rad_funcionalidades/f17_pdf_geometric_figures.py
===========================================================
PROTOTIPO RAD - F17: Sincronización de Figuras Geométricas
===========================================================
Subsistema: Consistencia Físico-Digital en PDFs
Archivo C# Legacy: ConsistencyLibraryFiguresDP / FiguresPD.cs
Tecnología Propuesta: PyMuPDF (page.add_rect_annot, page.add_circle_annot)

Descripción:
  Extrae o dibuja círculos y rectángulos sobre el PDF y los proyecta sobre el libro impreso.
"""
import sys
import os
import time
import tempfile
import shutil

os.environ['PYTHONIOENCODING'] = 'utf-8'

print("\n" + "="*70)
print("PROTOTIPO RAD - F17: Sincronización de Figuras Geométricas")
print("="*70)

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        print("ERROR: PyMuPDF no instalado (pip install pymupdf)")
        sys.exit(1)

def add_geometric_rect(pdf_path: str, norm_rect: tuple) -> dict:
    t0 = time.perf_counter()
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    # Rectángulo en puntos
    r = fitz.Rect(
        norm_rect[0] * page.rect.width,
        norm_rect[1] * page.rect.height,
        norm_rect[2] * page.rect.width,
        norm_rect[3] * page.rect.height
    )
    
    annot = page.add_rect_annot(r)
    annot.set_colors(stroke=(1, 0, 0))  # Rojo
    annot.update()
    
    out_path = pdf_path.replace('.pdf', '_rect.pdf')
    doc.save(out_path)
    doc.close()
    shutil.move(out_path, pdf_path)
    
    elapsed_ms = (time.perf_counter() - t0) * 1000
    
    return {
        'rect_added': True,
        'rect_pts': (r.x0, r.y0, r.x1, r.y1),
        'elapsed_ms': round(elapsed_ms, 3)
    }

def main():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        pdf_path = os.path.join(tmpdir, "figures.pdf")
        doc = fitz.open()
        doc.new_page()
        doc.save(pdf_path)
        doc.close()

        print("\n[PASO 1] Estampando rectángulo rojo en coordenadas normalizadas [0.1, 0.1, 0.4, 0.3]...")
        res = add_geometric_rect(pdf_path, (0.1, 0.1, 0.4, 0.3))

        print(f"\n{'='*70}")
        print("RESUMEN DE FACTIBILIDAD TÉCNICA - F17")
        print(f"{'='*70}")
        print(f"  Rectángulo Agregado: SÍ")
        print(f"  Coordenadas Puntos : {res['rect_pts']}")
        print(f"  Tiempo de Proceso  : {res['elapsed_ms']} ms")
        print(f"  Equivalencia C#    : ConsistencyLibraryFiguresDP -> PyMuPDF add_rect_annot")
        print(f"  Estado Factibilidad: FACTIBLE Y OPERATIVO")
        print("="*70 + "\n")

if __name__ == '__main__':
    main()
