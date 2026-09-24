"""
prototypes/rad_funcionalidades/f16_pdf_postit_comments.py
===========================================================
PROTOTIPO RAD - F16: Sincronización de Notas Adhesivas (Post-It / Comentarios)
===========================================================
Subsistema: Consistencia Físico-Digital en PDFs
Archivo C# Legacy: ConsistencyLibraryCommentsDP / CommentsPD.cs
Tecnología Propuesta: PyMuPDF (page.add_text_annot)

Descripción:
  Sincroniza notas escritas en el papel hacia el PDF digital como anotaciones de texto (post-it),
  o proyecta notas digitales sobre el libro impreso.
"""
import sys
import os
import time
import tempfile
import shutil

os.environ['PYTHONIOENCODING'] = 'utf-8'

print("\n" + "="*70)
print("PROTOTIPO RAD - F16: Sincronización de Notas Adhesivas (Post-It)")
print("="*70)

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        print("ERROR: PyMuPDF no instalado (pip install pymupdf)")
        sys.exit(1)

def add_postit_comment(pdf_path: str, comment_text: str, norm_x: float = 0.5, norm_y: float = 0.3) -> dict:
    t0 = time.perf_counter()
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    px = norm_x * page.rect.width
    py = norm_y * page.rect.height
    
    annot = page.add_text_annot((px, py), comment_text)
    annot.update()
    
    out_path = pdf_path.replace('.pdf', '_commented.pdf')
    doc.save(out_path)
    doc.close()
    shutil.move(out_path, pdf_path)
    
    elapsed_ms = (time.perf_counter() - t0) * 1000
    
    return {
        'comment_added': True,
        'text': comment_text,
        'pos_pts': (round(px, 1), round(py, 1)),
        'elapsed_ms': round(elapsed_ms, 3)
    }

def main():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        pdf_path = os.path.join(tmpdir, "doc.pdf")
        doc = fitz.open()
        doc.new_page()
        doc.save(pdf_path)
        doc.close()

        print("\n[PASO 1] Insertando nota adhesiva (Post-It) en el PDF...")
        res = add_postit_comment(pdf_path, "Nota física capturada desde la cámara de EDDIE")

        print(f"\n{'='*70}")
        print("RESUMEN DE FACTIBILIDAD TÉCNICA - F16")
        print(f"{'='*70}")
        print(f"  Nota Insertada     : '{res['text']}'")
        print(f"  Posición Puntos    : {res['pos_pts']}")
        print(f"  Tiempo de proceso  : {res['elapsed_ms']} ms")
        print(f"  Equivalencia C#    : ConsistencyLibraryCommentsDP -> PyMuPDF add_text_annot")
        print(f"  Estado Factibilidad: FACTIBLE Y OPERATIVO")
        print("="*70 + "\n")

if __name__ == '__main__':
    main()
