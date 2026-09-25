"""
DEMO REAL F22 – Cloud Vision: Pipeline completo de imagen
==========================================================
Captura un frame REAL de la cámara, lo codifica en base64,
construye el payload real para Google Cloud Vision API,
y muestra cada paso del pipeline visualmente.

(No envía la solicitud porque requiere API key, pero el
pipeline completo de preparación de datos SÍ es real)

S = capturar y procesar  |  Q = salir
"""
import cv2, base64, json, pathlib, hashlib, time
import numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

print("="*55)
print("  DEMO REAL F22 – Cloud Vision Pipeline")
print("="*55)
print("  Apunta la cámara a cualquier objeto o texto")
print("  S = capturar y procesar  |  Q = salir\n")

cap = None
for idx in range(5):
    for backend in [cv2.CAP_MSMF, cv2.CAP_ANY]:
        try:
            c = cv2.VideoCapture(idx, backend)
            if c.isOpened():
                cap = c; print(f"  [+] Cámara idx={idx}"); break
            c.release()
        except Exception: pass
    if cap: break

if not cap:
    print("  [!] Sin cámara."); import sys; sys.exit(1)

processed_frame = None
pipeline_result = None

def process_frame(frame):
    """Pipeline completo de preparación para Cloud Vision API"""
    steps = {}

    # Paso 1: Frame original
    steps["1_original"] = f"{frame.shape[1]}x{frame.shape[0]} BGR"

    # Paso 2: Codificar a JPEG
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, 85]
    _, jpeg_buf  = cv2.imencode(".jpg", frame, encode_params)
    jpeg_bytes   = jpeg_buf.tobytes()
    steps["2_jpeg"] = f"{len(jpeg_bytes)/1024:.1f} KB"

    # Paso 3: Base64
    b64_content  = base64.b64encode(jpeg_bytes).decode("utf-8")
    steps["3_base64"] = f"{len(b64_content)} chars"

    # Paso 4: MD5 para verificación de integridad
    md5 = hashlib.md5(jpeg_bytes).hexdigest()
    steps["4_md5"] = md5[:16] + "…"

    # Paso 5: Payload real para Cloud Vision API
    payload = {
        "requests": [{
            "image": {
                "content": b64_content[:50] + "…"  # truncado para visualización
            },
            "features": [
                {"type": "TEXT_DETECTION",       "maxResults": 50},
                {"type": "OBJECT_LOCALIZATION",  "maxResults": 10},
                {"type": "SAFE_SEARCH_DETECTION"},
                {"type": "IMAGE_PROPERTIES"},
            ],
            "imageContext": {
                "languageHints": ["es", "en"]
            }
        }]
    }
    payload_json = json.dumps(payload, indent=2)
    steps["5_payload"] = f"{len(payload_json)} chars JSON"
    steps["5_features"] = ["TEXT_DETECTION","OBJECT_LOCALIZATION",
                           "SAFE_SEARCH_DETECTION","IMAGE_PROPERTIES"]

    # Paso 6: Headers que se enviarían
    steps["6_headers"] = {
        "Content-Type": "application/json",
        "Authorization": "Bearer [API_KEY_REQUIRED]",
        "X-Goog-FieldMask": "responses.textAnnotations"
    }
    steps["6_endpoint"] = "https://vision.googleapis.com/v1/images:annotate"

    return steps, b64_content, payload

while True:
    ret, frame = cap.read()
    if not ret: break

    display = frame.copy()
    cv2.putText(display,"EDDIE F22 | Cloud Vision Pipeline",
                (8,28),cv2.FONT_HERSHEY_SIMPLEX,0.65,(0,220,100),2)
    cv2.putText(display,"S=capturar y procesar  |  Q=salir",
                (8,52),cv2.FONT_HERSHEY_SIMPLEX,0.45,(200,200,200),1)

    if pipeline_result:
        steps, _, _ = pipeline_result
        y = 80
        for k,v in steps.items():
            if k.startswith("5_feat"):
                cv2.putText(display,f"  features: {', '.join(v[:3])}",
                            (8,y),cv2.FONT_HERSHEY_SIMPLEX,0.36,(0,200,200),1)
            elif k.startswith("6_head"):
                pass
            else:
                cv2.putText(display,f"  {k}: {str(v)[:45]}",
                            (8,y),cv2.FONT_HERSHEY_SIMPLEX,0.4,(180,255,180),1)
            y += 20

    cv2.imshow("EDDIE – F22 Cloud Vision", display)
    key = cv2.waitKey(30) & 0xFF
    if key == ord('q') or key == 27: break
    elif key == ord('s'):
        steps, b64, payload = process_frame(frame)
        pipeline_result = (steps, b64, payload)
        processed_frame = frame.copy()

        print("\n  Pipeline Cloud Vision ejecutado:")
        for k,v in steps.items():
            print(f"    {k}: {str(v)[:60]}")

        # Guardar panel de resultados
        W2, H2 = 950, 520
        panel = np.full((H2, W2, 3), 28, np.uint8)
        cv2.putText(panel,"F22 – Cloud Vision API Pipeline (REAL)",(15,38),
                    cv2.FONT_HERSHEY_SIMPLEX,0.65,(0,220,100),2)

        thumb = cv2.resize(processed_frame, (240,180))
        panel[60:240, 15:255] = thumb
        cv2.putText(panel,"Frame capturado",(15,255),
                    cv2.FONT_HERSHEY_SIMPLEX,0.38,(150,150,150),1)

        y2 = 60
        for k, v in steps.items():
            if k.startswith("5_feat"):
                cv2.putText(panel,f"  features: {', '.join(v)}",(270,y2),
                            cv2.FONT_HERSHEY_SIMPLEX,0.38,(0,200,200),1)
            elif k.startswith("6_head"):
                for hi, (hk,hv) in enumerate(v.items()):
                    cv2.putText(panel,f"  {hk}: {hv[:30]}",(270,y2+hi*16),
                                cv2.FONT_HERSHEY_SIMPLEX,0.35,(160,200,255),1)
                y2 += 48; continue
            else:
                cv2.putText(panel,f"  {k}: {str(v)[:55]}",(270,y2),
                            cv2.FONT_HERSHEY_SIMPLEX,0.4,(200,255,200),1)
            y2 += 22

        # B64 preview
        cv2.putText(panel,f"Base64 (primeros 80 chars):",(15,285),
                    cv2.FONT_HERSHEY_SIMPLEX,0.38,(120,120,120),1)
        cv2.putText(panel,b64[:80]+"…",(15,300),
                    cv2.FONT_HERSHEY_SIMPLEX,0.3,(100,150,100),1)

        out = EVID/"real_f22_vision_pipeline.png"
        cv2.imwrite(str(out), panel)
        print(f"  [GUARDADO] {out}")
        cv2.imshow("EDDIE – F22 Pipeline resultado", panel)
        cv2.waitKey(2000)

cap.release()
cv2.destroyAllWindows()
print("  F22 COMPLETADO\n")
