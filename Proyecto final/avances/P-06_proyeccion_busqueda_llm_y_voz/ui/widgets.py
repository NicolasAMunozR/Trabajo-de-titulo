# Controles propios de la interfaz renovada; conservan la API que usa la lógica de EDDIE.
from typing import Optional

import numpy as np
from PySide6.QtCore import QElapsedTimer, QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ui import theme
from ui.form_builder import ImageButton, bgr_to_qimage


class ActionButton(QPushButton):
    # Botón de acción con variante visual (primary, secondary, ghost, danger, projection).

    def __init__(self, text: str = "", parent=None, variant: str = "secondary", icon: Optional[str] = None) -> None:
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.set_variant(variant)
        if icon:
            self.set_icon(icon)

    def set_variant(self, variant: str) -> None:
        self.setProperty("variant", variant)
        self.style().unpolish(self)
        self.style().polish(self)
        self._variant = variant

    def set_icon(self, name: str) -> None:
        color = "#FFFFFF" if self._variant == "primary" else (theme.PROY_TEXTO if self._variant == "projection"
                                                              else theme.TINTA)
        self.setIcon(theme.icon(name, color, 18))
        self.setIconSize(QSize(18, 18))


class NavButton(QPushButton):
    # Elemento del menú lateral: icono, texto y un punto de estado del módulo.
    STATE_COLORS = {"ok": theme.OK, "warn": "#E0A23A", "off": "#56617D"}

    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(text, parent)
        self._icon_name = ""
        self._state = "off"
        self._selected = False
        self.show_status = True
        self.pending = ""                    # avance en que se integra el módulo (solo en avances intermedios)
        self.setCheckable(False)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(44)
        self.setFlat(True)
        self.setStyleSheet("QPushButton{border:none;background:transparent;}")

    def configure(self, text: str, icon: str) -> None:
        self.setText(text)
        self._icon_name = icon
        self.update()

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.update()

    def set_status(self, state: str, tooltip: str = "") -> None:
        self._state = state
        self.setToolTip(tooltip)
        self.update()

    @property
    def status(self) -> str:
        return self._state

    def set_pending(self, stage: str) -> None:
        # Módulo aún no integrado: el botón queda deshabilitado y muestra el avance en que llega.
        self.pending = stage
        self.setEnabled(False)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.setToolTip(f"Este módulo se integra en el avance {stage}")
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(8, 2, -8, -2)
        hover = self.underMouse() and self.isEnabled()
        if self._selected or hover:
            path = QPainterPath()
            path.addRoundedRect(QRectF(r), 8, 8)
            p.fillPath(path, QColor(theme.TINTA_2 if not self._selected else "#33406A"))
        if self._selected:
            p.fillRect(QRectF(r.left(), r.top() + 10, 3, r.height() - 20), QColor(theme.PROY_ACTIVO))
        text_color = "#FFFFFF" if self._selected else (theme.TINTA_TEXTO if self.isEnabled() else "#6B7694")
        if self._icon_name:
            p.drawPixmap(r.left() + 14, r.center().y() - 9, theme.icon_pixmap(self._icon_name, text_color, 18))
        p.setPen(QColor(text_color))
        f = theme.font(10.5, theme.QFont.Weight.DemiBold if self._selected else theme.QFont.Weight.Normal)
        p.setFont(f)
        p.drawText(QRectF(r.left() + 44, r.top(), r.width() - 70, r.height()),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        if self.pending:
            p.setFont(theme.font(8.5))
            p.setPen(QColor("#6B7694"))
            p.drawText(QRectF(r.right() - 48, r.top(), 40, r.height()),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, self.pending)
        elif self.show_status:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(self.STATE_COLORS.get(self._state, "#56617D")))
            p.drawEllipse(QPointF(r.right() - 14, r.center().y()), 4, 4)


