# Mediciones reproducibles de los prototipos desechables F01–F27.
# Aplica el mismo algoritmo de cada prototipo sobre datos con verdad terreno conocida y calcula las métricas de la tesis.
# Tipos de medición: pdf, codigo, sintetico y laboratorio (este último queda pendiente con su protocolo).
# Uso:
# python mediciones\medir_prototipos.py --pdf "ruta\al\libro.pdf"
# python mediciones\medir_prototipos.py --pdf libro.pdf --camara 0   → agrega F01 con la cámara real
# Salida en evidencias/: mediciones.json, MEDICIONES.md y prototipos_datos.tex.
import argparse
import asyncio
import importlib.util
import json
import math
import platform
import re
import socket
import statistics as st
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import pymupdf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "evidencias"
RNG = np.random.default_rng(2026)
RESULTS: dict[str, dict] = {}


# ---------------------------------------------------------------------------- utilidades
def mean_sd(values) -> tuple[float, float]:
    values = list(values)
    if not values:
        return float("nan"), float("nan")
    return float(st.fmean(values)), float(st.stdev(values)) if len(values) > 1 else 0.0


def timed(fn, *args, repeat: int = 200, warmup: int = 10) -> tuple[float, float]:
    # Tiempo de ejecución en ms (media ± desviación estándar), con calentamiento.
    for _ in range(warmup):
        fn(*args)
    samples = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn(*args)
        samples.append((time.perf_counter() - t0) * 1000)
    return mean_sd(samples)


def levenshtein(a, b) -> int:
    # Distancia de edición (sustituciones + supresiones + inserciones) entre dos secuencias.
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def record(fid: str, nombre: str, tipo: str, metricas: dict, protocolo: str, formula: str = "",
           nota: str = "") -> None:
    RESULTS[fid] = {"nombre": nombre, "tipo": tipo, "metricas": metricas, "protocolo": protocolo,
                    "formula": formula, "nota": nota}
    shown = ", ".join(f"{k}={v}" for k, v in metricas.items())
    print(f"  {fid:<4} [{tipo}] {nombre}: {shown}")


def pending(fid: str, nombre: str, protocolo: str, formula: str = "") -> None:
    record(fid, nombre, "laboratorio", {"estado": "pendiente"}, protocolo, formula)


def render_page(doc, index: int, width: int = 640) -> tuple[np.ndarray, float]:
    page = doc[index]
    zoom = width / page.rect.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), colorspace=pymupdf.csRGB)
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)
    return cv2.cvtColor(img, cv2.COLOR_RGB2BGR), zoom


def text_pages(doc, minimum_words: int = 120) -> list[int]:
    return [i for i in range(doc.page_count) if len(doc[i].get_text("words")) >= minimum_words]


# ---------------------------------------------------------------------------- F01 cámaras
def f01(camera: int | None) -> None:
    proto = ("Se abre la cámara con OpenCV (MSMF y respaldo CAP_ANY, como prototipo_f01.py), se descartan 30 "
             "cuadros de calentamiento y se leen 300 cuadros a 640×480 midiendo cada cap.read().")
    formula = r"\mathrm{FPS}=N/\sum_{i=1}^{N}\Delta t_i"
    if camera is None:
        pending("F01", "Enumeración e inicialización de cámaras", proto + " Ejecutar con --camara <índice>.", formula)
        return
    cap = None
    for backend in (cv2.CAP_MSMF, cv2.CAP_ANY):
        cap = cv2.VideoCapture(camera, backend)
        if cap.isOpened():
            break
    if cap is None or not cap.isOpened():
        pending("F01", "Enumeración e inicialización de cámaras", proto + f" No se pudo abrir la cámara {camera}.",
                formula)
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    for _ in range(30):
        cap.read()
    dts, ok = [], 0
    for _ in range(300):
        t0 = time.perf_counter()
        ret, _frame = cap.read()
        dts.append(time.perf_counter() - t0)
        ok += bool(ret)
    cap.release()
    fps = len(dts) / sum(dts)
    lat = mean_sd([d * 1000 for d in dts])
    record("F01", "Enumeración e inicialización de cámaras", "laboratorio",
           {"fps": round(fps, 2), "lectura_ms": round(lat[0], 2), "lectura_sd_ms": round(lat[1], 2),
            "cuadros_validos": f"{ok}/300"}, proto, formula)


# ---------------------------------------------------------------------------- F02 binarización
def f02_pipeline(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, bw = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return bw


def degrade(frame, glare: bool = True, shadow: bool = True):
    # Simula la luz del proyector: destello elíptico (sobreexposición) y sombra parcial.
    h, w = frame.shape[:2]
    img = frame.astype(np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    affected = np.zeros((h, w), bool)
    if glare:
        cx, cy = RNG.uniform(0.3, 0.7) * w, RNG.uniform(0.3, 0.7) * h
        g = np.exp(-(((xx - cx) / (0.18 * w)) ** 2 + ((yy - cy) / (0.12 * h)) ** 2))
        img += (g * 150)[..., None]
        affected |= g > 0.25
    if shadow:
        x0 = RNG.uniform(0.0, 0.5) * w
        s = np.clip((xx - x0) / (0.25 * w), 0, 1)
        factor = 0.45 + 0.55 * s
        img *= factor[..., None]
        affected |= factor < 0.8
    img += RNG.normal(0, 4, img.shape)
    return np.clip(img, 0, 255).astype(np.uint8), affected


def f02(doc) -> None:
    pages = text_pages(doc)[:30]
    effs, f1s = [], []
    frame = None
    for p in pages:
        clean, _ = render_page(doc, p)
        truth = f02_pipeline(clean) == 0                          # píxeles de tinta en la página limpia
        frame, affected = degrade(clean)
        pred = f02_pipeline(frame) == 0
        fp = np.sum(pred & ~truth & affected)                     # destello/sombra confundido con tinta
        fn = np.sum(~pred & truth & affected)                     # tinta perdida en la zona afectada
        effs.append(100 * (1 - (fp + fn) / max(1, affected.sum())))
        tp = np.sum(pred & truth)
        f1s.append(100 * 2 * tp / max(1, 2 * tp + np.sum(pred & ~truth) + np.sum(~pred & truth)))
    t = timed(f02_pipeline, frame, repeat=1000)
    e, f = mean_sd(effs), mean_sd(f1s)
    adaptive = []
    for p in pages:                                               # alternativa: umbral adaptativo local
        clean, _ = render_page(doc, p)
        truth = f02_pipeline(clean) == 0
        frame_a, affected = degrade(clean)
        gray = cv2.GaussianBlur(cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY), (5, 5), 0)
        pred = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10) == 0
        fp, fn = np.sum(pred & ~truth & affected), np.sum(~pred & truth & affected)
        adaptive.append(100 * (1 - (fp + fn) / max(1, affected.sum())))
    a = mean_sd(adaptive)
    record("F02", "Preprocesamiento y binarización (Otsu)", "sintetico",
           {"paginas": len(pages), "eficacia_pct": round(e[0], 1), "eficacia_sd": round(e[1], 1),
            "f1_tinta_pct": round(f[0], 1), "eficacia_adaptativo_pct": round(a[0], 1),
            "tiempo_ms": round(t[0], 2), "tiempo_sd_ms": round(t[1], 2)},
           f"{len(pages)} páginas del PDF renderizadas a 640 px de ancho; a cada una se le agrega un destello "
           "elíptico y una sombra lateral simulados más ruido gaussiano (σ = 4). La verdad terreno es la "
           "binarización de la página limpia. Se compara con un umbral adaptativo gaussiano (bloque 31, C = 10). "
           "Tiempo: 1 000 ejecuciones tras 10 de calentamiento.",
           r"\mathrm{Eficacia}=\left(1-\frac{FP_{ruido}+FN_{corte}}{P_{afectados}}\right)\times 100\%",
           "Mide el algoritmo con iluminación simulada; la eficacia con el proyector real se mide en el laboratorio.")


