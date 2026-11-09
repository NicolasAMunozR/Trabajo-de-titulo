# Construye las pantallas Qt a partir de los layouts extraídos de los *.Designer.cs originales.
import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import QEvent, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (QColor, QCursor, QFont, QFontDatabase, QIcon, QImage, QMovie, QPainter,
                           QPainterPath, QPen, QPixmap)
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFrame, QGroupBox, QLabel,
                               QLineEdit, QListWidget, QPushButton, QRadioButton, QScrollArea,
                               QSpinBox, QTextEdit, QVBoxLayout, QWidget)

logger = logging.getLogger(__name__)

UI_DIR = Path(__file__).resolve().parent
RESOURCES = UI_DIR / "resources"
LAYOUTS = UI_DIR / "layouts"

SYSTEM_COLORS = {
    "Window": "#ffffff", "ControlLightLight": "#ffffff", "Control": "#f0f0f0", "White": "#ffffff",
    "Black": "#000000", "WindowText": "#000000", "Transparent": "transparent",
}

# Colores del sistema de diseño de EDDIE
CELESTE = "#1c9dec"
FONDO = "#f8f5fa"
AZUL_OSCURO = "#00003c"
MORADO = "#54216b"


def load_fonts() -> None:
    # Registra IBM Plex Sans (OFL) para que la interfaz luzca igual sin instalarla.
    for font in (RESOURCES / "fonts").glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(font))


def apply_light_theme(app) -> None:
    # Fija los colores claros de sistema de WinForms para que el texto no quede ilegible en modo oscuro.
    from PySide6.QtGui import QColor, QPalette
    from PySide6.QtWidgets import QStyleFactory

    try:
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)          # Qt ≥ 6.8
    except AttributeError:
        pass
    if "windowsvista" in [key.lower() for key in QStyleFactory.keys()]:
        app.setStyle("windowsvista")                                    # aspecto de los controles WinForms
    else:
        app.setStyle("Fusion")
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: "#f0f0f0", QPalette.ColorRole.WindowText: "#000000",
        QPalette.ColorRole.Base: "#ffffff", QPalette.ColorRole.AlternateBase: "#f7f7f7",
        QPalette.ColorRole.Text: "#000000", QPalette.ColorRole.Button: "#f0f0f0",
        QPalette.ColorRole.ButtonText: "#000000", QPalette.ColorRole.BrightText: "#ffffff",
        QPalette.ColorRole.Highlight: "#0078d7", QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.ToolTipBase: "#ffffe1", QPalette.ColorRole.ToolTipText: "#000000",
        QPalette.ColorRole.PlaceholderText: "#6d6d6d", QPalette.ColorRole.Link: "#0066cc",
        QPalette.ColorRole.Light: "#ffffff", QPalette.ColorRole.Midlight: "#e3e3e3",
        QPalette.ColorRole.Mid: "#a0a0a0", QPalette.ColorRole.Dark: "#696969",
        QPalette.ColorRole.Shadow: "#000000",
    }
    for role, value in roles.items():
        palette.setColor(role, QColor(value))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor("#6d6d6d"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor("#f0f0f0"))
    app.setPalette(palette)


def color(value) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, str) and value.startswith("@"):
        return SYSTEM_COLORS.get(value[1:], "#f0f0f0")
    return value if isinstance(value, str) else None


def make_font(spec: Optional[dict]) -> QFont:
    if not spec:
        font = QFont("Microsoft Sans Serif")
        font.setPointSizeF(8.25)
        return font
    family = spec["family"]
    font = QFont(family)
    font.setPointSizeF(float(spec["size"]))
    if "SemiBold" in family:
        font.setWeight(QFont.Weight.DemiBold)
    elif "Light" in family:
        font.setWeight(QFont.Weight.Light)
    if spec.get("bold") and "SemiBold" not in family:
        font.setBold(True)
    font.setItalic(bool(spec.get("italic")))
    font.setUnderline(bool(spec.get("underline")))
    if "Microsoft Sans Serif" in family:
        font.setFamilies(["Microsoft Sans Serif", "Segoe UI", "Arial"])
    elif "IBM Plex" in family:
        font.setFamilies([family, "IBM Plex Sans", "Segoe UI", "Arial"])
    return font


