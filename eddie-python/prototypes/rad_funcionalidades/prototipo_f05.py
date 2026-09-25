"""
Prototipo F05 Color Pen Tracking
Detecta un objeto de color (por defecto: rojo).
Muestra el centroide y la trayectoria del objeto en la cámara.
  R = detectar ROJO  |  G = detectar VERDE  |  B = detectar AZUL
  S = guardar frame  |  Q = salir
"""
import cv2, pathlib, sys, collections
import numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

# Rangos HSV por color
COLOR_RANGES = {
    "ROJO":  [(np.array([0,120,70]),   np.array([10,255,255])),
               (np.array([170,120,70]),np.array([180,255,255]))],
    "VERDE": [(np.array([40,80,60]),   np.array([80,255,255]))],
    "AZUL":  [(np.array([100,100,50]), np.array([130,255,255]))],
}
COLOR_DISPLAY = {"ROJO":(0,0,220), "VERDE":(0,200,0), "AZUL":(200,80,0)}

print("  R=Rojo  G=Verde  B=Azul  S=guardar  Q=salir\n")

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

current_color = "ROJO"
trail = collections.deque(maxlen=60)  # últimas 60 posiciones

while True:
    ret, frame = cap.read()
    if not ret: break

    hsv   = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask  = np.zeros(frame.shape[:2], dtype=np.uint8)
    for (lo, hi) in COLOR_RANGES[current_color]:
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lo, hi))

    # Morfología para limpiar ruido
    k    = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9,9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  k, iterations=1)

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cx = cy = None
    if cnts:
        c_max = max(cnts, key=cv2.contourArea)
        if cv2.contourArea(c_max) > 200:
            M = cv2.moments(c_max)
            if M["m00"] > 0:
                cx = int(M["m10"]/M["m00"])
                cy = int(M["m01"]/M["m00"])
                trail.append((cx, cy))

    result = frame.copy()
    col    = COLOR_DISPLAY[current_color]

    # Dibujar trayectoria
    for i in range(1, len(trail)):
        if trail[i-1] and trail[i]:
            thickness = max(1, int(3 * i / len(trail)))
            cv2.line(result, trail[i-1], trail[i], col, thickness)

    # Dibujar centroide actual
    if cx is not None:
        cv2.circle(result, (cx,cy), 18, col, 3)
        cv2.circle(result, (cx,cy), 5, col, -1)
        cv2.putText(result, f"({cx},{cy})", (cx+22, cy-8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 2)

    # Máscara en esquina
    mask_sm = cv2.resize(mask, (160, 90))
    mask_bgr = cv2.cvtColor(mask_sm, cv2.COLOR_GRAY2BGR)
    result[8:98, result.shape[1]-168:result.shape[1]-8] = mask_bgr
    cv2.putText(result,"Mascara HSV",(result.shape[1]-165,108),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35,(120,120,120),1)

    # HUD
    cv2.putText(result, f"F05 | Detectando: {current_color}",
                (8,28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, col, 2)
    cv2.putText(result, "R=Rojo G=Verde B=Azul  S=guardar Q=salir",
                (8, result.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.42,(200,200,200),1)

    cv2.imshow("F05 Color Pen Tracking", result)
    key = cv2.waitKey(30) & 0xFF
    if key == ord('q') or key == 27: break
    elif key == ord('r'): current_color="ROJO";  trail.clear()
    elif key == ord('g'): current_color="VERDE"; trail.clear()
    elif key == ord('b'): current_color="AZUL";  trail.clear()
    elif key == ord('s'):
        out = EVID/"f05_colorpen.png"
        cv2.imwrite(str(out), result)
        print(f"[GUARDADO] {out}")

cap.release(); cv2.destroyAllWindows()
print("F05 COMPLETADO\n")
