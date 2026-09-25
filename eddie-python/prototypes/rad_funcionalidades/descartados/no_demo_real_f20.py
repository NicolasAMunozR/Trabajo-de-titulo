"""
DEMO REAL F20 – Ollama LLM (definiciones locales)
===================================================
Consulta al LLM local Ollama (llama3.2) para obtener
definiciones de términos de lectura aumentada.
Si Ollama no está corriendo, guía para iniciarlo.

Presiona cualquier tecla para consultar el siguiente término.
"""
import urllib.request, json, pathlib, time
import cv2, numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL      = "llama3.2"
TERMS      = [
    "OCR (Reconocimiento Óptico de Caracteres)",
    "eye tracking",
    "homografía en visión computacional",
    "binarización de imagen",
    "dwell time en interfaces gaze",
]

print("="*55)
print("  DEMO REAL F20 – Ollama LLM Definitions")
print(f"  URL: {OLLAMA_URL}  Modelo: {MODEL}")
print("="*55)

def check_ollama():
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read())
            models = [m["name"] for m in data.get("models",[])]
            return True, models
    except Exception as e:
        return False, str(e)

def query_ollama(term):
    prompt = (f"Define brevemente en español (máximo 3 oraciones) el término: '{term}'. "
              f"Responde directamente sin introducción.")
    payload = json.dumps({
        "model":  MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 150}
    }).encode()
    try:
        req = urllib.request.Request(OLLAMA_URL, data=payload, method="POST",
                                     headers={"Content-Type":"application/json"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            elapsed = time.time()-t0
            return data.get("response","").strip(), elapsed, True
    except Exception as e:
        return str(e), 0, False

# Verificar Ollama
online, models_or_err = check_ollama()

W, H = 950, 550

if not online:
    print(f"\n  [!] Ollama no está corriendo: {models_or_err}")
    print("  Para iniciarlo ejecuta en otra terminal:")
    print("    ollama serve")
    print(f"  Y asegúrate de tener el modelo: ollama pull {MODEL}")

    canvas = np.full((H, W, 3), 30, np.uint8)
    cv2.putText(canvas,"F20 – Ollama LLM (no disponible)",(15,40),
                cv2.FONT_HERSHEY_SIMPLEX,0.75,(80,80,220),2)
    cv2.putText(canvas,"Para ejecutar Ollama:",(15,90),
                cv2.FONT_HERSHEY_SIMPLEX,0.55,(180,180,180),1)
    cv2.putText(canvas,"  1. ollama serve",(15,120),
                cv2.FONT_HERSHEY_SIMPLEX,0.5,(100,200,255),1)
    cv2.putText(canvas,f"  2. ollama pull {MODEL}",(15,150),
                cv2.FONT_HERSHEY_SIMPLEX,0.5,(100,200,255),1)
    cv2.putText(canvas,"  3. volver a ejecutar este demo",(15,180),
                cv2.FONT_HERSHEY_SIMPLEX,0.5,(100,200,255),1)
    cv2.putText(canvas,f"Error: {str(models_or_err)[:60]}",(15,220),
                cv2.FONT_HERSHEY_SIMPLEX,0.4,(100,100,180),1)
    out = EVID/"real_f20_ollama_offline.png"
    cv2.imwrite(str(out), canvas)
    cv2.imshow("EDDIE – F20 Ollama", canvas)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("  F20 COMPLETADO (Ollama offline)\n")
else:
    print(f"  [✓] Ollama online | Modelos: {models_or_err}")
    results = []
    for i, term in enumerate(TERMS):
        print(f"\n  [{i+1}/{len(TERMS)}] Consultando: '{term}'…")
        resp, elapsed, ok = query_ollama(term)
        results.append({"term": term, "resp": resp, "t": elapsed, "ok": ok})
        print(f"  Respuesta ({elapsed:.1f}s): {resp[:100]}…")

        # Mostrar en ventana
        canvas = np.full((H, W, 3), 28, np.uint8)
        cv2.putText(canvas,"F20 – Ollama LLM Definitions (REAL)",(15,40),
                    cv2.FONT_HERSHEY_SIMPLEX,0.65,(0,220,100),2)
        cv2.putText(canvas,f"Modelo: {MODEL} | Consulta {i+1}/{len(TERMS)} | t={elapsed:.1f}s",
                    (15,68),cv2.FONT_HERSHEY_SIMPLEX,0.42,(180,180,180),1)
        cv2.putText(canvas,f"Término: {term}",(15,105),
                    cv2.FONT_HERSHEY_SIMPLEX,0.55,(0,180,255),1)

        words = resp.split()
        line, lines = "", []
        for w in words:
            if len(line)+len(w)+1<=80: line += (" " if line else "")+w
            else: lines.append(line); line=w
        if line: lines.append(line)
        for j,l in enumerate(lines[:8]):
            cv2.putText(canvas,l,(15,140+j*28),
                        cv2.FONT_HERSHEY_SIMPLEX,0.48,(220,220,200),1)

        # Historial
        for k,r in enumerate(results[:-1]):
            cv2.putText(canvas,f"✓ {r['term'][:50]}",(15,H-80+k*18),
                        cv2.FONT_HERSHEY_SIMPLEX,0.36,(100,160,100),1)

        cv2.putText(canvas,"Presiona cualquier tecla para continuar…",
                    (15,H-15),cv2.FONT_HERSHEY_SIMPLEX,0.42,(120,120,120),1)
        cv2.imshow("EDDIE – F20 Ollama", canvas)
        cv2.waitKey(0)

    # Guardar evidencia del último resultado
    out = EVID/"real_f20_ollama.png"
    cv2.imwrite(str(out), canvas)
    print(f"\n  [GUARDADO] {out}")
    cv2.destroyAllWindows()
    print(f"  {len(results)} consultas completadas a Ollama")
    print("  F20 COMPLETADO\n")
