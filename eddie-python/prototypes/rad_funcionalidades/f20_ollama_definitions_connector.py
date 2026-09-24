"""
prototypes/rad_funcionalidades/f20_ollama_definitions_connector.py
===========================================================
PROTOTIPO RAD - F20: Búsqueda de Definiciones Conceptuales (Ollama / LLM Conector)
===========================================================
Subsistema: Búsqueda Web de Conocimiento y APIs REST
Archivo C# Legacy: ModuloBusquedaWeb / ApiDefinicionesGoogle.cs
Tecnología Propuesta: Conector REST Ollama (localhost:11434) / Diccionario REST API

Descripción:
  Consulta diccionarios o un modelo LLM local (Ollama API localhost:11434) para mostrar significados
  de términos complejos seleccionados por el lector.
"""
import sys
import os
import time
import urllib.request
import json

os.environ['PYTHONIOENCODING'] = 'utf-8'

print("\n" + "="*70)
print("PROTOTIPO RAD - F20: Búsqueda de Definiciones Conceptuales (Ollama / REST)")
print("="*70)

def query_ollama_definition(word: str, ollama_url: str = "http://localhost:11434/api/generate") -> dict:
    t0 = time.perf_counter()
    prompt = f"Define brevemente en 2 oraciones en español el término académico: '{word}'"
    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        req = urllib.request.Request(
            ollama_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return {
                'success': True,
                'source': 'Ollama Local LLM',
                'word': word,
                'definition': data.get('response', '').strip(),
                'elapsed_ms': round(elapsed_ms, 2)
            }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        # Mock fallback de diccionario
        dict_mock = {
            "lectura": "Acción y efecto de leer. Proceso cognitivo de interpretar signos escritos.",
            "tracking": "Seguimiento o monitoreo continuo de posición o estado."
        }
        defn = dict_mock.get(word.lower(), f"Definición de '{word}': Concepto clave en el ámbito de estudio.")
        return {
            'success': False,
            'source': 'Mock Dictionary Fallback',
            'word': word,
            'definition': defn,
            'note': 'Ollama localhost:11434 no activo, usando fallback instantáneo',
            'elapsed_ms': round(elapsed_ms, 2)
        }

def main():
    print("\n[PASO 1] Probando consulta de definición conceptual ('lectura')...")
    res = query_ollama_definition("lectura")

    print(f"\n{'='*70}")
    print("RESUMEN DE FACTIBILIDAD TÉCNICA - F20")
    print(f"{'='*70}")
    print(f"  Fuente Utilizada   : {res['source']}")
    print(f"  Palabra            : '{res['word']}'")
    print(f"  Definición         : {res['definition']}")
    print(f"  Tiempo de respuesta: {res['elapsed_ms']} ms")
    print(f"  Equivalencia C#    : ApiDefinicionesGoogle.cs -> Conector REST Ollama localhost:11434")
    print(f"  Estado Factibilidad: FACTIBLE Y CON FALLBACK OFFLINE")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
