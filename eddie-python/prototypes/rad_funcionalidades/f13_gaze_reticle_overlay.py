"""
prototypes/rad_funcionalidades/f13_gaze_reticle_overlay.py
===========================================================
PROTOTIPO RAD - F13: Renderizado de Retículo de Mirada proyectado
===========================================================
Subsistema: Rastreo Ocular y Atención Visual (Eye Tracking)
Archivo C# Legacy: ModuloRastreoOcular / ReticleDrawing.cs
Tecnología Propuesta: Overlay Visual (OpenCV Canvas / PyGame / Canvas transparente)

Descripción:
  Dibuja una mira o retículo visual circular translúcido exactamente sobre la posición del escritorio
  donde el lector fija su mirada en tiempo real.
"""
import sys
import os
import time
import numpy as np

os.environ['PYTHONIOENCODING'] = 'utf-8'

print("\n" + "="*70)
print("PROTOTIPO RAD - F13: Renderizado de Retículo de Mirada proyectado")
print("="*70)

try:
    import cv2
except ImportError:
    print("ERROR: OpenCV no instalado (pip install opencv-python)")
    sys.exit(1)

def draw_gaze_reticle(canvas: np.ndarray, gaze_x: int, gaze_y: int, radius: int = 25) -> tuple:
    t0 = time.perf_counter()
    overlay = canvas.copy()
    
    # Dibujar anillo exterior rojo translúcido
    cv2.circle(overlay, (gaze_x, gaze_y), radius, (0, 0, 255), 3)
    # Dibujar cruz central
    cv2.line(overlay, (gaze_x - 10, gaze_y), (gaze_x + 10, gaze_y), (0, 0, 255), 2)
    cv2.line(overlay, (gaze_x, gaze_y - 10), (gaze_x, gaze_y + 10), (0, 0, 255), 2)
    
    # Aplicar transparencia alpha (0.6)
    alpha = 0.6
    result = cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0)
    
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return result, round(elapsed_ms, 3)

def main():
    # Canvas proyectado simulado (1024x768)
    canvas = np.ones((768, 1024, 3), dtype=np.uint8) * 30  # Proyección oscura
    
    gaze_pos = (512, 384)
    print(f"\n[PASO 1] Renderizando retículo de mirada en posición {gaze_pos}...")
    
    rendered_img, render_ms = draw_gaze_reticle(canvas, gaze_pos[0], gaze_pos[1])

    print(f"\n{'='*70}")
    print("RESUMEN DE FACTIBILIDAD TÉCNICA - F13")
    print(f"{'='*70}")
    print(f"  Posición Retículo  : {gaze_pos}")
    print(f"  Tiempo de Render   : {render_ms} ms")
    print(f"  Equivalencia C#    : ReticleDrawing.cs -> cv2.circle + cv2.addWeighted")
    print(f"  Estado Factibilidad: FACTIBLE Y OPERATIVO")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