@lru_cache(maxsize=256)
def pixmap(name: str) -> QPixmap:
    # Busca una imagen por nombre de recurso (Properties.Resources) o recurso .resx.
    for candidate in (RESOURCES / f"{name}.png", RESOURCES / f"{name}.gif", RESOURCES / "resx" / f"{name}.png",
                      RESOURCES / "resx" / f"{name}.gif", RESOURCES / name):
        if candidate.exists():
            return QPixmap(str(candidate))
    logger.warning("Recurso gráfico no encontrado: %s", name)
    return QPixmap()


def image_ref(form: str, value) -> Optional[str]:
    if isinstance(value, dict):
        if "resource" in value:
            return value["resource"]
        if "resx" in value:
            return f"{form}.{value['resx'].replace('.Image', '')}"
    return None


def bgr_to_qimage(frame: np.ndarray) -> QImage:
    if frame.ndim == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    rgb = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    h, w, _ = rgb.shape
    return QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()


# ---------------------------------------------------------------------------- widgets
class RoundedButton(QPushButton):
    # ButtonModified.cs: botón celeste con esquinas redondeadas (radio 18) y borde de 5 px.

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._bg = QColor(CELESTE)
        self._fg = QColor(FONDO)
        self._border = QColor(CELESTE)
        self._pressed_bg = QColor(MORADO)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFlat(True)

    def set_colors(self, bg: Optional[str], fg: Optional[str], border: Optional[str] = None) -> None:
        if bg:
            self._bg = QColor(bg)
        if fg:
            self._fg = QColor(fg)
        if border:
            self._border = QColor(border)
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2)
        path = QPainterPath()
        path.addRoundedRect(rect, 9, 9)
        down = self.isDown()
        painter.fillPath(path, self._pressed_bg if down else self._bg)
        painter.setPen(QPen(self._border if not down else self._pressed_bg, 3))
        painter.drawPath(path)
        painter.setPen(QColor("#ffffff") if down else self._fg)
        painter.setFont(self.font())
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.text())


class ImageButton(QPushButton):
    # Botón de imagen con estados normal/hover/presionado; con control por mirada hace clic por permanencia.
    dwell_clicked = Signal()
    dwell_ms = 0                      # global: lo fija la configuración de Eye tracking

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._images = {"normal": None, "hover": None, "pressed": None}
        self.setFlat(True)
        self.setStyleSheet("QPushButton{border:none;background:transparent;}")
        self._dwell = QTimer(self)
        self._dwell.setSingleShot(True)
        self._dwell.timeout.connect(self._dwell_click)

    def set_images(self, normal: Optional[str], hover: Optional[str] = None, pressed: Optional[str] = None) -> None:
        self._images = {"normal": normal, "hover": hover or normal, "pressed": pressed or hover or normal}
        self._show("normal")

    def set_image(self, name: str) -> None:
        self._images["normal"] = name
        self._show("normal")

    def _show(self, state: str) -> None:
        name = self._images.get(state)
        if name:
            pm = pixmap(name)
            self.setIcon(QIcon(pm))
            self.setIconSize(pm.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio))

    def enterEvent(self, event) -> None:
        self._show("hover")
        if ImageButton.dwell_ms > 0:
            self._dwell.start(ImageButton.dwell_ms)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._show("normal")
        self._dwell.stop()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        self._show("pressed")
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._show("hover")
        super().mouseReleaseEvent(event)

    def _dwell_click(self) -> None:
        if self.isVisible() and self.isEnabled():
            self.dwell_clicked.emit()
            self.click()


class FrameView(QLabel):
    # ImageBox de Emgu.CV: muestra un frame BGR estirado al tamaño del control.

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setScaledContents(True)
        self.setStyleSheet("background:#ffffff;border:1px solid #000000;")

    def show_frame(self, frame: Optional[np.ndarray]) -> None:
        if frame is None:
            return
        self.setPixmap(QPixmap.fromImage(bgr_to_qimage(frame)))

    def clear_frame(self) -> None:
        self.clear()


