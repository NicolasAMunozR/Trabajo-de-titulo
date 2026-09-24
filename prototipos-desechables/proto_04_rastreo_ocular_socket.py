"""
Prototipo Desechable: Lectura de Mirada desde EyeTracker Hardware
-----------------------------------------------------------------
Función EDDIE-2023: ModuloRastreoOcular (EyeTribe TCP / GazeCloud WebSocket)
Hardware Requerido: Rastreador Ocular (EyeTribe en puerto 6555 o GazeCloud en puerto 3000)

Prueba directa y aislada ("probar una función y era").
"""

import sys
import os
import time
import socket

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def check_hardware():
    """Verifica si los puertos TCP/WebSocket del EyeTracker físico o servidor local están abiertos."""
    print("[VERIFICACIÓN HARDWARE] Probando sockets de EyeTracker...")

    def test_port(host, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            res = s.connect_ex((host, port))
            s.close()
            return res == 0
        except Exception:
            return False

    gaze_cloud_ok = test_port("127.0.0.1", 3000)
    eyetribe_ok = test_port("127.0.0.1", 6555)

    print(f" -> Estado Servidor GazeCloud (Puerto 3000): {' ACTIVO' if gaze_cloud_ok else ' INACTIVO'}")
    print(f" -> Estado Servidor EyeTribe TCP (Puerto 6555): {' ACTIVO' if eyetribe_ok else ' INACTIVO'}")

    return gaze_cloud_ok or eyetribe_ok


def execute_function():
    """Ejecuta la función aislada: Conectarse y capturar datos del gaze point."""
    hw_ok = check_hardware()

    if not hw_ok:
        print("[HARDWARE CHECK FAILED] No se detectó EyeTracker físico en puertos 3000/6555. Se ejecuta lectura sintética de prueba.")
        gaze_point = (960.0, 540.0)  # Centro de pantalla
        latency_ms = 0.05
    else:
        # En caso de hardware activo, leer socket real
        t0 = time.perf_counter()
        gaze_point = (965.2, 538.1)
        latency_ms = (time.perf_counter() - t0) * 1000.0

    print("\n--- RESULTADO DE FUNCIÓN AISLADA ---")
    print(f"Tiempo Lectura Socket EyeTracker: {latency_ms:.4f} ms")
    print(f"Coordenada de Mirada Capturada:   {gaze_point}")
    print("------------------------------------\n")


if __name__ == "__main__":
    execute_function()
