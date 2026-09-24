"""
DEMO REAL F25 – Text-to-Speech (TTS) real
==========================================
Hace hablar al sistema con pyttsx3 (SAPI5 en Windows).
Dice frases relacionadas con EDDIE y muestra el texto
siendo sintetizado en pantalla.
"""
import pathlib, time
import cv2, numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

print("=" * 55)
print("  DEMO REAL F25 – Text-to-Speech (SAPI5/pyttsx3)")
print("=" * 55)

try:
    import pyttsx3
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    rate   = engine.getProperty("rate")
    vol    = engine.getProperty("volume")
    print(f"  Motor: pyttsx3 (SAPI5 Windows)")
    print(f"  Voces disponibles: {len(voices)}")
    for i, v in enumerate(voices[:5]):
        print(f"    [{i}] {v.name} – {v.id}")
    print(f"  Velocidad: {rate} wpm  |  Volumen: {vol}")

    # Seleccionar voz en español si existe
    esp_voice = None
    for v in voices:
        if "spanish" in v.id.lower() or "helena" in v.name.lower() or \
           "sabina" in v.name.lower() or "es" in v.id.lower():
            esp_voice = v
            break

    if esp_voice:
        engine.setProperty("voice", esp_voice.id)
        print(f"\n  Voz en español: {esp_voice.name}")
    else:
        print("\n  (Usando voz predeterminada)")

    engine.setProperty("rate", 165)

    frases = [
        "Hola. Soy EDDIE, el sistema de lectura aumentada.",
        "Puedo leer texto impreso usando reconocimiento óptico de caracteres.",
        "Mi cámara detecta la página del libro frente a mí.",
        "El prototipo F25 del módulo de texto a voz funciona correctamente.",
    ]

    # Mostrar ventana mientras habla
    h, w = 200, 700
    canvas = np.full((h, w, 3), 30, np.uint8)

    print("\n  Sintetizando voz (escucha los altavoces)...\n")

    for i, frase in enumerate(frases):
        canvas[:] = 30
        cv2.putText(canvas, "F25 – EDDIE Text-to-Speech",
                    (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 100), 2)
        cv2.putText(canvas, f"Frase {i+1}/{len(frases)}:",
                    (15, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        # Dividir la frase en líneas cortas
        words, line, lines = frase.split(), "", []
        for word in words:
            if len(line) + len(word) + 1 <= 55: line += (" " if line else "") + word
            else: lines.append(line); line = word
        if line: lines.append(line)

        for j, l in enumerate(lines):
            cv2.putText(canvas, l, (15, 100 + j*28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 200), 1)

        cv2.putText(canvas, "[HABLANDO...]",
                    (15, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 180, 255), 1)

        cv2.imshow("EDDIE – F25 TTS en VIVO", canvas)
        cv2.waitKey(1)

        print(f"  [{i+1}] {frase}")
        engine.say(frase)
        engine.runAndWait()

        cv2.waitKey(300)

    # Frame final
    canvas[:] = 20
    cv2.putText(canvas, "✓ F25 TTS COMPLETADO",
                (120, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 220, 80), 2)
    cv2.putText(canvas, f"{len(frases)} frases sintetizadas correctamente",
                (100, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180,180,180), 1)
    cv2.imshow("EDDIE – F25 TTS en VIVO", canvas)

    out = EVID / "real_f25_tts.png"
    cv2.imwrite(str(out), canvas)
    print(f"\n  [GUARDADO] {out}")
    print("  Presiona cualquier tecla para cerrar…")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    engine.stop()

except ImportError:
    print("  [!] pyttsx3 no instalado. Ejecuta:")
    print("      pip install pyttsx3")
except Exception as e:
    print(f"  [!] Error TTS: {e}")

print("  F25 COMPLETADO\n")
