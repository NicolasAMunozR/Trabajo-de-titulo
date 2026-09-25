"""
Prototipo F02 Preprocesamiento y Binarización
Captura un frame REAL de DroidCam y muestra en tiempo real:
  - Ventana izquierda: frame original de la cámara
  - Ventana derecha:   frame binarizado (Otsu) en tiempo real
Apunta la cámara a un texto impreso (libro, hoja, etc.)
Presiona S para guardar evidencia, Q para salir.
"""
import cv2, time, pathlib, sys
import numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

print("  S = guardar  |  Q = salir\n")

# Abrir cámara
cap = None
for idx in range(5):
    for backend in [cv2.CAP_MSMF, cv2.CAP_ANY]:
        try:
            c = cv2.VideoCapture(idx, backend)
            if c.isOpened():
                cap = c
                print(f"Cámara abierta: idx={idx}")
                break
            c.release()
        except Exception:
            pass
    if cap: break

if not cap:
    print("No se encontró cámara.")
    sys.exit(1)

t_start = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Pipeline F02
    gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, bw   = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bw_bgr  = cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)

    # Labels
    cv2.putText(frame, "ORIGINAL (BGR)", (8, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 100), 2)
    cv2.putText(bw_bgr, "BINARIZADO Otsu", (8, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (100, 100, 255), 2)

    # Side by side
    combined = np.hstack([frame, np.full((frame.shape[0], 4, 3), 80, np.uint8), bw_bgr])
    cv2.putText(combined, "EDDIE F02 | S=guardar Q=salir",
                (8, combined.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)

    cv2.imshow("F02 Binarización", combined)

    key = cv2.waitKey(30) & 0xFF
    if key == ord('q') or key == 27:
        break
    if key == ord('s'):
        out = EVID / "f02_binarizacion.png"
        cv2.imwrite(str(out), combined)
        print(f"  [GUARDADO] {out}")
        cv2.putText(combined, "GUARDADO!", (combined.shape[1]//2 - 60, combined.shape[0]//2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        cv2.imshow("F02 Binarización", combined)
        cv2.waitKey(1000)

cap.release()
cv2.destroyAllWindows()
print("F02 COMPLETADO\n")
