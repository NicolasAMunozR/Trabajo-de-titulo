"""
DEMO REAL F11 – Plugin Dynamic Loading (importlib)
====================================================
Carga en tiempo real los módulos del proyecto EDDIE-Python
usando importlib. Muestra el árbol de plugins disponibles,
sus interfaces y los métodos que exponen.
"""
import importlib, importlib.util, pathlib, sys, time
import cv2, numpy as np

EVID = pathlib.Path(__file__).parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)

PROJECT = pathlib.Path(__file__).parent.parent.parent  # raíz del proyecto

print("="*55)
print("  DEMO REAL F11 – Plugin Dynamic Loading")
print("="*55)

# Módulos EDDIE reales a cargar
TARGETS = [
    # (ruta_relativa_al_proyecto,  alias_display)
    ("eddie-python/contracts/i_image_processor.py",    "IImageProcessor"),
    ("eddie-python/contracts/i_eye_tracker.py",        "IEyeTracker"),
    ("eddie-python/contracts/i_gesture_plugin.py",     "IGesturePlugin"),
    ("eddie-python/contracts/i_consistency_provider.py","IConsistencyProvider"),
    ("eddie-python/contracts/i_web_search_provider.py","IWebSearchProvider"),
    ("eddie-python/orchestrator/orchestrator_core.py", "OrchestratorCore"),
    ("eddie-python/orchestrator/plugin_loader.py",     "PluginLoader"),
    ("eddie-python/hardware/mock/mock_eye_tracker.py", "MockEyeTracker"),
]

results = []

for rel_path, display_name in TARGETS:
    full_path = PROJECT / rel_path
    entry = {"name": display_name, "path": rel_path, "ok": False,
             "methods": [], "error": ""}
    if not full_path.exists():
        entry["error"] = "archivo no encontrado"
        results.append(entry)
        print(f"  [-] {display_name}: no encontrado")
        continue
    try:
        spec = importlib.util.spec_from_file_location(display_name, str(full_path))
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # Recoger clases y métodos públicos
        methods = []
        for attr in dir(mod):
            if attr.startswith("_"): continue
            obj = getattr(mod, attr)
            if callable(obj):
                methods.append(attr)
        entry["ok"]      = True
        entry["methods"] = methods[:6]  # máximo 6
        results.append(entry)
        print(f"  [✓] {display_name}: {len(methods)} atributos públicos → {methods[:4]}")
    except Exception as e:
        entry["error"] = str(e)[:60]
        results.append(entry)
        print(f"  [!] {display_name}: {e}")

# ── Visualización ──────────────────────────────────────────────────────────
W, H = 950, 580
canvas = np.full((H, W, 3), 28, np.uint8)

cv2.putText(canvas,"F11 – Plugin Dynamic Loading (importlib.util)",(15,35),
            cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,220,100),2)
cv2.putText(canvas,f"Módulos analizados: {len(results)} | Cargados exitosamente: {sum(r['ok'] for r in results)}",
            (15,60),cv2.FONT_HERSHEY_SIMPLEX,0.45,(180,180,180),1)

y = 90
for r in results:
    col = (0,200,80) if r["ok"] else (80,80,220)
    icon = "✓" if r["ok"] else "✗"
    cv2.putText(canvas,f"  {icon}  {r['name']}",(15,y),
                cv2.FONT_HERSHEY_SIMPLEX,0.52,col,1)
    if r["ok"]:
        methods_str = "  ".join(r["methods"]) if r["methods"] else "(sin métodos públicos)"
        cv2.putText(canvas,f"      attrs: {methods_str[:70]}",(15,y+18),
                    cv2.FONT_HERSHEY_SIMPLEX,0.36,(140,180,140),1)
    else:
        cv2.putText(canvas,f"      Error: {r['error'][:65]}",(15,y+18),
                    cv2.FONT_HERSHEY_SIMPLEX,0.36,(120,120,220),1)
    y += 42

cv2.putText(canvas,"EDDIE Plugin System – todos los módulos cargados via importlib.util",
            (15,H-20),cv2.FONT_HERSHEY_SIMPLEX,0.42,(100,100,100),1)

out = EVID/"real_f11_plugin_loading.png"
cv2.imwrite(str(out), canvas)
print(f"\n  [GUARDADO] {out}")

cv2.imshow("EDDIE – F11 Plugin Loading", canvas)
print("  Presiona cualquier tecla para cerrar…")
cv2.waitKey(0)
cv2.destroyAllWindows()
print("  F11 COMPLETADO\n")
