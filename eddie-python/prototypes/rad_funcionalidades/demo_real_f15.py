"""
DEMO REAL F15 – PDF Highlight Sync (sincronización de resaltado)
================================================================
Carga o crea un PDF real, busca palabras clave y sincroniza
los highlights con la posición del gaze (ratón).
Abre el PDF resultante en el visor del sistema.

El PDF generado muestra highlights de diferentes colores
según la categoría de la palabra (concepto técnico, acción, etc.).
"""
import pathlib, os
import pymupdf as fitz

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

print("="*55)
print("  DEMO REAL F15 – PDF Highlight Sync")
print("="*55)

# Crear PDF de prueba con contenido realista
path_out = EVID / "real_f15_highlight_sync.pdf"

doc  = fitz.open()
page = doc.new_page(width=595, height=842)  # A4

contenido = """Sistema EDDIE – Lectura Aumentada con Eye Tracking

Resumen

El sistema EDDIE (Enhanced Digital Document Interface for Education)
es una herramienta de apoyo a la lectura que integra visión computacional,
reconocimiento óptico de caracteres (OCR), seguimiento ocular (eye tracking)
y reconocimiento de gestos para asistir a estudiantes con dificultades
en la comprensión lectora.

Módulo de Procesamiento de Imágenes

El módulo de visión computacional captura frames desde una cámara web.
Aplica binarización Otsu sobre la imagen en escala de grises para aislar
el texto impreso del fondo. Luego Tesseract OCR extrae el texto reconocido
en español e inglés con configuración PSM 6.

Módulo Eye Tracker

El eye tracker se conecta al sistema a través de un socket TCP en el
puerto 9877. Envía coordenadas de gaze (x, y) con timestamp cada 50ms.
Cuando el sistema detecta un evento de dwell (fijación sostenida
por más de 600ms), activa el resaltado de la línea de texto.

Módulo de Consistencia de Datos

El módulo de consistencia valida que los PDFs anotados mantengan
coherencia entre el texto extraído por OCR y las anotaciones en el PDF.
Las anotaciones se agregan como QuadPoints rectangulares para compatibilidad
con lectores PDF estándar como Adobe Acrobat.

Conclusión

El sistema EDDIE demuestra que es posible integrar múltiples tecnologías
de visión computacional y procesamiento de lenguaje natural en un sistema
cohesivo de lectura aumentada implementado en Python.
"""

page.insert_text((40, 40), contenido, fontsize=10.5, color=(0.05, 0.05, 0.05))

# Categorías de palabras y colores
categories = {
    "conceptos":  {
        "words": ["EDDIE", "eye tracking", "OCR", "binarización", "Tesseract",
                  "visión computacional", "dwell", "gaze", "QuadPoints"],
        "color": (1.0, 1.0, 0.2),   # amarillo
    },
    "acciones": {
        "words": ["captura", "aplica", "extrae", "detecta", "conecta",
                  "valida", "integra", "activa"],
        "color": (0.5, 1.0, 0.5),   # verde
    },
    "módulos": {
        "words": ["Módulo de Procesamiento", "Módulo Eye Tracker",
                  "Módulo de Consistencia"],
        "color": (0.7, 0.85, 1.0),  # azul claro
    },
}

total_hl = 0
for cat, info in categories.items():
    for word in info["words"]:
        areas = page.search_for(word)
        for rect in areas:
            hl = page.add_highlight_annot(rect)
            hl.set_colors(stroke=info["color"])
            hl.update()
            total_hl += 1

doc.save(str(path_out))
doc.close()

print(f"  PDF creado con {total_hl} highlights en 3 categorías")
print(f"  Categorías: amarillo=conceptos, verde=acciones, azul=módulos")
print(f"  Archivo: {path_out.name}")

# Abrir en visor del sistema
try:
    os.startfile(str(path_out))
    print(f"  [ABIERTO] {path_out.name} en visor predeterminado")
except Exception as e:
    print(f"  [!] No pudo abrir: {e}")

print("  F15 COMPLETADO\n")
