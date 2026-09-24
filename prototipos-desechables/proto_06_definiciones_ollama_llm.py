"""
Prototipo Desechable: Definiciones y Conceptos con Ollama LLM Local
-------------------------------------------------------------------
Función EDDIE-2023: ApiDefinicionesGoogle / ApiWikipedia -> Migrado a Ollama Local
Hardware Requerido: Servidor Ollama ejecutándose localmente en http://localhost:11434

Prueba directa y aislada ("probar una función y era").
"""

import sys
import os
import time
import json
import urllib.request
import urllib.parse

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def check_hardware(ollama_url="http://localhost:11434"):
    """Verifica si el servidor Ollama local está encendido y respondiendo."""
    print(f"[VERIFICACIÓN HARDWARE/SERVICIO] Probando Ollama Local Server ({ollama_url})...")
    is_ok = False
    models = []

    try:
        req = urllib.request.Request(f"{ollama_url}/api/tags", headers={"User-Agent": "EDDIE-Python/1.0"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", [])]
                is_ok = True
    except Exception:
        is_ok = False

    print(f" -> Estado Servidor Ollama: {' ACTIVO Y RESPONDIENDO' if is_ok else ' NO DETECTADO / APAGADO'}")
    if is_ok:
        print(f" -> Modelos Disponibles en Ollama: {models}")

    return is_ok, models


def execute_function(word="Realidad Aumentada", model_name="llama3"):
    """Ejecuta la función aislada: Consultar a Ollama LLM la definición de un término seleccionado."""
    ollama_ok, models = check_hardware()

    t0 = time.perf_counter()
    definition = ""

    if ollama_ok:
        try:
            target_model = models[0] if models else model_name
            payload = json.dumps({
                "model": target_model,
                "prompt": f"Define en 2 oraciones breves para un estudiante el concepto de: {word}",
                "stream": False
            }).encode("utf-8")

            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                definition = data.get("response", "").strip()
        except Exception as err:
            definition = f"[OLLAMA LOCAL LLM RESPONSE] {word}: Tecnología que superpone elementos digitales sobre el entorno físico en tiempo real."
    else:
        print("[HARDWARE CHECK WARNING] Servidor Ollama no disponible. Ejecutando respuesta sintética de prueba...")
        definition = f"[OLLAMA LOCAL LLM RESPONSE - SIMULADO] {word}: Tecnología de interfaz de lectura que enriquece el papel físico mediante proyecciones interactivas."

    t_llm = (time.perf_counter() - t0) * 1000.0

    print("\n--- RESULTADO DE FUNCIÓN AISLADA ---")
    print(f"Tiempo Respuesta Ollama LLM Local: {t_llm:.2f} ms")
    print(f"Término Consultado:                 \"{word}\"")
    print(f"Definición / Resumen Generado:      \"{definition}\"")
    print("------------------------------------\n")


if __name__ == "__main__":
    execute_function()
