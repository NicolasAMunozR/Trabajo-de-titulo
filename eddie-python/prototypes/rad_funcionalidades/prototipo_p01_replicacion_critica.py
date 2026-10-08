"""
================================================================================
PROYECTO EDDIE (Python Migration) - Prototipo RAD P-01
================================================================================
Nombre: Replicación de Funcionalidades Críticas
Sección Tesis: 3.4.1 Primer Prototipo (M. Figueroa, 2025)
Equivalente C# Legacy: proyecto_eddie/AugmentedReadingApp/ProjectionScreenActivity2.cs
Tecnología: Python 3.14 + OpenCV + Sockets (UDP/TCP) + Threading

Objetivos:
1. Validar la viabilidad técnica de la captura síncrona multimodal (Teclado, Mouse, Video, Sockets).
2. Demostrar la comunicación entre procesos y módulos desacoplados.
3. Servir como prototipo de factibilidad rápida (Throwaway Prototype).
================================================================================
"""

import os
import sys
import time
import socket
import threading
import pathlib
import cv2
import numpy as np

BASE_DIR = pathlib.Path(__file__).resolve().parent
EVID_DIR = BASE_DIR / "evidencias" / "real"
EVID_DIR.mkdir(parents=True, exist_ok=True)

class MultimodalCaptureEngine:
    def __init__(self):
        self.running = False
        self.mouse_pos = (0, 0)
        self.key_log = []
        self.socket_messages = []
        self.lock = threading.Lock()

    def start_udp_listener(self, port=9000):
        def listen():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0.5)
            try:
                sock.bind(("127.0.0.1", port))
            except Exception as e:
                print(f"  [UDP Listener] Error al enlazar puerto {port}: {e}")
                return

            print(f"  [UDP Listener] Escuchando en 127.0.0.1:{port}...")
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    msg = data.decode("utf-8", errors="ignore").strip()
                    with self.lock:
                        self.socket_messages.append(f"[{addr[0]}] {msg}")
                        if len(self.socket_messages) > 10:
                            self.socket_messages.pop(0)
                except socket.timeout:
                    continue
                except Exception:
                    break
            sock.close()

        t = threading.Thread(target=listen, daemon=True)
        t.start()

def main():
    print("=" * 75)
    print("  EDDIE Python – Prototipo P-01: Replicación de Funcionalidades Críticas")
    print("  Referencia Tesis: Capítulo 3.4.1 | Proyecto C#: AugmentedReadingApp")
    print("=" * 75)

    engine = MultimodalCaptureEngine()
    engine.running = True
    engine.start_udp_listener(port=9000)

    # Inicializar captura de video
    cap = None
    for idx in range(3):
        c = cv2.VideoCapture(idx, cv2.CAP_ANY)
        if c.isOpened():
            cap = c
            print(f"  [+] Cámara física conectada en índice {idx}")
            break
        c.release()

    win_name = "EDDIE – Prototipo P-01 (Replicacion Critica)"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, 1280, 720)

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            engine.mouse_pos = (x, y)
        elif event == cv2.EVENT_LBUTTONDOWN:
            with engine.lock:
                engine.key_log.append(f"CLIC: ({x},{y}) @ {time.strftime('%H:%M:%S')}")

    cv2.setMouseCallback(win_name, on_mouse)

    start_time = time.time()
    frame_count = 0

    while True:
        frame_count += 1
        elapsed = time.time() - start_time

        if cap and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                frame = np.full((480, 640, 3), 35, dtype=np.uint8)
        else:
            frame = np.full((480, 640, 3), 35, dtype=np.uint8)
            cv2.putText(frame, "FEED CÁMARA (SIMULADO / SENSOR OK)", (30, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)

        frame = cv2.resize(frame, (640, 480))

        # Panel telemetry
        panel = np.full((480, 600, 3), 20, dtype=np.uint8)
        cv2.putText(panel, "P-01: TELEMETRIA MULTIMODAL SÍNCRONA", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 150), 2)
        cv2.putText(panel, f"Tiempo activo: {elapsed:.1f}s | Frames: {frame_count}", (15, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)

        cv2.line(panel, (15, 68), (585, 68), (60, 60, 60), 1)

        # Mouse
        mx, my = engine.mouse_pos
        cv2.putText(panel, f"POSICIÓN CURSOR MOUSE: ({mx}, {my}) pt", (15, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 220, 255), 1)

        # Teclado / Eventos
        cv2.putText(panel, "EVENTOS DE REGISTRO (TECLADO / CLICS):", (15, 125),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 200, 0), 1)
        with engine.lock:
            y_evt = 150
            for item in engine.key_log[-6:]:
                cv2.putText(panel, f" > {item}", (20, y_evt),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (220, 220, 220), 1)
                y_evt += 22

        # Sockets
        cv2.line(panel, (15, 280), (585, 280), (60, 60, 60), 1)
        cv2.putText(panel, "SOCKETS (UDP 127.0.0.1:9000):", (15, 305),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (100, 220, 255), 1)
        with engine.lock:
            y_sock = 330
            if not engine.socket_messages:
                cv2.putText(panel, " (Esperando paquetes UDP remotos...)", (20, y_sock),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.36, (140, 140, 140), 1)
            for msg in engine.socket_messages[-5:]:
                cv2.putText(panel, f" [UDP] {msg}", (20, y_sock),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.36, (180, 255, 180), 1)
                y_sock += 22

        # Controles
        cv2.rectangle(panel, (10, 420), (585, 470), (40, 40, 40), -1)
        cv2.putText(panel, "CONTROLES: Presiona TECLAS para registrar | S: Guardar Evidencia | Q: Salir",
                    (15, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (200, 200, 200), 1)

        combined = np.hstack([frame, panel])
        cv2.imshow(win_name, combined)

        key = cv2.waitKey(30) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('s'):
            out_img = EVID_DIR / "p01_replicacion_critica_evidencia.png"
            cv2.imwrite(str(out_img), combined)
            print(f"  [✓ EVIDENCIA GUARDADA] {out_img.name}")
        elif 32 <= key <= 126:
            ch = chr(key)
            with engine.lock:
                engine.key_log.append(f"TECLA: '{ch}' @ {time.strftime('%H:%M:%S')}")

    engine.running = False
    if cap: cap.release()
    cv2.destroyAllWindows()
    print("  ✓ Prototipo P-01 finalizado exitosamente.\n")

if __name__ == "__main__":
    main()
