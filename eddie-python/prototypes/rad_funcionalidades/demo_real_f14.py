"""
DEMO REAL F14 – Búsqueda y Mapeo de Coordenadas QuadPoints en PDF
===================================================================
Basado en: ModuloConsistenciaDatos / DigitalDocSync.cs (EDDIE Legacy C#)

Funcionalidad REAL:
1. Carga un documento PDF real (o genera un documento formal de lectura aumentada).
2. Permite buscar términos interactivos dentro del PDF mediante PyMuPDF (fitz).
3. Extrae las coordenadas exactas: Bounding Boxes [x0, y0, x1, y1] y QuadPoints
   (8 puntos: [x_tl, y_tl, x_tr, y_tr, x_bl, y_bl, x_br, y_br]) para cada coincidencia.
4. Aplica anotaciones Highlight reales en el PDF con los QuadPoints mapeados.
5. Muestra una ventana interactiva con el visor del PDF renderizado, los recuadros
   de QuadPoints detectados y una tabla de coordenadas en tiempo real.
6. Abre el archivo PDF resultante en el visor predeterminado del sistema (Acrobat/Edge).

Controles:
  1-5 = Buscar términos predefinidos  |  S = Guardar captura  |  Q = Salir
"""

import os
import sys
import pathlib
import time
import cv2
import numpy as np
import pymupdf as fitz

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

PDF_SAMPLE_PATH = EVID / "real_f14_quadpoints_input.pdf"
PDF_OUTPUT_PATH = EVID / "real_f14_quadpoints_highlighted.pdf"

PRESET_QUERIES = [
    "EDDIE",
    "visión computacional",
    "OCR",
    "eye tracking",
    "consistencia",
]

def crear_pdf_base_si_no_existe():
    """Genera un documento PDF estructurado para pruebas de búsqueda de texto y QuadPoints."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Carta estándar (Letter)
    
    # Encabezado
    page.insert_text((50, 50), "SISTEMA EDDIE: Lectura Aumentada y Consistencia de Datos", 
                     fontsize=14, color=(0.1, 0.2, 0.5))
    page.draw_line((50, 58), (560, 58), color=(0.1, 0.2, 0.5), width=1.5)

    contenido = """
1. Introducción al Sistema EDDIE
El sistema EDDIE (Enhanced Digital Document Interface for Education) combina visión computacional,
reconocimiento óptico de caracteres (OCR) y seguimiento ocular (eye tracking) para asistir a estudiantes
con dificultades lectoras.

2. Módulo de Consistencia de Datos (DigitalDocSync)
Para mantener sincronizados el documento físico y el PDF digital, el sistema extrae las coordenadas
geométricas exactas (QuadPoints y Bounding Boxes) de cada palabra y línea de texto.

3. Mapeo de QuadPoints
Un QuadPoint define un cuadrilátero orientado en el espacio del documento PDF mediante 8 valores:
(x_top_left, y_top_left, x_top_right, y_top_right, x_bottom_left, y_bottom_left, x_bottom_right, y_bottom_right).
Esto permite aplicar anotaciones de resaltado consistentes incluso en textos justificados o rotados.

