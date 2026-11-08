"""
main.py — Avance P-01 (núcleo orquestador y contratos)
======================================================
Todavía no hay interfaz: el núcleo se ejecuta sin ventana y muestra en consola
qué plugins se cargaron, cuáles fallaron (sin detener el sistema) y la latencia
de cada ciclo.

Uso:
  python main.py                 → 300 ciclos con la configuración de config/plugins.json
  python main.py --cycles 1000   → otra cantidad de ciclos
  python main.py --config ruta   → otro archivo de plugins
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
    parser = argparse.ArgumentParser(description="EDDIE P-01 — núcleo orquestador sin interfaz")
    parser.add_argument("--config", default="config/plugins.json")
    parser.add_argument("--cycles", type=int, default=300)
    args = parser.parse_args()
    (PROJECT_DIR / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                        datefmt="%H:%M:%S", force=True,
                        handlers=[logging.StreamHandler(),
                                  logging.FileHandler(PROJECT_DIR / "logs" / "eddie.log", encoding="utf-8")])

    from orchestrator.orchestrator_core import OrchestratorCore
    orch = OrchestratorCore(args.config)
    if not orch.initialize():
        print("ERROR: No se pudo inicializar ningún plugin.")
        return 1
    print("\nReporte de inicialización:")
    print(json.dumps(orch.initialization_report, indent=2, ensure_ascii=False))
    orch.run(max_cycles=args.cycles)
    history = orch._latency_history
    print(f"\nCiclos: {orch.cycle_count} | latencia media {statistics.mean(history):.3f} ms | "
          f"máx {max(history):.3f} ms | objetivo ≤ 8,3 ms")
    orch.release()
    return 0


if __name__ == "__main__":
    sys.exit(main())
