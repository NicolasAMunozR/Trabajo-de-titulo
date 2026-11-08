"""
app/settings_store.py
=====================
Ajustes persistentes del usuario.

Reemplaza Properties.Settings2 / Properties.Settings (App.config userSettings) con las
mismas claves y valores por defecto, guardados en config/user_settings.json.
"""
import json
import logging
from copy import deepcopy
from pathlib import Path

logger = logging.getLogger(__name__)

# Settings2.settings + Settings.settings (mismos nombres y valores por defecto)
DEFAULTS = {
    "voiceInteraction": "",
    "buttonDisplay": "",
    "encyclopediaApi": "",
    "definitionApi": "",
    "imageApi": "",
    "translationApi": "",
    "videoApi": "",
    "languageTranslate": "",
    "cameraTextIndex": 0,
    "cameraTextWidth": 640,
    "cameraTextHeight": 480,
    "gestureComplementIndex": 0,
    "gestureValorX1": 0,
    "gestureValorX2": 0,
    "gestureValorY1": 0,
    "gestureValorY2": 0,
    "cameraGestureIndex": 1,
    "gestureRecognitionOnChecked": False,
    "cameraGestureWidth": 960,
    "cameraGestureHeight": 720,
    "encyclopediaApiIndex": 0,
    # Properties.Settings (calibración guardada con "Save calibration")
    "ValorX1": 0, "ValorX2": 0, "ValorX3": 0,
    "ValorY1": 0, "ValorY2": 0, "ValorY3": 0,
    # Nuevos (antes vivían solo en memoria)
    "pdfPath": "",
    "deviceMode": "",
}


class SettingsStore:
    def __init__(self, path: str | Path = "config/user_settings.json") -> None:
        self.path = Path(path)
        self._values = deepcopy(DEFAULTS)
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            stored = json.loads(self.path.read_text(encoding="utf-8"))
            self._values.update({k: v for k, v in stored.items() if k in DEFAULTS})
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("No se pudieron leer los ajustes (%s); se usan los valores por defecto.", exc)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._values, indent=2, ensure_ascii=False), encoding="utf-8")

    def reset(self) -> None:
        """Properties.Settings2.Default.Reset()."""
        self._values = deepcopy(DEFAULTS)
        self.save()

    def __getitem__(self, key: str):
        return self._values[key]

    def __setitem__(self, key: str, value) -> None:
        if key not in DEFAULTS:
            raise KeyError(key)
        self._values[key] = value

    def get(self, key: str, default=None):
        return self._values.get(key, default)

    def as_dict(self) -> dict:
        return dict(self._values)

    def plugin_overrides(self) -> dict:
        """Traduce los ajustes a overrides de plugins.json para el OrchestratorCore."""
        overrides = {
            "TextCamera": {"config": {"camera_index": int(self["cameraTextIndex"]),
                                      "width": int(self["cameraTextWidth"]),
                                      "height": int(self["cameraTextHeight"])}},
            "GestureCamera": {"config": {"camera_index": int(self["cameraGestureIndex"]),
                                         "width": int(self["cameraGestureWidth"]),
                                         "height": int(self["cameraGestureHeight"])}},
            "ConsistencyProvider": {"config": {"pdf_path": self["pdfPath"] if self["pdfPath"]
                                               and Path(self["pdfPath"]).exists() else ""}},
        }
        if self["deviceMode"] in ("real", "sim"):
            for name in ("TextCamera", "GestureCamera"):
                overrides[name]["device_mode"] = self["deviceMode"]
        return overrides