class ToolButton(ImageButton):
    # Botón de la proyección con icono, estado encendido y barra de progreso del clic por mirada.

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._icon_name = ""
        self._label = ""
        self._active = False
        self._dwell_clock = QElapsedTimer()
        self._dwell_paint = QTimer(self)
        self._dwell_paint.setInterval(40)
        self._dwell_paint.timeout.connect(self.update)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet("")

    def configure(self, icon: str, label: str) -> None:
        self._icon_name, self._label = icon, label
        self.setAccessibleName(label)
        self.update()

    def set_active(self, active: bool) -> None:
        self._active = active
        self.update()

    @property
    def active(self) -> bool:
        return self._active

    @property
    def label(self) -> str:
        return self._label

    # ImageButton usa imágenes PNG del original; aquí el botón se dibuja, así que se ignoran.
    def set_images(self, normal=None, hover=None, pressed=None) -> None:
        self.update()

    def set_image(self, name: str) -> None:
        self.update()

    def _show(self, state: str) -> None:
        self.update()

    def enterEvent(self, event) -> None:
        if ImageButton.dwell_ms > 0:
            self._dwell_clock.start()
            self._dwell_paint.start()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._dwell_paint.stop()
        self._dwell_clock.invalidate()
        super().leaveEvent(event)
        self.update()

    def _dwell_click(self) -> None:
        self._dwell_paint.stop()
        self._dwell_clock.invalidate()
        super()._dwell_click()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        path = QPainterPath()
        path.addRoundedRect(r, 10, 10)
        hover, down = self.underMouse(), self.isDown()
        if self._active:
            p.fillPath(path, QColor(theme.PROY_ACTIVO))
            fg = QColor("#001014")
        else:
            p.fillPath(path, QColor("#1A2236" if (hover or down) else "#000000"))
            fg = QColor("#FFFFFF" if hover else theme.PROY_TEXTO)
        p.setPen(QPen(QColor(theme.PROY_ACTIVO if (hover or self._active) else theme.PROY_TRAZO), 1.5))
        p.drawPath(path)
        horizontal = self.width() >= 2.2 * self.height()
        pm = theme.icon_pixmap(self._icon_name, fg.name(), 22) if self._icon_name else QPixmap()
        p.setPen(fg)
        p.setFont(theme.font(9.5, theme.QFont.Weight.DemiBold))
        if horizontal:
            x = r.left() + 14
            if not pm.isNull():
                p.drawPixmap(int(x), int(r.center().y() - 11), pm)
                x += 30
            p.drawText(QRectF(x, r.top(), r.right() - x - 8, r.height()),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap,
                       self._label)
        else:
            if not pm.isNull():
                p.drawPixmap(int(r.center().x() - 11), int(r.top() + 7), pm)
            p.drawText(QRectF(r.left() + 2, r.top() + 31, r.width() - 4, r.height() - 33),
                       Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._label)
        if self._dwell_clock.isValid() and ImageButton.dwell_ms > 0:
            frac = min(1.0, self._dwell_clock.elapsed() / ImageButton.dwell_ms)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(theme.PROY_ACTIVO if not self._active else "#FFFFFF"))
            p.drawRoundedRect(QRectF(r.left() + 8, r.bottom() - 5, (r.width() - 16) * frac, 3), 1.5, 1.5)


class FitFrameView(QLabel):
    # ImageBox de Emgu.CV, pero sin deformar: la imagen se ajusta conservando su proporción.

    def __init__(self, parent=None, placeholder: str = "Sin imagen") -> None:
        super().__init__(parent)
        self.placeholder = placeholder
        self.setMinimumSize(160, 110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._frame_pm: Optional[QPixmap] = None

    def show_frame(self, frame: Optional[np.ndarray]) -> None:
        if frame is None:
            return
        pm = QPixmap.fromImage(bgr_to_qimage(frame))
        self._frame_pm = pm
        self.setPixmap(pm)

    def setPixmap(self, pm: QPixmap) -> None:      # noqa: N802 (API Qt)
        self._frame_pm = pm
        super().setPixmap(pm)
        self.update()

    def clear_frame(self) -> None:
        self._frame_pm = None
        self.clear()

    def clear(self) -> None:
        self._frame_pm = None
        super().clear()
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(r, 8, 8)
        p.fillPath(path, QColor("#121A2C"))
        p.setClipPath(path)
        pm = self._frame_pm
        if pm is not None and not pm.isNull():
            scaled = pm.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
            x = (self.width() - scaled.width()) / 2
            y = (self.height() - scaled.height()) / 2
            p.drawPixmap(QRectF(x, y, scaled.width(), scaled.height()), pm, QRectF(pm.rect()))
        else:
            p.setPen(QColor("#7E8AA6"))
            p.setFont(theme.font(9.5))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.placeholder)


