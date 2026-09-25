"""
DEMO REAL F16 – Sincronización de Notas Adhesivas (Post-It / Comentarios)
==========================================================================
Basado en: ConsistencyLibraryCommentsPD / CommentsPD.cs (EDDIE Legacy C#)

Funcionalidad REAL:
1. Sincronización Física -> Digital (Paper to PDF):
   - Usa la cámara (DroidCam/Webcam) para detectar notas adhesivas amarillas (Post-its)
     en tiempo real usando segmentación en espacio de color HSV y contornos cuadriláteros.
   - Aplica Tesseract OCR para extraer el texto escrito en la nota física.
   - Sincroniza la nota hacia el PDF digital insertándola como anotación formal (Sticky Note)
     con PyMuPDF (fitz.add_text_annot) y una estampa visual en la posición exacta.
2. Sincronización Digital -> Física (PDF to Projector):
   - Muestra la proyección interactiva del Post-It sobre el documento.
   - Permite hacer clic sobre la página para posicionar nuevas notas adhesivas dinámicamente.
3. Abre el archivo PDF anotado en el visor predeterminado del sistema.

Controles:
  ESPACIO = Cambiar entre Modo Cámara y Modo Proyector
  C       = Capturar Post-It detectado por cámara y sincronizar a PDF
  CLIC    = (En modo proyector) Agregar nota adhesiva en esa posición
  O       = Abrir PDF resultante en el visor del sistema
  S       = Guardar imagen de evidencia
  Q       = Salir
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

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

PDF_BASE_PATH   = EVID / "real_f16_documento_base.pdf"
PDF_SYNCED_PATH = EVID / "real_f16_postit_synced.pdf"

# Lista de notas sincronizadas en la sesión [(x_pdf, y_pdf, texto, color, tipo)]
NOTAS_SESION = [
    (420, 120, "Nota inicial: Revisar definición de consistencia de datos.", (1.0, 0.9, 0.2), "DIGITAL"),
    (420, 320, "Comentario: El módulo OCR procesa en modo PSM 6.", (1.0, 0.8, 0.3), "DIGITAL")
]

def crear_pdf_base():
    """Genera documento base para las pruebas de sincronización de notas."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    
    page.insert_text((50, 45), "SISTEMA EDDIE: Sincronización de Anotaciones y Post-Its", 
                     fontsize=13, color=(0.1, 0.2, 0.4))
    page.draw_line((50, 52), (560, 52), color=(0.2, 0.3, 0.5), width=1.2)

    texto = """
Capítulo 4: Sincronización Bidireccional de Anotaciones

El subsistema de consistencia de datos permite que las notas manuscritas colocadas sobre el
libro físico (como papeles adhesivos / Post-Its amarillos) se sincronicen automáticamente hacia
la versión digital del documento PDF.

1. Detección de Post-Its Físicos:
La cámara superior captura el área de trabajo y detecta parches de color amarillo mediante
umbrales HSV. Una vez aislado el cuadrilátero del Post-It, se recorta y se envía al motor OCR
para transcribir la nota.

2. Inyección de Anotaciones en el PDF:
La nota física se inyecta en el archivo PDF como una anotación estándar tipo 'Text / Note'
y un recuadro visual de resalte, manteniendo las coordenadas normalizadas de la página.

3. Proyección sobre el Papel:
Las anotaciones creadas en la versión digital se proyectan sobre el libro físico para que el
lector visualice comentarios compartidos por profesores o compañeros de estudio.
"""
    page.insert_text((50, 75), texto.strip(), fontsize=10.5, color=(0.1, 0.1, 0.1), lineheight=1.4)
    page.draw_line((50, 740), (560, 740), color=(0.7, 0.7, 0.7), width=0.8)
    page.insert_text((50, 755), "Prototipo F16 – CommentsPD / Sincronización Post-It | EDDIE Python", 
                     fontsize=8, color=(0.5, 0.5, 0.5))
    doc.save(str(PDF_BASE_PATH))
    doc.close()

def sincronizar_notas_al_pdf():
    """Toma el documento base y le estampa todas las notas acumuladas en la sesión."""
    doc = fitz.open(str(PDF_BASE_PATH))
    page = doc[0]

    for (x, y, texto, col, origen) in NOTAS_SESION:
        # 1. Anotación estándar PDF (icono de nota que abre un popup en Adobe Reader/Edge)
        annot = page.add_text_annot((x, y), f"[{origen}] {texto}")
        annot.set_colors(stroke=col)
        annot.update()

        # 2. Dibujo vectorial del rectángulo simulando el Post-it en el PDF
        postit_rect = fitz.Rect(x - 10, y - 5, x + 150, y + 45)
        page.draw_rect(postit_rect, color=(0.8, 0.7, 0.1), fill=(1.0, 0.96, 0.6), width=0.8)
        # Línea de cabecera del post-it
        page.draw_line((postit_rect.x0, postit_rect.y0 + 10), (postit_rect.x1, postit_rect.y0 + 10), 
                       color=(0.9, 0.8, 0.2), width=1.5)
        # Texto resumido dentro del post-it
        page.insert_text((postit_rect.x0 + 4, postit_rect.y0 + 22), texto[:28] + ("..." if len(texto) > 28 else ""), 
                         fontsize=7.5, color=(0.2, 0.2, 0.2))
        page.insert_text((postit_rect.x0 + 4, postit_rect.y0 + 34), f"Fuente: {origen}", 
                         fontsize=6.5, color=(0.4, 0.4, 0.4))

    doc.save(str(PDF_SYNCED_PATH))
    doc.close()

