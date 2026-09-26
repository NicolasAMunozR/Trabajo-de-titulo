"""
================================================================================
PROYECTO EDDIE (Python Migration) - Prototipo RAD F16
================================================================================
Función: Sincronización Bidireccional de Notas Adhesivas (Post-It / Comentarios)
Equivalente C# Legacy: ConsistencyLibraryCommentsPD / CommentsPD.cs & CommentsDP.cs
Tecnología: OpenCV + Tesseract OCR + PyMuPDF (fitz)

Características Operativas:
1. Documento PDF Real:
   - Trabaja sobre el PDF real 'Informe Seminario Observaciones resueltas signed rg.pdf'.
   - Permite navegar entre páginas con N / P.
2. Sincronización Física -> Digital (Notas en papel a PDF digital):
   - Transmisión en vivo desde DroidCam / Webcam enfocando el área de trabajo.
   - Detecta notas escritas en papel físico o Post-Its amarillos mediante segmentación HSV y contornos.
   - Recorta la nota física y aplica Tesseract OCR para extraer el texto manuscrito/impreso.
   - Inyecta automáticamente la nota en el PDF digital real en disco como anotación tipo 'Text/Note' y estampa visual.
3. Sincronización Digital -> Física (PDF digital a Proyección sobre papel):
   - Cuando el usuario hace clic en el documento digital o agrega una nota digital, esta se
     PROYECTA INMEDIATAMENTE SOBRE EL PAPEL FÍSICO en la Vista Proyector Simulada.
4. Persistencia en Disco y Visor:
   - Mantiene el archivo PDF real sincronizado con copias de seguridad (.bac) y permite abrirlo en Adobe Reader/Edge.

Controles:
  MOSTRAR NOTA EN CÁMARA : Colocar nota/papel frente a la cámara para detección
  C                      : Capturar nota física detectada, aplicar OCR e inyectar al PDF real
  CLIC IZQUIERDO         : (En el PDF digital) Crear nota digital y proyectarla sobre el papel
  N / P                  : Página Siguiente / Anterior en el PDF real
  R                      : Reiniciar notas de la sesión
  O                      : Abrir el PDF real sincronizado en el visor del sistema
  S                      : Guardar captura de evidencia PNG
  Q / ESC                : Salir
================================================================================
"""

import os
import sys
import pathlib
import time
import cv2
import numpy as np
import pymupdf as fitz
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

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

PDF_OUTPUT_PATH = EVID_DIR / "f16_real_pdf_postit_synced.pdf"
PDF_BACKUP_PATH = EVID_DIR / "f16_real_pdf_postit_synced.pdf.bac"

# Registro de notas de sesión [(page_idx, x_pdf, y_pdf, texto, color_rgb, origen)]
NOTAS_SESION = [
    (5, 360, 120, "Revisar arquitectura de plugins de EDDIE", (1.0, 0.9, 0.2), "DIGITAL"),
    (5, 360, 310, "Verificar contratos de interfaz IImageProcessor", (1.0, 0.8, 0.3), "DIGITAL"),
]

def inicializar_pdf_salida():
    """Copia el PDF base al archivo de salida."""
    doc = fitz.open(str(PDF_ORIGINAL_PATH))
    doc.save(str(PDF_OUTPUT_PATH))
    doc.close()

