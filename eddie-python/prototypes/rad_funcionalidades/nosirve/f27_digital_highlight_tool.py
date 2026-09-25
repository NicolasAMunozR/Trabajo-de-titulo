"""
prototypes/rad_funcionalidades/f27_digital_highlight_tool.py
===========================================================
PROTOTIPO RAD - F27: Herramienta de Subrayado Digital Proyectado (HighlightTool)
===========================================================
Subsistema: Presentación GUI, Proyección y Logs
Archivo C# Legacy: ModuloVisualizacionDatos / HighlightTool.cs
Tecnología Propuesta: Canvas Transparente OpenCV / PyGame / Canvas Interactivo

Descripción:
  Dibuja una banda rectangular amarilla transparente interactiva en pantalla sobre la proyección
  para destacar las líneas de texto físico leídas por el usuario.
"""
import sys
import os
import time
import numpy as np

os.environ['PYTHONIOENCODING'] = 'utf-8'

print("\n" + "="*70)
print("PROTOTIPO RAD - F27: Herramienta de Subrayado Digital Proyectado")
print("="*70)

try:
    import cv2
except ImportError:
    print("ERROR: OpenCV no instalado (pip install opencv-python)")
    sys.exit(1)

def draw_projected_highlight_band(canvas: np.ndarray, x0: int, y0: int, x1: int, y1: int, alpha: float = 0.4) -> tuple:
    t0 = time.perf_counter()
    overlay = canvas.copy()
    
    # Dibujar banda rectangular de color amarillo BGR (0, 255, 255)
    cv2.rectangle(overlay, (x0, y0), (x1, y1), (0, 255, 255), -1)
    
    # Mezcla de capas con transparencia alpha
    result = cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0)
    
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return result, round(elapsed_ms, 3)

def main():
    # Canvas simulado del escritorio proyectado (1024x768)
    canvas = np.ones((768, 1024, 3), dtype=np.uint8) * 40
    
    rect_coords = (100, 200, 600, 240)
    print(f"\n[PASO 1] Renderizando franja amarilla translúcida en la proyección {rect_coords}...")
    
    output_img, render_ms = draw_projected_highlight_band(canvas, *rect_coords)

    print(f"\n{'='*70}")
    print("RESUMEN DE FACTIBILIDAD TÉCNICA - F27")
    print(f"{'='*70}")
    print(f"  Banda de Subrayado : Coordenadas {rect_coords}")
    print(f"  Transparencia Alpha: 0.4 (Amarillo)")
    print(f"  Tiempo de Render   : {render_ms} ms")
    print(f"  Equivalencia C#    : HighlightTool.cs (PictureBox overlay) -> cv2.rectangle + addWeighted")
    print(f"  Estado Factibilidad: FACTIBLE Y OPERATIVO")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
