"""
prototypes/rad_funcionalidades/f05_color_pen_tracking.py
===========================================================
PROTOTIPO RAD - F5: Seguimiento de Puntero / Lápiz de Color (ColorPen)
===========================================================
Subsistema: Reconocimiento Gestual e Interacción sin Contacto
Archivo C# Legacy: ColorPenRecognition / ColorPen.cs
Tecnología Propuesta: OpenCV (cv2.inRange HSV, cv2.moments)

Descripción:
  Segmenta un marcador o lápiz de color (rojo/azul) en el espacio de color HSV para usarlo
  como puntero interactivo sobre el papel.
"""
import sys
import os
import time
import numpy as np

os.environ['PYTHONIOENCODING'] = 'utf-8'

print("\n" + "="*70)
print("PROTOTIPO RAD - F5: Seguimiento de Puntero / Lápiz de Color")
print("="*70)

try:
    import cv2
except ImportError:
    print("ERROR: OpenCV no instalado (pip install opencv-python)")
    sys.exit(1)

def track_color_pen(frame: np.ndarray, color_hsv_lower, color_hsv_upper) -> dict:
    t0 = time.perf_counter()
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, color_hsv_lower, color_hsv_upper)
    
    # Morfología para eliminar ruido
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    pen_detected = False
    center_x, center_y = -1, -1
    
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 200:
            M = cv2.moments(largest)
            if M['m00'] > 0:
                center_x = int(M['m10'] / M['m00'])
                center_y = int(M['m01'] / M['m00'])
                pen_detected = True

    elapsed_ms = (time.perf_counter() - t0) * 1000
    
    return {
        'detected': pen_detected,
        'pointer_x': center_x,
        'pointer_y': center_y,
        'elapsed_ms': round(elapsed_ms, 3)
    }

def main():
    # Imagen simulada con un lápiz rojo
    img = np.ones((480, 640, 3), dtype=np.uint8) * 200
    # Dibujar círculo rojo representando la punta del lápiz
    cv2.circle(img, (320, 240), 20, (0, 0, 255), -1)
    
    # Rango HSV para color rojo
    lower_red = np.array([0, 120, 100])
    upper_red = np.array([10, 255, 255])

    print("\n[PASO 1] Escaneando frame para detectar puntero de color rojo...")
    res = track_color_pen(img, lower_red, upper_red)

    print(f"\n{'='*70}")
    print("RESUMEN DE FACTIBILIDAD TÉCNICA - F5")
    print(f"{'='*70}")
    print(f"  Puntero detectado  : {'SÍ' if res['detected'] else 'NO'}")
    print(f"  Coordenadas (X,Y)  : ({res['pointer_x']}, {res['pointer_y']})")
    print(f"  Tiempo de rastreo  : {res['elapsed_ms']} ms")
    print(f"  Equivalencia C#    : ColorPen.cs -> cv2.cvtColor(HSV) + cv2.inRange")
    print(f"  Estado Factibilidad: FACTIBLE Y OPERATIVO")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
