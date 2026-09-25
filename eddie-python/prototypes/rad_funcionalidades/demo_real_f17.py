"""
DEMO REAL F17 – Sincronización de Figuras Geométricas (Físico <-> Digital)
===========================================================================
Basado en: ConsistencyLibraryFiguresPD / FiguresPD.cs (EDDIE Legacy C#)

Funcionalidad REAL:
1. Sincronización Física -> Digital (Paper to PDF):
   - Captura frames de la cámara y detecta figuras geométricas dibujadas a mano
     (rectángulos, círculos, elipses, triángulos) usando aproximación poligonal (approxPolyDP)
     y métrica de circularidad (4*pi*Area/Perimeter^2).
   - Transfiere las figuras detectadas vectorialmente hacia el documento PDF digital.
2. Sincronización Digital -> Física (PDF to Projector):
   - Permite al usuario dibujar/proyectar figuras geométricas interactivas:
     * Rectángulo de zona de lectura / ROI (rojo)
     * Círculo de fijación ocular / Gaze Point (azul)
     * Línea de avance de lectura (verde)
3. Genera un documento PDF real con las figuras vectoriales impresas y lo abre en el visor del sistema.

Controles:
  ESPACIO = Alternar entre Modo Cámara y Modo Proyector
  1 / 2 / 3 = (Modo Proyector) Seleccionar figura: 1=Rectángulo, 2=Círculo, 3=Línea
  CLIC Y ARRASTRE = Dibujar figura sobre el documento proyectado
  C       = (Modo Cámara) Capturar figuras detectadas por cámara y exportar al PDF
  O       = Abrir PDF resultante en el visor del sistema
  S       = Guardar imagen de evidencia
  Q       = Salir
"""

import os
import sys
import pathlib
import time
import math
import cv2
import numpy as np
import pymupdf as fitz

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

PDF_BASE_PATH   = EVID / "real_f17_documento_base.pdf"
PDF_SYNCED_PATH = EVID / "real_f17_figuras_synced.pdf"

# Lista de figuras sincronizadas [(tipo, params, color, origen)]
FIGURAS_SESION = [
    ("RECT", (50, 85, 545, 175), (0.9, 0.1, 0.1), "DIGITAL"),
    ("CIRCLE", (300, 260, 30), (0.1, 0.4, 0.9), "DIGITAL"),
    ("LINE", (50, 340, 545, 340), (0.0, 0.7, 0.2), "DIGITAL"),
]

def crear_pdf_base():
    """Genera documento base para las pruebas de sincronización geométrica."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    
    page.insert_text((50, 45), "SISTEMA EDDIE: Sincronización de Figuras Geométricas", 
                     fontsize=13, color=(0.1, 0.3, 0.2))
    page.draw_line((50, 52), (560, 52), color=(0.1, 0.4, 0.3), width=1.2)

    texto = """
Capítulo 5: Consistencia de Figuras Geométricas (FiguresPD / FiguresDP)

El subsistema de consistencia geométrica de EDDIE sincroniza diagramas, encierros de párrafos,
marcas circulares y líneas de guía trazadas tanto en el documento físico como en el visor digital.

1. Extracción Geométrica mediante Visión:
El algoritmo analiza los contornos cerrados en el frame de la cámara. Aplica reducción poligonal
Ramer-Douglas-Peucker y evalúa la circularidad matemática:
   Circularidad = (4 * PI * Area) / (Perímetro ^ 2)
Permitiendo clasificar con precisión círculos (> 0.70), rectángulos y polígonos irregulares.

2. Mapeo Vectorial al PDF:
A diferencia de simples capturas de mapa de bits, las figuras se inyectan como primitivas
vectoriales en el PDF (draw_rect, draw_circle, draw_line), garantizando fidelidad visual
y compatibilidad con lectores PDF estándar.

