"""
actualizar_datos.py — copia a la tesis los resultados de los avances
===================================================================
Lee las evidencias de cada avance (evidencias/resumen.json, latencias.json) y las mediciones
de los prototipos (P-00/evidencias/prototipos_datos.tex) y escribe:

  datos/avances_datos.tex     → macros con pruebas, cobertura y latencias de P-01 … P-07
  datos/prototipos_datos.tex  → copia de las macros de medir_prototipos.py

Uso (desde la carpeta de la tesis):
  python datos/actualizar_datos.py "C:/…/Proyecto final/avances"

Después de regenerar las evidencias en el laboratorio (generar_todo.py --real y
medir_prototipos.py) basta con volver a ejecutar este script y recompilar la tesis.
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NUM = {"1": "Uno", "2": "Dos", "3": "Tres", "4": "Cuatro", "5": "Cinco", "6": "Seis", "7": "Siete"}
PLUGIN_NAMES = {"TextCamera": "CamTexto", "GestureCamera": "CamGestos", "ImageProcessor": "OCR",
                "ColorPenRecognition": "ColorPen", "HandSkinRecognition": "HandSkin", "MouseRecognition": "Mouse",
                "EyeTrackerMock": "EyeMock", "SpeechProvider": "Voz", "GazeSession": "Mirada",
                "ConsistencyProvider": "Consistencia", "LLM-Gemini": "Gemini"}


def num(value, decimals=2) -> str:
    text = f"{value:.{decimals}f}".rstrip("0").rstrip(".")
    return text.replace(".", "{,}")


def main(avances: Path) -> None:
    lines = ["% Generado por datos/actualizar_datos.py a partir de las evidencias de los avances. No editar."]
    for folder in sorted(avances.glob("P-0[1-7]_*")):
        key = NUM[folder.name[3]]
        resumen = json.loads((folder / "evidencias/resumen.json").read_text(encoding="utf-8"))
        tests = resumen["pruebas"]
        lat = resumen["latencias"].get("ciclo_completo", {})
        lines += [f"\\newcommand{{\\P{key}Pruebas}}{{{tests.get('passed', 0)}}}",
                  f"\\newcommand{{\\P{key}Xfail}}{{{tests.get('xfailed', 0)}}}",
                  f"\\newcommand{{\\P{key}Cobertura}}{{{tests.get('coverage_percent', 0)}}}",
                  f"\\newcommand{{\\P{key}CicloMedia}}{{{num(lat.get('media_ms', 0))}}}",
                  f"\\newcommand{{\\P{key}CicloPnoventaycinco}}{{{num(lat.get('p95_ms', 0))}}}",
                  f"\\newcommand{{\\P{key}CicloMax}}{{{num(lat.get('max_ms', 0))}}}",
                  f"\\newcommand{{\\P{key}Fecha}}{{{resumen.get('fecha', '')[:10]}}}"]
        if folder.name.startswith("P-07"):
            detail = json.loads((folder / "evidencias/latencias.json").read_text(encoding="utf-8"))
            lines.append(f"\\newcommand{{\\PSieteCiclos}}{{{detail['ciclos']}}}")
            rows = []
            for name, d in detail["por_plugin"].items():
                rows.append(f"{name} & {num(d['media_ms'], 3)} & {num(d['p95_ms'], 3)} & {num(d['max_ms'], 3)}")
            lines.append("\\newcommand{\\PSieteTablaLatencias}{" + " \\\\\n".join(rows) + "}")
            lines.append(f"\\newcommand{{\\PSieteEntorno}}{{{resumen.get('sistema', '') + ', Python ' + resumen.get('python', '')}}}")
    (HERE / "avances_datos.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    src = avances / "P-00_prototipos_desechables/evidencias/prototipos_datos.tex"
    if src.exists():
        shutil.copy2(src, HERE / "prototipos_datos.tex")
    if (avances / "tabla_prototipos.tex").exists():
        shutil.copy2(avances / "tabla_prototipos.tex", HERE / "tabla_prototipos.tex")
    print("Datos actualizados en", HERE)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent.parent / "avances")
