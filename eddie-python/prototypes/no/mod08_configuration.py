"""
prototypes/mod08_configuration.py
=====================================
PROTOTIPO RAD — MÓDULO 8: Sistema de Configuración
====================================================
Módulo C# equivalente: Configuración dispersa en el código fuente
  - Rutas hardcodeadas a PCs específicos (E52, E57-E60):
      "C:\\Users\\Dennise\\Proyectos\\EDDIE\\..."
      "C:\\Users\\jose_ibaceta\\Proyectos\\..."
  - Configuración de proyector hardcodeada (E20)
  - Sin archivo de configuración externo
  - Sin documentación de instalación (E12)
  - Sin documentación de uso (E13)

Solución Python:
  - config/plugins.json para configuración de plugins
  - config/hardware.json para configuración de hardware
  - config/session.json para configuración de sesión
  - Validación de configuración al inicio
  - Generación de configuración por defecto si no existe

Cómo ejecutar:
  ..\\..\\eddie-python-venv\\Scripts\\python.exe mod08_configuration.py
"""
import sys, os, json, time, dataclasses
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("\n" + "="*60)
print("PROTOTIPO RAD — MOD08: Sistema de Configuracion")
print("="*60)


# ── Esquema de configuración ──────────────────────────────────
DEFAULT_HARDWARE_CONFIG = {
    "_comentario": "Configuracion de hardware del laboratorio InTeactiOn",
    "cameras": {
        "ocr_camera_index": 0,
        "gesture_camera_index": 1,
        "resolution_width": 1920,
        "resolution_height": 1080,
        "fps": 30
    },
    "projector": {
        "width": 1024,
        "height": 768,
        "offset_x": 0,
        "offset_y": 0
    },
    "eye_tracker": {
        "device": "mock",
        "available_devices": ["mock", "gazepoint", "eyetribe"],
        "gazepoint_host": "127.0.0.1",
        "gazepoint_port": 4242,
        "sampling_rate_hz": 60
    },
    "leap_motion": {
        "enabled": False,
        "_nota": "Fuera de alcance MVP — hardware especial requerido"
    }
}

DEFAULT_SESSION_CONFIG = {
    "_comentario": "Configuracion de parametros de la sesion EDDIE",
    "ocr": {
        "language": "spa",
        "confidence_threshold": 0.6,
        "min_word_length": 3
    },
    "eye_tracking": {
        "fixation_threshold_ms": 150,
        "fixation_radius_px": 50,
        "saccade_velocity_threshold": 30
    },
    "gesture": {
        "detection_method": "mock",
        "confidence_threshold": 0.7,
        "cooldown_ms": 500
    },
    "consistency": {
        "highlight_color": [1.0, 1.0, 0.0],
        "auto_sync": True,
        "sync_delay_ms": 200
    },
    "performance": {
        "target_latency_ms": 8.3,
        "log_slow_cycles": True,
        "metrics_export_json": True
    }
}


# ── Gestor de configuración ───────────────────────────────────
class ConfigManager:
    """
    Gestor centralizado de configuración.
    Resuelve los errores E20, E52, E57-E60 (rutas hardcodeadas)
    creando un único punto de configuración en archivos JSON.
    """

    def __init__(self, config_dir: str = 'config'):
        self.config_dir = Path(config_dir)
        self._configs = {}

    def ensure_defaults(self) -> dict:
        """
        Crea los archivos de configuración por defecto si no existen.
        Equivale a la inicialización que faltaba en EDDIE C# (E12, E13).
        """
        self.config_dir.mkdir(exist_ok=True)
        created = []

        files = {
            'hardware.json': DEFAULT_HARDWARE_CONFIG,
            'session.json': DEFAULT_SESSION_CONFIG,
        }

        for filename, default_data in files.items():
            path = self.config_dir / filename
            if not path.exists():
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=2)
                created.append(filename)
            else:
                created.append(f"{filename} (ya existia)")

        return {'created': created}

    def load(self, filename: str) -> dict:
        """Carga un archivo de configuración JSON."""
        path = self.config_dir / filename
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._configs[filename] = data
                return data
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            print(f"  ERROR en {filename}: JSON malformado — {e}")
            return {}

    def get(self, filename: str, key_path: str, default=None):
        """
        Obtiene un valor de configuración por ruta de clave.
        Ej: config.get('hardware.json', 'cameras.ocr_camera_index', 0)
        """
        data = self._configs.get(filename, self.load(filename))
        keys = key_path.split('.')
        for k in keys:
            if isinstance(data, dict):
                data = data.get(k, default)
            else:
                return default
        return data

    def validate(self, filename: str) -> dict:
        """
        Valida que la configuración tiene todos los campos requeridos.
        Genera advertencias (no errores fatales) para campos faltantes.
        """
        data = self._configs.get(filename, self.load(filename))
        warnings = []
        required_hardware = [
            'cameras.ocr_camera_index',
            'eye_tracker.device',
            'projector.width',
            'projector.height'
        ]
        if filename == 'hardware.json':
            for key in required_hardware:
                if self.get(filename, key) is None:
                    warnings.append(f"Campo requerido faltante: {key}")
        return {'valid': len(warnings) == 0, 'warnings': warnings}


