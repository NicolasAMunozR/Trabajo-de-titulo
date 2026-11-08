"""
tools/generar_evidencias.py — evidencias reproducibles de cada avance
====================================================================
Mismo script en todas las carpetas de avance. Detecta qué módulos existen en el
avance y genera, dentro de ./evidencias:

  pruebas.txt / junit.xml     Salida de pytest (unitarias, de contrato e integración)
  cobertura.txt               Cobertura de líneas por módulo (pytest-cov), umbral ≥ 80 %
  inicializacion.json         Reporte de carga de cada plugin (initialized / load_failed / ...)
  latencias.csv / .json       Latencia por plugin y por ciclo del OrchestratorCore (objetivo ≤ 8,3 ms)
  capturas/*.png              Capturas de la interfaz (solo desde P-03), con dispositivos simulados
  resumen.json / RESULTADOS.md

Uso (desde la carpeta del avance, con el .venv del proyecto activado):
  python tools/generar_evidencias.py                  → todo, dispositivos simulados
  python tools/generar_evidencias.py --real           → latencias con el hardware real conectado
  python tools/generar_evidencias.py --ciclos 1000 --sin-capturas
"""
import argparse
import csv
import importlib.util
import json
import os
import platform
import re
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT / "evidencias"
MAX_LATENCY_MS = 8.3
WARMUP_CYCLES = 10
PACKAGES = ("contracts", "orchestrator", "hardware", "plugins", "app", "ui")


def has(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


# ---------------------------------------------------------------------------- 1. pruebas + cobertura
def run_tests() -> dict:
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={EVID / 'junit.xml'}"]
    coverage = has("pytest_cov")
    if coverage:
        cmd += [f"--cov={p}" for p in PACKAGES if (ROOT / p).is_dir()]
        cmd += ["--cov-report=term-missing"]
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONDONTWRITEBYTECODE="1")
    env.pop("EDDIE_DEVICE_MODE", None)
    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    output = proc.stdout + proc.stderr
    (EVID / "pruebas.txt").write_text(output, encoding="utf-8")
    summary = {"exit_code": proc.returncode, "seconds": round(time.perf_counter() - started, 1)}
    for key in ("passed", "failed", "skipped", "xfailed", "error", "errors"):
        found = re.findall(rf"(\d+) {key}\b", output)
        if found:
            summary[key.rstrip("s") if key == "errors" else key] = int(found[-1])
    if coverage:
        start = output.find("---------- coverage")
        (EVID / "cobertura.txt").write_text(output[start:] if start >= 0 else output, encoding="utf-8")
        total = re.search(r"^TOTAL\s+\d+\s+\d+\s+(\d+)%", output, re.MULTILINE)
        if total:
            summary["coverage_percent"] = int(total.group(1))
            summary["coverage_threshold_80"] = int(total.group(1)) >= 80
    return summary


# ---------------------------------------------------------------------------- 2. latencias
def _overrides(declared: set) -> dict:
    overrides = {}
    if has("app.settings_store"):
        from app.settings_store import SettingsStore
        overrides = SettingsStore(Path(tempfile.mkdtemp()) / "ajustes.json").plugin_overrides()
    if "EyeTrackerMock" in declared:                     # mirada sintética, como en una sesión de lectura
        overrides["EyeTrackerMock"] = {"enabled": True, "config": {"source": "synthetic"}}
    return {k: v for k, v in overrides.items() if k in declared}


