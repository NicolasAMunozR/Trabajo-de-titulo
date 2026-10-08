"""
================================================================================
PROYECTO EDDIE (Python Migration) - Prototipo RAD P-05
================================================================================
Nombre: Preferencias de Usuario y Ajustes de la Aplicación
Sección Tesis: 3.4.5 Quinto Prototipo (M. Figueroa, 2025)
Equivalente C# Legacy: proyecto_eddie/AugmentedReadingApp/MenuSettings.cs
Tecnología: Python 3.14 + JSON Preferences Manager + i18n Dictionary

Objetivos:
1. Administrar la persistencia de preferencias de usuario (`preferences.json`).
2. Soportar cambio dinámico de idioma (Español / Inglés).
3. Recordar la última sesión de trabajo y estado de ventana.
================================================================================
"""

import os
import sys
import json
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent
EVID_DIR = BASE_DIR / "evidencias" / "real"
EVID_DIR.mkdir(parents=True, exist_ok=True)
PREF_FILE = EVID_DIR / "preferences.json"

I18N = {
    "es": {
        "title": "Configuración y Preferencias de EDDIE",
        "lang": "Idioma seleccionado",
        "theme": "Modo de interfaz",
        "hotkey_start": "Atajo Iniciar Captura",
        "hotkey_stop": "Atajo Detener Captura",
        "minimize_on_start": "Minimizar aplicación al iniciar captura",
        "last_project": "Último Proyecto Seleccionado"
    },
    "en": {
        "title": "EDDIE Settings & User Preferences",
        "lang": "Selected Language",
        "theme": "UI Theme Mode",
        "hotkey_start": "Start Capture Hotkey",
        "hotkey_stop": "Stop Capture Hotkey",
        "minimize_on_start": "Minimize app when capture starts",
        "last_project": "Last Selected Project"
    }
}

class PreferencesManager:
    def __init__(self, filepath):
        self.filepath = filepath
        self.prefs = self._load()

    def _load(self):
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "language": "es",
            "theme": "dark",
            "minimize_on_capture": True,
            "hotkey_start": "CTRL+SHIFT+R",
            "hotkey_stop": "CTRL+SHIFT+S",
            "last_project_id": "PROJ-001",
            "window_geometry": {"width": 1280, "height": 720, "x": 100, "y": 100}
        }

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.prefs, f, indent=2, ensure_ascii=False)
        print(f"  [✓ GUARDADO] Preferencias persistidas en: {self.filepath.name}")

    def set_language(self, lang_code):
        if lang_code in I18N:
            self.prefs["language"] = lang_code
            self.save()

def main():
    print("=" * 75)
    print("  EDDIE Python – Prototipo P-05: Preferencias de Usuario y Ajustes")
    print("  Referencia Tesis: Capítulo 3.4.5 | Proyecto C#: MenuSettings")
    print("=" * 75)

    pm = PreferencesManager(PREF_FILE)

    current_lang = pm.prefs.get("language", "es")
    strings = I18N[current_lang]

    print(f"\n  [{strings['title'].upper()}]:")
    print(f"  * {strings['lang']}: {current_lang.upper()}")
    print(f"  * {strings['theme']}: {pm.prefs['theme']}")
    print(f"  * {strings['hotkey_start']}: {pm.prefs['hotkey_start']}")
    print(f"  * {strings['hotkey_stop']}: {pm.prefs['hotkey_stop']}")
    print(f"  * {strings['minimize_on_start']}: {pm.prefs['minimize_on_capture']}")
    print(f"  * {strings['last_project']}: {pm.prefs['last_project_id']}")

    print("\n  [PROBANDO CAMBIO DINÁMICO DE IDIOMA]:")
    new_lang = "en" if current_lang == "es" else "es"
    pm.set_language(new_lang)
    strings_new = I18N[new_lang]
    print(f"  [+] Idioma cambiado a '{new_lang.upper()}': {strings_new['title']}")

    print("\n  ✓ Prototipo P-05 finalizado exitosamente.\n")

if __name__ == "__main__":
    main()
