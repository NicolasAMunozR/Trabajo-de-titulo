"""
Prototipo F24 Comandos de voz para EDDIE
Grabar audio real desde el micrófono.
Guardar el WAV.
Reconocer voz con SpeechRecognition.
Interpretar comandos de voz en español.

Requisitos:
- pip install SpeechRecognition sounddevice opencv-python numpy
"""

import os
import re
import sys
import time
import wave
import webbrowser
import urllib.parse
import pathlib
import subprocess

import cv2
import numpy as np
import sounddevice as sd
import speech_recognition as sr

EVID = pathlib.Path(__file__).resolve().parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

WAV_OUT = EVID / "f24_command.wav"

SAMPLE_RATE = 16000
DURATION = 5

def instalar_paquete(nombre: str):
    print(f"  [INFO] Instalando {nombre}...")
    subprocess.run([sys.executable, "-m", "pip", "install", nombre, "--quiet"], check=False)

def verificar_dependencias():
    try:
        import speech_recognition  # noqa: F401
    except Exception:
        instalar_paquete("SpeechRecognition")

    try:
        import sounddevice  # noqa: F401
    except Exception:
        instalar_paquete("sounddevice")

    try:
        import cv2  # noqa: F401
    except Exception:
        instalar_paquete("opencv-python")

    try:
        import numpy  # noqa: F401
    except Exception:
        instalar_paquete("numpy")

verificar_dependencias()

def limpiar_texto(texto: str) -> str:
    return re.sub(r"\s+", " ", texto or "").strip()

