"""
main.py — Punto de entrada del sistema EDDIE Python
=====================================================
Uso:
  python main.py                    → Ejecuta 50 ciclos con plugins configurados
  python main.py --cycles 100       → Ejecuta N ciclos
  python main.py --config ruta.json → Usa archivo de config alternativo
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.orchestrator_core import OrchestratorCore


def main():
    parser = argparse.ArgumentParser(description='EDDIE Python - Sistema de Lectura Aumentada')
    parser.add_argument('--cycles', type=int, default=50, help='Número de ciclos a ejecutar (default: 50)')
    parser.add_argument('--config', type=str, default='config/plugins.json', help='Archivo de configuración de plugins')
    args = parser.parse_args()

    orch = OrchestratorCore(args.config)

    print(f"\n{'='*60}")
    print(f"  EDDIE Python — Sistema de Lectura Aumentada")
    print(f"  Config: {args.config}")
    print(f"  Ciclos: {args.cycles}")
    print(f"{'='*60}\n")

    if not orch.initialize():
        print("ERROR: No se pudo inicializar ningún plugin. Saliendo.")
        sys.exit(1)

    print(f"\nPlugins activos: {[p.name for p in orch.active_plugins]}\n")

    orch.run(max_cycles=args.cycles)
    orch.release()


if __name__ == '__main__':
    main()
