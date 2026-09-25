"""
DEMO REAL F10 – Eye Tracker real con diagnóstico de conexión
==========================================================
1) prueba GazeCloud WebSocket en ws://127.0.0.1:3000
2) si no responde, prueba EyeTribe TCP en 127.0.0.1:6555
3) si ninguno responde, muestra "no conectado"
4) si hay conexión real, dibuja el gaze recibido
"""

import json
import pathlib
import socket
import threading
import time

import cv2
import numpy as np

try:
    import websocket  # pip install websocket-client
except Exception:
    websocket = None

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

HOST = "127.0.0.1"
GAZECLOUD_URL = "ws://127.0.0.1:3000"
EYETRIBE_PORT = 6555
STOP_EVENT = threading.Event()
LOCK = threading.Lock()

gaze_received = []
latencies = []
server_log = []
tracker_name = "Sin tracker"
tracker_status = "Buscando eye tracker..."
last_valid_gaze = None

def add_log(msg):
    global server_log
    with LOCK:
        server_log.append(msg)
        if len(server_log) > 12:
            server_log = server_log[-12:]


def append_gaze(x, y, ts, source):
    global tracker_name, last_valid_gaze
    with LOCK:
        if x is None or y is None:
            return
        gaze_received.append((float(x), float(y), float(ts)))
        if len(gaze_received) > 200:
            gaze_received.pop(0)
        lat = (time.time() - float(ts)) * 1000.0
        latencies.append(lat)
        if len(latencies) > 120:
            latencies.pop(0)
        tracker_name = source
        last_valid_gaze = (float(x), float(y), float(ts))


def safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def parse_csv_gaze(raw):
    text = raw.decode("utf-8", "ignore") if isinstance(raw, (bytes, bytearray)) else str(raw)
    text = text.strip()
    if not text:
        return None

    for line in text.splitlines():
        line = line.strip()
        if not line or "," not in line:
            continue
        line = line.replace('"', "")
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue

        x = safe_float(parts[0])
        y = safe_float(parts[1])
        ts = safe_float(parts[2])

        if x is not None and y is not None:
            return x, y, ts

    return None


def extract_xy_from_json_obj(obj):
    if isinstance(obj, dict):
        for k in ("x", "X", "x_coordinate", "X_Coordinate"):
            if k in obj:
                if "y" in obj or "Y" in obj or "y_coordinate" in obj or "Y_Coordinate" in obj:
                    x = obj.get(k, obj.get("x"))
                    y = obj.get("y", obj.get("Y", obj.get("y_coordinate", obj.get("Y_Coordinate"))))
                    if x is not None and y is not None:
                        return safe_float(x), safe_float(y)

        if "values" in obj:
            res = extract_xy_from_json_obj(obj["values"])
            if res:
                return res
        if "avg" in obj:
            res = extract_xy_from_json_obj(obj["avg"])
            if res:
                return res
        if "gaze" in obj:
            res = extract_xy_from_json_obj(obj["gaze"])
            if res:
                return res
        if "frame" in obj:
            res = extract_xy_from_json_obj(obj["frame"])
            if res:
                return res

        for value in obj.values():
            res = extract_xy_from_json_obj(value)
            if res:
                return res

    elif isinstance(obj, list):
        for item in obj:
            res = extract_xy_from_json_obj(item)
            if res:
                return res

    return None


def parse_json_gaze(raw):
    text = raw.decode("utf-8", "ignore") if isinstance(raw, (bytes, bytearray)) else str(raw)
    text = text.strip()
    if not text:
        return None

    try:
        obj = json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                obj = json.loads(text[start:end + 1])
            except Exception:
                return None
        else:
            return None

    xy = extract_xy_from_json_obj(obj)
    if xy is None:
        return None

    x, y = xy
    if x is None or y is None:
        return None

    return float(x), float(y), time.time()


def check_gazecoud_available():
    if websocket is None:
        return False
    try:
        ws = websocket.create_connection(GAZECLOUD_URL, timeout=2)
        ws.close()
        return True
    except Exception:
        return False


def check_eyetribe_available():
    try:
        s = socket.create_connection((HOST, EYETRIBE_PORT), timeout=2)
        s.close()
        return True
    except Exception:
        return False


def gazecloud_worker():
    global tracker_status
    if websocket is None:
        add_log("GazeCloud: websocket-client no instalado. pip install websocket-client")
        tracker_status = "WebSocket no instalado"
        return

    while not STOP_EVENT.is_set():
        try:
            ws = websocket.create_connection(GAZECLOUD_URL, timeout=2)
            with LOCK:
                tracker_status = "Conectado: GazeCloud WebSocket"
            add_log("GazeCloud conectado en ws://127.0.0.1:3000")
            tracker_name = "GazeCloud"

            while not STOP_EVENT.is_set():
                try:
                    msg = ws.recv()
                    parsed = parse_csv_gaze(msg)
                    if parsed is not None:
                        x, y, ts = parsed
                        append_gaze(x, y, ts, "GazeCloud")
                    else:
                        parsed_json = parse_json_gaze(msg)
                        if parsed_json is not None:
                            x, y, ts = parsed_json
                            append_gaze(x, y, ts, "GazeCloud")
                except Exception:
                    break

            try:
                ws.close()
            except Exception:
                pass
            add_log("GazeCloud desconectado")
            break
        except Exception:
            tracker_status = "GazeCloud no responde"
            break


