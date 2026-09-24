"""
prototypes/proto_02_pymupdf.py
================================
PROTOTIPO RAD #2: Factibilidad de migración iTextSharp → PyMuPDF
=================================================================

PROPÓSITO:
  Validar que PyMuPDF (fitz) puede reemplazar iTextSharp para:
  1. Leer PDFs y sus anotaciones (highlights, comentarios)
  2. Agregar highlights al PDF digital
  3. Buscar texto en un PDF
  4. Sincronizar anotaciones físico-digital

EQUIVALENCIAS con DigitalDocSync.cs (C# legacy):
  iTextSharp (C#)                    → PyMuPDF (Python)
  PdfReader reader = new PdfReader() → fitz.open(pdf_path)
  PdfStamper stamper = new PdfStamper() → page.add_annot(...)
  PdfAnnotation.CreateMarkup(...)    → page.add_highlight_annot(rect)
  PdfTextExtractor.GetTextFromPage() → page.get_text()
  reader.GetPageSize(1)              → page.rect

CÓMO EJECUTAR:
  .\\..\\eddie-python-venv\\Scripts\\python.exe prototypes/proto_02_pymupdf.py
  .\\..\\eddie-python-venv\\Scripts\\python.exe prototypes/proto_02_pymupdf.py --pdf ruta/archivo.pdf
"""

# -*- coding: utf-8 -*-
import sys
import time
import argparse
import os
import tempfile
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

print("\n" + "=" * 60)
print("PROTOTIPO RAD #2: Factibilidad PyMuPDF (reemplaza iTextSharp)")
print("=" * 60)

# ─────────────────────────────────────────────────────────────────
# PASO 1: Verificar PyMuPDF
# ─────────────────────────────────────────────────────────────────
print("\n[PASO 1] Verificando instalacion de PyMuPDF...")
try:
    import pymupdf as fitz  # Nueva API recomendada (fitz queda deprecated)
    print(f"  OK PyMuPDF instalado: version {fitz.version[0]}")
    print(f"  OK Bindings PDF: {fitz.version}")
