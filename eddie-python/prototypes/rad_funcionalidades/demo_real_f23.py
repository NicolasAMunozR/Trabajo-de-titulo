"""
DEMO REAL F23 – YouTube Search vía YouTube Data API v3
=======================================================
Realiza búsquedas REALES en YouTube.
Si no hay API key configurada, usa la búsqueda de sugerencias
de YouTube (autocompletar) que sí es pública.

Muestra los resultados en consola y ventana.
"""
import urllib.request, urllib.parse, json, pathlib
import cv2, numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

print("="*55)
print("  DEMO REAL F23 – YouTube Search")
print("="*55)

QUERIES = [
    "eye tracking lectura aumentada",
    "tesseract ocr python tutorial",
    "opencv droidcam python",
    "sistema EDDIE lectura",
]

def youtube_autocomplete(query):
    """API pública de sugerencias de YouTube (sin clave)."""
    url = (f"http://suggestqueries.google.com/complete/search?"
           f"client=firefox&ds=yt&q={urllib.parse.quote(query)}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            suggestions = data[1] if len(data) > 1 else []
            return suggestions[:6], True
    except Exception as e:
        return [f"[offline: {e}]"], False

def youtube_search_api(query, api_key=None):
    """API oficial de YouTube Data v3 (requiere clave)."""
    if not api_key:
        return None, False
    url = (f"https://www.googleapis.com/youtube/v3/search?"
           f"part=snippet&q={urllib.parse.quote(query)}&type=video"
           f"&maxResults=5&key={api_key}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            items = data.get("items", [])
            results = [{
                "title":    i["snippet"]["title"],
                "channel":  i["snippet"]["channelTitle"],
                "date":     i["snippet"]["publishedAt"][:10],
                "videoId":  i["id"]["videoId"],
            } for i in items]
            return results, True
    except Exception as e:
        return str(e), False

all_results = []
print()
for q in QUERIES:
    print(f"  Query: '{q}'")
    suggestions, ok = youtube_autocomplete(q)
    entry = {"query": q, "suggestions": suggestions, "ok": ok}
    all_results.append(entry)
    for s in suggestions[:4]:
        print(f"    → {s}")
    print()

# Visualización
W, H = 950, 560
canvas = np.full((H, W, 3), 28, np.uint8)

cv2.putText(canvas,"F23 – YouTube Search (sugerencias API pública)",(15,38),
            cv2.FONT_HERSHEY_SIMPLEX,0.65,(0,80,200),2)
cv2.putText(canvas,"suggestqueries.google.com/complete/search?ds=yt (sin clave requerida)",
            (15,62),cv2.FONT_HERSHEY_SIMPLEX,0.38,(120,120,120),1)

y = 88
for entry in all_results:
    col_q = (0,160,255) if entry["ok"] else (100,100,200)
    cv2.putText(canvas,f"  🔍 '{entry['query']}'",(15,y),
                cv2.FONT_HERSHEY_SIMPLEX,0.52,col_q,1)
    y += 22
    for s in entry["suggestions"][:4]:
        cv2.putText(canvas,f"      • {s[:75]}",(15,y),
                    cv2.FONT_HERSHEY_SIMPLEX,0.38,(200,200,200),1)
        y += 17
    cv2.line(canvas,(15,y+3),(W-15,y+3),(50,50,50),1)
    y += 14

cv2.putText(canvas,"Para buscar videos reales, configura YOUTUBE_API_KEY y usa YouTube Data API v3",
            (15,H-15),cv2.FONT_HERSHEY_SIMPLEX,0.36,(100,100,100),1)

out = EVID/"real_f23_youtube.png"
cv2.imwrite(str(out), canvas)
print(f"  [GUARDADO] {out}")
cv2.imshow("EDDIE – F23 YouTube Search REAL", canvas)
print("  Presiona cualquier tecla para cerrar…")
cv2.waitKey(0)
cv2.destroyAllWindows()
print("  F23 COMPLETADO\n")