4. Procesamiento en Tiempo Real
Cuando el usuario enfoca su mirada (eye tracking dwell) o marca con un lápiz óptico, el módulo OCR
asocia el texto reconocido con las coordenadas QuadPoints del PDF original, asegurando consistencia
entre el texto físico y digital.
"""
    page.insert_text((50, 80), contenido.strip(), fontsize=10.5, color=(0.1, 0.1, 0.1), lineheight=1.4)
    
    # Pie de página
    page.draw_line((50, 740), (560, 740), color=(0.7, 0.7, 0.7), width=0.8)
    page.insert_text((50, 755), "Prototipo F14 – Consistencia de Coordenadas QuadPoints | EDDIE Python", 
                     fontsize=8, color=(0.5, 0.5, 0.5))
    
    doc.save(str(PDF_SAMPLE_PATH))
    doc.close()

def buscar_y_mapear_quadpoints(pdf_path, search_term):
    """
    Busca un término en el PDF usando PyMuPDF y retorna:
    - Lista de Rect (bounding boxes)
    - Lista de QuadPoints (8 coordenadas float por coincidencia)
    - Texto circundante / contexto
    """
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    
    # Búsqueda con retorno de quads (QuadPoints reales)
    quads = page.search_for(search_term, quads=True)
    rects = page.search_for(search_term, quads=False)
    
    results = []
    for i, (q, r) in enumerate(zip(quads, rects)):
        # Cada quad en PyMuPDF tiene puntos: ul (upper-left), ur, ll, lr
        quad_coords = [
            q.ul.x, q.ul.y,
            q.ur.x, q.ur.y,
            q.ll.x, q.ll.y,
            q.lr.x, q.lr.y,
        ]
        results.append({
            "index": i + 1,
            "rect": (r.x0, r.y0, r.x1, r.y1),
            "width": r.width,
            "height": r.height,
            "quadpoints": quad_coords,
        })
    doc.close()
    return results

def generar_pdf_anotado(search_term, color=(1, 1, 0)):
    """Aplica anotaciones Highlight con QuadPoints reales en el PDF y lo guarda."""
    doc = fitz.open(str(PDF_SAMPLE_PATH))
    page = doc[0]
    
    # Limpiar anotaciones previas
    for annot in page.annots():
        page.delete_annot(annot)
        
    quads = page.search_for(search_term, quads=True)
    for q in quads:
        annot = page.add_highlight_annot(quads=[q])
        annot.set_colors(stroke=color)
        annot.update()
        
    doc.save(str(PDF_OUTPUT_PATH))
    doc.close()

def renderizar_pagina_a_imagen(pdf_path, dpi=130):
    """Renderiza la primera página del PDF a imagen OpenCV BGR."""
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    pix = page.get_pixmap(dpi=dpi)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.h, pix.w, pix.n))
    doc.close()
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img, pix.w / 612.0  # factor de escala

def abrir_pdf_sistema(path):
    try:
        os.startfile(str(path))
        print(f"  [ABIERTO EN VISOR] {path.name}")
    except Exception as e:
        print(f"  [!] No se pudo abrir visor: {e}")

def main():
    print("=" * 65)
    print("  DEMO REAL F14 – Búsqueda y Mapeo de QuadPoints en PDF")
    print("  Módulo: ModuloConsistenciaDatos / DigitalDocSync.cs")
    print("=" * 65)
    
    crear_pdf_base_si_no_existe()
    print(f"  [+] Documento PDF base: {PDF_SAMPLE_PATH.name}")

    query_idx = 0
    current_query = PRESET_QUERIES[query_idx]
    
    cv2.namedWindow("EDDIE – F14 Mapeo QuadPoints en PDF", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("EDDIE – F14 Mapeo QuadPoints en PDF", 1280, 780)

    pdf_abierto = False

    while True:
        # 1. Buscar QuadPoints reales
        matches = buscar_y_mapear_quadpoints(PDF_SAMPLE_PATH, current_query)
        
        # 2. Guardar PDF con anotaciones reales
        generar_pdf_anotado(current_query)
        
        # 3. Renderizar PDF y superponer visualización
        page_img, scale = renderizar_pagina_a_imagen(PDF_OUTPUT_PATH)
        
        # Dibujar marcas de QuadPoints sobre la imagen renderizada
        display_page = page_img.copy()
        for m in matches:
            rx0, ry0, rx1, ry1 = m["rect"]
            x0, y0 = int(rx0 * scale), int(ry0 * scale)
            x1, y1 = int(rx1 * scale), int(ry1 * scale)
            
            # Recuadro verde con esquinas marcadas
            cv2.rectangle(display_page, (x0, y0), (x1, y1), (0, 0, 255), 2)
            cv2.circle(display_page, (x0, y0), 4, (0, 220, 0), -1)  # TL
            cv2.circle(display_page, (x1, y0), 4, (0, 220, 0), -1)  # TR
            cv2.circle(display_page, (x0, y1), 4, (0, 220, 0), -1)  # BL
            cv2.circle(display_page, (x1, y1), 4, (0, 220, 0), -1)  # BR
            
            # Etiqueta de ID de coincidencia
            cv2.putText(display_page, f"#{m['index']}", (x0, y0 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 220), 1)

        # 4. Crear panel lateral con detalles técnicos de QuadPoints
        panel_w = 480
        h = display_page.shape[0]
        panel = np.full((h, panel_w, 3), 28, dtype=np.uint8)
        
        cv2.putText(panel, "F14: DigitalDocSync (QuadPoints)", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 100), 2)
        cv2.putText(panel, f"Termino buscado: '{current_query}'", (15, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 1)
        cv2.putText(panel, f"Coincidencias encontradas: {len(matches)}", (15, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 200), 1)
        
        cv2.line(panel, (15, 100), (panel_w - 15, 100), (80, 80, 80), 1)

        y_offset = 125
        for m in matches[:6]:
            qp = m["quadpoints"]
            cv2.putText(panel, f"Match #{m['index']}: Box [{m['rect'][0]:.1f}, {m['rect'][1]:.1f}, {m['rect'][2]:.1f}, {m['rect'][3]:.1f}]",
                        (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (100, 255, 150), 1)
            y_offset += 18
            cv2.putText(panel, f"  W={m['width']:.1f}pt, H={m['height']:.1f}pt",
                        (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 180, 180), 1)
            y_offset += 18
            cv2.putText(panel, f"  TL:({qp[0]:.1f},{qp[1]:.1f}) TR:({qp[2]:.1f},{qp[3]:.1f})",
                        (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (200, 200, 255), 1)
            y_offset += 16
            cv2.putText(panel, f"  BL:({qp[4]:.1f},{qp[5]:.1f}) BR:({qp[6]:.1f},{qp[7]:.1f})",
                        (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (200, 200, 255), 1)
            y_offset += 24

        # Controles
        cv2.rectangle(panel, (10, h - 140), (panel_w - 10, h - 10), (40, 40, 40), -1)
        cv2.putText(panel, "CONTROLES INTERACTIVOS:", (18, h - 118),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 220, 100), 1)
        cv2.putText(panel, "1-5: Cambiar termino de busqueda", (18, h - 96),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (220, 220, 220), 1)
        cv2.putText(panel, "O  : Abrir PDF en visor del sistema", (18, h - 76),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 200, 255), 1)
        cv2.putText(panel, "S  : Guardar imagen de evidencia", (18, h - 56),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (220, 220, 220), 1)
        cv2.putText(panel, "Q  : Salir", (18, h - 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 180, 180), 1)

        # Unir visor de página y panel
        combined = np.hstack([display_page, panel])
        cv2.imshow("EDDIE – F14 Mapeo QuadPoints en PDF", combined)

        if not pdf_abierto:
            abrir_pdf_sistema(PDF_OUTPUT_PATH)
            pdf_abierto = True

        key = cv2.waitKey(0) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif ord('1') <= key <= ord('5'):
            query_idx = key - ord('1')
            if query_idx < len(PRESET_QUERIES):
                current_query = PRESET_QUERIES[query_idx]
                print(f"  [BUSCAR] Nuevo término: '{current_query}'")
        elif key == ord('o'):
            abrir_pdf_sistema(PDF_OUTPUT_PATH)
        elif key == ord('s'):
            out_img = EVID / "real_f14_quadpoints.png"
            cv2.imwrite(str(out_img), combined)
            print(f"  [GUARDADO] Evidencia: {out_img.name}")

    cv2.destroyAllWindows()
    print("  ✓ F14 COMPLETADO EXITOSAMENTE\n")

if __name__ == "__main__":
    main()