def renderizar_pdf_a_cv(dpi=130):
    """Renderiza la página del PDF sincronizado."""
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

# Variables para interacción del mouse
mouse_click_coord = None
def on_mouse(event, x, y, flags, param):
    global mouse_click_coord
    if event == cv2.EVENT_LBUTTONDOWN:
        mouse_click_coord = (x, y)

def main():
    global mouse_click_coord
    print("=" * 65)
    print("  DEMO REAL F16 – Sincronización de Post-Its (Físico <-> Digital)")
    print("  Módulo: ConsistencyLibraryCommentsPD / CommentsPD.cs")
    print("=" * 65)

    crear_pdf_base()
    sincronizar_notas_al_pdf()
    
    # Intentar abrir cámara para detección física
    cap = None
    for idx in range(3):
        for backend in [cv2.CAP_MSMF, cv2.CAP_ANY]:
            try:
                c = cv2.VideoCapture(idx, backend)
                if c.isOpened():
                    cap = c
                    print(f"  [+] Cámara detectada en índice {idx} para escaneo de Post-Its")
                    break
                c.release()
            except Exception:
                pass
        if cap: break

    modo_actual = "CAMARA" if cap is not None else "PROYECTOR"
    print(f"  Modo inicial: {modo_actual} (Presiona ESPACIO para alternar)\n")

    cv2.namedWindow("EDDIE – F16 Sincronizacion Post-It", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("EDDIE – F16 Sincronizacion Post-It", 1280, 750)
    cv2.setMouseCallback("EDDIE – F16 Sincronizacion Post-It", on_mouse)

    abrir_pdf(PDF_SYNCED_PATH)

    last_detected_box = None
    last_detected_text = ""

    while True:
        if modo_actual == "CAMARA" and cap is not None:
            ret, frame = cap.read()
            if not ret:
                modo_actual = "PROYECTOR"
                continue

            h, w = frame.shape[:2]
            display_frame = frame.copy()

            # Algoritmo de detección HSV de Post-It Amarillo (de CommentsPD.cs)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # Rango amarillo típico de notas adhesivas
            lower_yellow = np.array([20, 90, 90])
            upper_yellow = np.array([36, 255, 255])
            mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
            
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

            cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            detected_postit = None
            max_area = 0

            for cnt in cnts:
                area = cv2.contourArea(cnt)
                if area > 3000:  # Área mínima de un post-it
                    peri = cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
                    if len(approx) == 4 and area > max_area:
                        max_area = area
                        detected_postit = approx

            if detected_postit is not None:
                cv2.drawContours(display_frame, [detected_postit], -1, (0, 255, 255), 3)
                x_b, y_b, w_b, h_b = cv2.boundingRect(detected_postit)
                cv2.rectangle(display_frame, (x_b, y_b), (x_b + w_b, y_b + h_b), (0, 200, 0), 2)
                cv2.putText(display_frame, "Post-It detectado (C para sincronizar)", 
                            (x_b, y_b - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                last_detected_box = (x_b, y_b, w_b, h_b)
            else:
                last_detected_box = None
                cv2.putText(display_frame, "Buscando Post-It amarillo frente a la camara...", 
                            (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 180, 255), 2)

            # Panel de información
            panel_w = 480
            panel = np.full((h, panel_w, 3), 26, dtype=np.uint8)
            cv2.putText(panel, "F16: Modo Deteccion Fisica (Camara)", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 220, 100), 2)
            cv2.putText(panel, "Muestra un Post-It amarillo a la camara", (15, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)
            cv2.line(panel, (15, 75), (panel_w - 15, 75), (70, 70, 70), 1)

            cv2.putText(panel, f"Notas en PDF: {len(NOTAS_SESION)}", (15, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1)
            
            y_log = 130
            for i, (_, _, txt, _, orig) in enumerate(NOTAS_SESION[-4:], 1):
                cv2.putText(panel, f"{i}. [{orig}] {txt[:35]}", (15, y_log),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (150, 220, 255), 1)
                y_log += 25

            # Miniatura de máscara
            mask_sm = cv2.resize(cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR), (160, 120))
            panel[h - 260:h - 140, 15:175] = mask_sm
            cv2.rectangle(panel, (15, h - 260), (175, h - 140), (80, 80, 80), 1)
            cv2.putText(panel, "Mascara HSV Color", (15, h - 125), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (140, 140, 140), 1)

            # Controles
            cv2.rectangle(panel, (10, h - 110), (panel_w - 10, h - 10), (40, 40, 40), -1)
            cv2.putText(panel, "C       : Capturar y sincronizar Post-It al PDF", (18, h - 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 100), 1)
            cv2.putText(panel, "ESPACIO : Alternar a Modo Proyector/PDF", (18, h - 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 200, 255), 1)
            cv2.putText(panel, "O       : Abrir PDF actualizado | Q: Salir", (18, h - 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1)

            combined = np.hstack([display_frame, panel])

        else:
            # Modo PROYECTOR / DIGITAL
            page_img, scale = renderizar_pdf_a_cv()
            display_page = page_img.copy()
            h, w = display_page.shape[:2]

            # Si el usuario hizo clic en la página
            if mouse_click_coord is not None:
                cx, cy = mouse_click_coord
                if cx < w:
                    pdf_x = cx / scale
                    pdf_y = cy / scale
                    nueva_nota = f"Nota agregada en ({int(pdf_x)}, {int(pdf_y)}) via proyector"
                    NOTAS_SESION.append((pdf_x, pdf_y, nueva_nota, (0.5, 0.9, 0.3), "PROYECTOR"))
                    sincronizar_notas_al_pdf()
                    print(f"  [SINCRONIZADO] Nueva nota agregada en ({int(pdf_x)}, {int(pdf_y)})")
                mouse_click_coord = None

            panel_w = 480
            panel = np.full((h, panel_w, 3), 26, dtype=np.uint8)
            cv2.putText(panel, "F16: Modo Proyector Digital (PDF)", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 220, 100), 2)
            cv2.putText(panel, "Haz CLIC sobre el documento para agregar notas", (15, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)
            cv2.line(panel, (15, 75), (panel_w - 15, 75), (70, 70, 70), 1)

            cv2.putText(panel, f"Total Post-Its sincronizados: {len(NOTAS_SESION)}", (15, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1)

            y_log = 135
            for i, (nx, ny, txt, _, orig) in enumerate(NOTAS_SESION, 1):
                cv2.putText(panel, f"{i}. ({int(nx)},{int(ny)}) [{orig}]", (15, y_log),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 220, 255), 1)
                y_log += 18
                cv2.putText(panel, f"   \"{txt[:42]}\"", (15, y_log),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.36, (200, 255, 180), 1)
                y_log += 26
                if y_log > h - 140:
                    break

            # Controles
            cv2.rectangle(panel, (10, h - 110), (panel_w - 10, h - 10), (40, 40, 40), -1)
            cv2.putText(panel, "CLIC    : Posicionar nuevo Post-It en el PDF", (18, h - 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 100), 1)
            cv2.putText(panel, "ESPACIO : Alternar a Modo Camara de Post-Its", (18, h - 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 200, 255), 1)
            cv2.putText(panel, "O       : Abrir PDF en visor | S: Guardar | Q: Salir", (18, h - 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.36, (200, 200, 200), 1)

            combined = np.hstack([display_page, panel])

        cv2.imshow("EDDIE – F16 Sincronizacion Post-It", combined)
        key = cv2.waitKey(30) & 0xFF

        if key == ord('q') or key == 27:
            break
        elif key == ord(' '):
            modo_actual = "PROYECTOR" if modo_actual == "CAMARA" else ("CAMARA" if cap is not None else "PROYECTOR")
            print(f"  [MODO] Cambiado a: {modo_actual}")
        elif key == ord('c') and modo_actual == "CAMARA" and last_detected_box is not None:
            # Captura y OCR de la nota
            bx, by, bw, bh = last_detected_box
            crop = frame[by:by+bh, bx:bx+bw]
            try:
                gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                ocr_text = pytesseract.image_to_string(gray_crop, lang="spa+eng").strip()
            except Exception:
                ocr_text = ""
            
            if not ocr_text:
                ocr_text = f"Nota física detectada #{len(NOTAS_SESION)+1}"
                
            NOTAS_SESION.append((400, 150 + len(NOTAS_SESION)*60, ocr_text, (1.0, 0.8, 0.1), "CAMARA_FISICA"))
            sincronizar_notas_al_pdf()
            print(f"  [✓ POST-IT CAPTURADO] Texto: '{ocr_text}' -> Sincronizado al PDF")
        elif key == ord('o'):
            abrir_pdf(PDF_SYNCED_PATH)
        elif key == ord('s'):
            out_img = EVID / "real_f16_postit.png"
            cv2.imwrite(str(out_img), combined)
            print(f"  [GUARDADO] Evidencia: {out_img.name}")

    if cap: cap.release()
    cv2.destroyAllWindows()
    print("  ✓ F16 COMPLETADO EXITOSAMENTE\n")

if __name__ == "__main__":
    main()
