"""
================================================================================
PROYECTO EDDIE (Python Migration) - Prototipo RAD P-06
================================================================================
Nombre: Instalador del Núcleo y Conjunto de Plugins
Sección Tesis: 3.4.6 Sexto Prototipo (M. Figueroa, 2025)
Equivalente C# Legacy: proyecto_eddie/AugmentedReadingApp (Installer Script / Deployment)
Tecnología: Python 3.14 + ZipFile + Dependency Checker + CLI Installer

Objetivos:
1. Validar la instalación automatizada del entorno Python y dependencias (`requirements.txt`).
2. Empaquetar y descomprimir plugins distribuidos en formato `.zip`.
3. Garantizar un despliegue modular reproducible.
================================================================================
"""

import os
import sys
import zipfile
import shutil
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent
EVID_DIR = BASE_DIR / "evidencias" / "real"
EVID_DIR.mkdir(parents=True, exist_ok=True)
INSTALL_DIR = EVID_DIR / "eddie_install_test"

REQUIRED_PACKAGES = [
    "cv2",
    "numpy",
    "fitz",
    "pytesseract"
]

class PluginInstallerEngine:
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.plugins_dir = self.target_dir / "plugins"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

    def check_environment(self):
        print("\n  [1/3] VERIFICANDO ENTORNO PYTHON Y DEPENDENCIAS:")
        print(f"  * Versión de Python: {sys.version.split()[0]}")
        all_ok = True
        for pkg in REQUIRED_PACKAGES:
            try:
                __import__(pkg)
                print(f"  * Paquete '{pkg}': ✓ INSTALADO")
            except ImportError:
                print(f"  * Paquete '{pkg}': ✗ FALTANTE")
                all_ok = False
        return all_ok

    def package_sample_plugin(self, plugin_name):
        zip_path = EVID_DIR / f"{plugin_name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            manifest = {
                "name": plugin_name,
                "version": "1.0.0",
                "author": "EDDIE Team",
                "entrypoint": "plugin_main.py"
            }
            z.writestr("manifest.json", str(manifest))
            z.writestr("plugin_main.py", f"# Plugin {plugin_name}\nprint('Plugin {plugin_name} cargado')\n")
        print(f"  [+] Plugin empaquetado en: {zip_path.name}")
        return zip_path

    def install_plugin(self, zip_path):
        with zipfile.ZipFile(zip_path, "r") as z:
            plugin_target = self.plugins_dir / zip_path.stem
            plugin_target.mkdir(parents=True, exist_ok=True)
            z.extractall(plugin_target)
            print(f"  [✓ INSTALADO] Plugin '{zip_path.stem}' desplegado en {plugin_target.name}")

def main():
    print("=" * 75)
    print("  EDDIE Python – Prototipo P-06: Instalador del Núcleo y Conjunto de Plugins")
    print("  Referencia Tesis: Capítulo 3.4.6 | Proyecto C#: AugmentedReadingApp Installer")
    print("=" * 75)

    installer = PluginInstallerEngine(INSTALL_DIR)

    env_ok = installer.check_environment()
    if env_ok:
        print("  [✓ OK] El entorno Python cumple con todas las dependencias requeridas.")

    print("\n  [2/3] EMPAQUETADO DE PLUGINS:")
    zip1 = installer.package_sample_plugin("plugin_eye_tracker_v2")
    zip2 = installer.package_sample_plugin("plugin_gesture_colorpen")

    print("\n  [3/3] INSTALACIÓN DE PLUGINS EN EL SISTEMA:")
    installer.install_plugin(zip1)
    installer.install_plugin(zip2)

    print("\n  ✓ Prototipo P-06 finalizado exitosamente.\n")

if __name__ == "__main__":
    main()
