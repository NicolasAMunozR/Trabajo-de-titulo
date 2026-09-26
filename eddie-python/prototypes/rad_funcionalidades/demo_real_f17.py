"""
================================================================================
PROYECTO EDDIE (Python Migration) - Prototipo RAD F17
================================================================================
Función: Sincronización de Figuras Geométricas (PDF Digital -> Proyección sobre Papel)
Equivalente C# Legacy: ConsistencyLibraryFiguresPD / FiguresPD.cs & FiguresDP.cs
Tecnología: OpenCV + PyMuPDF (fitz)

Características Operativas:
1. Documento PDF Real:
   - Trabaja sobre el PDF real 'Informe Seminario Observaciones resueltas signed rg.pdf'.
   - Permite navegar entre páginas con N / P.
2. Dibujo y Extracción en PDF Digital -> Proyección sobre Papel Físico:
   - El usuario dibuja o extrae círculos, rectángulos y líneas sobre el PDF digital.
   - Las figuras SE PROYECTAN INMEDIATAMENTE SOBRE LA VISTA DEL PAPEL FÍSICO con efecto
     de haz de luz vectorial luminoso (Halo).
   - Se inyectan vectorialmente en el archivo PDF digital en disco (draw_rect, draw_circle, draw_line).
3. Detección Física por Cámara (Físico -> Digital):
   - La cámara cenital detecta figuras dibujadas a mano en papel (rectángulos, círculos, triángulos)
     mediante aproximación poligonal (approxPolyDP) y la fórmula de circularidad:
       Circularidad = (4 * PI * Area) / (Perímetro ^ 2)
     (Fórmula exacta de FiguresPD.cs).
   - Permite transferir las figuras detectadas en papel hacia el PDF digital con la tecla 'C'.
4. Persistencia en Disco y Visor:
   - Guarda el PDF real modificado con backup (.bac) y permite abrirlo en Adobe Reader/Edge.

Controles:
  1 / 2 / 3      : Seleccionar herramienta: 1=Rectángulo, 2=Círculo, 3=Línea de guía
  ARRASTRAR RATÓN: Dibujar figura sobre el PDF (se proyecta de inmediato sobre el papel)
  C              : Exportar figuras detectadas en cámara hacia el PDF real
  N / P          : Página Siguiente / Anterior en el PDF real
  R              : Reiniciar figuras de la sesión
  O              : Abrir el PDF real modificado en el visor del sistema
  S              : Guardar captura de evidencia PNG
  Q / ESC        : Salir
================================================================================
"""

import os
import sys
import pathlib
import time
import math
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

PDF_OUTPUT_PATH = EVID_DIR / "f17_real_pdf_figuras_synced.pdf"
PDF_BACKUP_PATH = EVID_DIR / "f17_real_pdf_figuras_synced.pdf.bac"

# Lista de figuras sincronizadas [(page_idx, tipo, params, color_rgb, origen)]
FIGURAS_SESION = [
    (5, "RECT", (50, 95, 550, 160), (0.9, 0.1, 0.1), "DIGITAL_ROI"),
    (5, "CIRCLE", (300, 240, 32), (0.1, 0.4, 0.9), "DIGITAL_GAZE"),
    (5, "LINE", (50, 310, 550, 310), (0.0, 0.7, 0.2), "DIGITAL_GUIA"),
]

def inicializar_pdf_salida():
    """Copia el PDF base al archivo de salida."""
    doc = fitz.open(str(PDF_ORIGINAL_PATH))
    doc.save(str(PDF_OUTPUT_PATH))
    doc.close()

