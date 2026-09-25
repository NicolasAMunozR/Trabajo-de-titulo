"""
Prototipo F06 Hand/Skin Segmentation mejorada
Muestra en tiempo real la segmentación de piel (mano)
usando YCrCb + HSV combinados con filtros más robustos.

S = guardar  |  Q = salir
"""

import cv2
import pathlib
import sys
import numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

print("  S = guardar  |  Q = salir\n")

cap = None
for idx in range(10):
    for backend in [cv2.CAP_MSMF, cv2.CAP_ANY]:
        try:
            c = cv2.VideoCapture(idx, backend)
            if c.isOpened():
                cap = c
                print(f"Cámara idx={idx}")
                break
            c.release()
        except Exception:
            pass
    if cap:
        break

if not cap:
    print("No se encontró cámara.")
    sys.exit(1)

k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))


def get_skin_mask(frame):
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    mask_y = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask_h = cv2.inRange(hsv, np.array([0, 20, 50]), np.array([30, 255, 255]))

    mask = cv2.bitwise_and(mask_y, mask_h)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k_close, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k_open, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filtered = np.zeros_like(mask)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 500:
            cv2.drawContours(filtered, [cnt], -1, 255, -1)

    return filtered


while True:
    ret, frame = cap.read()
    if not ret:
        break

    result = frame.copy()
    mask = get_skin_mask(frame)
    mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    n_fingers = 0
    if contours:
        big = []
        for c in contours:
            area = cv2.contourArea(c)
            if area > 2500:
                big.append(c)

        if big:
            best = max(big, key=cv2.contourArea)
            area_best = cv2.contourArea(best)

            hull = cv2.convexHull(best)
            cv2.drawContours(result, [best], -1, (0, 220, 80), 2)
            cv2.drawContours(result, [hull], -1, (0, 180, 255), 1)

            x, y, w_box, h_box = cv2.boundingRect(best)
            cv2.rectangle(result, (x, y), (x + w_box, y + h_box), (255, 200, 0), 1)

            area_pct = area_best / (frame.shape[0] * frame.shape[1]) * 100

            hull_points = cv2.convexHull(best, returnPoints=False)
            defects = cv2.convexityDefects(best, hull_points)

            if defects is not None:
                for i in range(defects.shape[0]):
                    defect = defects[i]

                    if defect.shape == (4,):
                        s, e, f, d = defect
                    elif defect.shape == (1, 4):
                        s, e, f, d = defect[0]
                    else:
                        continue

                    if d > 2000:
                        start = tuple(best[s][0])
                        far = tuple(best[f][0])

                        if np.linalg.norm(np.array(start) - np.array(far)) > 25:
                            cv2.circle(result, far, 5, (0, 0, 255), -1)
                            n_fingers += 1

            cv2.putText(
                result,
                f"Mano: {area_pct:.1f}% | Dedos estimados: {n_fingers}",
                (x, max(0, y - 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 200, 80),
                2,
            )

    mask_small = cv2.resize(mask_color, (220, 160))
    result[10:10 + mask_small.shape[0], 10:10 + mask_small.shape[1]] = mask_small
    cv2.putText(
        result,
        "Mascara piel",
        (18, 20 + mask_small.shape[0] + 16),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (180, 180, 180),
        1,
    )

    cv2.putText(
        result,
        "F06 | Segmentacion YCrCb + HSV",
        (8, result.shape[0] - 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 220, 100),
        2,
    )
    cv2.putText(
        result,
        "S=guardar  Q=salir",
        (8, result.shape[0] - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        (200, 200, 200),
        1,
    )

    cv2.imshow("F06 Skin Segmentation", result)

    key = cv2.waitKey(30) & 0xFF
    if key == ord('q') or key == 27:
        break
    elif key == ord('s'):
        out = EVID / "f06_handskin.png"
        cv2.imwrite(str(out), result)
        print(f"[GUARDADO] {out}")

cap.release()
cv2.destroyAllWindows()
print("F06 COMPLETADO\n")