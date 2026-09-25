"""
Prototipo F09 Mouse como fallback de Gaze
Abre una ventana de proyección. El ratón actúa como sustituto
del eye tracker. Se registra la posición y se dibuja
un retículo siguiendo el cursor en tiempo real.

Mueve el ratón por la ventana para simular el gaze.
S = guardar  |  Q = salir
"""
import cv2, pathlib, collections, time
import numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

print("="*55)
print("  PROTOTIPO F09 – Mouse Fallback como Gaze")
print("="*55)
print("  Mueve el ratón por la ventana")
print("  S = guardar  |  Q = salir\n")

mouse_pos = [0, 0]
trail = collections.deque(maxlen=80)
events_log = []

def on_mouse(event, x, y, flags, param):
    mouse_pos[0] = x
    mouse_pos[1] = y
    trail.append((x, y, time.time()))
    if event == cv2.EVENT_LBUTTONDOWN:
        events_log.append({"type":"CLICK","x":x,"y":y,"ts":time.time()})
        print(f"  Click en ({x},{y})")

W, H = 900, 600
# Simular página de libro
page_bg = np.full((H, W, 3), 248, np.uint8)
lines_text = [
    "Sistema EDDIE Lectura Aumentada",
    "El sistema procesa documentos PDF mediante OCR.",
    "La cámara detecta el libro y extrae el texto.",
    "El eye tracker determina qué línea está leyendo",
    "el usuario en tiempo real.",
    "El módulo de gestos permite interactuar sin tocar.",
    "Las definiciones de palabras se consultan online.",
    "F09: cuando no hay eye tracker, se usa el ratón.",
]
line_ys = [80 + i*55 for i in range(len(lines_text))]
for y, t in zip(line_ys, lines_text):
    cv2.putText(page_bg, t, (40, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30,30,30), 1)

cv2.namedWindow("F09 Mouse Fallback")
cv2.setMouseCallback("F09 Mouse Fallback", on_mouse)

t_start = time.time()

while True:
    canvas = page_bg.copy()

    mx, my = mouse_pos

    # Detectar línea más cercana
    closest_line = min(range(len(line_ys)), key=lambda i: abs(line_ys[i]-my))
    # Resaltar línea activa
    ly = line_ys[closest_line]
    overlay = canvas.copy()
    cv2.rectangle(overlay, (30, ly-22), (W-30, ly+8), (0,220,220), -1)
    canvas = cv2.addWeighted(overlay, 0.25, canvas, 0.75, 0)
    for y, t in zip(line_ys, lines_text):
        cv2.putText(canvas, t, (40, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30,30,30), 1)

    # Trayectoria del ratón
    pts = [(p[0],p[1]) for p in trail]
    for i in range(1, len(pts)):
        alpha = i / len(pts)
        col = (int(180*alpha), int(80*alpha), int(200*(1-alpha)))
        cv2.line(canvas, pts[i-1], pts[i], col, 2)

    # Retículo
    cv2.circle(canvas, (mx,my), 22, (0,180,220), 2)
    cv2.circle(canvas, (mx,my), 5,  (0,180,220), -1)
    cv2.line(canvas, (mx-38,my),(mx-24,my),(0,180,220),2)
    cv2.line(canvas, (mx+24,my),(mx+38,my),(0,180,220),2)
    cv2.line(canvas, (mx,my-38),(mx,my-24),(0,180,220),2)
    cv2.line(canvas, (mx,my+24),(mx,my+38),(0,180,220),2)

    # HUD
    elapsed = time.time()-t_start
    cv2.putText(canvas, f"F09 | Gaze(mouse): ({mx},{my}) | t={elapsed:.1f}s | clicks={len(events_log)}",
                (8, H-10), cv2.FONT_HERSHEY_SIMPLEX, 0.45,(80,80,80),1)
    cv2.putText(canvas, f"Leyendo: '{lines_text[closest_line][:40]}'",
                (8, H-28), cv2.FONT_HERSHEY_SIMPLEX, 0.42,(0,130,0),1)

    cv2.imshow("F09 Mouse Fallback", canvas)
    key = cv2.waitKey(16) & 0xFF
    if key == ord('q') or key == 27: break
    elif key == ord('s'):
        out = EVID/"f09_mouse.png"
        cv2.imwrite(str(out), canvas)
        print(f"[GUARDADO] {out}")

cv2.destroyAllWindows()
print(f"Total eventos registrados: {len(events_log)}")
print("F09 COMPLETADO\n")
