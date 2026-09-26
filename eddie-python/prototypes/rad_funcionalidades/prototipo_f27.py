"""
Prototipo F27 Highlight Digital sobre cámara (proyección)
=============================================================
Captura frames. Cuando el ratón
se detiene sobre una línea de texto, EDDIE proyecta una
banda de highlight semitransparente sobre esa zona.

Simula lo que se vería proyectado sobre el libro físico.
Mueve el ratón por la ventana para cambiar la línea resaltada.
S = guardar  |  Q = salir
"""
import cv2, pathlib, time, sys
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
                cap = c; print(f"Cámara idx={idx}"); break
            c.release()
        except Exception: pass
    if cap: break

if not cap:
    print("Sin cámara."); sys.exit(1)

mouse_y = [240]

def on_mouse(event, x, y, flags, param):
    mouse_y[0] = y

cv2.namedWindow("F27 Highlight Digital")
cv2.setMouseCallback("F27 Highlight Digital", on_mouse)

HIGHLIGHT_H  = 32   # altura de la banda en px
COLORS = [
    (0, 220, 220),   # cyan (línea actual)
    (0, 200, 80),    # verde (zona leída)
    (200, 180, 0),   # amarillo (zona previa)
]

history_lines = []   # líneas ya leídas (y_center)

while True:
    ret, frame = cap.read()
    if not ret: break

    h, w = frame.shape[:2]
    my   = mouse_y[0]

    result = frame.copy()

    # Snap a línea más cercana (cada 40px simula línea de texto)
    LINE_STEP = int(h / 10)
    snap_y    = round(my / LINE_STEP) * LINE_STEP
    snap_y    = max(HIGHLIGHT_H//2, min(h-HIGHLIGHT_H//2, snap_y))

    # Dibujar líneas previas (en verde, tenue)
    for prev_y in history_lines[-5:]:
        overlay = result.copy()
        cv2.rectangle(overlay, (0, prev_y-HIGHLIGHT_H//2),
                      (w, prev_y+HIGHLIGHT_H//2), COLORS[1], -1)
        result = cv2.addWeighted(overlay, 0.10, result, 0.90, 0)

    # Dibujar highlight activo (cyan)
    overlay = result.copy()
    cv2.rectangle(overlay, (0, snap_y-HIGHLIGHT_H//2),
                  (w, snap_y+HIGHLIGHT_H//2), COLORS[0], -1)
    result = cv2.addWeighted(overlay, 0.30, result, 0.70, 0)

    # Borde del highlight
    cv2.rectangle(result, (0, snap_y-HIGHLIGHT_H//2),
                  (w, snap_y+HIGHLIGHT_H//2), COLORS[0], 2)

    # HUD
    cv2.putText(result, "F27 EDDIE Highlight Digital",
                (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,220,100), 2)
    cv2.putText(result, f"Gaze y={snap_y} Líneas resaltadas: {len(set(history_lines))}",
                (8, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200,200,200), 1)
    cv2.putText(result, "Mueve el ratón para cambiar línea S=guardar Q=salir",
                (8, h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180,180,180), 1)

    # Registro de historial
    if not history_lines or abs(history_lines[-1]-snap_y) > LINE_STEP//2:
        history_lines.append(snap_y)

    cv2.imshow("F27 Highlight Digital", result)
    key = cv2.waitKey(30) & 0xFF
    if key == ord('q') or key == 27: break
    elif key == ord('s'):
        out = EVID/"f27_highlight.png"
        cv2.imwrite(str(out), result)
        print(f"  [GUARDADO] {out}")

cap.release()
cv2.destroyAllWindows()
print(f"Total líneas resaltadas: {len(set(history_lines))}")
print("F27 COMPLETADO\n")
