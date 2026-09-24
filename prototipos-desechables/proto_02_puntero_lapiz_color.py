"""
Prototipo Desechable: Detección de Puntero o Lápiz de Color
-----------------------------------------------------------
Función EDDIE-2023: ColorPenRecognition (Filtro RGB/HSV para lápiz físico)
Hardware Requerido: Cámara 2 (Cámara de Gestos / Puntero)

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
    """Verifica si la Cámara 2 (Cámara de Gestos) está conectada."""
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
    """Ejecuta la función aislada: Detectar centro de puntero de color en el frame."""
    cam_ok = check_hardware(camera_index)

    if not cam_ok:
        print("[HARDWARE CHECK FAILED] Cámara 2 no disponible. Generando 1 frame sintético para prueba de software.")
        frame = np.full((480, 640, 3), 200, dtype=np.uint8)
        # Dibujar un círculo azul simulando la punta de un lápiz de color en (200, 150)
        cv2.circle(frame, (200, 150), 15, (255, 0, 0), -1)
    else:
        cap = cv2.VideoCapture(camera_index)
        _, frame = cap.read()
        cap.release()

    t0 = time.perf_counter()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([100, 150, 50])
    upper_blue = np.array([140, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    center = None
    if contours:
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) > 20:
            M = cv2.moments(c)
            if M["m00"] > 0:
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

    t_proc = (time.perf_counter() - t0) * 1000.0

    print("\n--- RESULTADO DE FUNCIÓN AISLADA ---")
    print(f"Tiempo Procesamiento ColorPen HSV: {t_proc:.2f} ms")
    print(f"Coordenada Puntero Detectada:      {center}")
    print("------------------------------------\n")


if __name__ == "__main__":
    execute_function(camera_index=1)
