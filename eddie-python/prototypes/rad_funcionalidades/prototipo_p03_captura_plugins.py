"""
================================================================================
PROYECTO EDDIE (Python Migration) - Prototipo RAD P-03
================================================================================
Nombre: Módulo de Captura y Gestión de Plugins
Sección Tesis: 3.4.3 Tercer Prototipo (M. Figueroa, 2025)
Equivalente C# Legacy: proyecto_eddie/ModuloProcesamientoImagenes/CameraActivity.cs
Tecnología: Python 3.14 + OpenCV (VideoWriter) + JSON Event Logging

Objetivos:
1. Ejecutar sesión de captura multimodal síncrona.
2. Generar registro estructurado JSON para eventos de Teclado y Mouse.
3. Grabar flujo de video continuo (.mp4 / .avi).
================================================================================
"""

import os
import sys
import json
import time
import pathlib
import cv2
import numpy as np

BASE_DIR = pathlib.Path(__file__).resolve().parent
EVID_DIR = BASE_DIR / "evidencias" / "real"
EVID_DIR.mkdir(parents=True, exist_ok=True)

class SessionCaptureEngine:
    def __init__(self, session_id):
        self.session_id = session_id
        self.output_dir = EVID_DIR / f"session_{session_id}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.mouse_events = []
        self.key_events = []
        self.video_writer = None

    def start_session(self, width=640, height=480, fps=20):
        video_path = self.output_dir / "video_capture.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.video_writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
        print(f"  [+] Grabación de video iniciada: {video_path.name}")

    def log_mouse(self, x, y, event_type):
        self.mouse_events.append({
            "timestamp": time.time(),
            "time_str": time.strftime("%H:%M:%S.%MS"),
            "x": x,
            "y": y,
            "type": event_type
        })

    def log_key(self, key_str):
        self.key_events.append({
            "timestamp": time.time(),
            "time_str": time.strftime("%H:%M:%S.%MS"),
            "key": key_str
        })

    def save_frame(self, frame):
        if self.video_writer:
            self.video_writer.write(frame)

    def stop_session(self):
        if self.video_writer:
            self.video_writer.release()

        # Save JSONs
        mouse_file = self.output_dir / "mouse_events.json"
        with open(mouse_file, "w", encoding="utf-8") as f:
            json.dump(self.mouse_events, f, indent=2)

        key_file = self.output_dir / "keyboard_events.json"
        with open(key_file, "w", encoding="utf-8") as f:
            json.dump(self.key_events, f, indent=2)

        print(f"  [✓ SESIÓN FINALIZADA] Archivos guardados en: {self.output_dir.name}")
        print(f"    - Teclado: {len(self.key_events)} eventos")
        print(f"    - Mouse: {len(self.mouse_events)} eventos")

def main():
    print("=" * 75)
    print("  EDDIE Python – Prototipo P-03: Módulo de Captura y Gestión de Plugins")
    print("  Referencia Tesis: Capítulo 3.4.3 | Proyecto C#: ModuloProcesamientoImagenes")
    print("=" * 75)

    sess_id = f"SESS_{int(time.time())}"
    engine = SessionCaptureEngine(sess_id)
    engine.start_session(640, 480, 20)

    win_name = "EDDIE – Prototipo P-03 (Engine de Captura)"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, 1000, 600)

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            engine.log_mouse(x, y, "move")
        elif event == cv2.EVENT_LBUTTONDOWN:
            engine.log_mouse(x, y, "click_left")

    cv2.setMouseCallback(win_name, on_mouse)

    cap = None
    for idx in range(3):
        c = cv2.VideoCapture(idx, cv2.CAP_ANY)
        if c.isOpened():
            cap = c
            break
        c.release()

    print("\n  [GRABANDO SESIÓN... Presiona 'Q' para detener]")
    for i in range(120):  # Captura de 120 frames (~6 segundos)
        if cap and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                frame = np.full((480, 640, 3), 40, dtype=np.uint8)
        else:
            frame = np.full((480, 640, 3), 40, dtype=np.uint8)
            cv2.putText(frame, f"GRABANDO SESIÓN: {sess_id}", (30, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 150), 2)

        frame = cv2.resize(frame, (640, 480))
        engine.save_frame(frame)

        cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
        cv2.putText(frame, "REC", (50, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, f"Frame #{i+1}", (540, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        cv2.imshow(win_name, frame)
        key = cv2.waitKey(40) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif 32 <= key <= 126:
            engine.log_key(chr(key))

    if cap: cap.release()
    cv2.destroyAllWindows()
    engine.stop_session()
    print("  ✓ Prototipo P-03 finalizado exitosamente.\n")

if __name__ == "__main__":
    main()