# ---------------------------------------------------------------------------- F03 OCR
def f03_preprocess(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    deskew = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    return cv2.resize(deskew, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)


def normalize_words(text: str) -> list[str]:
    return re.sub(r"\s+", " ", text).strip().split(" ") if text.strip() else []


def f03(doc) -> None:
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
    except Exception:
        pending("F03", "Reconocimiento óptico de caracteres", "Requiere Tesseract-OCR instalado (spa+eng).")
        return
    langs = "spa+eng" if "spa" in pytesseract.get_languages(config="") else "eng"
    config = f"--oem 3 --psm 6 -l {langs}"
    rows = {"limpio": [], "degradado": [], "sin_preproceso": []}
    times = []
    blocks = 0
    for p in text_pages(doc):
        page = doc[p]
        lines = {}
        for x0, y0, x1, y1, word, b, l, _n in page.get_text("words"):
            lines.setdefault((b, l), []).append((x0, y0, x1, y1, word))
        textlines = []                                                 # líneas de texto corrido, de arriba abajo
        for words in lines.values():
            words.sort()
            width = words[-1][2] - words[0][0]
            text = " ".join(w[4] for w in words)
            if len(words) >= 6 and width >= 0.55 * page.rect.width and ". . ." not in text:
                textlines.append((min(w[1] for w in words), max(w[3] for w in words), words))
        textlines.sort(key=lambda r: r[0])
        i = 0
        while i + 2 < len(textlines):
            trio = textlines[i:i + 3]
            height = trio[0][1] - trio[0][0]
            if any(trio[k + 1][0] - trio[k][1] > 1.2 * height for k in range(2)):
                i += 1                                            # no son líneas consecutivas de un párrafo
                continue
            group = [w for r in trio for w in r[2]]
            i += 3
            rect = pymupdf.Rect(min(w[0] for w in group) - 4, min(w[1] for w in group) - 4,
                                max(w[2] for w in group) + 4, max(w[3] for w in group) + 4)
            truth = " ".join(w[4] for w in group)
            zoom = 150 / 72                                        # 150 ppp: resolución típica de la cámara
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=rect, colorspace=pymupdf.csRGB)
            img = cv2.cvtColor(np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3),
                               cv2.COLOR_RGB2BGR)
            for kind in rows:
                src = img
                if kind == "degradado":
                    src = cv2.GaussianBlur(img, (3, 3), 0.9)
                    src = np.clip(src.astype(np.float32) * RNG.uniform(0.75, 1.0) + RNG.normal(0, 6, src.shape),
                                  0, 255).astype(np.uint8)
                t0 = time.perf_counter()
                prepared = img if kind == "sin_preproceso" else f03_preprocess(src)
                text = pytesseract.image_to_string(prepared, config=config)
                if kind == "limpio":
                    times.append((time.perf_counter() - t0) * 1000)
                hyp = " ".join(normalize_words(text))
                rows[kind].append((levenshtein(truth, hyp), len(truth),
                                   levenshtein(truth.split(), hyp.split()), len(truth.split())))
            blocks += 1
            if blocks >= 60:
                break
        if blocks >= 60:
            break
    metrics = {"bloques": blocks}
    for kind, data in rows.items():
        ec, nc, ew, nw = (sum(x[i] for x in data) for i in range(4))
        metrics[f"cer_{kind}_pct"] = round(100 * ec / nc, 2)
        metrics[f"wer_{kind}_pct"] = round(100 * ew / nw, 2)
    metrics["caracteres"] = sum(x[1] for x in rows["limpio"])
    metrics["palabras"] = sum(x[3] for x in rows["limpio"])
    t = mean_sd(times)
    metrics["tiempo_ms"], metrics["tiempo_sd_ms"] = round(t[0], 1), round(t[1], 1)
    record("F03", "Reconocimiento óptico de caracteres", "pdf", metrics,
           f"Las tres primeras líneas de {blocks} párrafos de texto corrido del PDF (ancho ≥ 60 % de la página, sin "
           "tablas ni índices), renderizadas a 150 ppp, con el preprocesamiento de "
           f"prototipo_f03.py (CLAHE, Otsu, apertura 2×2, escala ×2) y Tesseract «{config}». Verdad terreno: "
           "texto del PDF (get_text). «Degradado» agrega desenfoque, variación de brillo y ruido; «sin preproceso» "
           "entrega la imagen limpia directo a Tesseract.",
           r"\mathrm{CER}=\frac{S_c+D_c+I_c}{N_c}\times 100\%,\quad \mathrm{WER}=\frac{S_w+D_w+I_w}{N_w}\times 100\%",
           "Es el límite superior (texto digital renderizado). La validez por palabra y posición con la cámara "
           "real se mide en el laboratorio, como Ibaceta (2023).")


# ---------------------------------------------------------------------------- F04 detección de página
def f04_detect(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    edges = cv2.dilate(cv2.Canny(blur, 30, 120), cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)), iterations=1)
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best, best_area = None, 0
    total = frame.shape[0] * frame.shape[1]
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        if area < total * 0.05:
            continue
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
        if len(approx) == 4 and area > best_area:
            best, best_area = approx.reshape(4, 2).astype(np.float32), area
    return best


def order_corners(pts):
    s, d = pts.sum(1), np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], np.float32)


