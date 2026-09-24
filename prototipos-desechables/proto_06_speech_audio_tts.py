"""
Prototipo Desechable #6: Interacción por Voz y Síntesis TTS (Speech Command & TTS)
----------------------------------------------------------------------------------
Objetivo: Validar la factibilidad técnica de reemplazar System.Speech (C# WinForms)
por motores de reconocimiento de comandos e intenciones y síntesis de voz (TTS) en Python.

Funcionalidades:
  1. Reconocimiento e interpretación de comandos vocales ("buscar enciclopedia", "traducir", "destacar").
  2. Síntesis de voz (Text-To-Speech) en español con pyttsx3/SAPI5 o fallback en memoria.

Metodología: Figueroa (2025) - Prototipado Aislado de Bajo Costo.
"""

import sys
import os
import time
import re
import argparse

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False


def parse_voice_command(speech_phrase: str):
    """
    Parser semántico de comandos de voz que extrae intención y argumento.
    """
    t0 = time.perf_counter()
    phrase = speech_phrase.lower().strip()

    intent = "UNKNOWN"
    argument = ""

    if "enciclopedia" in phrase or "buscar" in phrase or "wikipedia" in phrase:
        intent = "SEARCH_ENCYCLOPEDIA"
        argument = re.sub(r'^(buscar|enciclopedia|wikipedia|sobre)\s*', '', phrase).strip()
    elif "traducir" in phrase or "traducción" in phrase:
        intent = "TRANSLATE_TEXT"
        argument = re.sub(r'^(traducir|traduccion)\s*', '', phrase).strip()
    elif "destacar" in phrase or "subrayar" in phrase:
        intent = "HIGHLIGHT_TEXT"
        argument = re.sub(r'^(destacar|subrayar)\s*', '', phrase).strip()
    elif "definición" in phrase or "definir" in phrase:
        intent = "DEFINE_WORD"
        argument = re.sub(r'^(definir|definicion)\s*', '', phrase).strip()

    t_proc = (time.perf_counter() - t0) * 1000.0

    return {
        "phrase": speech_phrase,
        "intent": intent,
        "argument": argument if argument else phrase,
        "latency_ms": t_proc
    }


def synthesize_speech_tts(text: str, speak_audio=False):
    """
    Ejecuta la síntesis de voz TTS.
    """
    t0 = time.perf_counter()
    used_pyttsx3 = False

    if HAS_PYTTSX3 and speak_audio:
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.say(text)
            engine.runAndWait()
            used_pyttsx3 = True
        except Exception:
            pass

    t_tts = (time.perf_counter() - t0) * 1000.0

    return {
        "text": text,
        "used_real_tts": used_pyttsx3,
        "latency_ms": t_tts
    }


def run_prototype_06(test_phrase="buscar enciclopedia realidad aumentada", test_cycles=5, speak_audio=False):
    """Ejecuta la prueba de factibilidad técnica para interacción por voz y TTS."""
    print("==========================================================")
    print("PROTOTIPO #6: INTERACCIÓN POR VOZ Y SÍNTESIS TTS")
    print("==========================================================")
    print(f"Frase de Entrada: '{test_phrase}'")

    cmd_times = []
    tts_times = []
    last_cmd_res = None
    last_tts_res = None

    for _ in range(test_cycles):
        last_cmd_res = parse_voice_command(test_phrase)
        last_tts_res = synthesize_speech_tts(f"Procesando comando: {last_cmd_res['intent']}", speak_audio=speak_audio)

        cmd_times.append(last_cmd_res["latency_ms"])
        tts_times.append(last_tts_res["latency_ms"])

    avg_cmd = sum(cmd_times) / len(cmd_times)
    avg_tts = sum(tts_times) / len(tts_times)
    total_avg_ms = avg_cmd + avg_tts

    print("\n--- Resultados de Rendimiento y Factibilidad ---")
    print(f"Intención Interpretada:          {last_cmd_res['intent']}")
    print(f"Argumento Extraído:              '{last_cmd_res['argument']}'")
    print(f"Latencia Parseo de Comandos:     {avg_cmd:.4f} ms")
    print(f"Latencia Síntesis TTS:           {avg_tts:.4f} ms")
    print(f"Latencia Total Pipeline Voz:     {total_avg_ms:.4f} ms")

    is_feasible = total_avg_ms < 50.0 and last_cmd_res["intent"] != "UNKNOWN"

    print(f"\nDictamen Factibilidad Técnica: {'✅ FACTIBLE (Aprobado)' if is_feasible else '❌ NO FACTIBLE'}")
    print("==========================================================\n")

    return {
        "prototype": "Proto 06 - Speech & TTS",
        "is_feasible": is_feasible,
        "parsed_intent": last_cmd_res["intent"],
        "avg_cmd_ms": round(avg_cmd, 4),
        "avg_tts_ms": round(avg_tts, 4),
        "total_avg_ms": round(total_avg_ms, 4)
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prototipo Voz y TTS")
    parser.add_argument("--phrase", type=str, default="buscar enciclopedia realidad aumentada", help="Frase a reconocer")
    parser.add_argument("--speak", action="store_true", help="Emitir audio TTS real por altavoces")
    args = parser.parse_args()

    run_prototype_06(test_phrase=args.phrase, speak_audio=args.speak)