class Spinner(QWidget):
    # Indicador de carga dibujado (reemplaza el GIF del original).

    def __init__(self, parent=None, color: str = "#FFFFFF", size: int = 22) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = QColor(color)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._step)
        self._timer.start()

    def _step(self) -> None:
        self._angle = (self._angle + 12) % 360
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self._color, 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        r = QRectF(self.rect()).adjusted(3, 3, -3, -3)
        p.drawArc(r, -self._angle * 16, 270 * 16)


def card(title: str = "", hint: str = "", help_widget: Optional[QWidget] = None,
         title_label: Optional[QLabel] = None) -> tuple[QFrame, QVBoxLayout]:
    # Tarjeta blanca con título (opcional), icono de ayuda y una línea de explicación.
    frame = QFrame()
    frame.setProperty("card", True)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 14, 18, 16)
    layout.setSpacing(8)
    if title or title_label is not None:
        row = QHBoxLayout()
        row.setSpacing(6)
        label = title_label if title_label is not None else QLabel()
        if title:
            label.setText(title)
        label.setProperty("cardTitle", True)
        label.setWordWrap(False)
        row.addWidget(label)
        if help_widget is not None:
            row.addWidget(help_widget)
        row.addStretch(1)
        layout.addLayout(row)
    if hint:
        layout.addWidget(hint_label(hint))
    return frame, layout


def hint_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("hint", True)
    label.setWordWrap(True)
    return label


def field_label(widget_or_text, text: Optional[str] = None) -> QLabel:
    label = widget_or_text if isinstance(widget_or_text, QLabel) else QLabel(widget_or_text)
    if text is not None:
        label.setText(text)
    label.setProperty("field", True)
    label.setWordWrap(False)
    return label


def make_help(label: QLabel, size: int = 16) -> QLabel:
    # Convierte un PictureBox de información del original en un icono de ayuda.
    label.setPixmap(theme.icon_pixmap("circle-help", theme.APAGADO, size))
    label.setScaledContents(False)
    label.setFixedSize(size + 6, size + 6)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setProperty("help", True)
    label.setCursor(QCursor(Qt.CursorShape.WhatsThisCursor))
    return label


def segmented(*radios) -> QFrame:
    # Agrupa radios Sí/No como un selector segmentado (y los deja exclusivos entre sí).
    frame = QFrame()
    frame.setProperty("segmented", True)
    row = QHBoxLayout(frame)
    row.setContentsMargins(3, 3, 3, 3)
    row.setSpacing(2)
    for radio in radios:
        radio.setParent(frame)
        radio.setProperty("segment", True)
        radio.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        row.addWidget(radio)
    frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return frame


def hbox(*items, spacing: int = 8, stretch_end: bool = False) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(spacing)
    row.setContentsMargins(0, 0, 0, 0)
    for item in items:
        if item is None:
            row.addStretch(1)
        elif isinstance(item, int):
            row.addSpacing(item)
        elif isinstance(item, QWidget):
            row.addWidget(item)
        else:
            row.addLayout(item)
    if stretch_end:
        row.addStretch(1)
    return row


def vbox(*items, spacing: int = 8) -> QVBoxLayout:
    col = QVBoxLayout()
    col.setSpacing(spacing)
    col.setContentsMargins(0, 0, 0, 0)
    for item in items:
        if item is None:
            col.addStretch(1)
        elif isinstance(item, int):
            col.addSpacing(item)
        elif isinstance(item, QWidget):
            col.addWidget(item)
        else:
            col.addLayout(item)
    return col
