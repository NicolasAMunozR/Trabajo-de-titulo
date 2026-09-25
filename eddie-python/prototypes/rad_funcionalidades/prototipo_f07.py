"""
Prototipo F07 Homografía
Usa la cámara en vivo. El usuario hace CLIC en 4 esquinas
de la hoja/libro para definir el plano de referencia.
EDDIE calcula la homografía y muestra la vista "rectificada"
(como si la cámara mirara de frente a la hoja).

R = reiniciar puntos  |  S = guardar  |  Q = salir
"""
import cv2, pathlib, sys
import numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

print("  R=reiniciar  S=guardar  Q=salir\n")

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

points = []
ORDER_LABELS = ["TL (sup-izq)", "TR (sup-der)", "BR (inf-der)", "BL (inf-izq)"]

def on_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
        points.append((x, y))
        print(f"  Punto {len(points)}: {ORDER_LABELS[len(points)-1]} = ({x},{y})")

cv2.namedWindow("F07 Homografía")
cv2.setMouseCallback("F07 Homografía", on_click)

frame_saved = None

while True:
    ret, frame = cap.read()
    if not ret: break

    display = frame.copy()
    H_OUT, W_OUT = 480, 640

    # Dibujar puntos seleccionados
    colors = [(0,0,255),(0,255,0),(255,0,0),(0,220,255)]
    for i, pt in enumerate(points):
        cv2.circle(display, pt, 10, colors[i], -1)
        cv2.circle(display, pt, 12, (255,255,255), 2)
        cv2.putText(display, ORDER_LABELS[i], (pt[0]+14, pt[1]+6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, colors[i], 1)

    if len(points) >= 2:
        for i in range(len(points)-1):
            cv2.line(display, points[i], points[i+1], (255,255,255), 1)
    if len(points) == 4:
        cv2.line(display, points[3], points[0], (255,255,255), 1)

    if len(points) == 4:
        src = np.float32(points)
        dst = np.float32([[0,0],[W_OUT,0],[W_OUT,H_OUT],[0,H_OUT]])
        H, _ = cv2.findHomography(src, dst, cv2.RANSAC)
        if H is not None:
            warped = cv2.warpPerspective(frame, H, (W_OUT, H_OUT))
            cv2.putText(warped, "Vista rectificada (plano hoja)",
                        (8,28), cv2.FONT_HERSHEY_SIMPLEX, 0.6,(0,220,80),2)
            cv2.putText(warped,"F07 Homografia calculada",
                        (8,52), cv2.FONT_HERSHEY_SIMPLEX, 0.45,(180,180,180),1)
            cv2.imshow("F07 Vista Rectificada", warped)
            frame_saved = warped
        cv2.putText(display,"4 puntos Homografia activa",
                    (8,28), cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,220,80),2)
    else:
        cv2.putText(display,f"Clic en esquina {len(points)+1}: {ORDER_LABELS[len(points)]}",
                    (8,28), cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,180,255),2)

    cv2.putText(display,"R=reiniciar S=guardar Q=salir",
                (8,display.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX,0.42,(200,200,200),1)
    cv2.imshow("F07 Homografía", display)

    key = cv2.waitKey(30) & 0xFF
    if key == ord('q') or key == 27: break
    elif key == ord('r'):
        points.clear()
        print("  Puntos reiniciados.")
        cv2.destroyWindow("F07 Vista Rectificada")
        frame_saved = None
    elif key == ord('s') and frame_saved is not None:
        out = EVID/"f07_homografia_rectificada.png"
        cv2.imwrite(str(out), frame_saved)
        out2= EVID/"f07_homografia_camara.png"
        cv2.imwrite(str(out2), display)
        print(f"[GUARDADO] {out}")
        print(f"[GUARDADO] {out2}")

cap.release(); cv2.destroyAllWindows()
print("F07 COMPLETADO\n")
