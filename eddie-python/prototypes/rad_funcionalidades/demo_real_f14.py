"""
================================================================================
PROYECTO EDDIE (Python Migration) - Prototipo RAD F14
================================================================================
Función: Búsqueda y Mapeo de Coordenadas QuadPoints en PDF Real
Equivalente C# Legacy: ModuloConsistenciaDatos / DigitalDocSync.cs
Tecnología: PyMuPDF (fitz) + OpenCV

Características Operativas:
1. Documento PDF Real:
   - Trabaja sobre un documento PDF real del repositorio:
     'Informe Seminario Observaciones resueltas signed rg.pdf' (22 páginas reales).
   - Permite navegar por todas las páginas del PDF (teclas N / P).
2. Búsqueda Interactiva por Teclado:
   - El usuario puede ESCRIBIR cualquier término de búsqueda en tiempo real directamente en la interfaz.
   - Soporta borrado (Backspace), espacios y actualización instantánea.
3. Extracción y Retorno de Coordenadas QuadPoints:
   - Para cada coincidencia en el PDF real, extrae y muestra:
     * Bounding Box: [x0, y0, x1, y1] en puntos tipográficos (pt).
     * QuadPoints: 8 coordenadas exactas [x_tl, y_tl, x_tr, y_tr, x_bl, y_bl, x_br, y_br].
     * Dimensiones: Ancho (W) x Alto (H) y texto exacto de la región.
4. Inyección de Anotaciones Highlight en el PDF Real:
   - Inserta anotaciones de resaltado con QuadPoints nativos en el archivo PDF en disco.
5. Vista Dual en Tiempo Real:
   - Panel Izquierdo: Vista Proyector Simulada (luz de realce proyectada sobre el libro físico).
   - Panel Central: Inspector Digital del PDF con los 4 vértices del QuadPoint (TL, TR, BL, BR).
   - Panel Derecho: Consola de telemetría de coordenadas y caja de entrada de texto interactiva.

Controles:
  ESCRIBIR LETRAS : Escribir cualquier palabra para buscarla en el PDF en tiempo real
  BACKSPACE       : Borrar caracteres del término de búsqueda
  N / P           : Página Siguiente / Página Anterior en el PDF real
  CLIC IZQUIERDO  : Hacer clic sobre cualquier palabra del PDF para seleccionarla
  O               : Abrir el PDF real modificado en el visor del sistema (Adobe Reader/Edge)
  S               : Guardar captura de evidencia PNG
  Q / ESC         : Salir
================================================================================
"""

import os
import sys
import pathlib
import time
import cv2
import numpy as np
import pymupdf as fitz

# Rutas de almacenamiento
BASE_DIR = pathlib.Path(__file__).parent
WORKSPACE_DIR = BASE_DIR.parent.parent.parent
EVID_DIR = BASE_DIR / "evidencias" / "real"
EVID_DIR.mkdir(parents=True, exist_ok=True)

# Buscar el PDF real en el repositorio
REAL_PDF_CANDIDATES = [
    WORKSPACE_DIR / "Informe Seminario Observaciones resueltas signed rg.pdf",
    WORKSPACE_DIR / "taller de investigación (1).pdf",
    WORKSPACE_DIR / "Ibaceta_Jaña_José_Manuel.pdf",
]

PDF_ORIGINAL_PATH = None
for cand in REAL_PDF_CANDIDATES:
    if cand.exists():
        PDF_ORIGINAL_PATH = cand
        break

if PDF_ORIGINAL_PATH is None:
    # Si no se encuentra, usar el primer PDF disponible en el workspace
    pdf_files = list(WORKSPACE_DIR.glob("*.pdf"))
    if pdf_files:
        PDF_ORIGINAL_PATH = pdf_files[0]
    else:
        print("  [ERROR] No se encontró ningún archivo PDF real en el repositorio.")
        sys.exit(1)

