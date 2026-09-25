"""
DEMO REAL F19 – Wikipedia REST API
====================================
Consulta REAL a la API de Wikipedia en español.
Muestra el extracto de la página en consola Y en ventana.
"""
import urllib.request, urllib.parse, json, pathlib
import cv2, numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

QUERIES = ["lectura aumentada", "reconocimiento óptico de caracteres",
           "eye tracking", "visión computacional"]

print("=" * 55)
print("  DEMO REAL F19 – Wikipedia REST API")
print("=" * 55)

results = []
for query in QUERIES:
    url = (f"https://es.wikipedia.org/api/rest_v1/page/summary/"
           f"{urllib.parse.quote(query)}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"EDDIE-RAD/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            title   = data.get("title", "")
            extract = data.get("extract", "")[:300]
            results.append({"query": query, "title": title,
                            "extract": extract, "ok": True})
            print(f"\n  Query: {query}")
            print(f"  Título: {title}")
            print(f"  Extracto: {extract[:150]}…")
    except Exception as e:
        results.append({"query":query, "title":"(sin conexión)",
                        "extract":str(e), "ok":False})
        print(f"  [!] Error para '{query}': {e}")

# Crear imagen con resultados reales
canvas = np.full((600, 900, 3), 245, np.uint8)
cv2.putText(canvas, "F19 – Wikipedia REST API (resultados REALES)",
            (15, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20,20,80), 2)

y = 65
for r in results:
    color = (0, 130, 20) if r["ok"] else (180, 30, 30)
    cv2.putText(canvas, f"Query: '{r['query']}'", (15, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (60,60,60), 1)
    y += 20
    cv2.putText(canvas, f"  Titulo: {r['title']}", (15, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, color, 1)
    y += 18

    # Wrap del extracto
    words, line, lines = r["extract"].split(), "", []
    for w in words:
        if len(line) + len(w) + 1 <= 100: line += (" " if line else "") + w
        else: lines.append(line); line = w
    if line: lines.append(line)

    for l in lines[:2]:
        cv2.putText(canvas, f"  {l}", (15, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (80,80,80), 1)
        y += 16
    cv2.line(canvas, (15, y+4), (880, y+4), (200,200,200), 1)
    y += 18

out = EVID / "real_f19_wikipedia.png"
cv2.imwrite(str(out), canvas)
cv2.imshow("EDDIE – F19 Wikipedia API REAL", canvas)
print(f"\n  [GUARDADO] {out}")
print("  Presiona cualquier tecla para cerrar…")
cv2.waitKey(0)
cv2.destroyAllWindows()
print("  F19 COMPLETADO\n")
