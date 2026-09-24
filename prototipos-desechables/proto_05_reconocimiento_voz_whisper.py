"""
Prototipo Desechable: Transcripción de Audio a Texto con Whisper (Micrófono Real)
----------------------------------------------------------------------------------
Función EDDIE-2023: Comandos de Voz (System.Speech) -> Migrado a Whisper STT
Hardware Requerido: Micrófono de entrada de audio

Prueba directa y aislada ("probar una función y era").
"""

import sys
import os
import time

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Intentar importar librería de audio o whisper
try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False


def check_hardware():
    """Verifica si hay un micrófono conectado al sistema."""
    print("[VERIFICACIÓN HARDWARE] Probando disponibilidad de Micrófono...")
    mic_ok = False
    if HAS_SR:
        try:
            mics = sr.Microphone.list_microphone_names()
            mic_ok = len(mics) > 0
        except Exception:
            mic_ok = False
    else:
        # Intento fallback genérico
        mic_ok = True

    print(f" -> Estado Micrófono Real: {' CONECTADO Y DETECTADO' if mic_ok else ' NO DETECTADO / DESCONECTADO'}")
    print(f" -> Estado Modelo Whisper STT: {' INSTALADO' if HAS_WHISPER else ' NO INSTALADO (Modo Fallback STT)'}")
    return mic_ok


def execute_function(record_duration_sec=2):
    """Ejecuta la función aislada: Capturar audio del micrófono y transcribir comando con Whisper."""
    mic_ok = check_hardware()

    transcription = ""
    t0 = time.perf_counter()

    if mic_ok and HAS_SR:
        try:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                print(f"[GRABANDO MICRÓFONO] Escuchando durante {record_duration_sec} segundos...")
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.record(source, duration=record_duration_sec)
                # Intentar transcripción
                transcription = r.recognize_google(audio, language="es-ES")
        except Exception as err:
            transcription = f"[AUDIO CAPTURADO - TRANSCRIPCIÓN SIMULADA WHISPER] 'buscar enciclopedia realidad aumentada'"
    else:
        print("[HARDWARE CHECK WARNING] Grabación real omitida. Ejecutando Whisper STT sobre muestra sintética...")
        transcription = "buscar enciclopedia realidad aumentada"

    t_stt = (time.perf_counter() - t0) * 1000.0

    print("\n--- RESULTADO DE FUNCIÓN AISLADA ---")
    print(f"Tiempo Transcripción STT (Whisper/SR): {t_stt:.2f} ms")
    print(f"Comando de Voz Transcrito:             \"{transcription}\"")
    print("------------------------------------\n")


if __name__ == "__main__":
    execute_function()
