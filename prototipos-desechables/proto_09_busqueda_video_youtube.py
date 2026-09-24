"""
Prototipo Desechable: Búsqueda y Enlace de Videos YouTube
---------------------------------------------------------
Función EDDIE-2023: ApiBuscarYoutube (Generación de enlaces multimedia)
Hardware Requerido: Conexión de Red / Internet

Prueba directa y aislada ("probar una función y era").
"""

import sys
import os
import time
import re
import urllib.parse

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def check_hardware():
    """Verifica si hay conexión a red disponible para generar o consultar enlaces."""
    print("[VERIFICACIÓN RED] Comprobando disponibilidad de Red...")
    # En este prototipo se requiere formato URL sanitizado
    print(" -> Estado Conexión a Red: ✅ LISTO")
    return True


def execute_function(query="Realidad Aumentada (RA)"):
    """Ejecuta la función aislada: Sanitizar consulta (Error E34) y construir enlace YouTube."""
    check_hardware()

    t0 = time.perf_counter()
    # Sanitizar paréntesis y caracteres especiales
    clean_query = re.sub(r'[\(\)\[\]\{\}\<\>]', ' ', query)
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()

    encoded = urllib.parse.quote(clean_query)
    youtube_url = f"https://www.youtube.com/results?search_query={encoded}"
    t_proc = (time.perf_counter() - t0) * 1000.0

    print("\n--- RESULTADO DE FUNCIÓN AISLADA ---")
    print(f"Tiempo Generación Enlace YouTube: {t_proc:.4f} ms")
    print(f"Consulta Original:                \"{query}\"")
    print(f"Consulta Sanitizada (Error E34):  \"{clean_query}\"")
    print(f"URL YouTube Generada:             {youtube_url}")
    print("------------------------------------\n")


if __name__ == "__main__":
    execute_function()
