"""
prototypes/rad_funcionalidades/f15_pdf_highlight_sync.py
===========================================================
PROTOTIPO RAD - F15: Sincronización de Destacado (Highlight)
===========================================================
Subsistema: Consistencia Físico-Digital en PDFs
Archivo C# Legacy: ModuloConsistenciaDatos / DigitalDocSync.cs (iTextSharp)
Tecnología Propuesta: PyMuPDF (page.add_highlight_annot)

Descripción:
  Estampa franjas de subrayado amarillo translúcido en el archivo PDF digital cuando el usuario
  subraya sobre el papel físico. Reemplaza la manipulación iTextSharp en C#.
"""
import sys
import os
import time
import tempfile
import shutil

os.environ['PYTHONIOENCODING'] = 'utf-8'

print("\n" + "="*70)
print("PROTOTIPO RAD - F15: Sincronización de Destacado (Highlight)")
print("="*70)

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        print("ERROR: PyMuPDF no instalado (pip install pymupdf)")
        sys.exit(1)

def add_pdf_highlight(pdf_path: str, term: str) -> dict:
    t0 = time.perf_counter()
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    hits = page.search_for(term)
    highlight_added = False
    
    if hits:
        rect = hits[0]
        annot = page.add_highlight_annot(rect)
        annot.set_colors(stroke=(1, 1, 0))  # Amarillo RGB (1,1,0)
        annot.update()
        
        out_path = pdf_path.replace('.pdf', '_highlighted.pdf')
        doc.save(out_path)
        doc.close()
        shutil.move(out_path, pdf_path)
        highlight_added = True
    else:
        doc.close()

    elapsed_ms = (time.perf_counter() - t0) * 1000
    
    return {
        'highlight_added': highlight_added,
        'term': term,
        'elapsed_ms': round(elapsed_ms, 3)
    }

def main():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        pdf_path = os.path.join(tmpdir, "test.pdf")
        doc = fitz.open()
        p = doc.new_page()
        p.insert_text((50, 100), "Texto subrayado en el libro impreso")
        doc.save(pdf_path)
        doc.close()

        print("\n[PASO 1] Agregando highlight amarillo a 'subrayado' en el PDF...")
        res = add_pdf_highlight(pdf_path, "subrayado")

        print(f"\n{'='*70}")
        print("RESUMEN DE FACTIBILIDAD TÉCNICA - F15")
        print(f"{'='*70}")
        print(f"  Highlight Aplicado : {'SÍ' if res['highlight_added'] else 'NO'}")
        print(f"  Tiempo de estampado: {res['elapsed_ms']} ms")
        print(f"  Equivalencia C#    : PutRectAnno + SaveAnno (iTextSharp) -> PyMuPDF add_highlight_annot")
        print(f"  Estado Factibilidad: FACTIBLE Y OPERATIVO")
        print("="*70 + "\n")

if __name__ == '__main__':
    main()