def f04(doc) -> None:
    pages = text_pages(doc) or list(range(doc.page_count))
    errors, ok, n = [], 0, 80
    W, H = 640, 480
    for i in range(n):
        page, _ = render_page(doc, pages[i % len(pages)], width=240)
        ph, pw = page.shape[:2]
        angle = math.radians(RNG.uniform(-15, 15))
        scale = RNG.uniform(0.9, 1.25)
        cx, cy = W / 2 + RNG.uniform(-50, 50), H / 2 + RNG.uniform(-30, 30)
        base = np.array([[-pw / 2, -ph / 2], [pw / 2, -ph / 2], [pw / 2, ph / 2], [-pw / 2, ph / 2]]) * scale
        rot = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
        dst = (base @ rot.T + [cx, cy] + RNG.normal(0, 3, (4, 2))).astype(np.float32)   # leve perspectiva
        Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [pw, 0], [pw, ph], [0, ph]]), dst)
        desk = np.full((H, W, 3), RNG.integers(35, 90), np.uint8)
        desk = cv2.add(desk, RNG.integers(0, 25, (H, W, 3), dtype=np.uint8))
        light = RNG.uniform(0.75, 1.1)
        scene = cv2.warpPerspective(page, Hm, (W, H), dst=desk, borderMode=cv2.BORDER_TRANSPARENT)
        scene = np.clip(scene.astype(np.float32) * light + RNG.normal(0, 3, scene.shape), 0, 255).astype(np.uint8)
        found = f04_detect(scene)
        if found is None:
            continue
        err = np.linalg.norm(order_corners(found) - order_corners(dst), axis=1)
        rmse = float(np.sqrt(np.mean(err ** 2)))
        if rmse <= 10:
            ok += 1
            errors.append(rmse)
    r = mean_sd(errors)
    record("F04", "Detección automática de páginas", "sintetico",
           {"escenas": n, "exito_pct": round(100 * ok / n, 1), "rmse_px": round(r[0], 2), "rmse_sd_px": round(r[1], 2)},
           f"{n} escenas de 640×480: una página del PDF sobre un escritorio oscuro con textura, girada entre −15° y "
           "+15°, escala 0,9–1,25, leve perspectiva y brillo 0,75–1,1. Algoritmo de prototipo_f04.py (Canny 30/120, "
           "approxPolyDP 0,02·perímetro). Éxito: cuadrilátero con RMSE ≤ 10 px respecto de las esquinas reales.",
           r"\mathrm{RMSE}=\sqrt{\frac{1}{4N}\sum_{i=1}^{N}\sum_{k=1}^{4}\left[(x_{k,i}-\hat{x}_{k,i})^2+(y_{k,i}-\hat{y}_{k,i})^2\right]}",
           "La detección automática del libro quedó fuera del alcance del MVP (sección de alcances); el resultado "
           "solo indica factibilidad.")


# ---------------------------------------------------------------------------- F05 lápiz de color
def f05_detect(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.bitwise_or(cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255])),
                          cv2.inRange(hsv, np.array([170, 120, 70]), np.array([180, 255, 255])))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k, iterations=1)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if cnts:
        c = max(cnts, key=cv2.contourArea)
        if cv2.contourArea(c) > 200:
            m = cv2.moments(c)
            if m["m00"] > 0:
                return m["m10"] / m["m00"], m["m01"] / m["m00"]
    return None


def f05_run(page, red_content: bool, n: int = 300):
    H, W = 480, 640
    hits, spurious, errors, frame = 0, 0, [], None
    for i in range(n):
        frame = page.copy()
        for k in range(3):                                 # contenido proyectado de colores (distractores)
            x, y = RNG.integers(0, W - 80), RNG.integers(0, H - 60)
            hue = int(RNG.integers(20, 160))               # cualquier tono salvo rojo
            if red_content and k == 0:
                hue = int(RNG.integers(0, 8))              # un recuadro rojo (p. ej. una figura proyectada)
            color = cv2.cvtColor(np.uint8([[[hue, int(RNG.integers(130, 255)), int(RNG.integers(120, 255))]]]),
                                 cv2.COLOR_HSV2BGR)[0, 0]
            cv2.rectangle(frame, (int(x), int(y)), (int(x) + 80, int(y) + 60), [int(c) for c in color], -1)
        present = i % 5 != 0                               # 1 de cada 5 cuadros sin lápiz
        truth = (RNG.uniform(40, W - 40), RNG.uniform(40, H - 40))
        if present:
            cv2.circle(frame, (int(truth[0]), int(truth[1])), 12, (30, 30, 210), -1)
        frame = np.clip(frame.astype(np.float32) + RNG.normal(0, 5, frame.shape), 0, 255).astype(np.uint8)
        found = f05_detect(frame)
        if present and found is not None:
            err = math.dist(found, truth)
            if err <= 15:
                hits += 1
                errors.append(err)
            else:
                spurious += 1
        elif not present and found is not None:
            spurious += 1
    return hits / (n * 4 / 5), spurious / n, errors, frame


def f05(doc) -> None:
    page, _ = render_page(doc, (text_pages(doc) or [0])[0])
    page = cv2.resize(page, (640, 480))
    n = 300
    hit_a, sp_a, err_a, frame = f05_run(page, False, n)
    hit_b, sp_b, _err_b, _ = f05_run(page, True, n)
    e = mean_sd(err_a)
    t = timed(f05_detect, frame, repeat=500)
    record("F05", "Seguimiento de lápiz de color", "sintetico",
           {"cuadros": 2 * n, "deteccion_pct": round(100 * hit_a, 1), "falsas_por_100": round(100 * sp_a, 1),
            "deteccion_rojo_pct": round(100 * hit_b, 1), "falsas_rojo_por_100": round(100 * sp_b, 1),
            "error_px": round(e[0], 2), "error_sd_px": round(e[1], 2), "tiempo_ms": round(t[0], 2)},
           f"Dos series de {n} cuadros de 640×480 con una página del PDF, tres recuadros de color (contenido "
           "proyectado) y, en 4 de cada 5 cuadros, la punta roja de un lápiz (radio 12 px) en una posición conocida. "
           "Serie A: recuadros de cualquier tono salvo rojo; serie B: uno de ellos rojo. Algoritmo de "
           "prototipo_f05.py (rojo HSV H∈[0,10]∪[170,180], S≥120, V≥70; cierre y apertura elípticos 9×9; se "
           "toma el contorno rojo más grande). Acierto: centroide a ≤ 15 px del real.",
           r"e=\sqrt{(x-\hat{x})^2+(y-\hat{y})^2};\quad \text{falsas}=\frac{N_{\text{detecciones erróneas}}}{N_{\text{cuadros}}}\times 100",
           "La serie B muestra el riesgo con contenido proyectado rojo: el algoritmo toma el objeto rojo más grande.")


