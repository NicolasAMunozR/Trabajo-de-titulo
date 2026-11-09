# Estado compartido entre pantallas (lo que en C# se pasaba entre formularios por referencia).
from dataclasses import dataclass, field
from typing import Optional

from app.runtime import EddieRuntime
from app.settings_store import SettingsStore


@dataclass
class AppContext:
    runtime: EddieRuntime
    settings: SettingsStore
    projection: Optional[object] = None          # ProjectionScreen
    pages: dict = field(default_factory=dict)    # nombre → página de configuración
    capture_jpeg: Optional[bytes] = None         # byteImagenBuscada (captura del gesto)
    active_gesture: Optional[str] = None         # plugin gestual seleccionado