PDF_OUTPUT_PATH = EVID_DIR / "f14_real_pdf_quadpoints_synced.pdf"
PDF_BACKUP_PATH = EVID_DIR / "f14_real_pdf_quadpoints_synced.pdf.bac"

def buscar_y_aplicar_quadpoints(pdf_path, search_term, page_num=5, color=(1.0, 0.9, 0.0)):
    """
    Busca el término en la página del PDF real, extrae sus QuadPoints exactos
    y aplica la anotación Highlight en el archivo de salida en disco.
    """
    if not search_term or not search_term.strip():
        return [], 0, 0

    # Crear backup si ya existe salida
    if PDF_OUTPUT_PATH.exists():
        try:
            if PDF_BACKUP_PATH.exists():
                PDF_BACKUP_PATH.unlink()
            PDF_OUTPUT_PATH.rename(PDF_BACKUP_PATH)
        except Exception:
            pass

    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    page_num = max(0, min(total_pages - 1, page_num))
    page = doc[page_num]

    page_w = page.rect.width
    page_h = page.rect.height

    # Búsqueda con extracción de QuadPoints reales (PyMuPDF)
    quads = page.search_for(search_term.strip(), quads=True)
    rects = page.search_for(search_term.strip(), quads=False)

    matches_data = []
    for i, (q, r) in enumerate(zip(quads, rects)):
        # Aplicar anotación de resaltado nativa con QuadPoints
        annot = page.add_highlight_annot(quads=[q])
        annot.set_colors(stroke=color)
        annot.update()

        qp_list = [q.ul.x, q.ul.y, q.ur.x, q.ur.y, q.ll.x, q.ll.y, q.lr.x, q.lr.y]
        extracted_text = page.get_text("text", clip=r).strip()

        match_info = {
            "id": i + 1,
            "term": search_term,
            "page": page_num + 1,
            "rect": (r.x0, r.y0, r.x1, r.y1),
            "width": r.width,
            "height": r.height,
            "quadpoints": qp_list,
            "extracted_text": extracted_text
        }
        matches_data.append(match_info)

    doc.save(str(PDF_OUTPUT_PATH))
    doc.close()
    return matches_data, total_pages, (page_w, page_h)

def renderizar_pagina_real(pdf_path, page_num=5, dpi=120):
    """Renderiza la página del PDF real a imagen OpenCV BGR."""
    doc = fitz.open(str(pdf_path))
    try:
        page_num = max(0, min(len(doc) - 1, page_num))
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.h, pix.w, pix.n))

        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        page_rect = page.rect
        scale = pix.w / page_rect.width
        return img, scale, page_rect.width, page_rect.height
    finally:
        doc.close()

def obtener_palabra_en_coordenada(pdf_path, page_num, click_pt):
    """Detecta qué palabra del PDF real fue cliqueada y retorna su texto y Bounding Box."""
    doc = fitz.open(str(pdf_path))
    page_num = max(0, min(len(doc) - 1, page_num))
    page = doc[page_num]
    words = page.get_text("words")
    doc.close()

    cx, cy = click_pt
    for w in words:
        x0, y0, x1, y1, text = w[:5]
        if x0 <= cx <= x1 and y0 <= cy <= y1:
            clean_word = text.strip(".,;:()\"'[]{}¡!¿?")
            return clean_word, (x0, y0, x1, y1)
    return None, None

def abrir_pdf_visor(path):
    try:
        os.startfile(str(path))
        print(f"  [ABIERTO EN VISOR] {path.name}")
    except Exception as e:
        print(f"  [!] No se pudo abrir visor: {e}")

# Variables de interacción
mouse_click_pt = None
def on_mouse(event, x, y, flags, param):
    global mouse_click_pt
    if event == cv2.EVENT_LBUTTONDOWN:
        mouse_click_pt = (x, y)

