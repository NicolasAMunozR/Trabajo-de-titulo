"""
ui/projection_widgets.py
========================
Controles de la pantalla proyectada portados desde ModuloVisualizacionDatos y la UI C#:
  - HighlightTool  (HighlightTool.cs): área blanca donde se resalta o captura con el puntero.
  - FiguresOverlay (FiguresDP.cs): dibuja sobre el papel las figuras del PDF.
  - LineCanvas     (Line_Paint_*): líneas que conectan un resultado con su botón.
  - RecentSearchItem (busquedasRecientes2.cs): tarjeta del historial de búsquedas.
  - ReticleOverlay (ReticleDrawing.cs): retícula de la mirada sobre toda la pantalla.
"""
from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QWidget

from ui.modern_forms import build_modern


@dataclass
class NormRect:
    """Struct NormRect de HighlightTool.cs (izquierda, y/alto, ancho/alto, alto/alto)."""
    left: float = 0.0
    bottom: float = 0.0
    right: float = 0.0
    top: float = 0.0


class HighlightTool(QWidget):
    def __init__(self, highlight_height: int, width: int, height: int, parent=None) -> None:
        super().__init__(parent)
        self.resize(width, height)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(255, 255, 255))
        self.setPalette(pal)
        self.highlight_height = highlight_height
        self.highlight_on = False
        self.rect_drawn: Optional[QRect] = None
        self.rectangles: list[QRect] = []
        self.norm_rect = NormRect()
        self.page_size = (612.0, 792.0)              # pageSize.Right / pageSize.Top
        self._start = QPoint()
        self._end = QPoint()
        self._mouse_down = False
        self.on_first_click: Optional[Callable[[], None]] = None
        self.on_num_clicks: Optional[Callable[[], None]] = None

    def runtime_final_location(self, x: int, y: int) -> None:
        """RuntimeFinalLocation: la esquina inferior derecha pasa a (x, y)."""
        self.resize(max(1, x - self.x()), max(1, y - self.y()))
        self.update()

    def get_rectangle(self) -> QRect:
        """GetRectangle(HighlightHeight): banda del alto de una línea de texto."""
        rect = QRect(min(self._start.x(), self._end.x()), self._start.y(),
                     abs(self._start.x() - self._end.x()), abs(self.highlight_height))
        self.rect_drawn = rect
        w, h = max(1, self.width()), max(1, self.height())
        self.norm_rect = NormRect(rect.x() / w, rect.y() / h, rect.width() / w, rect.height() / h)
        return rect

    def normalized_selection(self) -> Optional[tuple[float, float, float, float]]:
        """Rectángulo resaltado en coordenadas de página normalizadas (x0, y0, x1, y1)."""
        n = self.norm_rect
        if n.right <= 0:
            return None
        return n.left, n.bottom, min(1.0, n.left + n.right), min(1.0, n.bottom + n.top)

    def set_page_rectangles(self, rects: list[tuple[float, float, float, float]]) -> None:
        """GetRectangles: resaltados del PDF (normalizados) proyectados sobre el área."""
        w, h = self.width(), self.height()
        self.rectangles = [QRect(int(x0 * w), int(y0 * h), int((x1 - x0) * w), int((y1 - y0) * h))
                           for x0, y0, x1, y1 in rects]
        self.update()

    def mousePressEvent(self, event) -> None:
        self._mouse_down = True
        self._start = event.position().toPoint()
        self._end = self._start
        if self.on_first_click:
            self.on_first_click()

    def mouseMoveEvent(self, event) -> None:
        if self._mouse_down:
            self._end = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if not self._mouse_down:
            return
        self._end = event.position().toPoint()
        self._mouse_down = False
        self.get_rectangle()
        self.update()
        if self.on_num_clicks:
            self.on_num_clicks()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        if not self.highlight_on:
            return
        yellow = QColor(255, 255, 0)
        if self._mouse_down or self.rect_drawn is not None:
            painter.fillRect(self.get_rectangle(), yellow)
        for rect in self.rectangles:
            painter.fillRect(rect, yellow)


class FiguresOverlay(QWidget):
    """FiguresDP: rectángulos y elipses del PDF proyectados en negro sobre fondo blanco."""

    def __init__(self, figures: dict, parent=None) -> None:
        super().__init__(parent)
        self.figures = figures
        self.resize(400, 450)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(255, 255, 255))
        self.setPalette(pal)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        for item in self.figures.get("rectangulos", []):
            painter.drawRect(QRectF(item["x"], item["y"], item["width"], item["height"]))
        for item in self.figures.get("circulos", []):
            painter.drawEllipse(QRectF(item["x"], item["y"], item["width"], item["height"]))


class LineCanvas(QWidget):
    """Panel con fondo de la interfaz donde se trazan las líneas guía de un resultado."""

    def __init__(self, panel: QWidget) -> None:
        super().__init__(panel)
        self.setGeometry(panel.rect())
        self.segments: list[tuple[int, int, int, int]] = []
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.show()

    def draw(self, *segments: tuple[int, int, int, int]) -> None:
        self.segments.extend(segments)
        self.update()

    def clear(self) -> None:
        self.segments.clear()
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        for x0, y0, x1, y1 in self.segments:
            painter.drawLine(x0, y0, x1, y1)


class RecentSearchItem(QFrame):
    """busquedasRecientes2: fecha y hora, término buscado y servicio utilizado."""

    def __init__(self, date_time: str, term: str, service: str) -> None:
        super().__init__()
        self.setObjectName("busquedasRecientes2")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        form = build_modern("busquedasRecientes2", self)
        self.setStyleSheet("QFrame#busquedasRecientes2{border:none;border-radius:8px;background:#FFFFFF;}")
        form.lbl_fecha_hora.setText(date_time.split("-")[-1][:5] if "-" in date_time else date_time)
        form.lbl_fecha_hora.setToolTip(date_time)
        form.lbl_palabraBuscada.setText(term)
        form.lbl_Api.setText(service)
        self.form = form


class ReticleOverlay(QWidget):
    """Ventana transparente, siempre encima y sin capturar el mouse, que dibuja la retícula."""

    def __init__(self, reticle_path: str) -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.reticle = QPixmap(reticle_path)
        geometry = QRect()
        for screen in QGuiApplication.screens():
            geometry = geometry.united(screen.geometry())
        self.setGeometry(geometry)
        self._point: Optional[QPoint] = None

    def update_point(self, x: int, y: int) -> None:
        self._point = self.mapFromGlobal(QPoint(x, y))
        self.update()

    def paintEvent(self, _event) -> None:
        if self._point is None or self.reticle.isNull():
            return
        painter = QPainter(self)
        painter.drawPixmap(QPointF(self._point.x() - self.reticle.width() / 2,
                                   self._point.y() - self.reticle.height() / 2), self.reticle)