class MultilineTextBox(QTextEdit):
    # TextBox con Multiline=true; conserva la API Text de WinForms (text/setText).

    def text(self) -> str:
        return self.toPlainText()

    def setText(self, text: str) -> None:
        self.setPlainText(text)


class ClickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)


# ---------------------------------------------------------------------------- builder
class Form:
    # Resultado de construir un layout: raíz + acceso a controles por nombre.

    def __init__(self, name: str, root: QWidget, data: dict) -> None:
        self.name = name
        self.root = root
        self.data = data
        self.controls: dict[str, QWidget] = {}

    def __getattr__(self, item: str) -> QWidget:
        controls = self.__dict__.get("controls", {})
        if item in controls:
            return controls[item]
        raise AttributeError(item)

    def __getitem__(self, item: str) -> QWidget:
        return self.controls[item]


def load_layout(name: str) -> dict:
    return json.loads((LAYOUTS / f"{name}.json").read_text(encoding="utf-8"))


def build_form(name: str, root: QWidget, apply_form_props: bool = True) -> Form:
    # Crea en `root` todos los controles del layout `name` con su geometría original.
    data = load_layout(name)
    form = Form(name, root, data)
    props = data["props"]
    if apply_form_props:
        size = props.get("ClientSize") or props.get("Size")
        if size:
            root.resize(*size)
        bg = color(props.get("BackColor"))
        if bg:
            if not root.objectName():
                root.setObjectName(name)
            root.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            root.setStyleSheet(root.styleSheet() + f"#{root.objectName()}{{background-color:{bg};}}")
    for node in reversed(data["controls"]):       # WinForms: el primero agregado queda al frente
        _create(form, node, root)
    return form


