"""
DEMO REAL F12 – Dwell Time Detection (ratón como gaze)
=======================================================
Abre una página de texto. Cuando el ratón (gaze proxy)
permanece MÁS DE 600ms en la misma zona, se activa el
evento de "dwell" y se resalta la palabra/zona.

Mueve el ratón lentamente y detente sobre una línea.
S = guardar  |  Q = salir
"""
import cv2, pathlib, time, collections
import numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

print("="*55)
print("  DEMO REAL F12 – Dwell Time Detection")
print("="*55)
print("  Detén el ratón sobre una zona por 0.6s para activar dwell")
print("  S = guardar  |  Q = salir\n")

W, H    = 900, 580
RADIUS  = 45
DWELL_T = 0.6  # segundos

mouse_pos = [W//2, H//2]
dwell_events = []
active_dwell = None
dwell_start  = None
zone_enter_pos = None

lines_text = [
    "Introducción al Sistema EDDIE",
    "EDDIE (Enhanced Digital Document Interface for Education)",
    "es un sistema de lectura aumentada diseñado para",
    "estudiantes con dificultades en lectura.",
    "Combina visión computacional con reconocimiento OCR",
    "para detectar el texto que el lector está mirando.",
    "El módulo de dwell detecta cuándo el lector se fija",
    "en una palabra o línea por un tiempo determinado.",
    "Al detectar el dwell, EDDIE puede leer en voz alta,",
    "mostrar definiciones o resaltar el texto automáticamente.",
]
line_ys = [70 + i*48 for i in range(len(lines_text))]

def on_mouse(event, x, y, flags, param):
    mouse_pos[0] = x
    mouse_pos[1] = y

cv2.namedWindow("EDDIE – F12 Dwell Time")
cv2.setMouseCallback("EDDIE – F12 Dwell Time", on_mouse)

bg = np.full((H, W, 3), 250, np.uint8)
for y, t in zip(line_ys, lines_text):
    cv2.putText(bg, t, (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (30,30,30), 1)

while True:
    canvas = bg.copy()
    mx, my = mouse_pos

    now = time.time()

    # Lógica de dwell
    if zone_enter_pos is None:
        zone_enter_pos = (mx, my)
        dwell_start    = now
    else:
        dist = np.hypot(mx - zone_enter_pos[0], my - zone_enter_pos[1])
        if dist > RADIUS:
            zone_enter_pos = (mx, my)
            dwell_start    = now
            active_dwell   = None
        else:
            elapsed_dwell = now - dwell_start
            progress = min(elapsed_dwell / DWELL_T, 1.0)

            # Arco de progreso
            center = (int(zone_enter_pos[0]), int(zone_enter_pos[1]))
            cv2.circle(canvas, center, RADIUS+4, (200,200,200), 2)
            angle = int(360 * progress)
            cv2.ellipse(canvas, center, (RADIUS+4, RADIUS+4),
                        -90, 0, angle, (0,180,255), 3)

            if progress >= 1.0 and active_dwell != zone_enter_pos:
                active_dwell = zone_enter_pos
                dwell_events.append({
                    "pos": zone_enter_pos,
                    "ts":  now,
                    "line": min(range(len(line_ys)), key=lambda i: abs(line_ys[i]-zone_enter_pos[1]))
                })
                print(f"  DWELL activado en ({zone_enter_pos[0]},{zone_enter_pos[1]}) → "
                      f"línea {dwell_events[-1]['line']+1}")

    # Mostrar highlights de dwell anteriores
    for ev in dwell_events:
        li = ev["line"]
        ly = line_ys[li]
        overlay = canvas.copy()
        cv2.rectangle(overlay, (20, ly-24), (W-20, ly+10), (0,200,100), -1)
        canvas = cv2.addWeighted(overlay, 0.25, canvas, 0.75, 0)

    # Redibujar texto
    for y, t in zip(line_ys, lines_text):
        cv2.putText(canvas, t, (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (30,30,30), 1)

    # Retículo del ratón
    cv2.circle(canvas, (mx,my), RADIUS, (180,180,180), 1)
    cv2.circle(canvas, (mx,my), 5, (0,180,255), -1)

    # HUD
    cv2.rectangle(canvas,(0,H-45),(W,H),(30,30,30),-1)
    cv2.putText(canvas,f"F12 | Dwell events: {len(dwell_events)} | Radio: {RADIUS}px | Umbral: {DWELL_T}s",
                (8,H-25),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,200,100),1)
    cv2.putText(canvas,"S=guardar  Q=salir",
                (8,H-8),cv2.FONT_HERSHEY_SIMPLEX,0.38,(150,150,150),1)

    cv2.imshow("EDDIE – F12 Dwell Time", canvas)
    key = cv2.waitKey(16) & 0xFF
    if key == ord('q') or key == 27: break
    elif key == ord('s'):
        out = EVID/"real_f12_dwell.png"
        cv2.imwrite(str(out), canvas)
        print(f"  [GUARDADO] {out}")

cv2.destroyAllWindows()
print(f"  Total dwells detectados: {len(dwell_events)}")
print("  F12 COMPLETADO\n")
