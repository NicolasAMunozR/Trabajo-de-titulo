"""
run_demos_reales.py
===================
Lanzador interactivo para TODAS las demos REALES de EDDIE-Python.
Ejecuta cada demo en secuencia y espera confirmación entre ellos.

Uso:
    python run_demos_reales.py              # todos los demos
    python run_demos_reales.py f01          # solo F01
    python run_demos_reales.py f01 f02 f03  # selección
    python run_demos_reales.py --list       # listar demos disponibles
"""
import subprocess, sys, pathlib, time

BASE = pathlib.Path(__file__).parent

# ─── Catálogo completo de demos ───────────────────────────────────────────────
DEMOS = [
    # (id,   archivo,                       descripción,                          requiere_camara)
    ("f01",  "demo_real_f01.py",            "📷  Cámara DroidCam EN VIVO (8s feed real)",           True),
    ("f02",  "demo_real_f02.py",            "📷  Binarización Otsu EN VIVO (apunta a texto)",         True),
    ("f03",  "demo_real_f03.py",            "📷  OCR Tesseract EN VIVO (apunta a texto impreso)",     True),
    ("f04",  "demo_real_f04.py",            "📷  Detección de página/libro EN VIVO",                  True),
    ("f05",  "demo_real_f05.py",            "📷  Color Pen Tracking EN VIVO (objeto rojo/verde/azul)",True),
    ("f06",  "demo_real_f06.py",            "📷  Segmentación de piel/mano EN VIVO",                  True),
    ("f07",  "demo_real_f07.py",            "📷  Homografía: clic en 4 esquinas → vista rectificada", True),
    ("f09",  "demo_real_f09.py",            "🖱️   Mouse como gaze proxy + retículo interactivo",      False),
    ("f10",  "demo_real_f10.py",            "🔌  Socket TCP real: servidor+cliente gaze (15s)",       False),
    ("f11",  "demo_real_f11.py",            "🔌  Plugin loading real: carga módulos EDDIE con importlib",False),
    ("f12",  "demo_real_f12.py",            "🖱️   Dwell Time: detente 0.6s sobre una línea → activa", False),
    ("f13",  "demo_real_f13.py",            "🖱️   Retículo de gaze overlay sobre texto proyectado",   False),
    ("f14",  "demo_real_f14_f16_f17.py",    "📄  PDFs reales: Highlight + Post-it + Figuras",        False),
    ("f15",  "demo_real_f15.py",            "📄  PDF Highlight Sync: palabras clave coloreadas",      False),
    ("f19",  "demo_real_f19.py",            "🌐  Wikipedia API REAL (requiere internet)",             False),
    ("f20",  "demo_real_f20.py",            "🤖  Ollama LLM REAL (localhost:11434, requiere ollama)", False),
    ("f21",  "demo_real_f21.py",            "🌐  Traducción ES→EN REAL vía MyMemory API",            False),
    ("f22",  "demo_real_f22.py",            "📷  Cloud Vision pipeline: frame→JPEG→B64→JSON",         True),
    ("f23",  "demo_real_f23.py",            "🌐  YouTube sugerencias REAL (API pública)",             False),
    ("f24",  "demo_real_f24.py",            "🎤  Grabación de micrófono REAL (5s) + forma de onda",  False),
    ("f25",  "demo_real_f25.py",            "🔊  TTS: EDDIE habla POR LOS ALTAVOCES (escucha!)",     False),
    ("f27",  "demo_real_f27.py",            "📷  Highlight digital sobre frame de cámara EN VIVO",    True),
    ("f28",  "demo_real_f28.py",            "⚙️   Async logging REAL: 4 hilos + JSONL (20s)",         False),
]

GROUPS = {
    "camara":   ["f01","f02","f03","f04","f05","f06","f07","f22","f27"],
    "raton":    ["f09","f12","f13"],
    "pdf":      ["f14","f15"],
    "api":      ["f19","f20","f21","f23"],
    "audio":    ["f24","f25"],
    "sistema":  ["f10","f11","f28"],
}

def print_list():
    print("\n  Demos disponibles:")
    print("  " + "─"*70)
    for id_, script, desc, cam in DEMOS:
        cam_tag = " [📷 cámara]" if cam else ""
        print(f"   [{id_.upper():4}] {desc}{cam_tag}")
    print("\n  Grupos disponibles (--grupo <nombre>):")
    for g, ids in GROUPS.items():
        print(f"    {g:10} → {', '.join(ids)}")
    print()

