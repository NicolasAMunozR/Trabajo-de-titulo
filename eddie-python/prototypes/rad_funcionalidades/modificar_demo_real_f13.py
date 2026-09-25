"""
DEMO REAL F13 – Retículo de Gaze + Overlay en Proyección
==========================================================
Abre una ventana que simula la superficie proyectada (libro).
El ratón actúa como el gaze del eye tracker.
El retículo sigue el cursor en tiempo real, resaltando
la línea de texto más cercana.

Mueve el ratón por el texto.
S = guardar  |  Q = salir
"""
import cv2, pathlib, time
import numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

print("="*55)
print("  DEMO REAL F13 – Retículo de Gaze Overlay")
print("="*55)
print("  Mueve el ratón para mover el retículo de gaze")
print("  S = guardar  |  Q = salir\n")

W, H = 950, 620
mouse_pos = [W//2, H//2]
history   = []

def on_mouse(event, x, y, flags, param):
    mouse_pos[0] = x
    mouse_pos[1] = y
    history.append((x, y, time.time()))

# Simular página proyectada
lines = [
    "SISTEMA EDDIE – Lectura Aumentada",
    "",
    "Capítulo 1: Introducción",
    "Este sistema asiste la lectura combinando cámara,",
    "eye tracking y reconocimiento óptico de caracteres.",
    "",
    "Capítulo 2: Arquitectura",
    "EDDIE utiliza un diseño modular basado en plugins.",
    "Cada módulo se carga dinámicamente con importlib.",
    "",
    "Capítulo 3: Hardware",
    "Se requiere una cámara web estándar (o DroidCam).",
    "El eye tracker conecta vía socket TCP en puerto 9877.",
]
line_ys = [50 + i*42 for i in range(len(lines))]

cv2.namedWindow("EDDIE – F13 Retículo Gaze Overlay")
cv2.setMouseCallback("EDDIE – F13 Retículo Gaze Overlay", on_mouse)

while True:
    # Fondo tipo página
    canvas = np.full((H, W, 3), 240, np.uint8)
    cv2.rectangle(canvas,(20,20),(W-20,H-20),(220,218,210),-1)
    cv2.rectangle(canvas,(20,20),(W-20,H-20),(180,175,170),2)

    mx, my = mouse_pos

    # Línea más cercana
    text_ys = [y for y,t in zip(line_ys,lines) if t]
    if text_ys:
        closest_y = min(text_ys, key=lambda y: abs(y-my))
        closest_i = line_ys.index(closest_y)

        # Highlight de línea
        ov = canvas.copy()
        cv2.rectangle(ov,(25, closest_y-26),(W-25, closest_y+8),(0,200,220),-1)
        canvas = cv2.addWeighted(ov, 0.2, canvas, 0.8, 0)

    # Dibujar texto
    for y, t in zip(line_ys, lines):
        if not t: continue
        size = 0.7 if "Capítulo" in t or "SISTEMA" in t else 0.55
        col  = (20,20,80) if "Capítulo" in t or "SISTEMA" in t else (30,30,30)
        weight = 2 if "Capítulo" in t or "SISTEMA" in t else 1
        cv2.putText(canvas, t, (40, y), cv2.FONT_HERSHEY_SIMPLEX, size, col, weight)

    # Retículo de gaze
    OUTER  = 28
    INNER  = 7
    GAP    = 12
    CROSS  = 40
    col_r  = (0, 200, 220)

    cv2.circle(canvas, (mx,my), OUTER, col_r, 2)
    cv2.circle(canvas, (mx,my), INNER, col_r, -1)
    # Cruz
    cv2.line(canvas,(mx-CROSS,my),(mx-GAP,my),col_r,2)
    cv2.line(canvas,(mx+GAP,my),(mx+CROSS,my),col_r,2)
    cv2.line(canvas,(mx,my-CROSS),(mx,my-GAP),col_r,2)
    cv2.line(canvas,(mx,my+GAP),(mx,my+CROSS),col_r,2)

    # Coordenadas
    cv2.putText(canvas,f"Gaze ({mx},{my})",(mx+32,my-12),
                cv2.FONT_HERSHEY_SIMPLEX,0.42,col_r,1)

    # HUD
    cv2.rectangle(canvas,(0,H-45),(W,H),(30,30,30),-1)
    cv2.putText(canvas,f"F13 | Retículo en ({mx},{my}) | Muestras: {len(history)}",
                (8,H-25),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,220,100),1)
    cv2.putText(canvas,"S=guardar  Q=salir",
                (8,H-8),cv2.FONT_HERSHEY_SIMPLEX,0.38,(150,150,150),1)

    cv2.imshow("EDDIE – F13 Retículo Gaze Overlay", canvas)
    key = cv2.waitKey(16) & 0xFF
    if key == ord('q') or key == 27: break
    elif key == ord('s'):
        out = EVID/"real_f13_reticulo.png"
        cv2.imwrite(str(out), canvas)
        print(f"  [GUARDADO] {out}")

cv2.destroyAllWindows()
print("  F13 COMPLETADO\n")
