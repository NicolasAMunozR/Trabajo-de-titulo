# Este módulo es el punto de entrada de EDDIE (equivale a ReadingSession.Main del C#).
# Uso:
# python main.py                 → Abre "EDDIE Menu Settings" (interfaz completa)
# python main.py --sim           → Igual, pero con cámaras y eye tracker simulados (DeviceFactory)
# python main.py --headless 100  → Solo el orquestador, N ciclos, sin interfaz (pruebas de latencia)
# python main.py --config ruta   → Otro archivo de plugins
import argparse
import logging
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
os.chdir(PROJECT_DIR)
sys.path.insert(0, str(PROJECT_DIR))


def _configure_logging() -> None:
    (PROJECT_DIR / "logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(), logging.FileHandler(PROJECT_DIR / "logs" / "eddie.log", encoding="utf-8")],
        force=True,
    )
    # El orquestador avisa cuando un plugin supera 8,3 ms; en la interfaz se registra solo en el archivo.
    logging.getLogger("orchestrator.orchestrator_core").setLevel(logging.INFO)


def run_headless(config: str, cycles: int) -> int:
    from orchestrator.orchestrator_core import OrchestratorCore
    from app.settings_store import SettingsStore
    orch = OrchestratorCore(config, SettingsStore().plugin_overrides())
    if not orch.initialize():
        print("ERROR: No se pudo inicializar ningún plugin.")
        return 1
    print("Plugins activos:", [p.instance_name for p in orch.active_plugins])
    orch.run(max_cycles=cycles)
    orch.release()
    return 0


def run_gui(config: str) -> int:
    from PySide6.QtCore import QCoreApplication, Qt
    from PySide6.QtWidgets import QApplication

    from app.runtime import EddieRuntime
    from app.settings_store import SettingsStore
    from ui.context import AppContext
    from ui.theme import apply_theme
    from ui.menu_settings import MenuSettingsWindow

    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)   # requerido por QtWebEngine
    app = QApplication(sys.argv)
    app.setApplicationName("EDDIE")
    apply_theme(app)
    settings = SettingsStore()
    runtime = EddieRuntime(settings, config)
    runtime.start()
    ctx = AppContext(runtime=runtime, settings=settings)
    window = MenuSettingsWindow(ctx)
    window.show()

    def shutdown() -> None:
        if ctx.projection is not None:
            ctx.projection.write_activity_log()
        for name in ("SpeechProvider",):
            if runtime.plugin(name) is not None:
                runtime.invoke(name, "stop_listening")
        eye_page = ctx.pages.get("eye")
        if eye_page is not None and eye_page.overlay is not None:
            eye_page.overlay.close()
        runtime.wait_for_jobs(3000)
        runtime.stop()

    app.aboutToQuit.connect(shutdown)
    return app.exec()


def main() -> int:
    parser = argparse.ArgumentParser(description="EDDIE — Lectura aumentada no obstructiva")
    parser.add_argument("--config", default="config/plugins.json", help="Archivo de plugins")
    parser.add_argument("--sim", action="store_true", help="Usa dispositivos simulados (EDDIE_DEVICE_MODE=sim)")
    parser.add_argument("--headless", type=int, metavar="CICLOS", help="Ejecuta solo el orquestador N ciclos")
    args = parser.parse_args()
    if args.sim:
        os.environ["EDDIE_DEVICE_MODE"] = "sim"
    _configure_logging()
    if args.headless:
        return run_headless(args.config, args.headless)
    return run_gui(args.config)


if __name__ == "__main__":
    sys.exit(main())
