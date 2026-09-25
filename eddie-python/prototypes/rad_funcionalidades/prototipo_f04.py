"""
Prototipo F04 Detección de Página/Libro
Captura frames de DroidCam y detecta en tiempo real
el rectángulo del libro/hoja más grande en la imagen.
Dibuja el contorno verde sobre el objeto detectado.
Apunta la cámara a un libro o hoja sobre fondo oscuro.
S = guardar  |  Q = salir
"""
import cv2, pathlib, sys
import numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

print("  S = guardar  |  Q = salir\n")

cap = None
for idx in range(5):
    for backend in [cv2.CAP_MSMF, cv2.CAP_ANY]:
        try:
            c = cv2.VideoCapture(idx, backend)
            if c.isOpened():
                cap = c
                print(f"Cámara: idx={idx}")
                break
            c.release()
        except Exception:
            pass
    if cap: break

if not cap:
    print("No se encontró cámara.")
    sys.exit(1)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    result = frame.copy()
    gray   = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur   = cv2.GaussianBlur(gray, (7, 7), 0)
    edges  = cv2.Canny(blur, 30, 120)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    edges  = cv2.dilate(edges, kernel, iterations=1)

    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected_area = 0
    detected_pts  = None
    total_area    = frame.shape[0] * frame.shape[1]

    for cnt in cnts:
        area = cv2.contourArea(cnt)
        if area < total_area * 0.05:   # ignorar contornos pequeños
            continue
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4 and area > detected_area:
            detected_area = area
            detected_pts  = approx

    if detected_pts is not None:
        cv2.drawContours(result, [detected_pts], -1, (0, 220, 80), 3)
        rect = cv2.boundingRect(detected_pts)
        pct  = detected_area / total_area * 100
        cv2.putText(result, f"Pagina detectada! Area={pct:.1f}%",
                    (rect[0]+5, rect[1]-10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 220, 80), 2)
    else:
        cv2.putText(result, "Buscando página/libro...", (8, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 180, 255), 2)

    # Mostrar mapa de bordes pequeño en esquina
    edges_sm = cv2.cvtColor(cv2.resize(edges, (160, 90)), cv2.COLOR_GRAY2BGR)
    result[10:100, result.shape[1]-170:result.shape[1]-10] = edges_sm
    cv2.rectangle(result, (result.shape[1]-170, 10), (result.shape[1]-10, 100), (80,80,80), 1)
    cv2.putText(result, "Canny", (result.shape[1]-165, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120,120,120), 1)

    cv2.putText(result, "S=guardar  Q=salir",
                (8, result.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200,200,200), 1)
    cv2.imshow("F04 Detección de Página", result)

    key = cv2.waitKey(30) & 0xFF
    if key == ord('q') or key == 27:
        break
    if key == ord('s'):
        out = EVID / "f04_pagina.png"
        cv2.imwrite(str(out), result)
        print(f"[GUARDADO] {out}")

cap.release()
cv2.destroyAllWindows()
print("F04 COMPLETADO\n")
