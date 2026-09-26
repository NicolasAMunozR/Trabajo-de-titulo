"""
================================================================================
PROYECTO EDDIE (Python Migration) - Prototipo RAD F15
================================================================================
Función: Sincronización de Resaltados (Subrayado en Papel Físico -> PDF Digital)
Equivalente C# Legacy: ModuloVisualizacionDatos / HighlightTool.cs & PageMarkerPD.cs
Tecnología: OpenCV + PyMuPDF (fitz)

Características Operativas:
1. Documento PDF Real:
   - Trabaja sobre el PDF real 'Informe Seminario Observaciones resueltas signed rg.pdf'.
   - Permite navegar entre páginas (N / P).
2. Detección de Subrayado / Resaltado Físico por Cámara (Físico -> Digital):
   - Transmisión en vivo desde DroidCam / Webcam enfocando el papel.
   - Cuando el usuario SUBRAYA O RESALTA en el papel físico (con resaltador fluorescente
     amarillo, verde, naranja o lápiz de color), la cámara detecta el trazo en HSV.
   - Mapea la posición vertical y horizontal del trazo físico hacia la línea de texto
     correspondiente en el PDF digital real.
   - INYECTA AUTOMÁTICAMENTE la anotación Highlight en el archivo PDF digital en disco.
3. Vista Proyector Simulada (Digital -> Físico):
   - Muestra cómo el proyector proyecta la banda de luz de realce sobre el libro físico.
   - El ratón también permite simular el movimiento ocular de lectura (Gaze tracking).
4. Persistencia en Disco y Visor:
   - Guarda el archivo PDF real modificado con backup (.bac) y lo abre en Adobe Reader/Edge.

Controles:
  SUBRAYAR EN PAPEL : Subrayar con resaltador/lápiz frente a la cámara (se refleja en el PDF)
  C                 : Forzar captura manual de trazo detectado por la cámara
  CLIC IZQUIERDO    : Resaltar línea directamente desde la Vista Proyector
  N / P             : Página Siguiente / Anterior en el PDF real
  R                 : Reiniciar anotaciones de la página actual
  O                 : Abrir el PDF real sincronizado en el visor del sistema
  S                 : Guardar captura de evidencia PNG
  Q / ESC           : Salir
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
    pdf_files = list(WORKSPACE_DIR.glob("*.pdf"))
    PDF_ORIGINAL_PATH = pdf_files[0] if pdf_files else None

PDF_OUTPUT_PATH = EVID_DIR / "f15_real_pdf_highlight_synced.pdf"
PDF_BACKUP_PATH = EVID_DIR / "f15_real_pdf_highlight_synced.pdf.bac"

# Rangos HSV para resaltadores fluorescentes (Amarillo, Verde, Naranja)
HIGHLIGHTER_HSV = {
    "AMARILLO": (np.array([20, 75, 75]), np.array([38, 255, 255])),
    "VERDE":    (np.array([39, 60, 60]), np.array([85, 255, 255])),
    "NARANJA":  (np.array([5, 80, 80]),  np.array([19, 255, 255])),
}

# Registro de resaltados aplicados en el PDF [(page_idx, rect_tuple, texto_linea, origen)]
HIGHLIGHTS_APLICADOS = []

def inicializar_pdf_salida():
    """Copia el PDF base al archivo de salida."""
    doc = fitz.open(str(PDF_ORIGINAL_PATH))
    doc.save(str(PDF_OUTPUT_PATH))
    doc.close()

def aplicar_highlight_en_linea_pdf(page_num, rect_pdf, texto=""):
    """Inserta una anotación Highlight real en la página indicada del PDF."""
    if PDF_OUTPUT_PATH.exists():
        try:
            if PDF_BACKUP_PATH.exists():
                PDF_BACKUP_PATH.unlink()
            PDF_OUTPUT_PATH.rename(PDF_BACKUP_PATH)
        except Exception:
            pass

    doc = fitz.open(str(PDF_BACKUP_PATH if PDF_BACKUP_PATH.exists() else PDF_ORIGINAL_PATH))
    page = doc[page_num]

    r = fitz.Rect(rect_pdf)
    annot = page.add_highlight_annot(r)
    annot.set_colors(stroke=(1.0, 0.9, 0.1))
    annot.update()

    doc.save(str(PDF_OUTPUT_PATH))
    doc.close()

def obtener_lineas_pagina_pdf(pdf_path, page_num):
    """Extrae todas las líneas de texto de la página del PDF real con sus rectángulos exactos."""
    doc = fitz.open(str(pdf_path))
    page_num = max(0, min(len(doc) - 1, page_num))
    page = doc[page_num]
    
    # Extraer bloques de texto con líneas
    blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)
    lines_data = []
    
    for b in blocks:
        if len(b) >= 5 and b[4].strip():
            # Dividir en líneas aproximadas
            b_x0, b_y0, b_x1, b_y1, b_text = b[:5]
            raw_lines = [l.strip() for l in b_text.split("\n") if l.strip()]
            if raw_lines:
                line_h = (b_y1 - b_y0) / len(raw_lines)
                for idx, line_str in enumerate(raw_lines):
                    ly0 = b_y0 + idx * line_h
                    ly1 = ly0 + line_h
                    lines_data.append({
                        "rect": (b_x0, ly0, b_x1, ly1),
                        "text": line_str,
                        "y_center": (ly0 + ly1) / 2.0
                    })
    doc.close()
    return lines_data

def renderizar_pagina_real(pdf_path, page_num=5, dpi=115):
    doc = fitz.open(str(pdf_path))
    try:
        page_num = max(0, min(len(doc) - 1, page_num))
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.h, pix.w, pix.n))
        total_pages = len(doc)

        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        page_rect = page.rect
        scale = pix.w / page_rect.width
        return img, scale, total_pages, page_rect.width, page_rect.height
    finally:
        doc.close()

def abrir_pdf_visor(path):
    try:
        os.startfile(str(path))
        print(f"  [ABIERTO EN VISOR] {path.name}")
    except Exception as e:
        print(f"  [!] No se pudo abrir visor: {e}")

# Variables de interacción
mouse_y_pos = 200
mouse_clicked = False
def on_mouse(event, x, y, flags, param):
    global mouse_y_pos, mouse_clicked
    if event == cv2.EVENT_MOUSEMOVE:
        mouse_y_pos = y
    elif event == cv2.EVENT_LBUTTONDOWN:
        mouse_clicked = True

def main():
    global mouse_y_pos, mouse_clicked
    print("=" * 75)
    print("  EDDIE Python – F15: Sincronización de Resaltados (Papel Físico -> PDF Real)")
    print(f"  Documento Real: {PDF_ORIGINAL_PATH.name}")
    print("  Módulo Legacy C#: ModuloVisualizacionDatos / HighlightTool.cs")
    print("=" * 75)

    inicializar_pdf_salida()
    current_page = 5  # Página 6 (Arquitectura y plugins de EDDIE)

    # Intentar abrir cámara DroidCam con MSMF o cámara estándar
    cap = None
    for idx in range(3):
        for backend in [cv2.CAP_MSMF, cv2.CAP_ANY]:
            try:
                c = cv2.VideoCapture(idx, backend)
                if c.isOpened():
                    cap = c
                    print(f"  [+] Cámara detectada en índice {idx} (MSMF/ANY) para escaneo físico")
                    break
                c.release()
            except Exception:
                pass
        if cap: break

    cv2.namedWindow("EDDIE – F15 Highlight Sync (Fisico -> Digital)", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("EDDIE – F15 Highlight Sync (Fisico -> Digital)", 1420, 800)
    cv2.setMouseCallback("EDDIE – F15 Highlight Sync (Fisico -> Digital)", on_mouse)

    abrir_pdf_visor(PDF_OUTPUT_PATH)

    last_detected_line = None
    auto_highlight_cooldown = 0

    while True:
        # Extraer líneas de texto de la página del PDF real
        lineas_pdf = obtener_lineas_pagina_pdf(PDF_ORIGINAL_PATH, current_page)

        # 1. Renderizar imagen del PDF real sincronizado
        active_render_pdf = PDF_OUTPUT_PATH if PDF_OUTPUT_PATH.exists() else PDF_ORIGINAL_PATH
        page_img, scale, total_pages, orig_w, orig_h = renderizar_pagina_real(active_render_pdf, current_page, dpi=115)
        h, w = page_img.shape[:2]

        # 2. VISTA PROYECTOR SIMULADA (Projector View)
        # Muestra la luz proyectada sobre el libro físico
        projector_view = page_img.copy()

        # Encontrar línea activa más cercana al cursor del ratón (Gaze simulator)
        closest_line = None
        min_dist = float("inf")
        for line in lineas_pdf:
            rx0, ry0, rx1, ry1 = line["rect"]
            line_py_center = ((ry0 + ry1) / 2.0) * scale
            dist = abs(line_py_center - mouse_y_pos)
            if dist < min_dist:
                min_dist = dist
                closest_line = line

        if closest_line is not None:
            rx0, ry0, rx1, ry1 = closest_line["rect"]
            px0, py0 = int(rx0 * scale), int(ry0 * scale)
            px1, py1 = int(rx1 * scale), int(ry1 * scale)

            # Luz del proyector interactiva
            light_overlay = np.zeros_like(projector_view)
            cv2.rectangle(light_overlay, (px0 - 3, py0 - 1), (px1 + 3, py1 + 1), (0, 240, 255), -1)
            light_overlay = cv2.GaussianBlur(light_overlay, (13, 13), 0)
            projector_view = cv2.addWeighted(projector_view, 0.85, light_overlay, 0.45, 0)
            
            # Guía de borde
            cv2.rectangle(projector_view, (px0 - 2, py0), (px1 + 2, py1), (0, 180, 255), 2)
            cv2.putText(projector_view, "Luz de Realce Proyectada (Gaze)", (px0, py0 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 140, 220), 1)

        cv2.rectangle(projector_view, (0, 0), (w - 1, h - 1), (0, 180, 255), 2)
        cv2.putText(projector_view, "[VISTA PROYECTOR SIMULADA]", (15, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 140, 220), 2)
        cv2.putText(projector_view, f"Haz de luz sobre el papel fisico | Pagina {current_page + 1}/{total_pages}", (15, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (80, 80, 80), 1)

        # Clic para fijar highlight en el PDF real desde el proyector
        if mouse_clicked and closest_line is not None:
            r_pdf = closest_line["rect"]
            txt = closest_line["text"]
            aplicar_highlight_en_linea_pdf(current_page, r_pdf, txt)
            HIGHLIGHTS_APLICADOS.append((current_page, r_pdf, txt, "PROYECTOR_GAZE"))
            print(f"  [✓ HIGHLIGHT FIJADO] Línea: \"{txt[:35]}...\" -> Sincronizada en PDF")
            mouse_clicked = False

        # 3. VISTA DE CÁMARA (Detección de Resaltado Físico sobre el Papel)
        last_detected_line = None
        if cap is not None:
            ret, frame = cap.read()
            if not ret:
                camera_view = np.full((h, w, 3), 40, dtype=np.uint8)
                cv2.putText(camera_view, "Camara no disponible", (50, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                cam_resized = cv2.resize(frame, (w, h))
                hsv = cv2.cvtColor(cam_resized, cv2.COLOR_BGR2HSV)

                # Combinar máscaras de amarillo y verde fluorescente
                mask_y = cv2.inRange(hsv, HIGHLIGHTER_HSV["AMARILLO"][0], HIGHLIGHTER_HSV["AMARILLO"][1])
                mask_g = cv2.inRange(hsv, HIGHLIGHTER_HSV["VERDE"][0], HIGHLIGHTER_HSV["VERDE"][1])
                mask = cv2.bitwise_or(mask_y, mask_g)

                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

                cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                camera_view = cam_resized.copy()

                for cnt in cnts:
                    if cv2.contourArea(cnt) > 900:  # Área representativa de trazo de resaltador
                        x_c, y_c, w_c, h_c = cv2.boundingRect(cnt)
                        cv2.rectangle(camera_view, (x_c, y_c), (x_c + w_c, y_c + h_c), (0, 255, 0), 2)
                        cv2.putText(camera_view, "SUBRAYADO EN PAPEL DETECTADO", (x_c, y_c - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 2)

                        # Mapear posición Y de cámara hacia la línea del PDF real
                        cam_y_normalized = (y_c + h_c / 2.0) / h
                        pdf_y_target = cam_y_normalized * orig_h

                        # Encontrar qué línea del PDF coincide
                        for line in lineas_pdf:
                            ly0, ly1 = line["rect"][1], line["rect"][3]
                            if ly0 - 15 <= pdf_y_target <= ly1 + 15:
                                last_detected_line = line
                                break
                        break

                cv2.rectangle(camera_view, (0, 0), (w - 1, h - 1), (0, 220, 100), 2)
                cv2.putText(camera_view, "[FEED CAMARA CENITAL (DROIDCAM)]", (15, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 220, 100), 2)
                cv2.putText(camera_view, "Subraya en el papel para sincronizar hacia el PDF", (15, 45),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1)
        else:
            camera_view = np.full((h, w, 3), 30, dtype=np.uint8)
            cv2.putText(camera_view, "MODO EMULACION DE CAMARA", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 180, 255), 2)
            cv2.putText(camera_view, "Conecta DroidCam para deteccion de subrayado fisico", (15, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)

        # 4. PANEL DE TELEMETRÍA Y ESTADO
        panel_w = 460
        panel = np.full((h, panel_w, 3), 24, dtype=np.uint8)

        cv2.putText(panel, "F15: HighlightTool (PDF Real)", (15, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 220, 100), 2)
        cv2.putText(panel, f"Doc: {PDF_ORIGINAL_PATH.name[:38]}...", (15, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, (180, 180, 180), 1)
        cv2.putText(panel, f"Pagina: {current_page + 1} de {total_pages} (N=Siguiente, P=Anterior)", (15, 68),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 200, 255), 1)
        cv2.line(panel, (15, 78), (panel_w - 15, 78), (60, 60, 60), 1)

        cv2.putText(panel, f"Total Highlights aplicados: {len(HIGHLIGHTS_APLICADOS)}", (15, 98),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (220, 220, 220), 1)

        # Estado de detección física por cámara
        if last_detected_line is not None:
            cv2.rectangle(panel, (15, 110), (panel_w - 15, 175), (30, 60, 40), -1)
            cv2.rectangle(panel, (15, 110), (panel_w - 15, 175), (0, 255, 100), 1)
            cv2.putText(panel, "TRAZO DETECTADO EN PAPEL:", (22, 128),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 200), 1)
            cv2.putText(panel, f"\"{last_detected_line['text'][:38]}...\"", (22, 148),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.36, (255, 255, 255), 1)
            cv2.putText(panel, "Presiona 'C' para sincronizar al PDF", (22, 166),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.34, (100, 255, 100), 1)
        else:
            cv2.rectangle(panel, (15, 110), (panel_w - 15, 175), (35, 35, 35), -1)
            cv2.putText(panel, "Buscando trazo de resaltador en papel...", (22, 145),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.36, (180, 180, 180), 1)

        # Registro de highlights sincronizados
        cv2.putText(panel, "REGISTRO DE RESALTADOS SINCRONIZADOS:", (15, 195),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 200, 0), 1)
        
        y_list = 215
        for i, (pg, r_box, desc, orig) in enumerate(HIGHLIGHTS_APLICADOS[-5:], 1):
            cv2.putText(panel, f"{i}. [Pag {pg + 1}] [{orig}]", (15, y_list),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 220, 255), 1)
            y_list += 18
            cv2.putText(panel, f"   \"{desc[:38]}...\"", (15, y_list),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.34, (180, 255, 180), 1)
            y_list += 24

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
        cv2.putText(panel, "C       : Sincronizar trazo fisico de camara a PDF", (18, h - 68), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (0, 220, 255), 1)
        cv2.putText(panel, "CLIC    : Fijar Highlight actual desde proyector", (18, h - 52), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (220, 220, 220), 1)
        cv2.putText(panel, "N / P   : Cambiar de pagina en el PDF real", (18, h - 36), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (180, 180, 180), 1)
        cv2.putText(panel, "O: Abrir PDF | R: Reiniciar | Q/ESC: Salir", (18, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (150, 150, 150), 1)

        # 5. Unir y mostrar todo
        combined_view = np.hstack([camera_view, projector_view, panel])
        cv2.imshow("EDDIE – F15 Highlight Sync (Fisico -> Digital)", combined_view)

        key = cv2.waitKey(30) & 0xFF

        if key == ord('q') or key == 27:
            break
        elif key == ord('c') and last_detected_line is not None:
            r_pdf = last_detected_line["rect"]
            txt = last_detected_line["text"]
            aplicar_highlight_en_linea_pdf(current_page, r_pdf, txt)
            HIGHLIGHTS_APLICADOS.append((current_page, r_pdf, txt, "CAMARA_FISICA"))
            print(f"  [✓ TRAZO FÍSICO SINCRONIZADO] Línea: \"{txt[:35]}...\" -> Añadida a {PDF_OUTPUT_PATH.name}")
        elif key == ord('n') or key == ord('N'):
            if current_page < total_pages - 1:
                current_page += 1
                print(f"  [PAGINA] Siguiente -> {current_page + 1}")
        elif key == ord('p') or key == ord('P'):
            if current_page > 0:
                current_page -= 1
                print(f"  [PAGINA] Anterior -> {current_page + 1}")
        elif key == ord('r'):
            inicializar_pdf_salida()
            HIGHLIGHTS_APLICADOS.clear()
            print("  [REINICIADO] Documento PDF restablecido al estado original.")
        elif key == ord('o'):
            abrir_pdf_visor(PDF_OUTPUT_PATH)
        elif key == ord('s'):
            out_path = EVID_DIR / "real_f15_highlight_sync.png"
            cv2.imwrite(str(out_path), combined_view)
            print(f"  [GUARDADO] Evidencia: {out_path.name}")

    if cap: cap.release()
    cv2.destroyAllWindows()
    print("  ✓ F15 Finalizado exitosamente.\n")

if __name__ == "__main__":
    main()
