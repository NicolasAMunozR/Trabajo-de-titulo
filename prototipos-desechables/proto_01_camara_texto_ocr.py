"""
Prototipo Desechable: Captura de Cámara de Texto y OCR
------------------------------------------------------
Función EDDIE-2023: ModuloProcesamientoImagenes (CameraActivity + OCRProcess)
Hardware Requerido: Cámara 1 (Cámara de Texto/Documentos) + Tesseract OCR

Prueba directa y aislada ("probar una función y era").
"""

import sys
import os
import time
import numpy as np
import cv2

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Intentar cargar pytesseract
try:
    import pytesseract
    tesseract_default_win = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_default_win):
        pytesseract.pytesseract.tesseract_cmd = tesseract_default_win
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


def check_hardware(camera_index=0):
    """Verifica explícitamente si el hardware real (Cámara 1 y Tesseract) está bien conectado."""
    print(f"[VERIFICACIÓN HARDWARE] Probando Cámara 1 (Índice {camera_index})...")
    cap = cv2.VideoCapture(camera_index)
    is_cam_ok = cap.isOpened()
    if is_cam_ok:
        ret, frame = cap.read()
        cap.release()
        is_cam_ok = ret and (frame is not None)

    is_tesseract_ok = False
    if HAS_PYTESSERACT:
        try:
            ver = pytesseract.get_tesseract_version()
            is_tesseract_ok = True
        except Exception:
            is_tesseract_ok = False

    print(f" -> Estado Cámara 1: {' CONECTADA Y RESPONDIENDO' if is_cam_ok else ' DESCONECTADA / NO DISPONIBLE'}")
    print(f" -> Estado Binario Tesseract OCR: {' INSTALADO' if is_tesseract_ok else ' NO ENCONTRADO'}")

    return is_cam_ok, is_tesseract_ok


def execute_function(camera_index=0):
    """Ejecuta la función aislada: Capturar 1 frame real y extraer texto mediante OCR."""
    cam_ok, tess_ok = check_hardware(camera_index)

    if not cam_ok:
        print("[HARDWARE CHECK FAILED] Cámara 1 no disponible. Se generará 1 frame sintético para prueba de software.")
        frame = np.full((300, 600, 3), 255, dtype=np.uint8)
        cv2.putText(frame, "EDDIE AR TEST 2026 - CAMARA 1", (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    else:
        cap = cv2.VideoCapture(camera_index)
        _, frame = cap.read()
        cap.release()

    t0 = time.perf_counter()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    t_proc = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    if tess_ok:
        text = pytesseract.image_to_string(thresh, lang="spa+eng", config="--psm 6").strip()
    else:
        text = "[OCR SIMULADO - SIN TESSERACT] EDDIE AR TEST 2026"
    t_ocr = (time.perf_counter() - t0) * 1000.0

    print("\n--- RESULTADO DE FUNCIÓN ISLADA ---")
    print(f"Tiempo Preprocesamiento OpenCV: {t_proc:.2f} ms")
    print(f"Tiempo OCR Tesseract:          {t_ocr:.2f} ms")
    print(f"Texto Reconocido:              \"{text[:100]}\"")
    print("------------------------------------\n")


if __name__ == "__main__":
    execute_function(camera_index=0)