# ---------------------------------------------------------------------------- F06 mano
def f06_mask(frame):
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.bitwise_and(cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127])),
                           cv2.inRange(hsv, np.array([0, 20, 50]), np.array([30, 255, 255])))
    kc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kc, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kc, iterations=2)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros_like(mask)
    for c in cnts:
        if cv2.contourArea(c) > 500:
            cv2.drawContours(out, [c], -1, 255, -1)
    return out


def f06(doc) -> None:
    page, _ = render_page(doc, (text_pages(doc) or [0])[0])
    H, W = 480, 640
    page = cv2.resize(page, (W, H))
    n, ious, tip_err, tips_ok, frame = 200, [], [], 0, None
    for _ in range(n):
        frame = page.copy()
        truth = np.zeros((H, W), np.uint8)
        tone = (int(RNG.integers(95, 140)), int(RNG.integers(130, 170)), int(RNG.integers(190, 235)))   # piel (BGR)
        wx, wy = int(RNG.integers(200, 440)), int(RNG.integers(300, 380))
        cv2.ellipse(truth, (wx, wy + 60), (70, 90), 0, 0, 360, 255, -1)                      # palma
        tip = (wx + int(RNG.integers(-20, 20)), wy - int(RNG.integers(110, 170)))
        cv2.line(truth, (wx, wy), tip, 255, 24)                                             # índice extendido
        cv2.circle(truth, tip, 12, 255, -1)
        frame[truth > 0] = tone
        frame = np.clip(frame.astype(np.float32) + RNG.normal(0, 4, frame.shape), 0, 255).astype(np.uint8)
        mask = f06_mask(frame) > 0
        inter, union = np.sum(mask & (truth > 0)), np.sum(mask | (truth > 0))
        ious.append(100 * inter / max(1, union))
        ys, xs = np.nonzero(mask)
        if len(ys):
            k = np.argmin(ys)                                                               # punto más alto
            err = math.dist((xs[k], ys[k]), (tip[0], tip[1] - 12))
            if err <= 15:
                tips_ok += 1
            tip_err.append(err)
    i, e = mean_sd(ious), mean_sd(tip_err)
    t = timed(f06_mask, frame, repeat=300)
    record("F06", "Segmentación de mano y apuntado", "sintetico",
           {"cuadros": n, "iou_pct": round(i[0], 1), "punta_ok_pct": round(100 * tips_ok / n, 1),
            "error_punta_px": round(e[0], 1), "tiempo_ms": round(t[0], 2)},
           f"{n} cuadros con una silueta de mano (palma + índice) en tonos de piel aleatorios sobre una página del "
           "PDF. Máscara de prototipo_f06.py (YCrCb Cr∈[133,173], Cb∈[77,127] ∧ HSV H≤30). La punta se estima como "
           "el punto más alto de la máscara; acierto si está a ≤ 15 px de la real.",
           r"\mathrm{IoU}=\frac{|M\cap G|}{|M\cup G|}\times 100\%",
           "Siluetas sintéticas: la precisión con manos reales, distintos tonos de piel y distancias se mide en el "
           "laboratorio con participantes.")


# ---------------------------------------------------------------------------- F07 homografía
def f07() -> None:
    W, H = 640, 480
    grid = np.array([[x, y] for y in np.linspace(0, H, 5) for x in np.linspace(0, W, 5)], np.float32)
    corners_idx = [0, 4, 24, 20]
    interior = np.array([p for i, p in enumerate(grid) if i not in corners_idx], np.float32)
    errs = []
    for _ in range(300):
        src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
        dst = src + RNG.uniform(-80, 80, (4, 2)).astype(np.float32)                 # cámara inclinada
        Ht = cv2.getPerspectiveTransform(src, dst)
        clicks = (dst + RNG.normal(0, 1.5, (4, 2))).astype(np.float32)              # clic en las esquinas (σ=1,5 px)
        He, _ = cv2.findHomography(clicks, src, cv2.RANSAC)                         # como prototipo_f07.py
        seen = cv2.perspectiveTransform(interior[None], Ht)[0]
        back = cv2.perspectiveTransform(seen[None], He)[0]
        errs.append(float(np.mean(np.linalg.norm(back - interior, axis=1))))
    e = mean_sd(errs)
    record("F07", "Mapeo de coordenadas (homografía)", "sintetico",
           {"ensayos": len(errs), "error_px": round(e[0], 2), "error_sd_px": round(e[1], 2),
            "p95_px": round(float(np.percentile(errs, 95)), 2)},
           "300 ensayos: una inclinación aleatoria de la cámara (esquinas desplazadas hasta ±80 px) y cuatro clics en "
           "las esquinas con error gaussiano σ = 1,5 px. Con la homografía estimada (findHomography, RANSAC) se "
           "reproyectan los 21 puntos interiores de una grilla 5×5 y se mide su distancia a la posición real.",
           r"e_{\mathrm{reproy}}=\frac{1}{21}\sum_{j=1}^{21}\left\lVert H\,p_j-p_j^{\ast}\right\rVert_2",
           "El error depende de la precisión del clic; con la cámara y la lámina patrón reales se mide en el laboratorio.")


# ---------------------------------------------------------------------------- F10 sockets
def f10() -> None:
    n, period = 3000, 1 / 60
    received = []

    def server(sock):
        conn, _ = sock.accept()
        start = time.perf_counter()
        for i in range(n):
            target = start + i * period
            while time.perf_counter() < target:
                time.sleep(0.0005)
            frame = {"category": "tracker", "statuscode": 200,
                     "values": {"frame": {"avg": {"x": 640 + i % 50, "y": 360}, "time": i}}}
            conn.sendall((json.dumps(frame) + "\n").encode())
        conn.close()

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    threading.Thread(target=server, args=(sock,), daemon=True).start()
    client = socket.create_connection(sock.getsockname())
    buf = b""
    while len(received) < n:
        chunk = client.recv(65536)
        if not chunk:
            break
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            obj = json.loads(line)                                   # mismo formato que EyeTribe (TCP 6555)
            received.append((time.perf_counter(), obj["values"]["frame"]["avg"]["x"]))
    client.close()
    sock.close()
    dts = np.diff([r[0] for r in received]) * 1000
    freq = 1000 / float(np.mean(dts))
    jitter = float(np.std(dts, ddof=1))
    record("F10", "Comunicación con el rastreador ocular (socket)", "sintetico",
           {"muestras": n, "recibidas": len(received), "perdida_pct": round(100 * (n - len(received)) / n, 2),
            "frecuencia_hz": round(freq, 2), "jitter_ms": round(jitter, 2)},
           f"Un servidor local envía {n} muestras de mirada a 60 Hz con el formato JSON del protocolo EyeTribe "
           "(TCP); el cliente las lee y decodifica como el prototipo. Se mide el intervalo entre recepciones.",
           r"\mathrm{Jitter}=\sqrt{\frac{1}{M-1}\sum_{k=1}^{M}\left(\Delta t_k-\overline{\Delta t}\right)^2}",
           "Enlace local (127.0.0.1): no incluye la latencia del dispositivo. Con GazePoint/EyeTribe reales se mide "
           "en el laboratorio.")