def sincronizar_todas_las_notas_al_pdf():
    """Inserta todas las notas acumuladas en la sesión directamente en el PDF real en disco."""
    if PDF_OUTPUT_PATH.exists():
        try:
            if PDF_BACKUP_PATH.exists():
                PDF_BACKUP_PATH.unlink()
            PDF_OUTPUT_PATH.rename(PDF_BACKUP_PATH)
        except Exception:
            pass

    doc = fitz.open(str(PDF_BACKUP_PATH if PDF_BACKUP_PATH.exists() else PDF_ORIGINAL_PATH))

    for pg_idx, x, y, texto, col, origen in NOTAS_SESION:
        if pg_idx < len(doc):
            page = doc[pg_idx]
            
            # 1. Anotación estándar tipo 'Text / Sticky Note'
            annot = page.add_text_annot((x, y), f"[{origen}] {texto}")
            annot.set_colors(stroke=col)
            annot.update()

            # 2. Estampa gráfica de Post-It en el PDF
            postit_rect = fitz.Rect(x - 5, y - 5, x + 175, y + 55)
            page.draw_rect(postit_rect, color=(0.8, 0.7, 0.1), fill=(1.0, 0.96, 0.6), width=0.8)
            # Cabecera coloreada
            page.draw_rect(fitz.Rect(postit_rect.x0, postit_rect.y0, postit_rect.x1, postit_rect.y0 + 13), 
                           color=(0.85, 0.75, 0.15), fill=(0.95, 0.85, 0.2), width=0.5)
            # Texto dentro del post-it
            page.insert_text((postit_rect.x0 + 5, postit_rect.y0 + 26), texto[:28] + ("..." if len(texto) > 28 else ""), 
                             fontsize=7.5, color=(0.15, 0.15, 0.15))
            page.insert_text((postit_rect.x0 + 5, postit_rect.y0 + 42), f"Origen: {origen}", 
                             fontsize=6.5, color=(0.4, 0.4, 0.4))

    doc.save(str(PDF_OUTPUT_PATH))
    doc.close()

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
mouse_click_coord = None
def on_mouse(event, x, y, flags, param):
    global mouse_click_coord
    if event == cv2.EVENT_LBUTTONDOWN:
        mouse_click_coord = (x, y)

