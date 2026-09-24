"""
Prototipo F03 OCR Tesseract sobre frame de cámara
Versión original en comportamiento:
- abre la primera cámara disponible
- muestra OCR en tiempo real sobre la imagen
- mejora el texto antes de reconocerlo

S = guardar evidencia  |  Q = salir
"""

import cv2
import numpy as np
import time
import pathlib
import pytesseract
import sys

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)


def wrap_text(text, width=32):
    """Divide el texto en líneas para que se vea completo en pantalla."""
    words = text.split()
    lines = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 <= width:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines

# Abrir la primera cámara disponible
cap = None
for idx in range(10):
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
    if cap:
        break

if not cap:
    print("No se encontró cámara.")
    sys.exit(1)

config = "--oem 3 --psm 6 -l spa+eng"
last_ocr_time = 0
ocr_text = "Buscando texto..."

# Bucle principal
while True:
    ret, frame = cap.read()
    if not ret:
        break

    now = time.time()

    # Recortar la región donde probablemente está el texto
    h, w = frame.shape[:2]
    roi = frame[int(h * 0.12):int(h * 0.88), int(w * 0.08):int(w * 0.92)]

    # Preprocesamiento para mejorar OCR
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # Binarización
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Intento de enderezar la imagen si el texto está inclinado
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    deskew = thresh

    if contours:
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area > 500:
            rect = cv2.minAreaRect(largest)
            angle = rect[-1]

            if angle < -45:
                angle = 90 + angle
            elif angle > 45:
                angle = angle - 90

            if abs(angle) > 1:
                M = cv2.getRotationMatrix2D(
                    (thresh.shape[1] / 2, thresh.shape[0] / 2),
                    angle,
                    1.0
                )
                deskew = cv2.warpAffine(
                    thresh,
                    M,
                    (thresh.shape[1], thresh.shape[0]),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )

    # Quitar ruido
    kernel = np.ones((2, 2), np.uint8)
    deskew = cv2.morphologyEx(deskew, cv2.MORPH_OPEN, kernel)

    # Aumentar resolución
    processed = cv2.resize(deskew, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Si sale vertical, rotarlo
    if processed.shape[0] > processed.shape[1]:
        processed = cv2.rotate(processed, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # OCR cada 1 segundo
    if now - last_ocr_time >= 1.0:
        try:
            raw = pytesseract.image_to_string(processed, config=config)
            ocr_text = raw.strip().replace("\n", " | ")
            print(f"  OCR: {ocr_text[:200]}")
        except Exception as e:
            ocr_text = f"[ERROR OCR: {e}]"
        last_ocr_time = now

    # Mostrar la imagen con texto en varias líneas
    cv2.putText(roi, "ROI", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(processed, "PREPROCESADO", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    # Panel derecho para mostrar el OCR completo
    panel_h, panel_w = processed.shape[:2]
    panel = np.full((panel_h, 500, 3), 25, dtype=np.uint8)

    cv2.putText(panel, "OCR TESSERACT", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 220, 100), 2)

    lines = wrap_text(ocr_text, width=38)
    for i, line in enumerate(lines[:12]):
        cv2.putText(panel, line, (10, 70 + i * 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

    combined = np.hstack([cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR), panel])
    cv2.imshow("OCR - CÁMARA", combined)

    key = cv2.waitKey(30) & 0xFF
    if key == ord('q') or key == 27:
        break
    if key == ord('s'):
        out = EVID / "f03_ocr.png"
        cv2.imwrite(str(out), combined)
        print(f"[GUARDADO] {out}")

cap.release()
cv2.destroyAllWindows()
print("F03 COMPLETADO\n")