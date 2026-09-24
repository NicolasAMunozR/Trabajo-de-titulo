"""
Prototipo Desechable #4: Reconocimiento Gestual y Segmentación (OpenCV Color & Hand Skin)
-----------------------------------------------------------------------------------------
Objetivo: Validar la factibilidad técnica de reemplazar los plugins C# de 
ColorPenRecognition y HandSkinRecognition (YCrCb + Convexity Defects en Emgu.CV)
por OpenCV nativo en Python.

Prioridad de Ejecución:
  1. Captura de Cámara Real (Webcam) si está conectada.
  2. Fallback automático a frames sintéticos de prueba con contornos simulados.

Metodología: Figueroa (2025) - Prototipado Aislado de Bajo Costo.
"""

import sys
import os
import time
import argparse
import numpy as np
import cv2

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def generate_synthetic_hand_frame():
    """Genera un frame sintético con una mano simulada (piel en YCrCb) y un marcador de color azul (HSV)."""
    img = np.full((480, 640, 3), 220, dtype=np.uint8)

    # Dibujar marcador azul (ColorPen) en (150, 150)
    cv2.circle(img, (150, 150), 20, (255, 0, 0), -1)

    # Dibujar región de mano (Piel simulada en BGR)
    # Tono de piel en BGR aproximado: R=190, G=140, B=120 -> BGR=(120, 140, 190)
    cv2.ellipse(img, (400, 300), (80, 120), 0, 0, 360, (120, 140, 190), -1)
    # Dedos simulados
    cv2.rectangle(img, (340, 140), (360, 220), (120, 140, 190), -1)  # Dedo 1
    cv2.rectangle(img, (380, 120), (400, 220), (120, 140, 190), -1)  # Dedo 2
    cv2.rectangle(img, (420, 130), (440, 220), (120, 140, 190), -1)  # Dedo 3

    return img


def detect_color_pen(frame):
    """
    Segmentación por rango en espacio HSV para detectar un puntero/marcador de color (ColorPenRecognition).
    """
    t0 = time.perf_counter()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Rango para color azul
    lower_blue = np.array([100, 150, 50])
    upper_blue = np.array([140, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    center = None
    if contours:
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) > 50:
            M = cv2.moments(c)
            if M["m00"] > 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                center = (cX, cY)

    t_proc = (time.perf_counter() - t0) * 1000.0
    return center, t_proc


def detect_hand_skin_defects(frame):
    """
    Segmentación de piel en espacio YCrCb y cálculo de defectos de convexidad para contar dedos.
    Reemplaza YCrCbSkinDetector.cs + CvInvoke.ConvexityDefects en C#.
    """
    t0 = time.perf_counter()
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)

    # Rangos universales de piel humana en YCrCb
    lower_skin = np.array([0, 133, 77], dtype=np.uint8)
    upper_skin = np.array([255, 173, 127], dtype=np.uint8)
    skin_mask = cv2.inRange(ycrcb, lower_skin, upper_skin)

    # Filtrado morfológico para eliminar ruido
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    skin_mask = cv2.erode(skin_mask, kernel, iterations=1)
    skin_mask = cv2.dilate(skin_mask, kernel, iterations=2)

    contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    fingers_count = 0
    pointer_tip = None

    if contours:
        hand_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(hand_contour) > 1000:
            hull = cv2.convexHull(hand_contour, returnPoints=False)
            if len(hull) > 3 and len(hand_contour) > 3:
                try:
                    defects = cv2.convexityDefects(hand_contour, hull)
                    if defects is not None:
                        for i in range(defects.shape[0]):
                            s, e, f, d = defects[i, 0]
                            depth = d / 256.0
                            if depth > 10.0:  # Umbral de hendidura entre dedos
                                fingers_count += 1
                except Exception:
                    pass

            # Obtener el punto más alto del contorno como punta del dedo índice
            topmost = tuple(hand_contour[hand_contour[:, :, 1].argmin()][0])
            pointer_tip = topmost

    t_proc = (time.perf_counter() - t0) * 1000.0
    return fingers_count, pointer_tip, t_proc


def run_prototype_04(camera_index=None, test_cycles=10):
    """Ejecuta la prueba de factibilidad técnica para reconocimiento gestual."""
    print("==========================================================")
    print("PROTOTIPO #4: RECONOCIMIENTO GESTUAL (COLOR PEN & HAND SKIN)")
    print("==========================================================")

    frame = None
    source_type = ""

    if camera_index is not None:
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            ret, captured_frame = cap.read()
            cap.release()
            if ret and captured_frame is not None:
                frame = captured_frame
                source_type = f"Hardware Real (Cámara index {camera_index})"

    if frame is None:
        frame = generate_synthetic_hand_frame()
        source_type = "Frame Sintético de Evaluación (Fallback)"

    print(f"Origen de Entrada: {source_type}")

    pen_times = []
    skin_times = []
    last_pen_center = None
    last_fingers = 0
    last_pointer_tip = None

    for _ in range(test_cycles):
        center, t_pen = detect_color_pen(frame)
        fingers, tip, t_skin = detect_hand_skin_defects(frame)

        pen_times.append(t_pen)
        skin_times.append(t_skin)
        last_pen_center = center
        last_fingers = fingers
        last_pointer_tip = tip

    avg_pen_ms = sum(pen_times) / len(pen_times)
    avg_skin_ms = sum(skin_times) / len(skin_times)
    total_avg_ms = avg_pen_ms + avg_skin_ms
    fps_est = 1000.0 / total_avg_ms if total_avg_ms > 0 else 999.0

    print("\n--- Resultados de Rendimiento y Factibilidad ---")
    print(f"ColorPen HSV Detección Puntero:  {avg_pen_ms:.3f} ms")
    print(f"HandSkin YCrCb + Defectos Conv:  {avg_skin_ms:.3f} ms")
    print(f"Latencia Total Procesamiento:    {total_avg_ms:.3f} ms")
    print(f"Rendimiento Estimado:            {fps_est:.1f} FPS")
    print(f"Puntero Color Detectado:         {last_pen_center}")
    print(f"Dedos Levantados Estimados:      {last_fingers}")
    print(f"Punta Dedo Índice Detectada:     {last_pointer_tip}")

    is_feasible = total_avg_ms < 33.0  # Garantiza >30 FPS

    print(f"\nDictamen Factibilidad Técnica: {' FACTIBLE (Aprobado)' if is_feasible else ' NO FACTIBLE'}")
    print("==========================================================\n")

    return {
        "prototype": "Proto 04 - Gesture Recognition",
        "source_type": source_type,
        "is_feasible": is_feasible,
        "avg_pen_ms": round(avg_pen_ms, 3),
        "avg_skin_ms": round(avg_skin_ms, 3),
        "total_avg_ms": round(total_avg_ms, 3),
        "estimated_fps": round(fps_est, 1)
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prototipo Reconocimiento Gestual")
    parser.add_argument("--camera", type=int, default=None, help="Índice de cámara real")
    args = parser.parse_args()

    run_prototype_04(camera_index=args.camera)