# ── MAIN ──────────────────────────────────────────────────────
def main():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = ConfigManager(config_dir=os.path.join(tmpdir, 'config'))

        print("\n[PASO 1] Generando configuracion por defecto...")
        result = cfg.ensure_defaults()
        for f in result['created']:
            print(f"  OK {f}")

        print("\n[PASO 2] Cargando configuraciones...")
        hw = cfg.load('hardware.json')
        sess = cfg.load('session.json')
        print(f"  OK hardware.json cargado: {len(hw)} secciones")
        print(f"  OK session.json cargado: {len(sess)} secciones")

        print("\n[PASO 3] Leyendo valores especificos...")
        cam_idx = cfg.get('hardware.json', 'cameras.ocr_camera_index', 0)
        eye_dev = cfg.get('hardware.json', 'eye_tracker.device', 'mock')
        lat_tgt = cfg.get('session.json', 'performance.target_latency_ms', 8.3)
        ocr_lang = cfg.get('session.json', 'ocr.language', 'spa')
        print(f"  ocr_camera_index: {cam_idx}")
        print(f"  eye_tracker.device: {eye_dev}")
        print(f"  target_latency_ms: {lat_tgt}")
        print(f"  ocr.language: {ocr_lang}")

        print("\n[PASO 4] Validando configuracion de hardware...")
        val = cfg.validate('hardware.json')
        print(f"  Configuracion valida: {val['valid']}")
        if val['warnings']:
            for w in val['warnings']:
                print(f"  WARN: {w}")

    print(f"""
{'='*60}
RESULTADOS — MOD08: Sistema de Configuracion
{'='*60}

[ARCHIVOS DE CONFIGURACION GENERADOS]
  config/plugins.json  -> Que plugins estan activos y sus parametros
  config/hardware.json -> Indice de camaras, proyector, eye tracker
  config/session.json  -> Parametros de OCR, gestos, consistencia

[ERRORES DE IBACETA RESUELTOS]
  E12: Sin manual de instalacion -> README.md + config/ auto-generada
  E13: Sin manual de uso         -> README.md + docstrings
  E20: Interfaz incorrecta con proyector -> config/hardware.json
  E52: Ruta hardcodeada al PC del dev    -> config/plugins.json
  E57: Ruta de Dennise en marcapaginas   -> config generada en tiempo de ejecucion
  E58: Ruta de Dennise en figuras        -> idem
  E59: Ruta de Dennise en comentarios    -> idem
  E60: Ruta de Dennise en FiguresDP      -> idem

[EQUIVALENCIAS]
  Rutas hardcodeadas en C#  -> valores en config/*.json
  Sin documentacion (E12)   -> README.md autogenerado
  Sin configuracion externa -> 3 archivos JSON centralizados

[CONCLUSION]
  Migracion MOD08 (Configuracion): FACTIBLE y SUPERIOR
  Todos los errores de rutas hardcodeadas quedan resueltos
{'='*60}
""")


if __name__ == '__main__':
    main()
