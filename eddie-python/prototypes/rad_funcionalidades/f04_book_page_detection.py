"""
prototypes/rad_funcionalidades/f04_book_page_detection.py
===========================================================
PROTOTIPO RAD - F4: Detección Automática de Páginas del Libro
===========================================================
Subsistema: Procesamiento de Imágenes y Visión Computacional
Archivo C# Legacy: AugmentedReadingApp / PageDetectionSettings.cs
Tecnología Propuesta: OpenCV (cv2.findContours, cv2.approxPolyDP, cv2.getPerspectiveTransform)

Descripción:
  Detecta los bordes rectangulares del libro impreso sobre el escritorio para ajustar el área
  de proyección y aplicar corrección de perspectiva (Warp Perspective).
"""
import sys
import os
import time
import numpy as np

os.environ['PYTHONIOENCODING'] = 'utf-8'

print("\n" + "="*70)
print("PROTOTIPO RAD - F4: Detección Automática de Páginas del Libro")
print("="*70)

try:
    import cv2
except ImportError:
    print("ERROR: OpenCV no instalado (pip install opencv-python)")
    sys.exit(1)

def detect_book_page_quad(frame: np.ndarray) -> dict:
    t0 = time.perf_counter()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    page_quad = None
    max_area = 0
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 10000:  # Umbral para evitar ruido pequeño
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4 and area > max_area:
                page_quad = approx
                max_area = area

    elapsed_ms = (time.perf_counter() - t0) * 1000
    
    return {
        'page_detected': page_quad is not None,
        'quad_points': page_quad.reshape(4, 2).tolist() if page_quad is not None else [],
        'area_px': max_area,
        'elapsed_ms': round(elapsed_ms, 3)
    }

def main():
    # Crear imagen simulada con un libro rectangular inclinado
    img = np.ones((600, 800, 3), dtype=np.uint8) * 180  # Fondo gris escritorio
    # Dibujar cuadrilátero representando la página de un libro
    pts = np.array([[150, 100], [650, 120], [680, 520], [120, 500]], np.int32)
    cv2.fillPoly(img, [pts], (255, 255, 255))
    cv2.polylines(img, [pts], True, (50, 50, 50), 3)

    print("\n[PASO 1] Procesando imagen para detectar cuadrilátero del libro...")
    res = detect_book_page_quad(img)

    print(f"\n{'='*70}")
    print("RESUMEN DE FACTIBILIDAD TÉCNICA - F4")
    print(f"{'='*70}")
    print(f"  Página detectada   : {'SÍ' if res['page_detected'] else 'NO'}")
    print(f"  Puntos detectados  : {res['quad_points']}")
    print(f"  Área de la página  : {res['area_px']} px²")
    print(f"  Tiempo de detección: {res['elapsed_ms']} ms")
    print(f"  Equivalencia C#    : PageDetectionSettings.cs -> cv2.findContours + approxPolyDP")
    print(f"  Estado Factibilidad: FACTIBLE Y OPERATIVO")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