def measure_latency(cycles: int, real: bool) -> dict:
    os.environ["EDDIE_DEVICE_MODE"] = "real" if real else "sim"
    from orchestrator.orchestrator_core import OrchestratorCore
    config = json.loads((ROOT / "config" / "plugins.json").read_text(encoding="utf-8"))
    declared = {p["name"] for p in config["plugins"]}
    try:
        orch = OrchestratorCore("config/plugins.json", _overrides(declared))
    except TypeError:                                    # núcleo de P-01 (sin overrides)
        orch = OrchestratorCore("config/plugins.json")
    orch.initialize()
    (EVID / "inicializacion.json").write_text(json.dumps(orch.initialization_report, indent=2, ensure_ascii=False),
                                              encoding="utf-8")
    active_gesture = None
    for name in ("ColorPenRecognition", "HandSkinRecognition"):
        plugin = orch.get_plugin(name) if hasattr(orch, "get_plugin") else None
        if plugin is not None:
            plugin.set_recognition_active(True)          # como "Start Recognition"
            active_gesture = name
            break
    for _ in range(WARMUP_CYCLES):                       # primer frame, carga de OpenCV/Tesseract: no se registra
        orch.execute_cycle()
        time.sleep(1 / 120)
    per_plugin: dict[str, list[float]] = {}
    totals = []
    rows = []
    for cycle in range(1, cycles + 1):
        start = time.perf_counter()
        orch.execute_cycle()
        totals.append((time.perf_counter() - start) * 1000)
        for name, metric in orch.last_cycle_metrics.items():
            per_plugin.setdefault(name, []).append(metric["latency_ms"])
            rows.append([cycle, name, metric["status"], metric["latency_ms"]])
        time.sleep(1 / 120)                              # da tiempo a que los sensores publiquen frames
    orch.release()
    with (EVID / "latencias.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ciclo", "plugin", "estado", "latencia_ms"])
        writer.writerows(rows)

    def stats(values: list[float]) -> dict:
        ordered = sorted(values)
        return {"n": len(values), "media_ms": round(statistics.mean(values), 4),
                "p95_ms": round(ordered[int(0.95 * (len(ordered) - 1))], 4), "max_ms": round(max(values), 4),
                "sobre_8_3ms": sum(v > MAX_LATENCY_MS for v in values)}

    result = {"modo": "real" if real else "simulado", "ciclos": cycles, "ciclos_calentamiento": WARMUP_CYCLES,
              "gesto_activo": active_gesture,
              "ciclo_completo": stats(totals), "por_plugin": {k: stats(v) for k, v in per_plugin.items()}}
    result["cumple_8_3ms_p95"] = all(v["p95_ms"] <= MAX_LATENCY_MS for v in result["por_plugin"].values())
    (EVID / "latencias.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


# ---------------------------------------------------------------------------- 3. capturas de la interfaz
def hand_scene(path: Path) -> None:
    """Escena sintética para la cámara gestual: mano (tono piel) arriba a la izquierda y el rótulo ARRIBA."""
    import cv2
    import numpy as np
    frame = np.full((720, 960, 3), 40, np.uint8)
    cv2.ellipse(frame, (230, 260), (95, 125), 0, 0, 360, (120, 160, 220), -1)          # palma
    for i, dx in enumerate((-70, -25, 20, 65)):                                         # dedos hacia arriba
        cv2.ellipse(frame, (230 + dx, 120 - (i % 2) * 15), (18, 60), 0, 0, 360, (120, 160, 220), -1)
    cv2.putText(frame, "ARRIBA", (560, 90), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 4)
    cv2.arrowedLine(frame, (700, 330), (700, 140), (255, 255, 255), 6, tipLength=0.25)
    cv2.imwrite(str(path), frame)


def sample_pdf(path: Path) -> Path:
    """PDF de 3 páginas para la captura de Page detection (no se usa ningún PDF personal)."""
    import pymupdf
    document = pymupdf.open()
    for number in range(1, 4):
        page = document.new_page()
        page.insert_text((72, 90), f"Capítulo {number}: lectura aumentada", fontsize=22)
        y = 140
        for line in ("EDDIE proyecta definiciones, traducciones y contenido", "digital sobre el libro impreso.",
                     "El lector resalta una palabra y el sistema la reconoce", "con OCR para buscarla."):
            page.insert_text((72, y), line, fontsize=13)
            y += 22
    document.save(path)
    document.close()
    return path


def projection_flow(ctx, runtime, app, tmp: Path, grab) -> None:
    """P-08: capturas de la proyección en uso (búsqueda, sincronizador e historial).

    Las respuestas las da un LLM local de prueba (el mismo servidor falso de tests/conftest.py), así la
    captura muestra el flujo real de la interfaz sin depender de una clave de Gemini.
    """
    if not has("tests.conftest"):
        return
    import threading
    from http.server import HTTPServer
    from tests.conftest import _FakeLLM
    server = HTTPServer(("127.0.0.1", 0), _FakeLLM)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        if not runtime.restart("LLM-Gemini", {"base_url": f"http://127.0.0.1:{server.server_port}",
                                              "api_key": "prueba-local"}):
            return
        web = ctx.pages["web"]
        web.refresh_providers()
        web.load_settings()
        screen = ctx.projection
        f = screen.form
        screen.toggle_mode()                                   # modo resaltado
        screen.highlight._start.setX(60)
        screen.highlight._start.setY(118)
        screen.highlight._end.setX(230)
        screen.highlight._end.setY(118)
        screen.highlight.get_rectangle()
        f.textBox1.setPlainText("aumentada")                   # término (OCR o corregido por el lector)
        screen.toggle_web_search()
        screen.search_definition()
        screen.search_encyclopedia()
        runtime.wait_for_jobs(15000)
        app.processEvents()
        grab(screen, "11_proyeccion_busqueda")
        screen.close_left()
        screen.close_right()
        pdf = sample_pdf(tmp / "libro_sync.pdf")
        ctx.pages["page"].open_pdf(str(pdf))
        screen.toggle_synchronizer()
        screen.sync_highlight()
        f.searchTextBox.setText("1")
        screen.load_pdf_content()
        grab(screen, "12_proyeccion_pdf")
        screen.toggle_synchronizer()
        if screen.figures_overlay is not None:
            screen.figures_overlay.hide()
        screen.toggle_history()
        grab(screen, "13_proyeccion_historial")
        screen.csv_lines = screen.csv_lines[:1]              # la captura no escribe en el CSV de actividades
    finally:
        server.shutdown()


def screenshots() -> list[str]:
    if not has("ui.menu_settings") or not has("PySide6"):
        return []
    os.environ["EDDIE_DEVICE_MODE"] = "sim"
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")
    from PySide6.QtCore import QCoreApplication, Qt
    from PySide6.QtWidgets import QApplication

    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication.instance() or QApplication([])
    from app.runtime import EddieRuntime
    from app.settings_store import SettingsStore
    from ui import dialogs, menu_settings
    from ui.context import AppContext
    try:
        from ui.theme import apply_theme             # interfaz renovada (P-08)
        apply_theme(app)
    except ImportError:
        from ui.form_builder import apply_light_theme, load_fonts
        apply_light_theme(app)
        load_fonts()
    messages: list[str] = []
    for module in (dialogs, menu_settings):              # sin ventanas modales durante la captura
        module.message = lambda parent, text, title="EDDIE": messages.append(text)

    shots = EVID / "capturas"
    shots.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    hand = tmp / "escena_mano.png"
    hand_scene(hand)
    settings = SettingsStore(tmp / "ajustes.json")
    runtime = EddieRuntime(settings, trace_dir=tmp)
    if "GestureCamera" in {p["name"] for p in runtime.orchestrator._load_config() or []}:
        runtime.orchestrator._config_overrides.setdefault("GestureCamera", {}).setdefault("config", {})["source"] = str(hand)
    runtime.start()
    ctx = AppContext(runtime=runtime, settings=settings)
    window = menu_settings.MenuSettingsWindow(ctx)
    window.show()

    def settle(n: int = 6) -> None:
        for _ in range(n):
            runtime._tick()
            app.processEvents()
            time.sleep(0.03)

    saved = []

    def grab(widget, name: str) -> None:
        settle()
        path = shots / f"{name}.png"
        widget.grab().save(str(path))
        saved.append(path.name)

    grab(window, "00_menu_settings")
    buttons = {"text": "TextRecognitiionButton", "page": "PageDetectionButton", "gesture": "GestureRecognitionButton",
               "eye": "EyeTrackingButton", "web": "WebSearchServicesButton", "interactions": "InteractionsButton"}
    for index, (key, button) in enumerate(buttons.items(), start=1):
        if key not in ctx.pages:
            continue
        window.open_page(button)
        if key == "gesture":
            page = ctx.pages["gesture"]
            for plugin_name, label in (("HandSkinRecognition", "mano"), ("ColorPenRecognition", "lapiz")):
                idx = page.form.comboBox1.findData(plugin_name)
                if idx < 0:
                    continue
                page.form.comboBox1.setCurrentIndex(idx)
                page.start_recognition()
                grab(window, f"{index:02d}_{key}_{label}")
                page.stop_recognition()
            continue
        if key == "text" and hasattr(ctx.pages["text"], "recognize_now"):
            settle()
            ctx.pages["text"].recognize_now()               # botón "Recognize text"
            runtime.wait_for_jobs(15000)
            app.processEvents()
        if key == "page" and hasattr(ctx.pages["page"], "show_preview"):
            ctx.pages["page"].open_pdf(str(sample_pdf(tmp / "libro_de_prueba.pdf")))
        grab(window, f"{index:02d}_{key}")
    if menu_settings.__dict__.get("projection_available", lambda: True)() and has("ui.projection_screen"):
        try:
            window.start_projection()
            if ctx.projection is not None:
                grab(ctx.projection, "10_proyeccion")
                projection_flow(ctx, runtime, app, tmp, grab)
                ctx.projection.close()
        except Exception as exc:                          # la captura no debe impedir el resto
            messages.append(f"proyección: {exc}")
    (shots / "mensajes.txt").write_text("\n".join(messages), encoding="utf-8")
    runtime.wait_for_jobs(3000)
    window.close()
    runtime.stop()
    return saved


# ---------------------------------------------------------------------------- resumen
def write_summary(summary: dict) -> None:
    (EVID / "resumen.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    t, lat = summary.get("pruebas", {}), summary.get("latencias", {})
    lines = [f"# Resultados — {summary['avance']}", "",
             f"Generado: {summary['fecha']} · Python {summary['python']} · {summary['sistema']} · "
             f"dispositivos {lat.get('modo', '-')}", "",
             "## Pruebas automatizadas", "",
             "| Aprobadas | Fallidas | Omitidas | Fallo esperado (hallazgo documentado) | Cobertura de líneas | "
             "Umbral 80 % |", "|---|---|---|---|---|---|",
             f"| {t.get('passed', 0)} | {t.get('failed', 0) + t.get('error', 0)} | {t.get('skipped', 0)} | "
             f"{t.get('xfailed', 0)} | "
             f"{str(t['coverage_percent']) + ' %' if 'coverage_percent' in t else 'n/d'} | "
             f"{'cumple' if t.get('coverage_threshold_80') else 'no cumple' if 'coverage_percent' in t else 'n/d'} |",
             ""]
    if lat:
        lines += ["## Latencia del OrchestratorCore", "",
                  f"{lat['ciclos']} ciclos medidos (tras {lat.get('ciclos_calentamiento', 0)} de calentamiento). "
                  f"Objetivo por plugin: ≤ {MAX_LATENCY_MS} ms (50 % de una muestra a 60 Hz)."
                  + (f" Gesto activo durante la medición: {lat['gesto_activo']}." if lat.get("gesto_activo") else ""), "",
                  "| Plugin | Media (ms) | p95 (ms) | Máx. (ms) | Ciclos > 8,3 ms |", "|---|---|---|---|---|"]
        for name, s in lat["por_plugin"].items():
            lines.append(f"| {name} | {s['media_ms']} | {s['p95_ms']} | {s['max_ms']} | {s['sobre_8_3ms']} |")
        c = lat["ciclo_completo"]
        lines += [f"| **Ciclo completo** | {c['media_ms']} | {c['p95_ms']} | {c['max_ms']} | {c['sobre_8_3ms']} |", ""]
    if summary.get("inicializacion"):
        lines += ["## Carga de plugins", "", "| Plugin | Estado | Detalle |", "|---|---|---|"]
        for name, r in summary["inicializacion"].items():
            lines.append(f"| {name} | {r['status']} | {r.get('error') or ''} |")
        lines.append("")
    demo = EVID / "consistencia" / "reporte.json"
    if demo.exists():
        data = json.loads(demo.read_text(encoding="utf-8"))
        calls = data.get("calls", [])
        lines += ["## Demostración de consistencia papel ↔ PDF (demos/demo_consistencia.py)", "",
                  "| Llamada (por OrchestratorCore.invoke) | Correcta | Latencia (ms) | Resultado |", "|---|---|---|---|"]
        for c in calls:
            value = str(c.get("value"))[:60].replace("|", "/")
            lines.append(f"| {c['method']} | {'sí' if c['ok'] else 'no'} | {c['latency_ms']} | {value} |")
        persist = data.get("persistencia")
        if persist:
            ok = (persist["anotaciones_por_pagina"] == persist["esperado"]["anotaciones_por_pagina"]
                  and len(persist["marcadores"]) == persist["esperado"]["marcadores"])
            lines += ["", f"Al reabrir el PDF guardado: anotaciones por página {persist['anotaciones_por_pagina']} "
                          f"(esperado {persist['esperado']['anotaciones_por_pagina']}), "
                          f"{len(persist['marcadores'])} marcadores (esperado {persist['esperado']['marcadores']}), "
                          f"PDF reparado al abrir: {persist['pdf_reparado_al_abrir']}. "
                          f"**{'Se conservan todos los cambios.' if ok else 'Se perdieron cambios (hallazgo H-02).'}**"]
        lines.append("")
    if summary.get("capturas"):
        lines += ["## Capturas", ""] + [f"- capturas/{name}" for name in summary["capturas"]] + [""]
    (EVID / "RESULTADOS.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ciclos", type=int, default=500)
    parser.add_argument("--real", action="store_true", help="Latencias con hardware real (cámaras/eye tracker)")
    parser.add_argument("--sin-pruebas", action="store_true")
    parser.add_argument("--sin-capturas", action="store_true")
    args = parser.parse_args()
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    EVID.mkdir(exist_ok=True)
    import logging
    logging.basicConfig(level=logging.WARNING, force=True)
    summary = {"avance": ROOT.name, "fecha": datetime.now().isoformat(timespec="seconds"),
               "python": platform.python_version(), "sistema": f"{platform.system()} {platform.release()}"}
    if not args.sin_pruebas:
        print("Ejecutando pruebas…")
        summary["pruebas"] = run_tests()
        print("  ", summary["pruebas"])
    print("Midiendo latencias…")
    summary["latencias"] = measure_latency(args.ciclos, args.real)
    summary["inicializacion"] = json.loads((EVID / "inicializacion.json").read_text(encoding="utf-8"))
    print("   ciclo completo:", summary["latencias"]["ciclo_completo"])
    if not args.sin_capturas:
        print("Capturando interfaz…")
        summary["capturas"] = screenshots()
    for extra in ("demos/demo_consistencia.py",):
        if (ROOT / extra).exists():
            subprocess.run([sys.executable, extra], cwd=ROOT, capture_output=True)
            summary["demo_consistencia"] = "evidencias/consistencia/"
    write_summary(summary)
    print(f"Listo: {EVID / 'RESULTADOS.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
