"""
DEMO REAL F24 – Speech-to-Text (grabación real de micrófono)
=============================================================
Graba audio REAL desde el micrófono por 5 segundos,
guarda el archivo WAV y muestra la forma de onda.
Si sounddevice no está instalado, lo instala automáticamente.

Habla algo durante la grabación.
"""
import pathlib, sys, subprocess, time, struct, wave
import cv2, numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

print("="*55)
print("  DEMO REAL F24 – STT: Grabación de micrófono")
print("="*55)

# Intentar importar sounddevice
try:
    import sounddevice as sd
    HAS_SD = True
except ImportError:
    print("  Instalando sounddevice…")
    subprocess.run([sys.executable, "-m", "pip", "install", "sounddevice", "--quiet"], check=False)
    try:
        import sounddevice as sd
        HAS_SD = True
    except Exception:
        HAS_SD = False

if not HAS_SD:
    print("  [!] sounddevice no disponible. Verifica tu entorno.")
    sys.exit(1)

SAMPLE_RATE = 16000
DURATION    = 5       # segundos de grabación
WAV_OUT     = EVID / "real_f24_recording.wav"

# Mostrar ventana de cuenta regresiva
W, H = 700, 350
cv2.namedWindow("EDDIE – F24 Grabación STT")

# Cuenta regresiva antes de grabar
for i in range(3, 0, -1):
    canvas = np.full((H, W, 3), 25, np.uint8)
    cv2.putText(canvas,"F24 – Grabación de voz",(W//2-180,80),
                cv2.FONT_HERSHEY_SIMPLEX,0.9,(0,220,100),2)
    cv2.putText(canvas,f"Grabando en {i}…",(W//2-120,180),
                cv2.FONT_HERSHEY_SIMPLEX,1.2,(0,180,255),3)
    cv2.putText(canvas,"Prepárate para hablar",(W//2-145,240),
                cv2.FONT_HERSHEY_SIMPLEX,0.6,(180,180,180),1)
    cv2.imshow("EDDIE – F24 Grabación STT", canvas)
    cv2.waitKey(1000)

# Ventana "grabando"
canvas = np.full((H, W, 3), 25, np.uint8)
cv2.putText(canvas,"● GRABANDO…",(W//2-130,160),
            cv2.FONT_HERSHEY_SIMPLEX,1.3,(0,0,220),3)
cv2.putText(canvas,f"Duración: {DURATION} segundos",(W//2-150,210),
            cv2.FONT_HERSHEY_SIMPLEX,0.6,(180,180,180),1)
cv2.putText(canvas,"Habla ahora por favor",(W//2-130,240),
            cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,200,200),1)
cv2.imshow("EDDIE – F24 Grabación STT", canvas)
cv2.waitKey(1)

print(f"\n  ● GRABANDO {DURATION} segundos… ¡Habla ahora!\n")

# Grabación real
audio_data = sd.rec(int(DURATION * SAMPLE_RATE),
                    samplerate=SAMPLE_RATE, channels=1,
                    dtype=np.int16)
t_start = time.time()

# Mostrar progreso durante grabación
while time.time()-t_start < DURATION:
    elapsed   = time.time()-t_start
    remaining = DURATION - elapsed
    progress  = elapsed / DURATION

    canvas = np.full((H, W, 3), 25, np.uint8)
    cv2.putText(canvas,"● GRABANDO…",(W//2-130,80),
                cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,0,220),3)

    # Barra de progreso
    bar_w = int((W-60)*progress)
    cv2.rectangle(canvas,(30,130),(W-30,160),(50,50,50),-1)
    cv2.rectangle(canvas,(30,130),(30+bar_w,160),(0,180,255),-1)
    cv2.putText(canvas,f"{elapsed:.1f}s / {DURATION}s",
                (W//2-50,155),cv2.FONT_HERSHEY_SIMPLEX,0.45,(255,255,255),1)

    # Nivel de audio en tiempo real (aproximado)
    idx = max(0, int(elapsed*SAMPLE_RATE)-1024)
    chunk = audio_data[idx:idx+1024] if idx < len(audio_data) else np.zeros(1024,np.int16)
    level = np.abs(chunk).mean() / 32768.0
    bar_h = int(level * 120)
    cv2.rectangle(canvas,(W//2-10,270),(W//2+10,270-bar_h),(0,220,100),-1)
    cv2.putText(canvas,"Nivel",(W//2-18,290),cv2.FONT_HERSHEY_SIMPLEX,0.35,(120,120,120),1)

    cv2.putText(canvas,f"Faltan: {remaining:.1f}s",
                (W//2-60,320),cv2.FONT_HERSHEY_SIMPLEX,0.55,(200,200,200),1)

    cv2.imshow("EDDIE – F24 Grabación STT", canvas)
    cv2.waitKey(30)

sd.wait()
print("  ✓ Grabación completada.")

# Guardar WAV
with wave.open(str(WAV_OUT), "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)   # 16-bit
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(audio_data.tobytes())
print(f"  [GUARDADO] {WAV_OUT.name}  ({WAV_OUT.stat().st_size/1024:.1f} KB)")

# Mostrar forma de onda
audio_flat = audio_data.flatten().astype(np.float32) / 32768.0
canvas = np.full((H, W, 3), 25, np.uint8)
cv2.putText(canvas,"F24 – STT: Forma de onda grabada",(15,38),
            cv2.FONT_HERSHEY_SIMPLEX,0.65,(0,220,100),2)
cv2.putText(canvas,f"WAV: {WAV_OUT.name} | {SAMPLE_RATE}Hz | {DURATION}s | {len(audio_flat)} muestras",
            (15,62),cv2.FONT_HERSHEY_SIMPLEX,0.38,(180,180,180),1)

# Dibujar forma de onda
step    = max(1, len(audio_flat)//(W-60))
samples = audio_flat[::step][:W-60]
prev    = None
for i, s in enumerate(samples):
    y_val = int(H//2 - s*(H//2-70))
    pt    = (30+i, y_val)
    if prev:
        cv2.line(canvas, prev, pt, (0,180,255), 1)
    prev = pt

# Línea central
cv2.line(canvas,(30,H//2),(W-30,H//2),(60,60,60),1)
rms = float(np.sqrt(np.mean(audio_flat**2)))
peak= float(np.max(np.abs(audio_flat)))
cv2.putText(canvas,f"RMS={rms:.4f}  Peak={peak:.4f}  Fs={SAMPLE_RATE}Hz",
            (15,H-40),cv2.FONT_HERSHEY_SIMPLEX,0.42,(150,150,150),1)
cv2.putText(canvas,"Siguiente paso: Whisper ASR para transcripción",
            (15,H-18),cv2.FONT_HERSHEY_SIMPLEX,0.38,(100,100,100),1)

# Intentar transcripción con whisper si está instalado
try:
    import whisper
    print("  Transcribiendo con Whisper…")
    model = whisper.load_model("tiny")
    result = model.transcribe(str(WAV_OUT), language="es")
    transcription = result.get("text","").strip()
    print(f"  Transcripción: '{transcription}'")
    cv2.putText(canvas,f"Whisper: '{transcription[:60]}'",
                (15,H-5),cv2.FONT_HERSHEY_SIMPLEX,0.42,(0,220,100),1)
except ImportError:
    cv2.putText(canvas,"(Instala openai-whisper para transcripción automática)",
                (15,H-5),cv2.FONT_HERSHEY_SIMPLEX,0.38,(100,100,100),1)
except Exception as e:
    cv2.putText(canvas,f"Whisper: {str(e)[:50]}",(15,H-5),
                cv2.FONT_HERSHEY_SIMPLEX,0.36,(100,100,120),1)

out = EVID/"real_f24_waveform.png"
cv2.imwrite(str(out), canvas)
print(f"  [GUARDADO] {out}")
cv2.imshow("EDDIE – F24 Grabación STT", canvas)
print("  Presiona cualquier tecla para cerrar…")
cv2.waitKey(0)
cv2.destroyAllWindows()
print("  F24 COMPLETADO\n")