def eyetribe_worker():
    global tracker_status
    while not STOP_EVENT.is_set():
        try:
            s = socket.create_connection((HOST, EYETRIBE_PORT), timeout=2)
            s.settimeout(2)
            with LOCK:
                tracker_status = "Conectado: EyeTribe TCP"
            add_log("EyeTribe conectado en 127.0.0.1:6555")
            tracker_name = "EyeTribe"

            try:
                s.sendall(b'{"category":"tracker","request":"set","values":{"push":true}}')
            except Exception:
                pass

            while not STOP_EVENT.is_set():
                try:
                    raw = s.recv(4096)
                except socket.timeout:
                    continue
                if not raw:
                    break

                parsed = parse_json_gaze(raw)
                if parsed is not None:
                    x, y, ts = parsed
                    append_gaze(x, y, ts, "EyeTribe")

            s.close()
            add_log("EyeTribe desconectado")
            break
        except Exception:
            tracker_status = "EyeTribe no responde"
            break


# Diagnóstico inicial
if check_gazecoud_available():
    print("GazeCloud: CONECTADO en ws://127.0.0.1:3000")
    tracker_name = "GazeCloud"
    tracker_status = "Conectado: GazeCloud WebSocket"
    threading.Thread(target=gazecloud_worker, daemon=True).start()
elif check_eyetribe_available():
    print("EyeTribe: CONECTADO en 127.0.0.1:6555")
    tracker_name = "EyeTribe"
    tracker_status = "Conectado: EyeTribe TCP"
    threading.Thread(target=eyetribe_worker, daemon=True).start()
else:
    print("Ningún eye tracker detectado.")
    print("GazeCloud: NO responde en ws://127.0.0.1:3000")
    print("EyeTribe: NO responde en 127.0.0.1:6555")
    tracker_name = "Sin tracker"
    tracker_status = "No conectado"
    time.sleep(1.5)
    raise SystemExit("No hay eye tracker conectado.")

# Si hay conexión real, abrimos ventana
W, H = 900, 500
page = np.full((H, W, 3), 240, np.uint8)
for i in range(8):
    cv2.putText(
        page,
        f"Línea {i + 1}: El sistema EDDIE lee esta línea del documento PDF.",
        (30, 80 + i * 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (50, 50, 50),
        1,
    )

t_start = time.time()

while True:
    canvas = page.copy()
    elapsed = time.time() - t_start

    with LOCK:
        cur_gaze = list(gaze_received)
        cur_lat = list(latencies)
        cur_log = list(server_log[-7:])

    if cur_gaze:
        gx, gy, _ = cur_gaze[-1]
        gx = int(gx)
        gy = int(gy)
        if 0 < gx < W and 0 < gy < H:
            cv2.circle(canvas, (gx, gy), 18, (0, 220, 220), 2)
            cv2.circle(canvas, (gx, gy), 5, (0, 220, 220), -1)
            cv2.line(canvas, (gx - 30, gy), (gx - 18, gy), (0, 220, 220), 2)
            cv2.line(canvas, (gx + 18, gy), (gx + 30, gy), (0, 220, 220), 2)
            cv2.line(canvas, (gx, gy - 30), (gx, gy - 18), (0, 220, 220), 2)
            cv2.line(canvas, (gx, gy + 18), (gx, gy + 30), (0, 220, 220), 2)

    if len(cur_gaze) > 1:
        for i in range(1, len(cur_gaze)):
            x0, y0, _ = cur_gaze[i - 1]
            x1, y1, _ = cur_gaze[i]
            alpha = i / len(cur_gaze)
            col = (int(200 * alpha), int(100 * alpha), int(200 * (1 - alpha)))
            cv2.line(canvas, (int(x0), int(y0)), (int(x1), int(y1)), col, 2)

    cv2.rectangle(canvas, (0, H - 140), (W, H), (22, 22, 22), -1)
    cv2.putText(canvas, "F10 | Eye Tracker real", (8, H - 115),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 100), 2)
    cv2.putText(canvas, f"Tracker: {tracker_name} | Estado: {tracker_status}", (8, H - 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1)
    cv2.putText(canvas, f"Muestras: {len(cur_gaze)} | t={elapsed:.1f}s", (8, H - 68),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)

    if cur_lat:
        media = float(np.mean(cur_lat))
        mx = float(np.max(cur_lat))
        mn = float(np.min(cur_lat))
        cv2.putText(canvas, f"Latencia media={media:.2f}ms  max={mx:.2f}ms  min={mn:.2f}ms",
                    (8, H - 46), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 200, 200), 1)

    for i, log in enumerate(cur_log):
        cv2.putText(canvas, log, (8, H - 30 + i * 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.28, (150, 150, 150), 1)

    cv2.putText(canvas, "Q=salir  S=guardar", (W - 180, H - 115),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (140, 140, 140), 1)
    cv2.imshow("EDDIE – Eye Tracker real", canvas)

    key = cv2.waitKey(30) & 0xFF
    if key == ord("q") or key == 27:
        break
    elif key == ord("s"):
        out = EVID / "real_f10_eye_tracker.png"
        cv2.imwrite(str(out), canvas)
        print(f"  [GUARDADO] {out}")

STOP_EVENT.set()
cv2.destroyAllWindows()
if latencies:
    print(f"  Total muestras: {len(latencies)}")
    print(f"  Latencia media: {np.mean(latencies):.2f}ms")
print("  F10 COMPLETADO\n")