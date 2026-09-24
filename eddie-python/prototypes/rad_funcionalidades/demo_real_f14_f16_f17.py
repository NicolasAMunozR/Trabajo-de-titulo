"""
DEMO REAL F14–F17 – PDFs: Highlight, Post-it, Figuras
=======================================================
Crea PDFs REALES con anotaciones y los abre en el visor
del sistema (Acrobat, Edge, etc.) para que los veas.

- F14: Highlight de palabras clave
- F16: Comentario post-it  
- F17: Figuras geométricas dibujadas en PDF
"""
import pathlib, subprocess, sys, os
import pymupdf as fitz  # PyMuPDF

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

def abrir_pdf(path):
    """Abre el PDF con el visor predeterminado del sistema."""
    try:
        os.startfile(str(path))
        print(f"  [ABIERTO] {path.name}")
    except Exception as e:
        print(f"  [!] No pudo abrir: {e}  →  Revisa en {path}")

# ── F14: Highlight real ──────────────────────────────────────────────────────
print("=" * 55)
print("  F14 – PDF con Highlight de texto real")
print("=" * 55)

path_f14 = EVID / "real_f14_highlight.pdf"
doc = fitz.open()
page = doc.new_page(width=595, height=842)   # A4

texto = """
SISTEMA EDDIE – Lectura Aumentada Aumentada

EDDIE (Enhanced Digital Document Interface for Education)
es un sistema de lectura aumentada que combina visión
computacional, reconocimiento óptico de caracteres (OCR),
seguimiento ocular (eye tracking) y reconocimiento gestual
para asistir a estudiantes con dificultades de lectura.

El sistema procesa documentos PDF e imágenes capturadas
por cámara, aplicando binarización Otsu y Tesseract OCR
para extraer el texto de la página actual.

Las palabras clave como "OCR", "Tesseract", "eye tracking"
y "binarización" son detectadas y resaltadas automáticamente
por el módulo de Procesamiento de Imágenes de EDDIE.
"""

page.insert_text((50, 60), texto, fontsize=11, color=(0, 0, 0))

# Resaltar palabras clave
keywords = ["OCR", "Tesseract", "eye tracking", "binarización", "EDDIE"]
colors_map = {
    "OCR":         (1, 1, 0),
    "Tesseract":   (0.5, 1, 0.5),
    "eye tracking":(0.5, 0.8, 1),
    "binarización":(1, 0.7, 0.3),
    "EDDIE":       (1, 0.5, 0.5),
}

highlighted = 0
for kw in keywords:
    areas = page.search_for(kw)
    for rect in areas:
        hl = page.add_highlight_annot(rect)
        col = colors_map.get(kw, (1,1,0))
        hl.set_colors(stroke=col)
        hl.update()
        highlighted += 1

doc.save(str(path_f14))
doc.close()
print(f"  PDF creado con {highlighted} highlights → {path_f14.name}")
abrir_pdf(path_f14)

# ── F16: Post-it ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  F16 – PDF con Post-it / Anotaciones")
print("=" * 55)

path_f16 = EVID / "real_f16_postit.pdf"
doc = fitz.open()
page = doc.new_page(width=595, height=842)

page.insert_text((50, 60), """
MÓDULO OCR – Reconocimiento Óptico de Caracteres

El módulo OCR de EDDIE utiliza Tesseract 5.4 con soporte
para español e inglés (spa+eng). El pipeline de procesamiento
incluye los siguientes pasos:

  1. Captura de frame desde DroidCam (640×480 @ 30fps)
  2. Conversión BGR a escala de grises
  3. Filtro Gaussiano 5×5 para reducir ruido
  4. Binarización Otsu para aislar el texto
  5. Tesseract OCR con modo PSM 6 (bloque de texto uniforme)
  6. Post-procesamiento y entrega al módulo de resaltado

El texto reconocido se sincroniza con el PDF abierto para
ubicar la región correspondiente y aplicar highlights.
""", fontsize=10.5)

# Agregar post-its
notas = [
    ((400, 80),  "TODO: Probar con más idiomas (fr, de)"),
    ((400, 180), "REVISAR: Paso 4 puede fallar con texto manuscrito"),
    ((400, 300), "OK: Funciona bien con impresión láser a 300+ DPI"),
]
for (x, y), texto_nota in notas:
    annot = page.add_text_annot((x, y), texto_nota)
    annot.set_colors(stroke=(1, 0.8, 0))
    annot.update()
    print(f"  Post-it añadido: {texto_nota[:40]}")

doc.save(str(path_f16))
doc.close()
abrir_pdf(path_f16)

# ── F17: Figuras geométricas ──────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  F17 – PDF con Figuras Geométricas")
print("=" * 55)

path_f17 = EVID / "real_f17_figuras.pdf"
doc = fitz.open()
page = doc.new_page(width=595, height=842)

page.insert_text((50, 40), "F17 – EDDIE: Figuras Geométricas en PDF", fontsize=14)
page.insert_text((50, 65), "Zonas de interés marcadas por el sistema de eye tracking:", fontsize=10)

# Rectángulo rojo = zona de lectura actual
page.draw_rect(fitz.Rect(50, 90, 545, 200), color=(0.9, 0.1, 0.1), width=2)
page.insert_text((55, 105), "Zona activa (gaze dwell detectado)", fontsize=9, color=(0.8,0,0))

# Círculo azul = punto de fijación
page.draw_circle(fitz.Point(297, 260), 35, color=(0.1, 0.3, 0.9), fill=(0.8, 0.9, 1.0))
page.insert_text((260, 262), "Fijación", fontsize=9, color=(0,0,0.8))

# Línea verde = línea de lectura
page.draw_line(fitz.Point(50, 330), fitz.Point(545, 330), color=(0, 0.7, 0.2), width=2)
page.insert_text((50, 342), "Línea de lectura (tracker)", fontsize=9, color=(0, 0.6, 0))

# Polígono = área de interés irregular
poly = [fitz.Point(80, 370), fitz.Point(200, 360), fitz.Point(220, 430),
        fitz.Point(160, 450), fitz.Point(70, 430)]
page.draw_polyline(poly, color=(0.6, 0.1, 0.8), width=1.5)
page.insert_text((85, 375), "ROI irregular", fontsize=8, color=(0.5, 0, 0.7))

doc.save(str(path_f17))
doc.close()
print(f"  PDF con figuras creado → {path_f17.name}")
abrir_pdf(path_f17)

print("\n  ✓ F14, F16, F17 – PDFs reales creados y abiertos en el visor del sistema")
print(f"  Guardados en: {EVID}\n")
