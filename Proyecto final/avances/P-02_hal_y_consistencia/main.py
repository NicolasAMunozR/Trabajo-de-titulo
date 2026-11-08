"""
main.py — Avance P-02 (capa de abstracción de hardware + módulo de consistencia)
================================================================================
Sigue sin interfaz gráfica. El núcleo ya usa DeviceFactory: la cámara puede ser la
real (OpenCV) o la simulada sin cambiar código, y el plugin de consistencia (PDF)
se carga con el mismo mecanismo que el resto.

Uso:
  python main.py --sim                 → cámara simulada, 300 ciclos
  python main.py                       → cámara real (índice de config/plugins.json)
  python main.py --sim --cycles 1000
  python demos/demo_consistencia.py    → demostración papel ↔ PDF con frames sintéticos
"""
import argparse
import json
import logging
import os
import statistics
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
os.chdir(PROJECT_DIR)
sys.path.insert(0, str(PROJECT_DIR))


def main() -> int:
    parser = argparse.ArgumentParser(description="EDDIE P-02 — núcleo + HAL + consistencia (sin interfaz)")
    parser.add_argument("--config", default="config/plugins.json")
    parser.add_argument("--sim", action="store_true", help="Usa dispositivos simulados (EDDIE_DEVICE_MODE=sim)")
    parser.add_argument("--cycles", "--headless", type=int, default=300, dest="cycles")
    args = parser.parse_args()
    if args.sim:
        os.environ["EDDIE_DEVICE_MODE"] = "sim"
    (PROJECT_DIR / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                        datefmt="%H:%M:%S", force=True,
                        handlers=[logging.StreamHandler(),
                                  logging.FileHandler(PROJECT_DIR / "logs" / "eddie.log", encoding="utf-8")])

    from app.settings_store import SettingsStore
    from orchestrator.orchestrator_core import OrchestratorCore
    orch = OrchestratorCore(args.config, SettingsStore().plugin_overrides())
    if not orch.initialize():
        print("ERROR: No se pudo inicializar ningún plugin.")
        return 1
    print("\nReporte de inicialización:")
    print(json.dumps(orch.initialization_report, indent=2, ensure_ascii=False))
    print("Plugins activos:", [f"{p.instance_name} ({type(p).__name__})" for p in orch.active_plugins])
    orch.run(max_cycles=args.cycles)
    history = orch._latency_history
    print(f"\nCiclos: {orch.cycle_count} | latencia media {statistics.mean(history):.3f} ms | "
          f"máx {max(history):.3f} ms | objetivo ≤ 8,3 ms")
    orch.release()
    return 0


if __name__ == "__main__":
    sys.exit(main())