def main():
    global mouse_click_pt
    print("=" * 75)
    print("  EDDIE Python – F14: Búsqueda y Mapeo de QuadPoints en PDF Real")
    print(f"  Documento Real: {PDF_ORIGINAL_PATH.name}")
    print("  Módulo Legacy C#: ModuloConsistenciaDatos / DigitalDocSync.cs")
    print("=" * 75)

    current_page = 5  # Página 6 (índice 5: Sección de plugins y arquitectura de EDDIE)
    search_input = "EDDIE"  # Término inicial por defecto

    cv2.namedWindow("EDDIE – F14 QuadPoints & Projector View", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("EDDIE – F14 QuadPoints & Projector View", 1420, 800)
    cv2.setMouseCallback("EDDIE – F14 QuadPoints & Projector View", on_mouse)

    matches, total_pages, (pdf_w, pdf_h) = buscar_y_aplicar_quadpoints(PDF_ORIGINAL_PATH, search_input, current_page)
    abrir_pdf_visor(PDF_OUTPUT_PATH)

    last_search = search_input
    last_page = current_page

    print(f"\n  [INICIO] Página {current_page + 1}/{total_pages} | Búsqueda: '{search_input}' -> {len(matches)} coincidencias")
    for m in matches:
        qp = m["quadpoints"]
        print(f"    * Match #{m['id']}: Box=[{m['rect'][0]:.1f}, {m['rect'][1]:.1f}, {m['rect'][2]:.1f}, {m['rect'][3]:.1f}] pt")
        print(f"      QuadPoints: TL=({qp[0]:.1f},{qp[1]:.1f}) TR=({qp[2]:.1f},{qp[3]:.1f}) BL=({qp[4]:.1f},{qp[5]:.1f}) BR=({qp[6]:.1f},{qp[7]:.1f})")

    while True:
        # Reejecutar búsqueda si cambió el término o la página
        if search_input != last_search or current_page != last_page:
            target_pdf = PDF_ORIGINAL_PATH
            matches, total_pages, (pdf_w, pdf_h) = buscar_y_aplicar_quadpoints(target_pdf, search_input, current_page)
            last_search = search_input
            last_page = current_page

        # 1. Renderizar imagen del PDF real con anotaciones
        active_render_pdf = PDF_OUTPUT_PATH if PDF_OUTPUT_PATH.exists() else PDF_ORIGINAL_PATH
        page_img, scale, orig_w, orig_h = renderizar_pagina_real(active_render_pdf, current_page, dpi=115)
        h, w = page_img.shape[:2]

        # 2. VISTA PROYECTOR SIMULADA (Projector View)
        # Proyecta luz de realce difusa sobre el texto físico
        projector_view = page_img.copy()
        light_layer = np.zeros_like(projector_view)

        for m in matches:
            rx0, ry0, rx1, ry1 = m["rect"]
            px0, py0 = int(rx0 * scale), int(ry0 * scale)
            px1, py1 = int(rx1 * scale), int(ry1 * scale)
            # Haz de luz de proyector
            cv2.rectangle(light_layer, (px0 - 3, py0 - 2), (px1 + 3, py1 + 2), (0, 240, 255), -1)

        light_layer = cv2.GaussianBlur(light_layer, (9, 9), 0)
        projector_view = cv2.addWeighted(projector_view, 0.85, light_layer, 0.45, 0)

        cv2.rectangle(projector_view, (0, 0), (w - 1, h - 1), (0, 180, 255), 2)
        cv2.putText(projector_view, "[VISTA PROYECTOR SIMULADA]", (15, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 140, 220), 2)
        cv2.putText(projector_view, f"Luz proyectada sobre libro | Pagina {current_page + 1}/{total_pages}", (15, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (80, 80, 80), 1)

        # 3. VISTA INSPECTOR DIGITAL (PDF Real con QuadPoints)
        inspector_view = page_img.copy()
        for m in matches:
            rx0, ry0, rx1, ry1 = m["rect"]
            px0, py0 = int(rx0 * scale), int(ry0 * scale)
            px1, py1 = int(rx1 * scale), int(ry1 * scale)

            # Bounding Box
            cv2.rectangle(inspector_view, (px0, py0), (px1, py1), (0, 0, 255), 2)

            # 4 Vértices del QuadPoint marcados
            cv2.circle(inspector_view, (px0, py0), 4, (0, 220, 0), -1)  # Top-Left
            cv2.circle(inspector_view, (px1, py0), 4, (0, 220, 0), -1)  # Top-Right
            cv2.circle(inspector_view, (px0, py1), 4, (0, 220, 0), -1)  # Bottom-Left
            cv2.circle(inspector_view, (px1, py1), 4, (0, 220, 0), -1)  # Bottom-Right

            cv2.putText(inspector_view, f"#{m['id']}", (px0, py0 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.36, (0, 0, 220), 1)

        cv2.rectangle(inspector_view, (0, 0), (w - 1, h - 1), (0, 220, 100), 2)
        cv2.putText(inspector_view, "[INSPECTOR DIGITAL DEL PDF REAL]", (15, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 180, 80), 2)
        cv2.putText(inspector_view, "Bounding Boxes [x0,y0,x1,y1] y QuadPoints (pt)", (15, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (80, 80, 80), 1)

        # 4. Procesar clic de ratón (Selección de palabra en el documento real)
        if mouse_click_pt is not None:
            mx, my = mouse_click_pt
            click_pdf_x, click_pdf_y = None, None
            if mx < w:  # Clic en panel proyector
                click_pdf_x = mx / scale
                click_pdf_y = my / scale
            elif w <= mx < 2 * w:  # Clic en panel inspector
                click_pdf_x = (mx - w) / scale
                click_pdf_y = my / scale

            if click_pdf_x is not None:
                clicked_word, _ = obtener_palabra_en_coordenada(PDF_ORIGINAL_PATH, current_page, (click_pdf_x, click_pdf_y))
                if clicked_word:
                    search_input = clicked_word
                    print(f"  [CLIC EN PDF] Palabra seleccionada: '{search_input}'")
            mouse_click_pt = None

        # 5. PANEL DE TELEMETRÍA Y ENTRADA DE TEXTO
        panel_w = 460
        panel = np.full((h, panel_w, 3), 24, dtype=np.uint8)

        cv2.putText(panel, "F14: DigitalDocSync (PDF Real)", (15, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 220, 100), 2)
        cv2.putText(panel, f"Doc: {PDF_ORIGINAL_PATH.name[:38]}...", (15, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, (180, 180, 180), 1)
        cv2.putText(panel, f"Pagina: {current_page + 1} de {total_pages} (N=Siguiente, P=Anterior)", (15, 68),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 200, 255), 1)

        cv2.line(panel, (15, 78), (panel_w - 15, 78), (60, 60, 60), 1)

        # Campo de entrada de texto interactivo
        cv2.putText(panel, "ESCRIBE LA PALABRA A BUSCAR:", (15, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 200, 0), 1)

        # Caja de texto activa
        cv2.rectangle(panel, (15, 110), (panel_w - 15, 145), (40, 45, 55), -1)
        cv2.rectangle(panel, (15, 110), (panel_w - 15, 145), (0, 220, 255), 1)

        # Cursor parpadeante
        cursor = "_" if int(time.time() * 2) % 2 == 0 else ""
        cv2.putText(panel, f"> {search_input}{cursor}", (22, 134),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2)

        cv2.putText(panel, f"Coincidencias encontradas: {len(matches)}", (15, 165),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (200, 255, 200), 1)

        # Lista de QuadPoints retornados
        y_det = 190
        for m in matches[:5]:
            qp = m["quadpoints"]
            cv2.putText(panel, f"Match #{m['id']}: Box [{m['rect'][0]:.1f}, {m['rect'][1]:.1f}, {m['rect'][2]:.1f}, {m['rect'][3]:.1f}] pt",
                        (15, y_det), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 255, 150), 1)
            y_det += 18
            cv2.putText(panel, f"  W={m['width']:.1f}pt, H={m['height']:.1f}pt | Texto: '{m['extracted_text'][:24]}'",
                        (15, y_det), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (180, 180, 180), 1)
            y_det += 18
            cv2.putText(panel, f"  TL:({qp[0]:.1f},{qp[1]:.1f})  TR:({qp[2]:.1f},{qp[3]:.1f})",
                        (15, y_det), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (200, 200, 255), 1)
            y_det += 16
            cv2.putText(panel, f"  BL:({qp[4]:.1f},{qp[5]:.1f})  BR:({qp[6]:.1f},{qp[7]:.1f})",
                        (15, y_det), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (200, 200, 255), 1)
            y_det += 24

        # Estado del archivo
        cv2.rectangle(panel, (10, h - 200), (panel_w - 10, h - 115), (35, 35, 35), -1)
        cv2.putText(panel, "ARCHIVO PDF SINCRONIZADO:", (18, h - 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 100), 1)
        cv2.putText(panel, f"Salida: {PDF_OUTPUT_PATH.name}", (18, h - 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.34, (100, 255, 100), 1)
        cv2.putText(panel, f"Backup: {PDF_BACKUP_PATH.name if PDF_BACKUP_PATH.exists() else 'N/A'}", (18, h - 142),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (140, 140, 140), 1)
        cv2.putText(panel, f"Dimensiones: {orig_w:.0f} x {orig_h:.0f} pt", (18, h - 124),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (180, 180, 180), 1)

        # Controles
        cv2.rectangle(panel, (10, h - 105), (panel_w - 10, h - 10), (45, 45, 45), -1)
        cv2.putText(panel, "CONTROLES:", (18, h - 85), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 100), 1)
        cv2.putText(panel, "ESCRIBIR: Buscar cualquier palabra directamente", (18, h - 68), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (220, 220, 220), 1)
        cv2.putText(panel, "N / P   : Cambiar de pagina en el PDF real", (18, h - 52), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (0, 220, 255), 1)
        cv2.putText(panel, "CLIC    : Seleccionar palabra en el documento", (18, h - 36), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (200, 200, 200), 1)
        cv2.putText(panel, "O: Abrir PDF | S: Guardar | Q/ESC: Salir", (18, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (150, 150, 150), 1)

        # 6. Unir y mostrar todo
        combined_view = np.hstack([projector_view, inspector_view, panel])
        cv2.imshow("EDDIE – F14 QuadPoints & Projector View", combined_view)

        key = cv2.waitKey(40) & 0xFF

        if key == ord('q') or key == 27:
            break
        elif key == ord('o'):
            abrir_pdf_visor(PDF_OUTPUT_PATH)
        elif key == ord('s'):
            out_path = EVID_DIR / "real_f14_quadpoints_sync.png"
            cv2.imwrite(str(out_path), combined_view)
            print(f"  [GUARDADO] Evidencia: {out_path.name}")
        elif key == ord('n') or key == ord('N'):
            if current_page < total_pages - 1:
                current_page += 1
                print(f"  [PAGINA] Siguiente -> {current_page + 1}")
        elif key == ord('p') or key == ord('P'):
            if current_page > 0:
                current_page -= 1
                print(f"  [PAGINA] Anterior -> {current_page + 1}")
        elif key == 8:  # Backspace
            if len(search_input) > 0:
                search_input = search_input[:-1]
        elif 32 <= key <= 126:  # Caracteres ASCII imprimibles
            char = chr(key)
            search_input += char

    cv2.destroyAllWindows()
    print("  ✓ F14 Finalizado exitosamente.\n")

if __name__ == "__main__":
    main()