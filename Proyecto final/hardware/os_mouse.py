"""Control del cursor del sistema (SetCursorPos / mouse_event de user32.dll en C#).

Lo usan el reconocimiento gestual ("Recognition on") y el eye tracking ("Mouse Control").
En Windows se usa la misma API nativa que el original; en otros sistemas se intenta
pynput y, si no existe, se deja constancia en el log sin detener el sistema.
"""
import logging
import sys

logger = logging.getLogger(__name__)

_MOUSEEVENTF_LEFTDOWN = 0x0002
_MOUSEEVENTF_LEFTUP = 0x0004


class OSMouse:
    def __init__(self) -> None:
        self._user32 = None
        self._pynput = None
        if sys.platform == "win32":
            import ctypes
            self._user32 = ctypes.windll.user32
        else:
            try:
                from pynput.mouse import Button, Controller  # type: ignore
                self._pynput = (Controller(), Button)
            except Exception:
                logger.info("Control de cursor no disponible en este sistema (instale pynput).")

    @property
    def available(self) -> bool:
        return self._user32 is not None or self._pynput is not None

    def move(self, x: int, y: int) -> None:
        if self._user32 is not None:
            self._user32.SetCursorPos(int(x), int(y))
        elif self._pynput is not None:
            self._pynput[0].position = (int(x), int(y))

    def left_down(self) -> None:
        if self._user32 is not None:
            self._user32.mouse_event(_MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        elif self._pynput is not None:
            self._pynput[0].press(self._pynput[1].left)

    def left_up(self) -> None:
        if self._user32 is not None:
            self._user32.mouse_event(_MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        elif self._pynput is not None:
            self._pynput[0].release(self._pynput[1].left)

    def click(self) -> None:
        self.left_down()
        self.left_up()

    def position(self) -> tuple[int, int]:
        if self._user32 is not None:
            import ctypes

            class _Point(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            point = _Point()
            self._user32.GetCursorPos(ctypes.byref(point))
            return point.x, point.y
        if self._pynput is not None:
            x, y = self._pynput[0].position
            return int(x), int(y)
        return 0, 0


_instance: OSMouse | None = None


def os_mouse() -> OSMouse:
    global _instance
    if _instance is None:
        _instance = OSMouse()
    return _instance
