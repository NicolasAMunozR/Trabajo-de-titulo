"""
================================================================================
PROYECTO EDDIE (Python Migration) - Prototipo RAD P-04
================================================================================
Nombre: Módulo de Visualización y Gestión de Plugins en Interfaz
Sección Tesis: 3.4.4 Cuarto Prototipo (M. Figueroa, 2025)
Equivalente C# Legacy: proyecto_eddie/ModuloVisualizacionDatos/HighlightTool.cs
Tecnología: Python 3.14 + OpenCV + Synchronous Timeline Sync

Objetivos:
1. Reproducir sesiones síncronas multimodales (Video + Trazo de Mouse + Registro Teclado).
2. Proporcionar barra de línea de tiempo interactiva (Scrubbing / Play / Pause).
3. Validar desacoplamiento de vistas en entorno multicanal.
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

class PlaybackViewer:
    def __init__(self):
        self.playing = True
        self.current_frame = 0
        self.total_frames = 200
        self.fps = 25

    def run(self):
        print("=" * 75)
        print("  EDDIE Python – Prototipo P-04: Módulo de Visualización (Playback)")
        print("  Referencia Tesis: Capítulo 3.4.4 | Proyecto C#: ModuloVisualizacionDatos")
        print("=" * 75)

        win_name = "EDDIE – Prototipo P-04 (Synchronous Playback Viewer)"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win_name, 1280, 720)

        # Generar datos sintéticos de prueba para la reproducción síncrona
        mouse_track = [(int(200 + 150 * np.sin(i * 0.05)), int(200 + 100 * np.cos(i * 0.05))) for i in range(self.total_frames)]
        keyboard_log = [f"Palabra #{i//10}: 'EDDIE_v2_{i}'" for i in range(self.total_frames)]

        while True:
            # Render video canal 1
            frame_video = np.full((480, 640, 3), 30, dtype=np.uint8)
            cv2.putText(frame_video, "REPRODUCCIÓN VIDEO CANAL 1", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 255), 2)

            # Dibujar cursor de mouse sincronizado
            mx, my = mouse_track[self.current_frame]
            cv2.circle(frame_video, (mx, my), 8, (0, 255, 0), -1)
            cv2.putText(frame_video, f"Cursor ({mx},{my})", (mx + 12, my + 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)

            # Panel multicanal teclado
            panel_text = np.full((480, 600, 3), 20, dtype=np.uint8)
            cv2.putText(panel_text, "P-04: LÍNEA DE TIEMPO SÍNCRONA", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 150), 2)

            state_str = "▶ REPRODUCIENDO" if self.playing else "⏸ PAUSADO"
            cv2.putText(panel_text, f"Estado: {state_str} | Frame {self.current_frame}/{self.total_frames}", (15, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

            cv2.line(panel_text, (15, 68), (585, 68), (60, 60, 60), 1)

            # Reconstrucción de texto
            cv2.putText(panel_text, "EVENTOS DE TECLADO RECONSTRUIDOS:", (15, 95),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 200, 0), 1)
            start_idx = max(0, self.current_frame - 5)
            y_t = 120
            for idx in range(start_idx, self.current_frame + 1):
                prefix = "  >> " if idx == self.current_frame else "     "
                cv2.putText(panel_text, f"{prefix}{keyboard_log[idx]}", (15, y_t),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 255, 180) if idx == self.current_frame else (140, 140, 140), 1)
                y_t += 22

            # Barra de progreso timeline
            cv2.rectangle(panel_text, (15, 400), (585, 420), (50, 50, 50), -1)
            progress_w = int((self.current_frame / self.total_frames) * 570)
            cv2.rectangle(panel_text, (15, 400), (15 + progress_w, 420), (0, 200, 255), -1)
            cv2.putText(panel_text, f"Línea de tiempo: {self.current_frame * 0.04:.2f}s / {self.total_frames * 0.04:.2f}s",
                        (15, 392), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (220, 220, 220), 1)

            # Controles
            cv2.rectangle(panel_text, (10, 435), (585, 470), (40, 40, 40), -1)
            cv2.putText(panel_text, "CONTROLES: ESPACIO: Play/Pausa | FLECHAS: Retroceder/Avanzar | S: Evidencia | Q: Salir",
                        (15, 458), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (200, 200, 200), 1)

            combined = np.hstack([frame_video, panel_text])
            cv2.imshow(win_name, combined)

            key = cv2.waitKey(40 if self.playing else 100) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == 32:  # Espacio
                self.playing = not self.playing
            elif key == 81 or key == 2424832:  # Flecha Izquierda
                self.current_frame = max(0, self.current_frame - 5)
            elif key == 83 or key == 2555904:  # Flecha Derecha
                self.current_frame = min(self.total_frames - 1, self.current_frame + 5)
            elif key == ord('s'):
                out_img = EVID_DIR / "p04_visualizacion_playback_evidencia.png"
                cv2.imwrite(str(out_img), combined)
                print(f"  [✓ EVIDENCIA GUARDADA] {out_img.name}")

            if self.playing:
                self.current_frame = (self.current_frame + 1) % self.total_frames

        cv2.destroyAllWindows()
        print("  ✓ Prototipo P-04 finalizado exitosamente.\n")

if __name__ == "__main__":
    v = PlaybackViewer()
    v.run()
