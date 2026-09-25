"""
DEMO REAL F21 – Traducción ES→EN vía MyMemory API
===================================================
Consulta REAL a la API pública de MyMemory (sin clave).
Traduce términos clave del proyecto EDDIE de español a inglés.
Muestra los resultados en ventana y en consola.
"""
import urllib.request, urllib.parse, json, pathlib
import cv2, numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

print("="*55)
print("  DEMO REAL F21 – Traducción ES→EN (MyMemory API)")
print("="*55)

TERMS_ES = [
    "lectura aumentada",
    "reconocimiento óptico de caracteres",
    "seguimiento ocular",
    "visión computacional",
    "binarización de imagen",
    "tiempo de fijación",
    "procesamiento de imágenes",
    "sistema de apoyo a la lectura",
    "interfaz de usuario",
    "plugin de reconocimiento gestual",
]

def translate(text_es):
    url = (f"https://api.mymemory.translated.net/get?"
           f"q={urllib.parse.quote(text_es)}&langpair=es|en")
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"EDDIE-RAD/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            trans = data.get("responseData",{}).get("translatedText","")
            quality = data.get("responseData",{}).get("match", 0)
            return trans, float(quality), True
    except Exception as e:
        return f"[Error: {e}]", 0.0, False

results = []
print()
for term in TERMS_ES:
    trans, qual, ok = translate(term)
    results.append({"es": term, "en": trans, "q": qual, "ok": ok})
    status = "✓" if ok else "✗"
    print(f"  {status} '{term}' → '{trans}'  (score={qual:.2f})")

# Visualización
W, H = 950, 520
canvas = np.full((H, W, 3), 28, np.uint8)
cv2.putText(canvas,"F21 – Traducción ES→EN vía MyMemory API (REAL)",(15,38),
            cv2.FONT_HERSHEY_SIMPLEX,0.65,(0,220,100),2)
ok_count = sum(1 for r in results if r["ok"])
cv2.putText(canvas,f"Términos traducidos: {ok_count}/{len(results)} | API: mymemory.translated.net",
            (15,62),cv2.FONT_HERSHEY_SIMPLEX,0.42,(180,180,180),1)

# Encabezado tabla
cv2.rectangle(canvas,(15,75),(W-15,100),(40,80,40),-1)
cv2.putText(canvas,"  Español",(20,93),cv2.FONT_HERSHEY_SIMPLEX,0.45,(200,255,200),1)
cv2.putText(canvas,"  Traducción (EN)",(380,93),cv2.FONT_HERSHEY_SIMPLEX,0.45,(200,255,200),1)
cv2.putText(canvas,"Score",(850,93),cv2.FONT_HERSHEY_SIMPLEX,0.45,(200,255,200),1)

for i, r in enumerate(results):
    y = 118 + i*38
    bg_col = (35,45,35) if i%2==0 else (30,30,30)
    cv2.rectangle(canvas,(15,y-22),(W-15,y+10),bg_col,-1)

    col_es = (180,220,255)
    col_en = (200,255,180) if r["ok"] else (100,100,220)
    col_q  = (0,200,100) if r["q"]>0.7 else (200,150,0)

    cv2.putText(canvas, r["es"][:38], (20,y),
                cv2.FONT_HERSHEY_SIMPLEX,0.42,col_es,1)
    cv2.putText(canvas, r["en"][:40], (380,y),
                cv2.FONT_HERSHEY_SIMPLEX,0.42,col_en,1)
    cv2.putText(canvas, f"{r['q']:.2f}", (855,y),
                cv2.FONT_HERSHEY_SIMPLEX,0.42,col_q,1)

    cv2.line(canvas,(15,y+11),(W-15,y+11),(50,50,50),1)

out = EVID/"real_f21_traduccion.png"
cv2.imwrite(str(out), canvas)
print(f"\n  [GUARDADO] {out}")
cv2.imshow("EDDIE – F21 Traducción API REAL", canvas)
print("  Presiona cualquier tecla para cerrar…")
cv2.waitKey(0)
cv2.destroyAllWindows()
print("  F21 COMPLETADO\n")
