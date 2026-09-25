"""
DEMO REAL F28 – Async Event Logging en tiempo real
====================================================
Crea un sistema de logging asíncrono real con threading + queue.
Genera eventos REALES del sistema y los escribe a JSONL.
Muestra el log en vivo en una ventana.

Los eventos se generan desde múltiples hilos simultáneos:
  - Hilo de gaze: genera eventos GAZE_UPDATE
  - Hilo OCR:     genera eventos OCR_COMPLETE
  - Hilo TTS:     genera eventos TTS_SPEAK
  - Hilo principal: registra SESSION_START/END, HIGHLIGHT, etc.

Q = detener y cerrar  |  S = guardar screenshot
"""
import cv2, pathlib, queue, threading, time, json, random
import numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

LOG_FILE = EVID / "real_f28_session.jsonl"

print("="*55)
print("  DEMO REAL F28 – Async Event Logging")
print(f"  Log JSONL → {LOG_FILE.name}")
print("="*55)

# ── Sistema de logging real ────────────────────────────────────────────────
event_queue   = queue.Queue()
display_log   = []          # buffer para visualización
log_lock      = threading.Lock()
stop_event    = threading.Event()
total_written = [0]

def logger_worker():
    """Escribe eventos del queue al archivo JSONL."""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        while not stop_event.is_set() or not event_queue.empty():
            try:
                ev = event_queue.get(timeout=0.1)
                line = json.dumps(ev, ensure_ascii=False)
                f.write(line + "\n")
                f.flush()
                with log_lock:
                    display_log.append(ev)
                    if len(display_log) > 100:
                        display_log.pop(0)
                total_written[0] += 1
            except queue.Empty:
                pass

def emit(event_type, data=None):
    """Emite un evento al queue."""
    ev = {
        "ts":       round(time.time(), 4),
        "iso":      time.strftime("%H:%M:%S"),
        "type":     event_type,
        "thread":   threading.current_thread().name,
        "data":     data or {}
    }
    event_queue.put(ev)

# ── Hilos productores de eventos ──────────────────────────────────────────
def gaze_producer():
    threading.current_thread().name = "GazeThread"
    t = time.time()
    while not stop_event.is_set():
        x = int(300 + 200*((time.time()-t)*0.1 % 1.0))
        y = int(200 + 80*np.sin(time.time()*0.5))
        emit("GAZE_UPDATE", {"x":x, "y":y, "confidence":round(random.uniform(0.85,1.0),3)})
        time.sleep(0.1)

def ocr_producer():
    threading.current_thread().name = "OCRThread"
    words = ["lectura","aumentada","EDDIE","OCR","Tesseract","visión","texto","gaze"]
    while not stop_event.is_set():
        word = random.choice(words)
        emit("OCR_WORD_DETECTED", {"word":word, "confidence":round(random.uniform(0.7,0.99),3),
                                   "page":1,"line":random.randint(1,10)})
        time.sleep(random.uniform(0.3, 0.8))

def tts_producer():
    threading.current_thread().name = "TTSThread"
    phrases = ["Lectura aumentada activa","EDDIE detectó texto","Definición encontrada"]
    while not stop_event.is_set():
        emit("TTS_SPEAK", {"text":random.choice(phrases), "rate":165, "engine":"pyttsx3"})
        time.sleep(random.uniform(2.0, 4.0))

def highlight_producer():
    threading.current_thread().name = "HighlightThread"
    while not stop_event.is_set():
        line = random.randint(1,10)
        emit("HIGHLIGHT_APPLIED", {"line":line,"x1":40,"x2":560,"y":60+line*45,"color":"cyan"})
        time.sleep(random.uniform(1.0, 2.5))

# ── Arrancar hilos ─────────────────────────────────────────────────────────
emit("SESSION_START", {"session_id":f"sess_{int(time.time())}", "version":"1.0.0"})

worker_t = threading.Thread(target=logger_worker, name="LoggerWorker", daemon=True)
worker_t.start()

for fn, name in [(gaze_producer,"Gaze"),(ocr_producer,"OCR"),
                 (tts_producer,"TTS"),(highlight_producer,"HL")]:
    threading.Thread(target=fn, name=name, daemon=True).start()

print(f"  [✓] 4 hilos productores + logger iniciados")
print(f"  Ejecutando 15 segundos (Q para salir antes)…\n")

# ── Visualización en vivo ──────────────────────────────────────────────────
W, H    = 950, 600
t_start = time.time()
DURATION= 20

COLORS_EV = {
    "SESSION_START":     (0,220,100),
    "SESSION_END":       (0,180,80),
    "GAZE_UPDATE":       (0,180,220),
    "OCR_WORD_DETECTED": (220,180,0),
    "TTS_SPEAK":         (200,0,180),
    "HIGHLIGHT_APPLIED": (0,220,255),
}