# ---------------------------------------------------------------------------- F11 carga dinámica
def f11(project: Path | None) -> None:
    targets = []
    if project is not None:
        targets = sorted((project / "plugins").glob("*.py")) + sorted((project / "plugins/gestures").glob("*.py"))
        targets = [t for t in targets if t.name != "__init__.py"]
    if not targets:
        pending("F11", "Carga dinámica de plugins (importlib)", "Indicar --proyecto con la carpeta del código.")
        return
    sys.path.insert(0, str(project))
    times, fails = [], 0
    for rep in range(30):
        for path in targets:
            name = f"_medicion_{path.stem}_{rep}"
            t0 = time.perf_counter()
            try:
                spec = importlib.util.spec_from_file_location(name, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception:
                fails += 1
                continue
            times.append((time.perf_counter() - t0) * 1000)
            sys.modules.pop(name, None)
    t = mean_sd(times)
    record("F11", "Carga dinámica de plugins (importlib)", "codigo",
           {"modulos": len(targets), "cargas": len(times), "fallas": fails, "tiempo_ms": round(t[0], 2),
            "tiempo_sd_ms": round(t[1], 2)},
           f"30 cargas de cada uno de los {len(targets)} módulos de plugins del código final con "
           "importlib.util.spec_from_file_location + exec_module (cada carga con un nombre nuevo, sin caché del "
           "módulo; las bibliotecas que importan ya están cargadas).",
           r"\bar{t}=\frac{1}{N}\sum_{i=1}^{N}t_i",
           "No hay telemetría de carga del C# para comparar; la comparación con AppDomain queda cualitativa.")


# ---------------------------------------------------------------------------- F12 permanencia
def dwell_events(trace, radius, dwell_s):
    # Algoritmo de modificar_demo_real_f12.py: zona de radio fijo desde el punto de entrada.
    events, enter, start, fired = [], None, None, False
    for t, x, y in trace:
        if enter is None or math.hypot(x - enter[0], y - enter[1]) > radius:
            enter, start, fired = (x, y), t, False
        elif not fired and t - start >= dwell_s:
            events.append(t)
            fired = True
    return events


def gaze_trace(minutes: float = 3.0, hz: int = 60, noise_px: float = 10.0):
    # Lectura simulada: fijaciones de 150–450 ms, regresiones y cada ~20 s una mirada de 1,2 s sobre un botón, con ruido gaussiano.
    trace, voluntary, t, x, y = [], [], 0.0, 300.0, 200.0
    next_button = 20.0
    while t < minutes * 60:
        if t >= next_button:
            bx, by = RNG.uniform(900, 1250), RNG.uniform(20, 120)
            voluntary.append((t, t + 1.2))
            for _ in range(int(1.2 * hz)):
                trace.append((t, bx + RNG.normal(0, noise_px), by + RNG.normal(0, noise_px)))
                t += 1 / hz
            next_button = t + RNG.uniform(15, 25)
            continue
        dur = float(np.clip(RNG.lognormal(math.log(0.24), 0.35), 0.15, 0.45))
        for _ in range(max(1, int(dur * hz))):
            trace.append((t, x + RNG.normal(0, noise_px), y + RNG.normal(0, noise_px)))
            t += 1 / hz
        x += RNG.uniform(25, 60) if RNG.random() > 0.12 else -RNG.uniform(40, 120)
        if x > 820:
            x, y = 300.0, y + 22 if y < 560 else 200.0
    return trace, voluntary


def f12() -> None:
    noise = {}
    for sigma in (5, 10, 15):
        trace, voluntary = gaze_trace(minutes=10.0, noise_px=sigma)
        ev = dwell_events(trace, 45, 0.6)
        vol = sum(any(a <= e <= b for e in ev) for a, b in voluntary)
        acc = sum(not any(a <= e <= b for a, b in voluntary) for e in ev)
        noise[sigma] = (round(100 * vol / len(voluntary), 1), round(acc / 10.0, 2))
    trace, voluntary = gaze_trace(minutes=10.0, noise_px=10)
    grid = []
    for t_dwell in (0.4, 0.5, 0.6, 0.8):
        for radius in (25, 35, 45):
            ev = dwell_events(trace, radius, t_dwell)
            vol = sum(any(a <= e <= b for e in ev) for a, b in voluntary)
            acc = sum(not any(a <= e <= b for a, b in voluntary) for e in ev)
            grid.append({"T_s": t_dwell, "R_px": radius, "voluntarias_pct": round(100 * vol / len(voluntary), 1),
                         "accidentales_por_min": round(acc / 10.0, 2)})
    proto = next(g for g in grid if g["T_s"] == 0.6 and g["R_px"] == 45)
    record("F12", "Clic por permanencia de la mirada", "sintetico",
           {"umbral_s": 0.6, "radio_px": 45, "voluntarias_pct": proto["voluntarias_pct"],
            "accidentales_por_min": proto["accidentales_por_min"], "miradas_voluntarias": len(voluntary),
            "voluntarias_ruido_bajo_pct": noise[5][0], "accidentales_ruido_bajo": noise[5][1],
            "voluntarias_ruido_alto_pct": noise[15][0], "accidentales_ruido_alto": noise[15][1], "barrido": grid},
           "Traza de 10 min a 60 Hz que simula lectura (fijaciones log-normales de 150–450 ms, avances de 25–60 px, "
           "12 % de regresiones) y una mirada voluntaria de 1,2 s sobre un botón cada 15–25 s, con ruido gaussiano "
           "σ = 10 px (y σ = 5 y 15 px para comparar). Algoritmo de modificar_demo_real_f12.py (zona de radio 45 px "
           "anclada al primer punto, 0,6 s) y barrido T × R con σ = 10 px.",
           r"\text{accidentales/min}=\frac{N_{\text{disparos fuera de miradas voluntarias}}}{t_{\text{lectura}}}",
           "Traza simulada: el umbral definitivo se calibra con lectores reales y el eye tracker del laboratorio.")


# ---------------------------------------------------------------------------- F13 retícula
def f13() -> None:
    W, H = 950, 620
    base = np.full((H, W, 3), 245, np.uint8)
    for i in range(18):
        cv2.putText(base, "Linea de texto del libro proyectado " * 2, (40, 60 + i * 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (40, 40, 40), 1)

    def frame(pos):
        canvas = base.copy()
        overlay = canvas.copy()
        cv2.circle(overlay, pos, 40, (0, 140, 255), -1)
        canvas = cv2.addWeighted(overlay, 0.25, canvas, 0.75, 0)
        cv2.circle(canvas, pos, 40, (0, 120, 255), 2)
        cv2.line(canvas, (pos[0] - 50, pos[1]), (pos[0] + 50, pos[1]), (0, 120, 255), 1)
        cv2.line(canvas, (pos[0], pos[1] - 50), (pos[0], pos[1] + 50), (0, 120, 255), 1)
        return canvas

    t = timed(frame, (475, 310), repeat=600)
    record("F13", "Retícula de mirada sobre la proyección", "sintetico",
           {"tiempo_ms": round(t[0], 2), "tiempo_sd_ms": round(t[1], 2), "fps_max": round(1000 / t[0], 1)},
           "600 cuadros de 950×620 con el dibujo de la retícula de modificar_demo_real_f13.py (círculo con mezcla "
           "alfa y cruz) tras 10 de calentamiento. Mide solo el dibujo, no la presentación en el proyector.",
           r"\mathrm{FPS}_{\max}=1000/\bar{t}_{\mathrm{ms}}",
           "La latencia de extremo a extremo (dispositivo → proyector) se mide en el laboratorio.")


# ---------------------------------------------------------------------------- F14 QuadPoints
def fold(text: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


TERMS = ["EDDIE", "lectura", "plugin", "proyección", "cámara", "PDF", "requerimientos", "prototipo", "OpenCV",
         "rastreo"]


def f14(doc) -> None:
    per_page, found, coherent = [], 0, 0
    for _ in range(3):
        for term in TERMS:
            for page in doc:
                t0 = time.perf_counter()
                quads = page.search_for(term, quads=True)
                per_page.append((time.perf_counter() - t0) * 1000)
                for q in quads:
                    found += 1
                    rect = q.rect + (-2, -1, 2, 1)                 # get_text(clip) omite caracteres cortados
                    text = page.get_text("text", clip=rect).replace("\n", " ")
                    coherent += fold(term) in fold(text)
    t = mean_sd(per_page)
    record("F14", "Búsqueda de coordenadas QuadPoints", "pdf",
           {"paginas": doc.page_count, "consultas": len(per_page), "coincidencias": found,
            "coherencia_pct": round(100 * coherent / max(1, found), 1), "tiempo_ms": round(t[0], 3),
            "tiempo_sd_ms": round(t[1], 3)},
           f"{len(TERMS)} términos buscados 3 veces en las {doc.page_count} páginas del PDF con "
           "page.search_for(term, quads=True). Coherencia: el texto extraído del rectángulo de cada QuadPoint "
           "(ampliado 2 pt para no cortar caracteres) contiene el término, sin distinguir tildes ni mayúsculas. "
           "Las palabras cortadas con guion al final de línea dan dos QuadPoints que no contienen el término "
           "completo.",
           r"\mathrm{Coherencia}=\frac{N_{\text{QuadPoints cuyo texto contiene el término}}}{N_{\text{QuadPoints}}}\times 100\%")


# ---------------------------------------------------------------------------- F15 resaltado
def f15(doc_path: Path, tmp: Path) -> None:
    work = tmp / "f15.pdf"
    work.write_bytes(doc_path.read_bytes())
    doc = pymupdf.open(work)
    pages = text_pages(doc)[:10] or [0]
    times = []
    lines = []
    for p in pages:
        for x0, y0, x1, y1, *_ in doc[p].get_text("blocks")[:5]:
            lines.append((p, pymupdf.Rect(x0, y0, x1, min(y1, y0 + 14))))
    lines = lines[:50]
    for p, rect in lines:
        t0 = time.perf_counter()
        page = doc[p]
        annot = page.add_highlight_annot(rect)
        annot.set_colors(stroke=(1.0, 0.9, 0.1))
        annot.update()
        tmp_out = work.with_suffix(".tmp.pdf")
        doc.save(tmp_out, garbage=1)                       # guardado completo (corrección H-02)
        doc.close()
        tmp_out.replace(work)
        doc = pymupdf.open(work)
        times.append((time.perf_counter() - t0) * 1000)
    doc.close()
    reopened = pymupdf.open(work)
    persisted = sum(1 for page in reopened for a in page.annots() if a.type[0] == pymupdf.PDF_ANNOT_HIGHLIGHT)
    reopened.close()
    t = mean_sd(times)
    record("F15", "Sincronización de resaltado (papel → PDF)", "pdf",
           {"anotaciones": len(lines), "persistidas": persisted, "tiempo_ms": round(t[0], 1),
            "tiempo_sd_ms": round(t[1], 1)},
           f"{len(lines)} resaltados agregados uno a uno sobre líneas de texto del PDF; cada uno se guarda con "
           "escritura completa a un archivo temporal y reemplazo (la corrección de H-02) y se vuelve a abrir. "
           "Persistencia: resaltados presentes al reabrir el archivo final.",
           r"t=t_{\text{reapertura}}-t_{\text{inicio}}",
           "No mide la coincidencia en posición y largo con lo marcado en el papel (E40/E41 de Ibaceta, 2023): eso "
           "requiere la cámara y el proyector.")


# ---------------------------------------------------------------------------- F16 notas adhesivas
def f16(doc) -> None:
    p = (text_pages(doc) or [0])[0]
    page_img, zoom = render_page(doc, p, width=640)
    h, w = page_img.shape[:2]
    errs, ok, n = [], 0, 40
    for _ in range(n):
        frame = page_img.copy()
        size = int(RNG.integers(70, 110))
        x, y = int(RNG.integers(10, w - size - 10)), int(RNG.integers(10, h - size - 10))
        cv2.rectangle(frame, (x, y), (x + size, y + size), (90, 230, 250), -1)       # amarillo canario (BGR)
        frame = np.clip(frame.astype(np.float32) + RNG.normal(0, 4, frame.shape), 0, 255).astype(np.uint8)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([18, 80, 80]), np.array([38, 255, 255]))
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in cnts:
            if cv2.contourArea(cnt) > 2500:
                approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
                if len(approx) == 4:
                    bx, by, bw, bh = cv2.boundingRect(approx)
                    det = ((bx + bw / 2) / zoom, (by + bh / 2) / zoom)                 # px de cámara → pt del PDF
                    real = ((x + size / 2) / zoom, (y + size / 2) / zoom)
                    errs.append(math.dist(det, real))
                    ok += 1
                    break
    e = mean_sd(errs)
    record("F16", "Sincronización de notas adhesivas", "sintetico",
           {"notas": n, "detectadas_pct": round(100 * ok / n, 1), "error_pt": round(e[0], 2), "error_sd_pt": round(e[1], 2)},
           f"{n} notas amarillas cuadradas (70–110 px) en posiciones aleatorias sobre una página del PDF "
           "renderizada; detección de prototipo_f16.py (HSV H∈[18,38], área > 2 500, 4 vértices) y conversión del "
           "centro a puntos del PDF con la escala de la página (1 pt = 0,3528 mm).",
           r"\Delta=\sqrt{(x_{\text{real}}-\hat{x}_{\text{pdf}})^2+(y_{\text{real}}-\hat{y}_{\text{pdf}})^2}",
           "Con la cámara real se agrega el error de la homografía cámara → página (F07) y la lectura de la nota "
           "manuscrita con OCR, que se miden en el laboratorio.")


# ---------------------------------------------------------------------------- F17 figuras
def f17_classify(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 40, 130)
    edges = cv2.dilate(edges, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=1)
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        if area > 1200:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.035 * peri, True)
            circ = 4 * math.pi * area / (peri * peri) if peri else 0
            if circ > 0.69:
                (cx, cy), r = cv2.minEnclosingCircle(cnt)
                out.append(("circulo", (cx, cy, r)))
            elif len(approx) == 4:
                out.append(("rectangulo", cv2.boundingRect(approx)))
            elif len(approx) == 3:
                out.append(("triangulo", cv2.boundingRect(approx)))
    return out


def f17() -> None:
    labels, correct, ious = [], 0, []
    n_each = 20
    for kind in ("circulo", "rectangulo", "triangulo"):
        for _ in range(n_each):
            frame = np.full((480, 640, 3), 250, np.uint8)
            truth = np.zeros((480, 640), np.uint8)
            cx, cy = int(RNG.integers(160, 480)), int(RNG.integers(140, 340))
            if kind == "circulo":
                r = int(RNG.integers(40, 110))
                cv2.circle(frame, (cx, cy), r, (180, 60, 200), 3)
                cv2.circle(truth, (cx, cy), r, 255, -1)
            elif kind == "rectangulo":
                w, h = int(RNG.integers(80, 220)), int(RNG.integers(60, 160))
                cv2.rectangle(frame, (cx - w // 2, cy - h // 2), (cx + w // 2, cy + h // 2), (180, 60, 200), 3)
                cv2.rectangle(truth, (cx - w // 2, cy - h // 2), (cx + w // 2, cy + h // 2), 255, -1)
            else:
                s = int(RNG.integers(90, 200))
                pts = np.array([[cx, cy - s // 2], [cx - s // 2, cy + s // 2], [cx + s // 2, cy + s // 2]], np.int32)
                cv2.polylines(frame, [pts], True, (180, 60, 200), 3)
                cv2.fillPoly(truth, [pts], 255)
            frame = np.clip(frame.astype(np.float32) + RNG.normal(0, 3, frame.shape), 0, 255).astype(np.uint8)
            found = f17_classify(frame)
            got = found[0][0] if found else "ninguna"
            labels.append((kind, got))
            if got == kind:
                correct += 1
                pred = np.zeros_like(truth)
                if kind == "circulo":
                    x, y, r = found[0][1]
                    cv2.circle(pred, (int(x), int(y)), int(r), 255, -1)
                else:
                    x, y, w, h = found[0][1]
                    if kind == "rectangulo":
                        cv2.rectangle(pred, (x, y), (x + w, y + h), 255, -1)
                    else:
                        cv2.fillPoly(pred, [np.array([[x + w // 2, y], [x, y + h], [x + w, y + h]], np.int32)], 255)
                ious.append(100 * np.sum((pred > 0) & (truth > 0)) / max(1, np.sum((pred > 0) | (truth > 0))))
    i = mean_sd(ious)
    confusion = {}
    for real, got in labels:
        confusion.setdefault(real, {}).setdefault(got, 0)
        confusion[real][got] += 1
    record("F17", "Sincronización de figuras geométricas", "sintetico",
           {"figuras": len(labels), "exactitud_pct": round(100 * correct / len(labels), 1), "iou_pct": round(i[0], 1),
            "iou_sd": round(i[1], 1), "confusion": confusion},
           f"{len(labels)} figuras dibujadas con trazo de 3 px ({n_each} círculos, {n_each} rectángulos, {n_each} "
           "triángulos de tamaño y posición aleatorios). Clasificador de prototipo_f17.py: compacidad "
           "C = 4πA/P² > 0,69 → círculo; 4 vértices → rectángulo; 3 → triángulo. IoU entre la primitiva "
           "reconstruida y la figura real (solo las bien clasificadas).",
           r"C=\frac{4\pi A}{P^2},\qquad \mathrm{IoU}=\frac{|F_{\text{PDF}}\cap F_{\text{real}}|}{|F_{\text{PDF}}\cup F_{\text{real}}|}\times 100\%",
           "Hallazgo: un cuadrado tiene compacidad π/4 ≈ 0,785 > 0,69, por lo que el prototipo, que evalúa la "
           "compacidad antes que el número de vértices, lo clasifica como círculo. Figuras dibujadas por computador; "
           "con trazos a mano y la cámara real se mide en el laboratorio.")


# ---------------------------------------------------------------------------- F27 banda de resaltado
def f27() -> None:
    W, H = 900, 600
    base = np.full((H, W, 3), 245, np.uint8)

    def band(y):
        overlay = base.copy()
        cv2.rectangle(overlay, (60, y - 12), (W - 60, y + 12), (0, 230, 255), -1)
        return cv2.addWeighted(overlay, 0.30, base, 0.70, 0)

    t = timed(band, 300, repeat=600)
    record("F27", "Banda de resaltado proyectada", "sintetico",
           {"alfa": 0.30, "tiempo_ms": round(t[0], 3), "tiempo_sd_ms": round(t[1], 3)},
           "600 cuadros de 900×600 con la banda de prototipo_f27.py (rectángulo amarillo y mezcla alfa 0,30). "
           "El contraste de Weber del texto bajo la luz proyectada se mide con luxómetro en el laboratorio.",
           r"C_W=\frac{L_{\text{texto}}-L_{\text{fondo}}}{L_{\text{fondo}}}")


# ---------------------------------------------------------------------------- salidas
def macro_name(fid: str, key: str) -> str:
    words = {1: "Uno", 2: "Dos", 3: "Tres", 4: "Cuatro", 5: "Cinco", 6: "Seis", 7: "Siete", 9: "Nueve", 10: "Diez",
             11: "Once", 12: "Doce", 13: "Trece", 14: "Catorce", 15: "Quince", 16: "Dieciseis", 17: "Diecisiete",
             24: "Veinticuatro", 25: "Veinticinco", 27: "Veintisiete"}
    base = "F" + words[int(fid[1:])]
    digits = {"0": "Cero", "1": "Uno", "2": "Dos", "3": "Tres", "4": "Cuatro", "5": "Cinco", "6": "Seis",
              "7": "Siete", "8": "Ocho", "9": "Nueve"}
    key = re.sub(r"\d+", lambda m: "_" + "".join(digits[c] for c in m.group()) + "_", key)
    clean = "".join(part.capitalize() for part in re.split(r"[^a-zA-Z]+", key) if part)
    return f"\\{base}{clean}"


def fmt(value) -> str:
    if isinstance(value, float):
        text = f"{value:.2f}" if abs(value) < 100 else f"{value:.1f}"
        return text.rstrip("0").rstrip(".").replace(".", "{,}") if "." in text else text
    return str(value).replace("%", r"\%")


def write_outputs(pdf: Path) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {"fecha": datetime.now().isoformat(timespec="seconds"), "python": sys.version.split()[0],
            "opencv": cv2.__version__, "pymupdf": pymupdf.__version__,
            "sistema": f"{platform.system()} {platform.release()}", "procesador": platform.processor() or platform.machine(),
            "pdf": pdf.name, "semilla": 2026}
    (OUT / "mediciones.json").write_text(json.dumps({"entorno": meta, "prototipos": RESULTS}, indent=2,
                                                    ensure_ascii=False), encoding="utf-8")
    lines = ["# Mediciones de los prototipos desechables", "",
             f"Ejecutado el {meta['fecha']} en {meta['sistema']} ({meta['procesador']}), Python {meta['python']}, "
             f"OpenCV {meta['opencv']}, PyMuPDF {meta['pymupdf']}. PDF: `{pdf.name}`. Semilla {meta['semilla']}.", "",
             "Tipo: **pdf** = sobre el PDF real; **codigo** = sobre los módulos reales; **sintetico** = datos generados con verdad terreno conocida; "
             "**laboratorio** = requiere hardware o participantes (pendiente).", ""]
    for fid, r in RESULTS.items():
        lines += [f"## {fid} — {r['nombre']} ({r['tipo']})", "", r["protocolo"], ""]
        if r["formula"]:
            lines += [f"Fórmula: `{r['formula']}`", ""]
        for k, v in r["metricas"].items():
            if k not in ("barrido", "confusion"):
                lines.append(f"- {k}: {v}")
        if "barrido" in r["metricas"]:
            lines += ["", "| T (s) | R (px) | Voluntarias (%) | Accidentales/min |", "|---|---|---|---|"]
            lines += [f"| {g['T_s']} | {g['R_px']} | {g['voluntarias_pct']} | {g['accidentales_por_min']} |"
                      for g in r["metricas"]["barrido"]]
        if "confusion" in r["metricas"]:
            lines += ["", f"Matriz de confusión: {r['metricas']['confusion']}"]
        if r["nota"]:
            lines += ["", f"_Alcance:_ {r['nota']}"]
        lines.append("")
    (OUT / "MEDICIONES.md").write_text("\n".join(lines), encoding="utf-8")
    tex = ["% Generado por mediciones/medir_prototipos.py — no editar a mano; volver a ejecutar el script.",
           f"\\newcommand{{\\MedicionFecha}}{{{meta['fecha'][:10]}}}",
           f"\\newcommand{{\\MedicionSistema}}{{{meta['sistema']}}}",
           f"\\newcommand{{\\MedicionPDF}}{{\\texttt{{{pdf.name.replace('_', chr(92) + '_')}}}}}"]
    for fid, r in RESULTS.items():
        for k, v in r["metricas"].items():
            if k in ("barrido", "confusion", "estado"):
                continue
            tex.append(f"\\newcommand{{{macro_name(fid, k)}}}{{{fmt(v)}}}")
        if "barrido" in r["metricas"]:
            rows = " \\\\\n".join(f"{fmt(g['T_s'])} & {g['R_px']} & {fmt(g['voluntarias_pct'])} & "
                                   f"{fmt(g['accidentales_por_min'])}" for g in r["metricas"]["barrido"])
            tex.append(f"\\newcommand{{\\FDoceBarrido}}{{{rows}}}")
        tipo = {"sintetico": "sintético", "codigo": "código"}.get(r["tipo"], r["tipo"])
        tex.append(f"\\newcommand{{{macro_name(fid, 'tipo')}}}{{{tipo}}}")
    (OUT / "prototipos_datos.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")
    print(f"\nResultados: {OUT / 'MEDICIONES.md'}\nMacros LaTeX: {OUT / 'prototipos_datos.tex'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pdf", type=Path, required=True, help="PDF real (por ejemplo, el libro o el informe)")
    parser.add_argument("--camara", type=int, default=None, help="Índice de la cámara para F01")
    parser.add_argument("--proyecto", type=Path, default=ROOT.parent / "P-07_version_final_verificada",
                        help="Carpeta del código final (para F11)")
    args = parser.parse_args()
    doc = pymupdf.open(args.pdf)
    tmp = OUT / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    print(f"Midiendo prototipos con {args.pdf.name} ({doc.page_count} páginas)…")
    f01(args.camara)
    f02(doc)
    f03(doc)
    f04(doc)
    f05(doc)
    f06(doc)
    f07()
    pending("F09", "Mouse como alternativa", "Ejecutar prototipo_f09.py y registrar 1 000 eventos (movimiento, "
            "clic, arrastre) con marcas de tiempo del callback; requiere la interfaz gráfica del PC.",
            r"\Delta t=t_{\text{callback}}-t_{\text{evento}}")
    f10()
    f11(args.proyecto if args.proyecto.exists() else None)
    f12()
    f13()
    f14(doc)
    f15(args.pdf, tmp)
    f16(doc)
    f17()
    pending("F24", "Comandos de voz", "Grabar los 8 comandos del módulo de búsqueda (Montanares, 2019) "
            "10 veces cada uno con 3 personas en la sala del laboratorio; exactitud = comandos correctos / emitidos "
            "y tiempo desde el fin de la frase hasta el texto reconocido (SpeechRecognition, es-ES).",
            r"\mathrm{Exactitud}=\frac{N_{\text{correctos}}}{N_{\text{emitidos}}}\times 100\%")
    pending("F25", "Síntesis de voz", "Leer 10 textos de 100 palabras con pyttsx3 (voz SAPI5 en español) en un "
            "hilo aparte; medir la duración de cada lectura (palabras por minuto) y que la interfaz no se bloquee.",
            r"\mathrm{WPM}=N_{\text{palabras}}/t_{\text{min}}")
    f27()
    doc.close()
    for f in tmp.glob("*"):
        f.unlink()
    tmp.rmdir()
    write_outputs(args.pdf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
