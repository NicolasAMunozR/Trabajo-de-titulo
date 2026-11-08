"""Enumeración de cámaras con su nombre (reemplaza CameraActivity.cs / DirectShow.NET).

En Windows el orden de DirectShow coincide con el índice de OpenCV usando CAP_DSHOW,
que es el backend por defecto de CameraSensorPlugin en ese sistema.
"""
import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


def _directshow_names() -> list[str]:
    try:
        from pygrabber.dshow_graph import FilterGraph  # type: ignore
    except ImportError:
        return []
    try:
        return list(FilterGraph().get_input_devices())
    except Exception as exc:                             # pragma: no cover - depende del SO
        logger.debug("pygrabber no pudo enumerar cámaras: %s", exc)
        return []


def _powershell_names() -> list[str]:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_PnPEntity | Where-Object {$_.PNPClass -eq 'Camera' -or "
             "$_.PNPClass -eq 'Image'} | Select-Object -ExpandProperty Name"],
            capture_output=True, text=True, timeout=6, check=False,
        )
    except Exception:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _probe_indices(max_index: int = 5) -> list[str]:
    import cv2
    names = []
    for index in range(max_index):
        capture = cv2.VideoCapture(index)
        if capture.isOpened():
            names.append(f"Cámara {index}")
            capture.release()
        else:
            capture.release()
            break
    return names


def list_cameras() -> list[tuple[int, str]]:
    """Retorna [(índice, nombre)] como CameraActivity.ListCameras()."""
    names: list[str] = []
    if sys.platform == "win32":
        names = _directshow_names() or _powershell_names()
    if not names:
        names = _probe_indices()
    return list(enumerate(names))