3. Proyección en Tiempo Real:
Las figuras geométricas asociadas al seguimiento ocular o a indicaciones de tutores se proyectan
directamente sobre la superficie del libro físico.
"""
    page.insert_text((50, 75), texto.strip(), fontsize=10.5, color=(0.1, 0.1, 0.1), lineheight=1.4)
    page.draw_line((50, 740), (560, 740), color=(0.7, 0.7, 0.7), width=0.8)
    page.insert_text((50, 755), "Prototipo F17 – FiguresPD / Sincronización Geométrica | EDDIE Python", 
                     fontsize=8, color=(0.5, 0.5, 0.5))
    doc.save(str(PDF_BASE_PATH))
    doc.close()

def sincronizar_figuras_al_pdf():
    """Toma el PDF base y dibuja vectorialmente todas las figuras de la sesión."""
    doc = fitz.open(str(PDF_BASE_PATH))
    page = doc[0]

    for tipo, params, col, origen in FIGURAS_SESION:
        if tipo == "RECT":
            x0, y0, x1, y1 = params
            rect = fitz.Rect(x0, y0, x1, y1)
            page.draw_rect(rect, color=col, width=1.8)
            page.insert_text((x0 + 4, y0 - 3), f"[ROI {origen}]", fontsize=7.5, color=col)
        elif tipo == "CIRCLE":
            cx, cy, r = params
            page.draw_circle(fitz.Point(cx, cy), r, color=col, fill=(col[0]*0.2 + 0.8, col[1]*0.2 + 0.8, col[2]*0.2 + 0.8), width=1.5)
            page.insert_text((cx - r, cy - r - 3), f"[Fijación {origen}]", fontsize=7.5, color=col)
        elif tipo == "LINE":
            x0, y0, x1, y1 = params
            page.draw_line(fitz.Point(x0, y0), fitz.Point(x1, y1), color=col, width=2.0)
            page.insert_text((x0, y0 - 3), f"[Guía {origen}]", fontsize=7.5, color=col)

    doc.save(str(PDF_SYNCED_PATH))
    doc.close()

def renderizar_pdf_a_cv(dpi=130):
    doc = fitz.open(str(PDF_SYNCED_PATH))
    page = doc[0]
    pix = page.get_pixmap(dpi=dpi)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.h, pix.w, pix.n))
    doc.close()
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img, pix.w / 612.0

def abrir_pdf(path):
    try:
        os.startfile(str(path))
        print(f"  [ABIERTO EN VISOR] {path.name}")
    except Exception as e:
        print(f"  [!] No pudo abrir visor: {e}")

# Variables de interacción mouse para dibujo
mouse_drag_start = None
mouse_drag_end = None
is_drawing = False
figura_seleccionada = "RECT"  # RECT, CIRCLE, LINE

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
    global mouse_drag_start, mouse_drag_end, is_drawing, figura_seleccionada
    print("=" * 65)
    print("  DEMO REAL F17 – Sincronización de Figuras Geométricas")
    print("  Módulo: ConsistencyLibraryFiguresPD / FiguresPD.cs")
    print("=" * 65)

    crear_pdf_base()
    sincronizar_figuras_al_pdf()

    # Intentar abrir cámara
    cap = None
    for idx in range(3):
        for backend in [cv2.CAP_MSMF, cv2.CAP_ANY]:
            try:
                c = cv2.VideoCapture(idx, backend)
                if c.isOpened():
                    cap = c
                    print(f"  [+] Cámara detectada en índice {idx} para reconocimiento de figuras")
                    break
                c.release()
            except Exception:
                pass
        if cap: break

    modo_actual = "PROYECTOR"
    print(f"  Modo inicial: {modo_actual} (Presiona ESPACIO para alternar)\n")

    cv2.namedWindow("EDDIE – F17 Figuras Geometricas", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("EDDIE – F17 Figuras Geometricas", 1280, 750)
    cv2.setMouseCallback("EDDIE – F17 Figuras Geometricas", on_mouse)

    abrir_pdf(PDF_SYNCED_PATH)

    detected_figures_cam = []

    while True:
        if modo_actual == "CAMARA" and cap is not None:
            ret, frame = cap.read()
            if not ret:
                modo_actual = "PROYECTOR"
                continue

            h, w = frame.shape[:2]
            display_frame = frame.copy()

            # Algoritmo de detección de figuras geométricas (FiguresPD.cs)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blur, 40, 140)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            edges = cv2.dilate(edges, kernel, iterations=1)

            cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            detected_figures_cam = []

            for cnt in cnts:
                area = cv2.contourArea(cnt)
                if area > 1500:
                    peri = cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)
                    circularidad = (4.0 * math.pi * area) / (peri * peri) if peri > 0 else 0

                    M = cv2.moments(cnt)
                    cx = int(M["m10"] / M["m00"]) if M["m00"] > 0 else 0
                    cy = int(M["m01"] / M["m00"]) if M["m00"] > 0 else 0

                    if circularidad > 0.70:
                        # Círculo
                        (x_c, y_c), radius = cv2.minEnclosingCircle(cnt)
                        cv2.circle(display_frame, (int(x_c), int(y_c)), int(radius), (255, 100, 0), 2)
                        cv2.putText(display_frame, f"Circulo (c={circularidad:.2f})", (cx - 30, cy),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 180, 0), 2)
                        detected_figures_cam.append(("CIRCLE", (cx, cy, int(radius)), (0.1, 0.4, 0.9)))
                    elif len(approx) == 4:
                        # Cuadrilátero / Rectángulo
                        x_r, y_r, w_r, h_r = cv2.boundingRect(approx)
                        cv2.rectangle(display_frame, (x_r, y_r), (x_r + w_r, y_r + h_r), (0, 0, 255), 2)
                        cv2.putText(display_frame, "Rectangulo", (x_r, y_r - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
                        detected_figures_cam.append(("RECT", (x_r, y_r, x_r + w_r, y_r + h_r), (0.9, 0.1, 0.1)))
                    elif len(approx) == 3:
                        # Triángulo
                        cv2.drawContours(display_frame, [approx], -1, (0, 220, 100), 2)
                        cv2.putText(display_frame, "Triangulo", (cx - 20, cy),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 100), 2)

            panel_w = 480
            panel = np.full((h, panel_w, 3), 26, dtype=np.uint8)
            cv2.putText(panel, "F17: Modo Deteccion Fisica (Camara)", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 220, 100), 2)
            cv2.putText(panel, "Dibuja figuras en papel y muestralas", (15, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)
            cv2.line(panel, (15, 75), (panel_w - 15, 75), (70, 70, 70), 1)

            cv2.putText(panel, f"Figuras detectadas en camara: {len(detected_figures_cam)}", (15, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1)

            y_log = 130
            for i, (fig_t, par, _) in enumerate(detected_figures_cam[:5], 1):
                cv2.putText(panel, f"{i}. Tipo: {fig_t} -> Params: {par}", (15, y_log),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 255, 200), 1)
                y_log += 25

            # Miniatura de bordes
            edges_sm = cv2.resize(cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR), (160, 120))
            panel[h - 260:h - 140, 15:175] = edges_sm
            cv2.rectangle(panel, (15, h - 260), (175, h - 140), (80, 80, 80), 1)
            cv2.putText(panel, "Mapa de Bordes Canny", (15, h - 125), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (140, 140, 140), 1)

            # Controles
            cv2.rectangle(panel, (10, h - 110), (panel_w - 10, h - 10), (40, 40, 40), -1)
            cv2.putText(panel, "C       : Exportar figuras detectadas al PDF", (18, h - 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 100), 1)
            cv2.putText(panel, "ESPACIO : Alternar a Modo Proyector / Dibujo", (18, h - 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 200, 255), 1)
            cv2.putText(panel, "O       : Abrir PDF actualizado | Q: Salir", (18, h - 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1)

            combined = np.hstack([display_frame, panel])

        else:
            # Modo PROYECTOR / DIGITAL
            page_img, scale = renderizar_pdf_a_cv()
            display_page = page_img.copy()
            h, w = display_page.shape[:2]

            # Dibuja preview de lo que el usuario está arrastrando
            if mouse_drag_start is not None and mouse_drag_end is not None:
                x0, y0 = mouse_drag_start
                x1, y1 = mouse_drag_end

                if is_drawing:
                    if figura_seleccionada == "RECT":
                        cv2.rectangle(display_page, (x0, y0), (x1, y1), (0, 0, 255), 2)
                    elif figura_seleccionada == "CIRCLE":
                        r = int(math.hypot(x1 - x0, y1 - y0))
                        cv2.circle(display_page, (x0, y0), r, (255, 100, 0), 2)
                    elif figura_seleccionada == "LINE":
                        cv2.line(display_page, (x0, y0), (x1, y1), (0, 200, 0), 2)
                else:
                    # Finalizó el trazo -> Agregar figura a la sesión
                    if abs(x1 - x0) > 5 or abs(y1 - y0) > 5:
                        if x0 < w and x1 < w:
                            px0, py0 = x0 / scale, y0 / scale
                            px1, py1 = x1 / scale, y1 / scale

                            if figura_seleccionada == "RECT":
                                rx0, rx1 = min(px0, px1), max(px0, px1)
                                ry0, ry1 = min(py0, py1), max(py0, py1)
                                FIGURAS_SESION.append(("RECT", (rx0, ry0, rx1, ry1), (0.9, 0.1, 0.1), "PROYECTOR"))
                            elif figura_seleccionada == "CIRCLE":
                                r_pdf = math.hypot(px1 - px0, py1 - py0)
                                FIGURAS_SESION.append(("CIRCLE", (px0, py0, r_pdf), (0.1, 0.4, 0.9), "PROYECTOR"))
                            elif figura_seleccionada == "LINE":
                                FIGURAS_SESION.append(("LINE", (px0, py0, px1, py1), (0.0, 0.7, 0.2), "PROYECTOR"))

                            sincronizar_figuras_al_pdf()
                            print(f"  [SINCRONIZADO] Figura {figura_seleccionada} agregada al PDF")
                    mouse_drag_start = None
                    mouse_drag_end = None

            panel_w = 480
            panel = np.full((h, panel_w, 3), 26, dtype=np.uint8)
            cv2.putText(panel, "F17: Modo Proyector / Editor de Figuras", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 220, 100), 2)
            cv2.putText(panel, f"Herramienta actual: {figura_seleccionada}", (15, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255), 1)
            cv2.line(panel, (15, 75), (panel_w - 15, 75), (70, 70, 70), 1)

            cv2.putText(panel, f"Figuras vectoriales en PDF: {len(FIGURAS_SESION)}", (15, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1)

            y_log = 135
            for i, (t_fig, p_fig, _, orig) in enumerate(FIGURAS_SESION, 1):
                cv2.putText(panel, f"{i}. [{t_fig}] {orig}", (15, y_log),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 220, 255), 1)
                y_log += 18
                if t_fig == "RECT":
                    p_str = f"Box: [{p_fig[0]:.0f}, {p_fig[1]:.0f}, {p_fig[2]:.0f}, {p_fig[3]:.0f}]"
                elif t_fig == "CIRCLE":
                    p_str = f"Centro: ({p_fig[0]:.0f},{p_fig[1]:.0f}), R={p_fig[2]:.0f}pt"
                else:
                    p_str = f"De ({p_fig[0]:.0f},{p_fig[1]:.0f}) a ({p_fig[2]:.0f},{p_fig[3]:.0f})"

                cv2.putText(panel, f"   {p_str}", (15, y_log),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (180, 255, 180), 1)
                y_log += 25
                if y_log > h - 140:
                    break

            # Controles
            cv2.rectangle(panel, (10, h - 130), (panel_w - 10, h - 10), (40, 40, 40), -1)
            cv2.putText(panel, "1/2/3   : 1=Rectangulo, 2=Circulo, 3=Linea", (18, h - 105),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 100), 1)
            cv2.putText(panel, "ARRASTRAR: Dibujar figura sobre el documento", (18, h - 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 255), 1)
            cv2.putText(panel, "ESPACIO : Alternar a Modo Camara de Figuras", (18, h - 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 200, 255), 1)
            cv2.putText(panel, "O       : Abrir PDF en visor | S: Guardar | Q: Salir", (18, h - 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.36, (200, 200, 200), 1)

            combined = np.hstack([display_page, panel])

        cv2.imshow("EDDIE – F17 Figuras Geometricas", combined)
        key = cv2.waitKey(30) & 0xFF

        if key == ord('q') or key == 27:
            break
        elif key == ord(' '):
            modo_actual = "PROYECTOR" if modo_actual == "CAMARA" else ("CAMARA" if cap is not None else "PROYECTOR")
            print(f"  [MODO] Cambiado a: {modo_actual}")
        elif key == ord('1'):
            figura_seleccionada = "RECT"
            print("  [HERRAMIENTA] Rectángulo ROI seleccionado")
        elif key == ord('2'):
            figura_seleccionada = "CIRCLE"
            print("  [HERRAMIENTA] Círculo de fijación seleccionado")
        elif key == ord('3'):
            figura_seleccionada = "LINE"
            print("  [HERRAMIENTA] Línea de lectura seleccionada")
        elif key == ord('c') and modo_actual == "CAMARA" and detected_figures_cam:
            for fig_t, pars, col in detected_figures_cam:
                # Escalar de coordenadas de cámara (640x480) a PDF (612x792)
                if fig_t == "RECT":
                    rx0, ry0, rx1, ry1 = pars
                    px0, px1 = (rx0 * 612.0) / w, (rx1 * 612.0) / w
                    py0, py1 = (ry0 * 792.0) / h, (ry1 * 792.0) / h
                    FIGURAS_SESION.append(("RECT", (px0, py0, px1, py1), col, "CAMARA_FISICA"))
                elif fig_t == "CIRCLE":
                    cx, cy, r = pars
                    pcx = (cx * 612.0) / w
                    pcy = (cy * 792.0) / h
                    pr  = (r * 612.0) / w
                    FIGURAS_SESION.append(("CIRCLE", (pcx, pcy, pr), col, "CAMARA_FISICA"))
            sincronizar_figuras_al_pdf()
            print(f"  [✓ FIGURAS CAPTURADAS] {len(detected_figures_cam)} figuras sincronizadas al PDF")
        elif key == ord('o'):
            abrir_pdf(PDF_SYNCED_PATH)
        elif key == ord('s'):
            out_img = EVID / "real_f17_figuras.png"
            cv2.imwrite(str(out_img), combined)
            print(f"  [GUARDADO] Evidencia: {out_img.name}")

    if cap: cap.release()
    cv2.destroyAllWindows()
    print("  ✓ F17 COMPLETADO EXITOSAMENTE\n")

if __name__ == "__main__":
    main()