def _create(form: Form, node: dict, parent: QWidget) -> Optional[QWidget]:
    kind, props, name = node["type"], node["props"], node["name"]
    widget: QWidget
    host: QWidget                                   # contenedor donde van los hijos
    if kind in ("Panel", "UserControl"):
        widget = QFrame(parent)
        host = widget
        if props.get("BorderStyle") == "FixedSingle":
            widget.setFrameShape(QFrame.Shape.Box)
            widget.setStyleSheet(f"QFrame#{name}{{border:1px solid #000000;}}")
    elif kind == "GroupBox":
        widget = QGroupBox(props.get("Text", ""), parent)
        host = widget
    elif kind == "FlowLayoutPanel":
        widget = QScrollArea(parent)
        widget.setWidgetResizable(True)
        widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(6)
        layout.addStretch(1)
        widget.setWidget(inner)
        host = inner
        widget.setProperty("flow_layout", layout)
    elif kind == "Label":
        widget = ClickableLabel(parent)
        widget.setText(props.get("Text", "").replace("\r\n", "\n"))
        ref = image_ref(form.name, props.get("Image"))
        if ref:
            path = next((p for p in (RESOURCES / "resx" / f"{ref}.gif", RESOURCES / f"{ref}.gif") if p.exists()), None)
            if path is not None:
                movie = QMovie(str(path))
                movie.setScaledSize(QSize(*props["Size"]))
                widget.setMovie(movie)
                movie.start()
            else:
                widget.setPixmap(pixmap(ref))
        align = props.get("TextAlign")
        if align == "TopCenter":
            widget.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        widget.setWordWrap(bool(props.get("MaximumSize")))
        host = widget
    elif kind == "PictureBox":
        widget = ClickableLabel(parent)
        widget.setScaledContents(props.get("SizeMode") in ("StretchImage", "Zoom", None))
        ref = image_ref(form.name, props.get("Image"))
        if ref:
            widget.setPixmap(pixmap(ref))
        if props.get("Cursor") == "Help":
            widget.setCursor(QCursor(Qt.CursorShape.WhatsThisCursor))
        host = widget
    elif kind == "ImageBox":
        widget = FrameView(parent)
        host = widget
    elif kind == "ButtonModified":
        widget = RoundedButton(parent)
        widget.setText(props.get("Text", ""))
        widget.set_colors(color(props.get("BackColor")), color(props.get("ForeColor")),
                          color(props.get("FlatAppearance.BorderColor")))
        host = widget
    elif kind in ("Button", "ButtonAlt"):
        ref = image_ref(form.name, props.get("Image"))
        if ref:
            widget = ImageButton(parent)
            widget.set_images(ref)
            widget.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            widget = QPushButton(props.get("Text", ""), parent)
        host = widget
    elif kind == "TextBox":
        if props.get("Multiline"):
            widget = MultilineTextBox(parent)
            widget.setPlainText(props.get("Text", ""))
            if props["Size"][1] < 30:
                widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        else:
            widget = QLineEdit(props.get("Text", ""), parent)
        if props.get("ReadOnly"):
            widget.setReadOnly(True)
        if props.get("BorderStyle") == "None":
            widget.setFrame(False) if isinstance(widget, QLineEdit) else widget.setFrameShape(QFrame.Shape.NoFrame)
        host = widget
    elif kind == "RichTextBox":
        widget = QTextEdit(parent)
        widget.setReadOnly(True)
        if props.get("BorderStyle") == "None":
            widget.setFrameShape(QFrame.Shape.NoFrame)
        host = widget
    elif kind == "ComboBox":
        widget = QComboBox(parent)
        widget.setEditable(props.get("DropDownStyle") != "DropDownList")
        if node.get("items"):
            widget.addItems(node["items"])
        if props.get("Text") and widget.isEditable():
            widget.lineEdit().setPlaceholderText(props["Text"])
        host = widget
    elif kind == "NumericUpDown":
        decimals = int(props.get("DecimalPlaces", 0))
        widget = QDoubleSpinBox(parent) if decimals else QSpinBox(parent)
        if decimals:
            widget.setDecimals(decimals)
        widget.setRange(props.get("Minimum", 0), props.get("Maximum", 100))
        widget.setValue(props.get("Value", props.get("Minimum", 0)))
        host = widget
    elif kind == "CheckBox":
        widget = QCheckBox(props.get("Text", ""), parent)
        widget.setChecked(bool(props.get("Checked")))
        host = widget
    elif kind == "RadioButton":
        widget = QRadioButton(props.get("Text", ""), parent)
        host = widget
    elif kind == "ListBox":
        widget = QListWidget(parent)
        host = widget
    else:
        logger.debug("Tipo no soportado %s (%s); se omite.", kind, name)
        return None

    widget.setObjectName(name)
    location, size = props.get("Location", [0, 0]), props.get("Size")
    if size:
        widget.setGeometry(QRect(location[0], location[1], size[0], size[1]))
    else:
        widget.move(*location)
    if kind not in ("ButtonModified",):
        widget.setFont(make_font(props.get("Font")))
    else:
        widget.setFont(make_font(props.get("Font") or {"family": "IBM Plex Sans SemiBold", "size": 12.75}))
    styles = []
    bg, fg = color(props.get("BackColor")), color(props.get("ForeColor"))
    if kind in ("Panel", "UserControl", "GroupBox", "Label", "PictureBox", "CheckBox", "RadioButton") and bg:
        styles.append(f"background-color:{bg};")
    if fg and kind not in ("ButtonModified",):
        styles.append(f"color:{fg};")
    if styles and kind not in ("Button", "ButtonAlt"):
        selector = {"Panel": "QFrame", "UserControl": "QFrame"}.get(kind, type(widget).__name__)
        widget.setStyleSheet(widget.styleSheet() + f"{selector}#{name}{{{''.join(styles)}}}")
    if props.get("AutoSize") and kind == "Label" and not props.get("MaximumSize"):
        widget.adjustSize()
    if props.get("Enabled") is False:
        widget.setEnabled(False)
    if props.get("Cursor") == "Hand":
        widget.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    widget.setVisible(props.get("Visible", True) is not False)
    form.controls[name] = widget
    for child in reversed(node.get("children", [])):
        _create(form, child, host)
    return widget