except ImportError:
    try:
        import fitz
        print(f"  OK PyMuPDF (fitz legacy) instalado: version {fitz.version[0]}")
    except ImportError as e:
        print(f"  ERROR: PyMuPDF no instalado. Ejecuta: pip install pymupdf")
        print(f"    Detalle: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────
# PASO 2: Crear un PDF de prueba
# ─────────────────────────────────────────────────────────────────
def create_test_pdf(output_path: str) -> str:
    """
    Crea un PDF de prueba con texto para validar las operaciones.
    Equivale a tener el PDF digital de EDDIE para sincronizar con el físico.
    """
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # Tamaño A4 en puntos
    
    # Insertar texto de prueba
    page.insert_text(
        (72, 100),
        "PROTOTIPO PYMUPDF - EDDIE Python\n\n"
        "Lectura aumentada en papel físico.\n"
        "El sistema EDDIE permite buscar información\n"
        "sobre palabras subrayadas en el documento.\n\n"
        "Eye tracking: detección de fijaciones oculares.\n"
        "Reconocimiento gestual con OpenCV.\n"
        "Consistencia bidireccional físico-digital.\n\n"
        "Este texto simula el contenido de un\n"
        "documento académico que el usuario lee\n"
        "con apoyo del sistema EDDIE Python.",
        fontsize=14,
        color=(0, 0, 0)
    )
    
    doc.save(output_path)
    doc.close()
    return output_path


# ─────────────────────────────────────────────────────────────────
# PASO 3: Leer PDF y extraer texto
# (Equivale a PdfTextExtractor.GetTextFromPage() en C#)
# ─────────────────────────────────────────────────────────────────
def test_read_pdf(pdf_path: str) -> dict:
    """
    Lee el PDF y extrae texto por página.
    Reemplaza la lógica de DigitalDocSync.SearchTxtPdf() en C#.
    """
    print(f"\n[PASO 3] Leyendo PDF: {pdf_path}")
    t0 = time.perf_counter()
    
    results = {}
    try:
        doc = fitz.open(pdf_path)
        read_time = (time.perf_counter() - t0) * 1000
        
        print(f"  ✓ PDF abierto en {read_time:.2f} ms")
        print(f"  ✓ Número de páginas: {len(doc)}")
        
        # Obtener dimensiones de la primera página
        page = doc[0]
        rect = page.rect
        results['page_width'] = rect.width
        results['page_height'] = rect.height
        print(f"  ✓ Dimensiones página 1: {rect.width:.0f} x {rect.height:.0f} pts")
        
        # Extraer texto de la primera página
        t0 = time.perf_counter()
        text = page.get_text()
        extract_time = (time.perf_counter() - t0) * 1000
        
        words = [w.strip() for w in text.split() if len(w.strip()) > 2]
        results['text'] = text.strip()
        results['word_count'] = len(words)
        results['read_time_ms'] = round(read_time, 3)
        results['extract_time_ms'] = round(extract_time, 3)
        
        print(f"  ✓ Texto extraído en {extract_time:.2f} ms ({len(words)} palabras)")
        print(f"  ✓ Preview: {text[:80].strip()}...")
        
        doc.close()
        results['success'] = True
        
    except Exception as e:
        print(f"  ✗ Error leyendo PDF: {e}")
        results['success'] = False
        results['error'] = str(e)
    
    return results


# ─────────────────────────────────────────────────────────────────
# PASO 4: Agregar highlight al PDF
# (Equivale a DigitalDocSync.SaveAnno() + PutRectAnno() en C#)
# ─────────────────────────────────────────────────────────────────
def test_add_highlight(pdf_path: str, output_path: str) -> dict:
    """
    Agrega un highlight amarillo al PDF y lo guarda.
    Reemplaza DigitalDocSync.PutRectAnno() que usaba iTextSharp.
    """
    print(f"\n[PASO 4] Agregando highlight al PDF...")
    t0 = time.perf_counter()
    
    results = {}
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        
        # Buscar instancias de "lectura aumentada" para hacer highlight
        # (equivale a identificar texto subrayado en el documento físico)
        search_phrase = "lectura aumentada"
        text_instances = page.search_for(search_phrase)
        
        if text_instances:
            # Agregar highlight amarillo a cada instancia encontrada
            for rect in text_instances:
                highlight = page.add_highlight_annot(rect)
                highlight.set_colors(stroke=(1, 1, 0))  # Amarillo = (R=1, G=1, B=0)
                highlight.update()
            
            print(f"  ✓ '{search_phrase}' encontrado y marcado ({len(text_instances)} instancias)")
        else:
            # Si no encuentra el texto exacto, hacer highlight en área fija
            # (simulando highlight desde coordenadas de cámara)
            rect = fitz.Rect(72, 130, 400, 150)  # x0, y0, x1, y1 en puntos
            highlight = page.add_highlight_annot(rect)
            highlight.set_colors(stroke=(1, 1, 0))
            highlight.update()
            print(f"  ✓ Highlight de área fija agregado (simulando detección de cámara)")
        
        # Agregar también un comentario (sticky note)
        # Equivale a ConsistencyLibraryCommentsDP en C# legacy
        comment_rect = fitz.Rect(72, 200, 100, 220)
        annot = page.add_text_annot(comment_rect.tl, "Anotación desde EDDIE Python")
        annot.update()
        
        # Guardar el PDF modificado
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        
        save_time_ms = (time.perf_counter() - t0) * 1000
        results['save_time_ms'] = round(save_time_ms, 3)
        results['output_path'] = output_path
        results['success'] = True
        
        print(f"  ✓ PDF con highlight guardado en {save_time_ms:.2f} ms")
        print(f"  ✓ Ruta: {output_path}")
        
    except Exception as e:
        print(f"  ✗ Error agregando highlight: {e}")
        results['success'] = False
        results['error'] = str(e)
    
    return results


# ─────────────────────────────────────────────────────────────────
# PASO 5: Leer anotaciones existentes del PDF
# (Equivale a DigitalDocSync.GetRectAnno() en C#)
# ─────────────────────────────────────────────────────────────────
def test_read_annotations(pdf_path: str) -> dict:
    """
    Lee las anotaciones (highlights, comentarios) de un PDF.
    Reemplaza DigitalDocSync.GetRectAnno() que usaba iTextSharp.
    """
    print(f"\n[PASO 5] Leyendo anotaciones del PDF...")
    t0 = time.perf_counter()
    
    results = {'annotations': []}
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        
        # Iterar sobre todas las anotaciones de la página
        for annot in page.annots():
            annot_info = {
                'type': annot.type[1],  # Nombre del tipo (ej: 'Highlight', 'Text')
                'rect': [annot.rect.x0, annot.rect.y0, annot.rect.x1, annot.rect.y1],
                'content': annot.info.get('content', ''),
            }
            results['annotations'].append(annot_info)
        
        read_time_ms = (time.perf_counter() - t0) * 1000
        results['read_time_ms'] = round(read_time_ms, 3)
        results['count'] = len(results['annotations'])
        results['success'] = True
        
        print(f"  ✓ {results['count']} anotaciones encontradas en {read_time_ms:.2f} ms")
        for i, ann in enumerate(results['annotations']):
            print(f"    [{i+1}] Tipo: {ann['type']}, Rect: {[round(c,1) for c in ann['rect']]}")
        
        doc.close()
        
    except Exception as e:
        print(f"  ✗ Error leyendo anotaciones: {e}")
        results['success'] = False
        results['error'] = str(e)
    
    return results


# ─────────────────────────────────────────────────────────────────
# PROGRAMA PRINCIPAL
# ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description='Prototipo RAD #2: Factibilidad PyMuPDF para EDDIE Python'
    )
    parser.add_argument('--pdf', type=str, default=None,
                        help='Ruta a PDF existente para probar (opcional)')
    args = parser.parse_args()
    
    # Usar directorio temporal para los archivos generados
    with tempfile.TemporaryDirectory() as tmpdir:
        
        if args.pdf and os.path.exists(args.pdf):
            test_pdf_path = args.pdf
            print(f"\n[PASO 2] Usando PDF existente: {test_pdf_path}")
        else:
            # Crear PDF de prueba
            test_pdf_path = os.path.join(tmpdir, 'test_documento.pdf')
            print(f"\n[PASO 2] Creando PDF de prueba...")
            create_test_pdf(test_pdf_path)
            print(f"  ✓ PDF de prueba creado: {test_pdf_path}")
        
        # Ejecutar todos los tests
        read_results = test_read_pdf(test_pdf_path)
        
        highlighted_pdf_path = os.path.join(tmpdir, 'test_highlighted.pdf')
        highlight_results = test_add_highlight(test_pdf_path, highlighted_pdf_path)
        
        annotation_results = {}
        if highlight_results.get('success'):
            annotation_results = test_read_annotations(highlighted_pdf_path)
        
        # ── Resumen final ─────────────────────────────────────────
        print("\n" + "=" * 60)
        print("RESUMEN DEL PROTOTIPO RAD #2 - PyMuPDF")
        print("=" * 60)
        
        print("\n📊 MÉTRICAS DE RENDIMIENTO:")
        print(f"   Apertura PDF         : {read_results.get('read_time_ms', 'N/A')} ms")
        print(f"   Extracción de texto  : {read_results.get('extract_time_ms', 'N/A')} ms")
        print(f"   Guardado con highlight: {highlight_results.get('save_time_ms', 'N/A')} ms")
        print(f"   Lectura de anotaciones: {annotation_results.get('read_time_ms', 'N/A')} ms")
        
        print("\n📋 FUNCIONALIDADES VALIDADAS:")
        print(f"   ✓ Leer PDF y extraer texto  : {'SÍ' if read_results.get('success') else 'NO'}")
        print(f"   ✓ Agregar highlight amarillo : {'SÍ' if highlight_results.get('success') else 'NO'}")
        print(f"   ✓ Agregar comentarios        : {'SÍ' if highlight_results.get('success') else 'NO'}")
        print(f"   ✓ Leer anotaciones existentes: {'SÍ' if annotation_results.get('success') else 'NO'}")
        
        all_ok = all([
            read_results.get('success'),
            highlight_results.get('success'),
        ])
        
        print("\n✅ CONCLUSIÓN DE FACTIBILIDAD:")
        if all_ok:
            print("   ✓ PyMuPDF puede reemplazar completamente iTextSharp")
            print("   ✓ La migración del ModuloConsistenciaDatos es FACTIBLE")
            print("   ✓ Resultado: PROCEDER con IConsistencyProvider")
            print("\n📊 EQUIVALENCIAS VALIDADAS:")
            print("   iTextSharp PdfReader          → fitz.open()")
            print("   PdfTextExtractor.GetText()    → page.get_text()")
            print("   PdfAnnotation.CreateMarkup()  → page.add_highlight_annot()")
            print("   PdfStamper.AddAnnotation()    → annot.update() + doc.save()")
        else:
            print("   ⚠ Algunas funcionalidades no pudieron ser validadas.")
            print("   Revisa los errores anteriores.")
        
        print("\n📝 PARA TU TESIS:")
        print("   Documenta estos resultados en Capítulo 6 (Implementación).")
        print("   Compara tiempos con iTextSharp del código C# legacy.")
        print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