def main():
    global mouse_click_coord
    print("=" * 75)
    print("  EDDIE Python – F16: Sincronización Bidireccional de Post-Its (Físico <-> Digital)")
    print(f"  Documento Real: {PDF_ORIGINAL_PATH.name}")
    print("  Módulo Legacy C#: ConsistencyLibraryCommentsPD / CommentsPD.cs & CommentsDP.cs")
    print("=" * 75)

    inicializar_pdf_salida()
    current_page = 5  # Página 6 (índice 5)
    sincronizar_todas_las_notas_al_pdf()

    # Intentar abrir cámara (DroidCam con MSMF o cámara estándar)
    cap = None
    for idx in range(3):
        for backend in [cv2.CAP_MSMF, cv2.CAP_ANY]:
            try:
                c = cv2.VideoCapture(idx, backend)
                if c.isOpened():
                    cap = c
                    print(f"  [+] Cámara detectada en índice {idx} (MSMF/ANY) para escaneo de notas físicas")
                    break
                c.release()
            except Exception:
                pass
        if cap: break

    cv2.namedWindow("EDDIE – F16 Sincronizacion de Post-Its (Bidireccional)", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("EDDIE – F16 Sincronizacion de Post-Its (Bidireccional)", 1420, 800)
    cv2.setMouseCallback("EDDIE – F16 Sincronizacion de Post-Its (Bidireccional)", on_mouse)

    abrir_pdf_visor(PDF_OUTPUT_PATH)

    last_detected_box = None
    last_detected_crop = None

    while True:
        # 1. Renderizar imagen del PDF real sincronizado
        active_render_pdf = PDF_OUTPUT_PATH if PDF_OUTPUT_PATH.exists() else PDF_ORIGINAL_PATH
        page_img, scale, total_pages, orig_w, orig_h = renderizar_pagina_real(active_render_pdf, current_page, dpi=115)
        h, w = page_img.shape[:2]

        # 2. VISTA PROYECTOR SIMULADA (Digital -> Proyección sobre Papel Físico)
        # Muestra las notas digitales PROYECTADAS sobre la superficie del libro físico
        projector_view = page_img.copy()

        # Filtrar notas de la página actual
        notas_pagina = [n for n in NOTAS_SESION if n[0] == current_page]

        for _, nx, ny, txt, col, orig in notas_pagina:
            px = int(nx * scale)
            py = int(ny * scale)
            pw = int(175 * scale)
            ph = int(55 * scale)

            # Sombra proyectada
            cv2.rectangle(projector_view, (px + 4, py + 4), (px + pw + 4, py + ph + 4), (40, 40, 40), -1)
            # Cuerpo luminoso del Post-It proyectado
            cv2.rectangle(projector_view, (px, py), (px + pw, py + ph), (0, 240, 255), -1)
            cv2.rectangle(projector_view, (px, py), (px + pw, py + ph), (0, 180, 200), 2)
            # Cabecera
            cv2.rectangle(projector_view, (px, py), (px + pw, py + int(13 * scale)), (0, 200, 220), -1)
            cv2.putText(projector_view, f"NOTA PROYECTADA [{orig[:3]}]", (px + 5, py + int(10 * scale)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (30, 30, 30), 1)
            cv2.putText(projector_view, txt[:22] + ("..." if len(txt) > 22 else ""), (px + 5, py + int(30 * scale)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (10, 10, 10), 1)

        cv2.rectangle(projector_view, (0, 0), (w - 1, h - 1), (0, 180, 255), 2)
        cv2.putText(projector_view, "[VISTA PROYECTOR (SOBRE PAPEL)]", (15, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 140, 220), 2)
        cv2.putText(projector_view, f"Notas digitales proyectadas sobre el libro | Pagina {current_page + 1}/{total_pages}", (15, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (80, 80, 80), 1)

        # 3. Procesar Clic en el PDF digital para crear nota digital y proyectarla
        if mouse_click_coord is not None:
            cx, cy = mouse_click_coord
            if w <= cx < 2 * w:  # Clic en el panel del proyector/PDF
                rel_x = (cx - w) / scale
                rel_y = cy / scale
                nueva_nota = f"Nota digital #{len(NOTAS_SESION) + 1} en ({int(rel_x)}, {int(rel_y)}) pt"
                NOTAS_SESION.append((current_page, rel_x, rel_y, nueva_nota, (0.5, 0.9, 0.3), "DIGITAL_CLICK"))
                sincronizar_todas_las_notas_al_pdf()
                print(f"  [✓ NOTA DIGITAL CREADA] Posición: ({int(rel_x)}, {int(rel_y)}) pt -> Proyectada sobre el papel")
            mouse_click_coord = None

        # 4. VISTA DE CÁMARA (Físico -> Digital: Detección de Notas Escritas en Papel)
        if cap is not None:
            ret, frame = cap.read()
            if not ret:
                camera_view = np.full((h, w, 3), 40, dtype=np.uint8)
                cv2.putText(camera_view, "Camara no disponible", (50, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                cam_resized = cv2.resize(frame, (w, h))
                hsv = cv2.cvtColor(cam_resized, cv2.COLOR_BGR2HSV)

                # Rango de amarillo para Post-Its físicos
                lower_yellow = np.array([18, 80, 80])
                upper_yellow = np.array([38, 255, 255])
                mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

                cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                camera_view = cam_resized.copy()
                last_detected_box = None
                last_detected_crop = None

                for cnt in cnts:
                    area = cv2.contourArea(cnt)
                    if area > 2500:  # Tamaño mínimo del post-it en cámara
                        peri = cv2.arcLength(cnt, True)
                        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
                        if len(approx) == 4:
                            x_b, y_b, w_b, h_b = cv2.boundingRect(approx)
                            cv2.drawContours(camera_view, [approx], -1, (0, 255, 255), 3)
                            cv2.rectangle(camera_view, (x_b, y_b), (x_b + w_b, y_b + h_b), (0, 255, 0), 2)
                            cv2.putText(camera_view, "NOTA FISICA DETECTADA (Presiona 'C')", 
                                        (x_b, y_b - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 2)
                            last_detected_box = (x_b, y_b, w_b, h_b)
                            last_detected_crop = cam_resized[y_b:y_b+h_b, x_b:x_b+w_b]
                            break

                cv2.rectangle(camera_view, (0, 0), (w - 1, h - 1), (0, 220, 100), 2)
                cv2.putText(camera_view, "[FEED CAMARA CENITAL (DROIDCAM)]", (15, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 220, 100), 2)
                cv2.putText(camera_view, "Muestra nota escrita en papel para extraer con OCR", (15, 45),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1)
        else:
            camera_view = np.full((h, w, 3), 30, dtype=np.uint8)
            cv2.putText(camera_view, "MODO EMULACION DE CAMARA", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 180, 255), 2)
            cv2.putText(camera_view, "Conecta DroidCam para captura fisica de notas", (15, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)

        # 5. PANEL DE TELEMETRÍA Y ESTADO
        panel_w = 460
        panel = np.full((h, panel_w, 3), 24, dtype=np.uint8)

        cv2.putText(panel, "F16: CommentsPD / Sincronizacion", (15, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 220, 100), 2)
        cv2.putText(panel, f"Doc: {PDF_ORIGINAL_PATH.name[:38]}...", (15, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, (180, 180, 180), 1)
        cv2.putText(panel, f"Pagina: {current_page + 1} de {total_pages} (N=Siguiente, P=Anterior)", (15, 68),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 200, 255), 1)
        cv2.line(panel, (15, 78), (panel_w - 15, 78), (60, 60, 60), 1)

        cv2.putText(panel, f"Total Notas en PDF: {len(NOTAS_SESION)} ({len(notas_pagina)} en esta pagina)", (15, 98),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1)

        # Registro de notas
        y_list = 120
        for i, (pg, nx, ny, txt, col, orig) in enumerate(NOTAS_SESION[-5:], 1):
            cv2.putText(panel, f"{i}. [Pag {pg + 1}] [{orig}] ({int(nx)}, {int(ny)}) pt", (15, y_list),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 255), 1)
            y_list += 18
            cv2.putText(panel, f"   \"{txt[:38]}\"", (15, y_list),
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
        cv2.putText(panel, "C       : Capturar nota fisica de camara + OCR -> PDF", (18, h - 68), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (0, 220, 255), 1)
        cv2.putText(panel, "CLIC    : Crear nota digital (se proyecta sobre papel)", (18, h - 52), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (220, 220, 220), 1)
        cv2.putText(panel, "N / P   : Cambiar de pagina en el PDF real", (18, h - 36), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (180, 180, 180), 1)
        cv2.putText(panel, "O: Abrir PDF | R: Reiniciar | Q/ESC: Salir", (18, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (150, 150, 150), 1)

        # 6. Unir y mostrar todo
        combined_view = np.hstack([camera_view, projector_view, panel])
        cv2.imshow("EDDIE – F16 Sincronizacion de Post-Its (Bidireccional)", combined_view)

        key = cv2.waitKey(30) & 0xFF

        if key == ord('q') or key == 27:
            break
        elif key == ord('c') and last_detected_crop is not None and last_detected_box is not None:
            # Extracción OCR de la nota física con Tesseract
            try:
                gray_crop = cv2.cvtColor(last_detected_crop, cv2.COLOR_BGR2GRAY)
                blur_crop = cv2.GaussianBlur(gray_crop, (3, 3), 0)
                _, bw_crop = cv2.threshold(blur_crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                ocr_text = pytesseract.image_to_string(bw_crop, lang="spa+eng", config="--psm 6").strip()
            except Exception:
                ocr_text = ""

            if not ocr_text:
                ocr_text = f"Nota física #{len(NOTAS_SESION) + 1} capturada por cámara"

            bx, by, bw_b, bh_b = last_detected_box
            pdf_x = (bx * orig_w) / w
            pdf_y = (by * orig_h) / h
            NOTAS_SESION.append((current_page, pdf_x, pdf_y, ocr_text, (1.0, 0.85, 0.1), "CAMARA_OCR"))
            sincronizar_todas_las_notas_al_pdf()
            print(f"  [✓ POST-IT FÍSICO CAPTURADO] OCR: \"{ocr_text}\" -> Inyectado en ({pdf_x:.1f}, {pdf_y:.1f}) pt del PDF")
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
            NOTAS_SESION.clear()
            print("  [REINICIADO] Notas eliminadas del PDF.")
        elif key == ord('o'):
            abrir_pdf_visor(PDF_OUTPUT_PATH)
        elif key == ord('s'):
            out_path = EVID_DIR / "real_f16_postit_sync.png"
            cv2.imwrite(str(out_path), combined_view)
            print(f"  [GUARDADO] Evidencia: {out_path.name}")

    if cap: cap.release()
    cv2.destroyAllWindows()
    print("  ✓ F16 Finalizado exitosamente.\n")

if __name__ == "__main__":
    main()