def sincronizar_todas_las_figuras_al_pdf():
    """Dibuja vectorialmente todas las figuras de la sesión en el archivo PDF real en disco."""
    if PDF_OUTPUT_PATH.exists():
        try:
            if PDF_BACKUP_PATH.exists():
                PDF_BACKUP_PATH.unlink()
            PDF_OUTPUT_PATH.rename(PDF_BACKUP_PATH)
        except Exception:
            pass

    doc = fitz.open(str(PDF_BACKUP_PATH if PDF_BACKUP_PATH.exists() else PDF_ORIGINAL_PATH))

    for pg_idx, tipo, params, col, origen in FIGURAS_SESION:
        if pg_idx < len(doc):
            page = doc[pg_idx]
            if tipo == "RECT":
                x0, y0, x1, y1 = params
                rect = fitz.Rect(x0, y0, x1, y1)
                page.draw_rect(rect, color=col, width=1.8)
                page.insert_text((x0 + 4, y0 - 4), f"[{origen}]", fontsize=7.5, color=col)
            elif tipo == "CIRCLE":
                cx, cy, r = params
                page.draw_circle(fitz.Point(cx, cy), r, color=col, 
                                 fill=(col[0]*0.2 + 0.8, col[1]*0.2 + 0.8, col[2]*0.2 + 0.8), width=1.5)
                page.insert_text((cx - r, cy - r - 4), f"[{origen}]", fontsize=7.5, color=col)
            elif tipo == "LINE":
                x0, y0, x1, y1 = params
                page.draw_line(fitz.Point(x0, y0), fitz.Point(x1, y1), color=col, width=2.0)
                page.insert_text((x0, y0 - 4), f"[{origen}]", fontsize=7.5, color=col)

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

# Variables de interacción mouse para dibujo vectorial
mouse_drag_start = None
mouse_drag_end = None
is_drawing = False
herramienta_actual = "RECT"  # RECT, CIRCLE, LINE

def on_mouse(event, x, y, flags, param):
    global mouse_drag_start, mouse_drag_end, is_drawing
    if event == cv2.EVENT_LBUTTONDOWN:
        mouse_drag_start = (x, y)
        mouse_drag_end = (x, y)
        is_drawing = True
    elif event == cv2.EVENT_MOUSEMOVE and is_drawing:
        mouse_drag_end = (x, y)
    elif event == cv2.EVENT_LBUTTONUP and is_drawing:
        mouse_drag_end = (x, y)
        is_drawing = False