def run_demo(script: str, label: str) -> int:
    path = BASE / script
    if not path.exists():
        print(f"  [!] Archivo no encontrado: {script}")
        return -1
    print(f"\n  ▶ Ejecutando: {script}")
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(path)],
        cwd=str(BASE)
    )
    return result.returncode

def main():
    args = [a.lower() for a in sys.argv[1:]]

    # --list
    if "--list" in args or "-l" in args:
        print_list()
        return

    # --grupo <nombre>
    group_ids = set()
    if "--grupo" in args:
        gi = args.index("--grupo")
        if gi+1 < len(args):
            gname = args[gi+1]
            group_ids = set(GROUPS.get(gname, []))
            args = [a for a in args if a not in ("--grupo", gname)]
            if not group_ids:
                print(f"  [!] Grupo '{gname}' no existe. Grupos: {list(GROUPS.keys())}")
                return

    # Filtrar demos
    filter_ids = group_ids | set(a for a in args if not a.startswith("--"))
    if filter_ids:
        to_run = [d for d in DEMOS if d[0] in filter_ids]
    else:
        to_run = DEMOS  # todos

    if not to_run:
        print(f"  [!] No se encontraron demos para: {filter_ids}")
        print("  Usa --list para ver las opciones.")
        return

    # ── Presentación ──────────────────────────────────────────────────────
    print("=" * 70)
    print("  EDDIE Python – Demos REALES por Prototipo RAD")
    print("=" * 70)
    print(f"\n  Se ejecutarán {len(to_run)} demos en secuencia:\n")
    for i, (id_, script, desc, cam) in enumerate(to_run, 1):
        cam_tag = " [requiere cámara]" if cam else ""
        print(f"   {i:2}. {desc}{cam_tag}")

    print("\n  ─" * 35)
    print("  CONTROLES GENERALES:")
    print("  • Q / ESC  → cerrar la ventana actual")
    print("  • S        → guardar screenshot como evidencia")
    print("  • Click    → interactuar (F07: marcar esquinas, F09: registrar click, etc.)")
    print("  ─" * 35)
    print()
    input("  ✅ Presiona ENTER para comenzar… ")

    passed = failed = skipped = 0
    t_total = time.time()

    for idx, (id_, script, desc, cam) in enumerate(to_run):
        print(f"\n{'='*70}")
        print(f"  Demo {idx+1}/{len(to_run)} [{id_.upper()}]")
        print(f"  {desc}")
        print(f"{'='*70}")

        try:
            cont = input(f"\n  Presiona ENTER para iniciar (o 's' para saltar): ")
        except KeyboardInterrupt:
            print("\n  Interrumpido.")
            break

        if cont.lower() == 's':
            skipped += 1
            print(f"  ⏭ [{id_.upper()}] Saltado.")
            continue

        rc = run_demo(script, id_)

        if rc == 0:
            passed += 1
            print(f"\n  ✅ [{id_.upper()}] Completado")
        else:
            failed += 1
            print(f"\n  ❌ [{id_.upper()}] Terminó con código {rc}")

    # ── Resumen final ──────────────────────────────────────────────────────
    total_t = time.time()-t_total
    print(f"\n{'='*70}")
    print(f"  RESUMEN FINAL")
    print(f"{'='*70}")
    print(f"  ✅ Exitosos: {passed}")
    print(f"  ❌ Fallidos: {failed}")
    print(f"  ⏭ Saltados: {skipped}")
    print(f"  ⏱  Tiempo total: {total_t/60:.1f} minutos")

    evid = BASE / "evidencias" / "real"
    if evid.exists():
        pngs = list(evid.glob("real_*.png"))
        wavs = list(evid.glob("*.wav"))
        pdfs = list(evid.glob("*.pdf"))
        jsonl= list(evid.glob("*.jsonl"))
        print(f"\n  Evidencias en {evid}:")
        print(f"    PNG:   {len(pngs)} imágenes")
        print(f"    WAV:   {len(wavs)} audios")
        print(f"    PDF:   {len(pdfs)} documentos")
        print(f"    JSONL: {len(jsonl)} logs")
    print("="*70)


if __name__ == "__main__":
    main()