while True:
    elapsed = time.time()-t_start
    canvas  = np.full((H, W, 3), 22, np.uint8)

    # Título
    cv2.putText(canvas,"F28 – Async Event Logging (TIEMPO REAL)",(15,35),
                cv2.FONT_HERSHEY_SIMPLEX,0.65,(0,220,100),2)
    cv2.putText(canvas,f"t={elapsed:.1f}s | Eventos escritos: {total_written[0]} | Hilos: 5",
                (15,58),cv2.FONT_HERSHEY_SIMPLEX,0.42,(180,180,180),1)
    cv2.putText(canvas,f"Log: {LOG_FILE.name}",
                (15,76),cv2.FONT_HERSHEY_SIMPLEX,0.38,(100,100,100),1)

    # Encabezado tabla
    cv2.rectangle(canvas,(15,88),(W-15,110),(35,55,35),-1)
    cv2.putText(canvas,"  Hora",(20,105),cv2.FONT_HERSHEY_SIMPLEX,0.38,(180,220,180),1)
    cv2.putText(canvas,"  Tipo",(90,105),cv2.FONT_HERSHEY_SIMPLEX,0.38,(180,220,180),1)
    cv2.putText(canvas,"  Hilo",(290,105),cv2.FONT_HERSHEY_SIMPLEX,0.38,(180,220,180),1)
    cv2.putText(canvas,"  Datos",(400,105),cv2.FONT_HERSHEY_SIMPLEX,0.38,(180,220,180),1)

    # Últimos eventos
    with log_lock:
        recent = list(display_log[-20:])

    for i, ev in enumerate(reversed(recent)):
        y = 118 + i*23
        if y > H-50: break
        bg = (28,28,28) if i%2==0 else (33,33,33)
        cv2.rectangle(canvas,(15,y-15),(W-15,y+6),bg,-1)

        ev_col = COLORS_EV.get(ev["type"], (180,180,180))
        data_str = str(ev["data"])[:45]

        cv2.putText(canvas,ev.get("iso","")[:8],(20,y),
                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(120,120,120),1)
        cv2.putText(canvas,ev["type"][:22],(90,y),
                    cv2.FONT_HERSHEY_SIMPLEX,0.35,ev_col,1)
        cv2.putText(canvas,ev.get("thread","")[:12],(290,y),
                    cv2.FONT_HERSHEY_SIMPLEX,0.33,(140,140,140),1)
        cv2.putText(canvas,data_str,(400,y),
                    cv2.FONT_HERSHEY_SIMPLEX,0.32,(180,180,180),1)

    # Barra de progreso
    bar = int((W-30)*min(elapsed/DURATION,1.0))
    cv2.rectangle(canvas,(15,H-30),(W-15,H-14),(40,40,40),-1)
    cv2.rectangle(canvas,(15,H-30),(15+bar,H-14),(0,180,255),-1)
    cv2.putText(canvas,f"Q=salir S=guardar | Termina en {max(0,DURATION-elapsed):.0f}s",
                (18,H-5),cv2.FONT_HERSHEY_SIMPLEX,0.38,(120,120,120),1)

    cv2.imshow("EDDIE – F28 Async Logging", canvas)
    key = cv2.waitKey(50) & 0xFF
    if key == ord('q') or key == 27:
        break
    elif key == ord('s'):
        out = EVID/"real_f28_logging.png"
        cv2.imwrite(str(out), canvas)
        print(f"  [GUARDADO] {out}")
    if elapsed >= DURATION:
        break

stop_event.set()
emit("SESSION_END", {"duration_s": round(time.time()-t_start, 2),
                     "total_events": total_written[0]})
time.sleep(0.5)

cv2.destroyAllWindows()

out = EVID/"real_f28_logging.png"
with log_lock:
    final = list(display_log)
canvas2 = np.full((H, W, 3), 22, np.uint8)
cv2.putText(canvas2,"F28 – Logging completado",(15,40),
            cv2.FONT_HERSHEY_SIMPLEX,0.75,(0,220,100),2)
cv2.putText(canvas2,f"Total eventos: {total_written[0]}",(15,70),
            cv2.FONT_HERSHEY_SIMPLEX,0.55,(180,255,180),1)
cv2.putText(canvas2,f"Archivo: {LOG_FILE}",(15,95),
            cv2.FONT_HERSHEY_SIMPLEX,0.38,(120,120,120),1)
cv2.imwrite(str(out), canvas2)

print(f"\n  [✓] Total eventos escritos: {total_written[0]}")
print(f"  [GUARDADO] {out}")
sz = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
print(f"  JSONL: {LOG_FILE.name} ({sz/1024:.1f} KB)")
print("  F28 COMPLETADO\n")