def main():
    global mouse_drag_start, mouse_drag_end, is_drawing, herramienta_actual
    print("=" * 75)
    print("  EDDIE Python – F17: Sincronización de Figuras (PDF Digital -> Proyección sobre Papel)")
    print(f"  Documento Real: {PDF_ORIGINAL_PATH.name}")
    print("  Módulo Legacy C#: ConsistencyLibraryFiguresPD / FiguresPD.cs & FiguresDP.cs")
    print("=" * 75)

    inicializar_pdf_salida()
    current_page = 5  # Página 6 (índice 5)
    sincronizar_todas_las_figuras_al_pdf()

    # Intentar abrir cámara (DroidCam con MSMF o cámara estándar)
    cap = None
    for idx in range(3):
        for backend in [cv2.CAP_MSMF, cv2.CAP_ANY]:
            try:
                c = cv2.VideoCapture(idx, backend)
                if c.isOpened():
                    cap = c
                    print(f"  [+] Cámara detectada en índice {idx} (MSMF/ANY) para escaneo geométrico")
                    break
                c.release()
            except Exception:
                pass
        if cap: break

    cv2.namedWindow("EDDIE – F17 Sincronizacion de Figuras Geometricas", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("EDDIE – F17 Sincronizacion de Figuras Geometricas", 1420, 800)
    cv2.setMouseCallback("EDDIE – F17 Sincronizacion de Figuras Geometricas", on_mouse)

    abrir_pdf_visor(PDF_OUTPUT_PATH)

    detected_figures_cam = []

    while True:
        # 1. Renderizar imagen del PDF real sincronizado
        active_render_pdf = PDF_OUTPUT_PATH if PDF_OUTPUT_PATH.exists() else PDF_ORIGINAL_PATH
        page_img, scale, total_pages, orig_w, orig_h = renderizar_pagina_real(active_render_pdf, current_page, dpi=115)
        h, w = page_img.shape[:2]

        # 2. VISTA PROYECTOR SIMULADA (Proyección sobre Papel Físico)
        # Las figuras del PDF digital SE PROYECTAN sobre la superficie del libro físico
        projector_view = page_img.copy()
        figuras_pagina = [f for f in FIGURAS_SESION if f[0] == current_page]

        for _, tipo, params, col_rgb, orig in figuras_pagina:
            col_bgr = (int(col_rgb[2] * 255), int(col_rgb[1] * 255), int(col_rgb[0] * 255))
            if tipo == "RECT":
                rx0, ry0, rx1, ry1 = params
                px0, py0 = int(rx0 * scale), int(ry0 * scale)
                px1, py1 = int(rx1 * scale), int(ry1 * scale)
                cv2.rectangle(projector_view, (px0, py0), (px1, py1), col_bgr, 2)
                cv2.putText(projector_view, f"ROI [{orig[:3]}]", (px0 + 4, py0 - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, col_bgr, 1)
            elif tipo == "CIRCLE":
                cx, cy, r = params
                pcx, pcy, pr = int(cx * scale), int(cy * scale), int(r * scale)
                overlay = projector_view.copy()
                cv2.circle(overlay, (pcx, pcy), pr, col_bgr, -1)
                projector_view = cv2.addWeighted(overlay, 0.25, projector_view, 0.75, 0)
                cv2.circle(projector_view, (pcx, pcy), pr, col_bgr, 2)
                cv2.putText(projector_view, f"Gaze [{orig[:3]}]", (pcx - pr, pcy - pr - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, col_bgr, 1)
            elif tipo == "LINE":
                lx0, ly0, lx1, ly1 = params
                plx0, ply0 = int(lx0 * scale), int(ly0 * scale)
                plx1, ply1 = int(lx1 * scale), int(ly1 * scale)
                cv2.line(projector_view, (plx0, ply0), (plx1, ply1), col_bgr, 2)

        # Previsualización de dibujo interactivo con el ratón sobre el PDF digital
        if mouse_drag_start is not None and mouse_drag_end is not None:
            x0, y0 = mouse_drag_start
            x1, y1 = mouse_drag_end

            # Verificar si el trazo es en el panel del proyector (Panel Central)
            if w <= x0 < 2 * w:
                local_x0, local_x1 = x0 - w, x1 - w

                if is_drawing:
                    if herramienta_actual == "RECT":
                        cv2.rectangle(projector_view, (local_x0, y0), (local_x1, y1), (0, 0, 255), 2)
                    elif herramienta_actual == "CIRCLE":
                        r = int(math.hypot(local_x1 - local_x0, y1 - y0))
                        cv2.circle(projector_view, (local_x0, y0), r, (255, 120, 0), 2)
                    elif herramienta_actual == "LINE":
                        cv2.line(projector_view, (local_x0, y0), (local_x1, y1), (0, 220, 0), 2)
                else:
                    # Finalizó el trazo -> Sincronizar hacia el PDF real y proyectar
                    if abs(local_x1 - local_x0) > 5 or abs(y1 - y0) > 5:
                        pdf_x0, pdf_y0 = local_x0 / scale, y0 / scale
                        pdf_x1, pdf_y1 = local_x1 / scale, y1 / scale

                        if herramienta_actual == "RECT":
                            rx0, rx1 = min(pdf_x0, pdf_x1), max(pdf_x0, pdf_x1)
                            ry0, ry1 = min(pdf_y0, pdf_y1), max(pdf_y0, pdf_y1)
                            FIGURAS_SESION.append((current_page, "RECT", (rx0, ry0, rx1, ry1), (0.9, 0.1, 0.1), "DIGITAL_ROI"))
                        elif herramienta_actual == "CIRCLE":
                            r_pdf = math.hypot(pdf_x1 - pdf_x0, pdf_y1 - pdf_y0)
                            FIGURAS_SESION.append((current_page, "CIRCLE", (pdf_x0, pdf_y0, r_pdf), (0.1, 0.4, 0.9), "DIGITAL_GAZE"))
                        elif herramienta_actual == "LINE":
                            FIGURAS_SESION.append((current_page, "LINE", (pdf_x0, pdf_y0, pdf_x1, pdf_y1), (0.0, 0.7, 0.2), "DIGITAL_GUIA"))

                        sincronizar_todas_las_figuras_al_pdf()
                        print(f"  [✓ FIGURA VECTORIAL SINCRONIZADA] {herramienta_actual} -> Inyectada al PDF y proyectada sobre papel")

                    mouse_drag_start = None
                    mouse_drag_end = None

        cv2.rectangle(projector_view, (0, 0), (w - 1, h - 1), (0, 180, 255), 2)
        cv2.putText(projector_view, "[VISTA PROYECTOR (SOBRE PAPEL)]", (15, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 140, 220), 2)
        cv2.putText(projector_view, f"Figuras proyectadas sobre libro | Herramienta: {herramienta_actual}", (15, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (80, 80, 80), 1)

        # 3. VISTA DE CÁMARA (Detección de Figuras Físicas en Papel: FiguresPD.cs)
        if cap is not None:
            ret, frame = cap.read()
            if not ret:
                camera_view = np.full((h, w, 3), 40, dtype=np.uint8)
                cv2.putText(camera_view, "Camara no disponible", (50, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                cam_resized = cv2.resize(frame, (w, h))
                gray = cv2.cvtColor(cam_resized, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray, (5, 5), 0)
                edges = cv2.Canny(blur, 40, 130)
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                edges = cv2.dilate(edges, kernel, iterations=1)

                cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                camera_view = cam_resized.copy()
                detected_figures_cam = []

                for cnt in cnts:
                    area = cv2.contourArea(cnt)
                    if area > 1200:
                        peri = cv2.arcLength(cnt, True)
                        approx = cv2.approxPolyDP(cnt, 0.035 * peri, True)
                        circularidad = (4.0 * math.pi * area) / (peri * peri) if peri > 0 else 0

                        M = cv2.moments(cnt)
                        cx = int(M["m10"] / M["m00"]) if M["m00"] > 0 else 0
                        cy = int(M["m01"] / M["m00"]) if M["m00"] > 0 else 0

                        if circularidad > 0.69:
                            (x_c, y_c), radius = cv2.minEnclosingCircle(cnt)
                            cv2.circle(camera_view, (int(x_c), int(y_c)), int(radius), (255, 120, 0), 2)
                            cv2.putText(camera_view, f"Circulo (C={circularidad:.2f})", (cx - 30, cy),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 180, 0), 1)
                            detected_figures_cam.append(("CIRCLE", (cx, cy, int(radius)), (0.1, 0.4, 0.9)))
                        elif len(approx) == 4:
                            x_r, y_r, w_r, h_r = cv2.boundingRect(approx)
                            cv2.rectangle(camera_view, (x_r, y_r), (x_r + w_r, y_r + h_r), (0, 0, 255), 2)
                            cv2.putText(camera_view, "Rectangulo", (x_r, y_r - 6),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 255), 1)
                            detected_figures_cam.append(("RECT", (x_r, y_r, x_r + w_r, y_r + h_r), (0.9, 0.1, 0.1)))
                        elif len(approx) == 3:
                            cv2.drawContours(camera_view, [approx], -1, (0, 220, 100), 2)
                            cv2.putText(camera_view, "Triangulo", (cx - 20, cy),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 220, 100), 1)

                cv2.rectangle(camera_view, (0, 0), (w - 1, h - 1), (0, 220, 100), 2)
                cv2.putText(camera_view, "[FEED CAMARA CENITAL (DROIDCAM)]", (15, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 220, 100), 2)
                cv2.putText(camera_view, "Clasificacion de figuras en papel (Presiona 'C')", (15, 45),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1)
        else:
            camera_view = np.full((h, w, 3), 30, dtype=np.uint8)
            cv2.putText(camera_view, "MODO EMULACION DE CAMARA", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 180, 255), 2)
            cv2.putText(camera_view, "Conecta DroidCam para deteccion por vision", (15, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)

        # 4. PANEL DE TELEMETRÍA Y CONTROL
        panel_w = 460
        panel = np.full((h, panel_w, 3), 24, dtype=np.uint8)

        cv2.putText(panel, "F17: FiguresPD (PDF Real)", (15, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 220, 100), 2)
        cv2.putText(panel, f"Doc: {PDF_ORIGINAL_PATH.name[:38]}...", (15, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, (180, 180, 180), 1)
        cv2.putText(panel, f"Pagina: {current_page + 1} de {total_pages} (N=Siguiente, P=Anterior)", (15, 68),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 200, 255), 1)
        cv2.line(panel, (15, 78), (panel_w - 15, 78), (60, 60, 60), 1)

        cv2.putText(panel, f"Figuras vectoriales en PDF: {len(FIGURAS_SESION)} ({len(figuras_pagina)} en esta pag)", (15, 98),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1)
        cv2.putText(panel, f"Herramienta de dibujo: {herramienta_actual}", (15, 118),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 255), 1)

        # Registro de figuras
        y_list = 142
        for i, (pg, t_fig, p_fig, _, orig) in enumerate(FIGURAS_SESION[-5:], 1):
            cv2.putText(panel, f"{i}. [Pag {pg + 1}] [{t_fig}] {orig}", (15, y_list),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 220, 255), 1)
            y_list += 18
            if t_fig == "RECT":
                p_str = f"Box: [{p_fig[0]:.0f}, {p_fig[1]:.0f}, {p_fig[2]:.0f}, {p_fig[3]:.0f}]"
            elif t_fig == "CIRCLE":
                p_str = f"Centro: ({p_fig[0]:.0f},{p_fig[1]:.0f}), R={p_fig[2]:.0f}pt"
            else:
                p_str = f"De ({p_fig[0]:.0f},{p_fig[1]:.0f}) a ({p_fig[2]:.0f},{p_fig[3]:.0f})"
            cv2.putText(panel, f"   {p_str}", (15, y_list),
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
        cv2.putText(panel, "1/2/3   : 1=Rectangulo, 2=Circulo, 3=Linea", (18, h - 68), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (0, 220, 255), 1)
        cv2.putText(panel, "ARRASTRAR: Dibujar figura (se proyecta sobre papel)", (18, h - 52), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (220, 220, 220), 1)
        cv2.putText(panel, "C       : Exportar figuras de camara -> PDF", (18, h - 36), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (0, 255, 200), 1)
        cv2.putText(panel, "N/P: Paginas | O: Abrir PDF | Q/ESC: Salir", (18, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (150, 150, 150), 1)

        # 5. Unir y mostrar todo
        combined_view = np.hstack([camera_view, projector_view, panel])
        cv2.imshow("EDDIE – F17 Sincronizacion de Figuras Geometricas", combined_view)

        key = cv2.waitKey(30) & 0xFF

        if key == ord('q') or key == 27:
            break
        elif key == ord('1'):
            herramienta_actual = "RECT"
            print("  [HERRAMIENTA] 1: Rectángulo ROI seleccionado")
        elif key == ord('2'):
            herramienta_actual = "CIRCLE"
            print("  [HERRAMIENTA] 2: Círculo de fijación ocular seleccionado")
        elif key == ord('3'):
            herramienta_actual = "LINE"
            print("  [HERRAMIENTA] 3: Línea de lectura seleccionada")
        elif key == ord('c') and detected_figures_cam:
            for fig_t, pars, col in detected_figures_cam:
                if fig_t == "RECT":
                    rx0, ry0, rx1, ry1 = pars
                    px0, px1 = (rx0 * orig_w) / w, (rx1 * orig_w) / w
                    py0, py1 = (ry0 * orig_h) / h, (ry1 * orig_h) / h
                    FIGURAS_SESION.append((current_page, "RECT", (px0, py0, px1, py1), col, "CAMARA_FISICA"))
                elif fig_t == "CIRCLE":
                    cx, cy, r = pars
                    pcx = (cx * orig_w) / w
                    pcy = (cy * orig_h) / h
                    pr  = (r * orig_w) / w
                    FIGURAS_SESION.append((current_page, "CIRCLE", (pcx, pcy, pr), col, "CAMARA_FISICA"))
            sincronizar_todas_las_figuras_al_pdf()
            print(f"  [✓ FIGURAS DE CÁMARA SINCRONIZADAS] {len(detected_figures_cam)} figuras inyectadas en la página {current_page + 1} del PDF")
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
            FIGURAS_SESION.clear()
            print("  [REINICIADO] Figuras eliminadas del PDF.")
        elif key == ord('o'):
            abrir_pdf_visor(PDF_OUTPUT_PATH)
        elif key == ord('s'):
            out_path = EVID_DIR / "real_f17_figuras_sync.png"
            cv2.imwrite(str(out_path), combined_view)
            print(f"  [GUARDADO] Evidencia: {out_path.name}")

    if cap: cap.release()
    cv2.destroyAllWindows()
    print("  ✓ F17 Finalizado exitosamente.\n")

if __name__ == "__main__":
    main()
