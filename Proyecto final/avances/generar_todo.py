"""
avances/generar_todo.py — regenera las evidencias de todos los avances (P-01 a P-07)
===================================================================================
Ejecuta tools/generar_evidencias.py dentro de cada carpeta de avance con el mismo
intérprete (el .venv de «Proyecto final»). Los argumentos se pasan tal cual:

  python avances\\generar_todo.py                 → dispositivos simulados
  python avances\\generar_todo.py --sin-capturas
  python avances\\generar_todo.py --real          → en el laboratorio, con el hardware conectado
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    status = 0
    for folder in sorted(p for p in HERE.iterdir() if p.is_dir() and (p / "tools" / "generar_evidencias.py").exists()):
        print(f"\n=== {folder.name}")
        code = subprocess.call([sys.executable, "tools/generar_evidencias.py", *sys.argv[1:]], cwd=folder)
        status = status or code
    print("\nResultados en <avance>/evidencias/RESULTADOS.md")
    return status


if __name__ == "__main__":
    sys.exit(main())
