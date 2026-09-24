"""
Prototipo Desechable: Detección de Mano y Dedo Índice (HandSkin)
----------------------------------------------------------------
Función EDDIE-2023: HandSkinRecognition (YCrCb + Defectos de Convexidad)
Hardware Requerido: Cámara 2 (Cámara de Gestos)

Prueba directa y aislada ("probar una función y era").
"""

import sys
import os
import time
import numpy as np
import cv2

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def check_hardware(camera_index=1):
    """Verifica si la Cámara 2 (Gestos) está conectada."""
    print(f"[VERIFICACIÓN HARDWARE] Probando Cámara 2 (Índice {camera_index})...")
    cap = cv2.VideoCapture(camera_index)
    is_ok = cap.isOpened()
    if is_ok:
        ret, frame = cap.read()
        cap.release()
        is_ok = ret and (frame is not None)

    print(f" -> Estado Cámara 2 (Gestos): {' CONECTADA Y RESPONDIENDO' if is_ok else ' DESCONECTADA / NO DISPONIBLE'}")
    return is_ok


def execute_function(camera_index=1):
    """Ejecuta la función aislada: Segmentar piel YCrCb y hallar la punta del dedo índice."""
    cam_ok = check_hardware(camera_index)

    if not cam_ok:
        print("[HARDWARE CHECK FAILED] Cámara 2 no disponible. Generando 1 frame sintético para prueba de software.")
        frame = np.full((480, 640, 3), 200, dtype=np.uint8)
        # Dibujar silueta sintética de mano en BGR=(120, 140, 190)
        cv2.ellipse(frame, (320, 300), (80, 120), 0, 0, 360, (120, 140, 190), -1)
        cv2.rectangle(frame, (300, 120), (320, 220), (120, 140, 190), -1)  # Índice
    else:
        cap = cv2.VideoCapture(camera_index)
        _, frame = cap.read()
        cap.release()

    t0 = time.perf_counter()
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    lower_skin = np.array([0, 133, 77], dtype=np.uint8)
    upper_skin = np.array([255, 173, 127], dtype=np.uint8)
    mask = cv2.inRange(ycrcb, lower_skin, upper_skin)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    finger_tip = None
    if contours:
        hand_c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(hand_c) > 500:
            topmost = tuple(hand_c[hand_c[:, :, 1].argmin()][0])
            finger_tip = topmost

    t_proc = (time.perf_counter() - t0) * 1000.0

    print("\n--- RESULTADO DE FUNCIÓN AISLADA ---")
    print(f"Tiempo Procesamiento YCrCb HandSkin: {t_proc:.2f} ms")
    print(f"Punta Dedo Índice Detectada (X, Y):  {finger_tip}")
    print("------------------------------------\n")


if __name__ == "__main__":
    execute_function(camera_index=1)