def mostrar_texto_central(window_name: str, titulo: str, subtitulo: str,
                         color_titulo=(0, 220, 100), color_sub=(180, 180, 180)):
    canvas = np.full((280, 700, 3), 25, dtype=np.uint8)
    cv2.putText(canvas, titulo, (120, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color_titulo, 2)
    cv2.putText(canvas, subtitulo, (140, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_sub, 2)
    cv2.imshow(window_name, canvas)
    cv2.waitKey(30)

def grabar_audio_real(segundos: int = 5, out_path: pathlib.Path = WAV_OUT):
    print(f"\nGRABANDO {segundos} segundos... habla ahora.\n")

    cv2.namedWindow("F24: Comandos por voz", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("F24: Comandos por voz", 700, 280)

    for count in range(3, 0, -1):
        mostrar_texto_central(
            "F24: Comandos por voz",
            "F24 Comandos de voz",
            f"Grabando en {count}",
            (0, 220, 100),
            (180, 180, 180),
        )
        time.sleep(1)

    audio_data = sd.rec(
        int(segundos * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype=np.int16,
    )

    t_start = time.time()
    while time.time() - t_start < segundos:
        elapsed = time.time() - t_start
        progress = elapsed / segundos
        canvas = np.full((280, 700, 3), 25, dtype=np.uint8)

        cv2.putText(canvas, "GRABANDO…", (220, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 220), 2)
        cv2.putText(canvas, f"Duración: {segundos}s", (240, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

        cv2.rectangle(canvas, (60, 150), (640, 190), (60, 60, 60), 2)
        bar_width = int((640 - 60) * progress)
        cv2.rectangle(canvas, (60, 150), (60 + bar_width, 190), (0, 180, 255), -1)

        idx = max(0, int(elapsed * SAMPLE_RATE) - 1024)
        chunk = audio_data[idx:idx + 1024] if idx < len(audio_data) else np.zeros(1024, np.int16)
        level = np.abs(chunk).mean() / 32768.0
        bar_h = int(level * 70)
        cv2.rectangle(canvas, (330, 210), (370, 210 - bar_h), (0, 220, 100), -1)
        cv2.putText(canvas, "Nivel", (300, 235), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (190, 190, 190), 1)

        cv2.imshow("F24: Comandos por voz", canvas)
        cv2.waitKey(30)

    sd.wait()

    with wave.open(str(out_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())

    print(f"[GUARDADO] {out_path.name} ({out_path.stat().st_size / 1024:.1f} KB)")
    cv2.destroyAllWindows()
    return out_path

def reconocer_voz_desde_wav(wav_path: pathlib.Path):
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(str(wav_path)) as source:
            audio = recognizer.record(source)
        texto = recognizer.recognize_google(audio, language="es-ES")
        texto = limpiar_texto(texto)
        print(f"[TRANSCRIPCIÓN] {texto}")
        return texto
    except sr.UnknownValueError:
        print("No se entendió el audio.")
        return ""
    except sr.RequestError as e:
        print(f"Error con SpeechRecognition/Google: {e}")
        return ""
    except Exception as e:
        print(f"Error al reconocer voz: {e}")
        return ""

def normalizar_comando(texto: str) -> str:
    return texto.lower().strip()

def interpretar_comando(texto: str):
    cmd = normalizar_comando(texto)
    if not cmd:
        return {"accion": "desconocido", "texto": ""}

    if "ayuda" in cmd or "menu" in cmd or "comandos" in cmd:
        return {"accion": "ayuda", "texto": texto}

    if "salir" in cmd or "cerrar" in cmd or "terminar" in cmd:
        return {"accion": "salir", "texto": texto}

    if "enciclopedia" in cmd or "buscar" in cmd:
        if "enciclopedia" in cmd:
            q = cmd.replace("enciclopedia", "").replace("buscar", "").strip()
        else:
            q = cmd.replace("buscar", "").strip()
        if not q:
            q = "EDDIE sistema educativo"
        return {"accion": "buscar_web", "texto": q}

    if "traducir" in cmd:
        q = cmd.replace("traducir", "").strip()
        if not q:
            q = "hola mundo"
        return {"accion": "traducir", "texto": q}

    if "abrir pdf" in cmd or "abrir documento" in cmd:
        return {"accion": "abrir_pdf", "texto": texto}

    return {"accion": "desconocido", "texto": texto}

def ejecutar_comando(comando):
    accion = comando.get("accion", "desconocido")
    texto = comando.get("texto", "")

    if accion == "ayuda":
        print("\n  COMANDOS DISPONIBLES:")
        print("    - buscar enciclopedia <texto>")
        print("    - buscar <texto>")
        print("    - traducir <texto>")
        print("    - abrir pdf")
        print("    - ayuda")
        print("    - salir")
        return

    if accion == "salir":
        print("  [ACCION] Saliendo del demo.")
        raise SystemExit(0)

    if accion == "buscar_web":
        query = urllib.parse.quote_plus(texto)
        url = f"https://www.google.com/search?q={query}"
        print(f"[ACCION] Abriendo búsqueda web: {url}")
        webbrowser.open(url)
        return

    if accion == "traducir":
        query = urllib.parse.quote_plus(texto)
        url = f"https://translate.google.com/?sl=es&tl=en&text={query}"
        print(f"[ACCION] Abriendo traductor: {url}")
        webbrowser.open(url)
        return

    if accion == "abrir_pdf":
        pdfs = sorted(p for p in pathlib.Path(__file__).resolve().parent.iterdir() if p.suffix.lower() == ".pdf")
        if pdfs:
            pdf = pdfs[0]
            print(f"[ACCION] Abriendo PDF: {pdf}")
            try:
                os.startfile(str(pdf))
            except Exception:
                webbrowser.open(f"file:///{pdf.resolve()}")
        else:
            print("No hay PDF en la carpeta actual.")
        return

    print(f"Comando no reconocido: '{texto}'")
    print("  Prueba: 'buscar enciclopedia EDDIE', 'traducir hola', 'abrir pdf', 'ayuda'.")

def main():
    wav_path = grabar_audio_real(DURATION, WAV_OUT)

    with wave.open(str(wav_path), "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

    texto = reconocer_voz_desde_wav(wav_path)

    if not texto:
        print("\nNo se pudo reconocer la voz.")
        texto = input("\nEscribe el comando manualmente: ").strip()
        if not texto:
            print("Comando vacío. Finalizando.")
            return

    print(f"\n[COMANDO DETECTADO] {texto}")

    comando = interpretar_comando(texto)
    ejecutar_comando(comando)

    print("\nF24 COMPLETADO")

if __name__ == "__main__":
    main()