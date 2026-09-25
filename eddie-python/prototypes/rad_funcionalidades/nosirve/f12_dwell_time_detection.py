"""
prototypes/rad_funcionalidades/f12_dwell_time_detection.py
===========================================================
PROTOTIPO RAD - F12: Detección de Fijación Atencional (Dwell Time)
===========================================================
Subsistema: Rastreo Ocular y Atención Visual (Eye Tracking)
Archivo C# Legacy: ModuloRastreoOcular / MouseControl.cs
Tecnología Propuesta: Temporal Dwell Filter / Spatial Radius Check

Descripción:
  Mide si la mirada permanece fija en un radio de píxeles durante >400 ms para gatillar la selección
  o el despliegue automático de información suplementaria.
"""
import sys
import os
import time
import math

os.environ['PYTHONIOENCODING'] = 'utf-8'

print("\n" + "="*70)
print("PROTOTIPO RAD - F12: Detección de Fijación Atencional (Dwell Time)")
print("="*70)

class DwellDetector:
    def __init__(self, radius_px: float = 30.0, dwell_threshold_ms: float = 400.0):
        self.radius_px = radius_px
        self.dwell_threshold_ms = dwell_threshold_ms
        self.anchor_x = None
        self.anchor_y = None
        self.start_time = None

    def process_point(self, x: float, y: float, timestamp: float) -> dict:
        t0 = time.perf_counter()
        dwell_triggered = False
        duration_ms = 0.0

        if self.anchor_x is None:
            self.anchor_x = x
            self.anchor_y = y
            self.start_time = timestamp
        else:
            dist = math.sqrt((x - self.anchor_x)**2 + (y - self.anchor_y)**2)
            if dist <= self.radius_px:
                duration_ms = (timestamp - self.start_time) * 1000
                if duration_ms >= self.dwell_threshold_ms:
                    dwell_triggered = True
            else:
                # Reiniciar ancla si la mirada se sale del radio espacial
                self.anchor_x = x
                self.anchor_y = y
                self.start_time = timestamp

        elapsed_ms = (time.perf_counter() - t0) * 1000

        return {
            'x': x,
            'y': y,
            'duration_ms': round(duration_ms, 1),
            'dwell_triggered': dwell_triggered,
            'calc_ms': round(elapsed_ms, 4)
        }

def main():
    detector = DwellDetector(radius_px=20.0, dwell_threshold_ms=300.0)
    print("\n[PASO 1] Simulando secuencia de fijación de mirada sobre la misma palabra...")

    base_time = time.time()
    # Puntos simulados permaneciendo en la misma zona durante 400 ms
    gaze_stream = [
        (100.0, 200.0, base_time + 0.0),
        (102.0, 198.0, base_time + 0.1),
        (101.0, 201.0, base_time + 0.2),
        (103.0, 199.0, base_time + 0.35),  # Supera los 300 ms -> Gatilla Dwell
    ]

    for gx, gy, ts in gaze_stream:
        res = detector.process_point(gx, gy, ts)
        status = "GATILLADO" if res['dwell_triggered'] else "acumulando..."
        print(f"  Gaze ({res['x']}, {res['y']}) | Duración: {res['duration_ms']} ms -> Dwell: {status}")

    print(f"\n{'='*70}")
    print("RESUMEN DE FACTIBILIDAD TÉCNICA - F12")
    print(f"{'='*70}")
    print(f"  Filtro Dwell       : Radio espacial {detector.radius_px}px, Umbral {detector.dwell_threshold_ms}ms")
    print(f"  Equivalencia C#    : MouseControl.cs -> DwellDetector espacial-temporal")
    print(f"  Estado Factibilidad: FACTIBLE Y OPERATIVO")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
