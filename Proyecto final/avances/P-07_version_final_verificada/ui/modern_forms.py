"""
ui/modern_forms.py
==================
Constructor de la interfaz renovada (P-08).

En P-07 cada pantalla se reconstruía con las posiciones absolutas de los *.Designer.cs
(ui/form_builder.build_form). Aquí se crean **los mismos controles, con el mismo nombre y
el mismo tipo de comportamiento** (rangos, ítems, estados del layout original), pero se
ordenan con layouts de Qt en tarjetas, con textos en español y con el sistema visual de
ui/theme.py. Como la lógica (settings_pages, menu_settings, projection_screen) accede a
los controles por nombre (self.form.<nombre>), sigue funcionando igual.

Los controles del original que el diseño nuevo no necesita (rótulos de unidades,
paneles decorativos, el GIF de carga...) se crean igual, pero quedan en un contenedor
oculto (`form.spare`): ninguna referencia de la lógica queda rota.
"""
import logging
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QPushButton, QRadioButton, QScrollArea, QSpinBox, QTextEdit,
                               QVBoxLayout, QWidget)

from ui import theme
from ui.form_builder import ClickableLabel, Form, MultilineTextBox, image_ref, load_layout
from ui.widgets import (ActionButton, FitFrameView, NavButton, ToolButton, card, field_label, hbox, hint_label,
                        make_help, segmented, vbox)

logger = logging.getLogger(__name__)


class ModernForm(Form):
    """Form con "ranuras" (slots): lugares del diseño donde la lógica agrega sus controles nuevos."""

    def __init__(self, name: str, root: QWidget, data: dict) -> None:
        super().__init__(name, root, data)
        self.nodes: dict[str, dict] = {}
        self.slots: dict[str, QHBoxLayout | QVBoxLayout] = {}
        self.spare = QWidget(root)
        self.spare.setObjectName("spare")
        self.spare.hide()

    def place(self, slot: str, *widgets: QWidget) -> None:
        """Agrega `widgets` a la ranura `slot` y los registra por su objectName."""
        layout = self.slots.get(slot)
        for widget in widgets:
            if layout is not None:
                layout.addWidget(widget)
            else:
                widget.setParent(self.spare)
            if widget.objectName():
                self.controls[widget.objectName()] = widget

    def add(self, name: str, widget: QWidget) -> QWidget:
        widget.setObjectName(name)
        self.controls[name] = widget
        return widget


# Tipos del original que cambian de clase en el diseño nuevo (además del mapeo general)
CLASS_OVERRIDES = {
    "MenuSettings": {name: NavButton for name in ("InteractionsButton", "WebSearchServicesButton", "EyeTrackingButton",
                                                  "TextRecognitiionButton", "GestureRecognitionButton",
                                                  "PageDetectionButton")},
}


def build_modern(name: str, root: QWidget) -> ModernForm:
    data = load_layout(name)
    form = ModernForm(name, root, data)
    overrides = CLASS_OVERRIDES.get(name, {})
    for node in _walk(data["controls"]):
        form.nodes[node["name"]] = node
        widget = _make(form, node, overrides.get(node["name"]))
        if widget is not None:
            widget.setObjectName(node["name"])
            widget.setParent(form.spare)
            form.controls[node["name"]] = widget
    ARRANGE[name](form, root)
    return form


def _walk(nodes):
    for node in nodes:
        yield node
        yield from _walk(node.get("children", []))


def _make(form: ModernForm, node: dict, cls=None) -> Optional[QWidget]:
    """Mismo mapeo de tipos WinForms → Qt que form_builder._create, sin geometría ni estilos del original."""
    kind, props = node["type"], node["props"]
    text = props.get("Text", "").replace("\r\n", "\n") if isinstance(props.get("Text"), str) else ""
    if cls is not None:
        widget = cls(text)
    elif kind in ("Panel", "UserControl", "GroupBox"):
        widget = QFrame()
    elif kind == "FlowLayoutPanel":
        widget = QScrollArea()
        widget.setWidgetResizable(True)
        widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        widget.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner.setObjectName("flowInner")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(8)
        layout.addStretch(1)
        widget.setWidget(inner)
        widget.setProperty("flow_layout", layout)
    elif kind in ("Label", "PictureBox"):
        widget = ClickableLabel(text if kind == "Label" else "")
    elif kind == "ImageBox":
        widget = FitFrameView()
    elif kind == "ButtonModified":
        widget = ActionButton(text)
    elif kind in ("Button", "ButtonAlt"):
        widget = ToolButton() if image_ref(form.name, props.get("Image")) else QPushButton(text)
    elif kind == "TextBox":
        widget = MultilineTextBox() if props.get("Multiline") else QLineEdit(text)
        if props.get("Multiline"):
            widget.setPlainText(text)
        if props.get("ReadOnly"):
            widget.setReadOnly(True)
    elif kind == "RichTextBox":
        widget = QTextEdit()
        widget.setReadOnly(True)
    elif kind == "ComboBox":
        widget = QComboBox()
        widget.setEditable(props.get("DropDownStyle") != "DropDownList")
        if node.get("items"):
            widget.addItems(node["items"])
    elif kind == "NumericUpDown":
        decimals = int(props.get("DecimalPlaces", 0))
        widget = QDoubleSpinBox() if decimals else QSpinBox()
        if decimals:
            widget.setDecimals(decimals)
        widget.setRange(props.get("Minimum", 0), props.get("Maximum", 100))
        widget.setValue(props.get("Value", props.get("Minimum", 0)))
        widget.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
    elif kind == "CheckBox":
        widget = QCheckBox(text)
        widget.setChecked(bool(props.get("Checked")))
    elif kind == "RadioButton":
        widget = QRadioButton(text)
    elif kind == "ListBox":
        widget = QListWidget()
    else:
        logger.debug("Tipo no soportado %s; se omite.", kind)
        return None
    if props.get("Enabled") is False:
        widget.setEnabled(False)
    if props.get("Visible") is False:
        widget.setVisible(False)
    return widget


# ============================================================================ páginas de configuración
def _page(form: ModernForm, root: QWidget, title: str, subtitle: str, help_name: Optional[str] = None) -> QVBoxLayout:
    """Encabezado (título + ayuda + bajada) y cuerpo desplazable de una página de configuración."""
    outer = QVBoxLayout(root)
    outer.setContentsMargins(32, 4, 32, 0)
    outer.setSpacing(4)
    title_label = form.controls["InteractionsTittle"]
    title_label.setText(title)
    title_label.setObjectName("pageTitle")
    form.controls["InteractionsTittle"] = title_label
    header = hbox(title_label, spacing=8)
    if help_name:
        header.addWidget(make_help(form[help_name], 18))
    header.addStretch(1)
    outer.addLayout(header)
    sub = QLabel(subtitle)
    sub.setObjectName("pageSubtitle")
    sub.setWordWrap(True)
    outer.addWidget(sub)
    outer.addSpacing(10)
    scroll = QScrollArea()
    scroll.setObjectName("pageBody")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    body = QWidget()
    body.setObjectName("pageBodyInner")
    body.setStyleSheet("QWidget#pageBodyInner{background:transparent;}")
    layout = QVBoxLayout(body)
    layout.setContentsMargins(0, 0, 6, 18)
    layout.setSpacing(14)
    scroll.setWidget(body)
    scroll.viewport().setObjectName("pageViewport")
    scroll.viewport().setStyleSheet("QWidget#pageViewport{background:transparent;}")
    outer.addWidget(scroll, 1)
    return layout


def _browse(button: QPushButton) -> QPushButton:
    button.setText("")
    button.setIcon(theme.icon("folder-open", theme.TINTA, 18))
    button.setProperty("browse", True)
    button.setFixedSize(34, 32)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


def _action(button: ActionButton, text: str, variant: str, icon: Optional[str] = None) -> ActionButton:
    button.setText(text)
    button.set_variant(variant)
    if icon:
        button.set_icon(icon)
    return button


def _wide(widget: QWidget, width: int) -> QWidget:
    widget.setMinimumWidth(width)
    widget.setMaximumWidth(width)
    return widget


def _resolution(x: QWidget, sep: QLabel, y: QWidget) -> QHBoxLayout:
    sep.setText("×")
    sep.setProperty("field", True)
    for spin in (x, y):
        _wide(spin, 96)
        spin.setSuffix(" px")
    return hbox(x, sep, y, stretch_end=True)


def arrange_interactions(form: ModernForm, root: QWidget) -> None:
    f = form
    body = _page(f, root, "Interacción", "Cómo pide el lector las búsquedas mientras lee con la proyección.")
    f.rbtn_voz_si.setText("Activados")
    f.rbtn_voz_no.setText("Desactivados")
    f.rbtn_Si_botones.setText("Visibles")
    f.rbtn_no_botones.setText("Ocultos")
    voice_card, voice = card(title_label=f.label1, title="Comandos de voz", help_widget=make_help(f.pictureBox1),
                             hint="Di «Buscar definición», «Lectura enciclopedia» o «Cerrar video» sin soltar el libro.")
    voice.addWidget(segmented(f.rbtn_voz_si, f.rbtn_voz_no))
    status = f.add("labelVoiceStatus", QLabel(""))
    status.setProperty("state", "off")
    voice.addWidget(status)
    voice.addStretch(1)
    buttons_card, buttons = card(title_label=f.label2, title="Botones de búsqueda",
                                 help_widget=make_help(f.pictureBox2),
                                 hint="Con la voz activada puedes ocultar los botones y dejar el escritorio más despejado.")
    buttons.addWidget(segmented(f.rbtn_Si_botones, f.rbtn_no_botones))
    buttons.addStretch(1)
    body.addLayout(hbox(voice_card, buttons_card, spacing=14))
    body.addStretch(1)


SERVICE_ROWS = [  # (etiqueta del original, combo, icono, nombre, explicación)
    ("lbl_Enciclopedias", "cbx_apisEnciclopedia", "library", "Enciclopedia", "Explica el concepto en párrafos."),
    ("label2", "cbx_apisDefiniciones", "book-a", "Definiciones", "Acepciones breves, en viñetas."),
    ("label3", "cbx_apisTraducciones", "languages", "Traducción", "Traduce el término resaltado."),
    ("label5", "cbx_idiomaTraducir", "arrow-left-right", "Idioma de destino", "Idioma al que se traduce."),
    ("label1", "cbx_apisVideos", "clapperboard", "Video", "Busca un video sobre el término."),
    ("label4", "cbx_apisImagenes", "image", "Imágenes", "Reconoce la imagen capturada con un gesto."),
]


def arrange_web(form: ModernForm, root: QWidget) -> None:
    f = form
    body = _page(f, root, "Servicios de búsqueda",
                 "Cada búsqueda del lector la responde un modelo de lenguaje (LLM). Elige cuál para cada servicio.",
                 "pictureBox1")
    providers_card, providers = card("Proveedores disponibles")
    status = f.add("labelProviderStatus", QLabel("Buscando proveedores…"))
    status.setWordWrap(True)
    status.setProperty("field", True)
    providers.addWidget(status)
    services_card, services = card("Servicio por tipo de búsqueda")
    grid = QGridLayout()
    grid.setHorizontalSpacing(14)
    grid.setVerticalSpacing(10)
    for row, (label_name, combo_name, icon_name, title, hint) in enumerate(SERVICE_ROWS):
        icon_label = QLabel()
        icon_label.setPixmap(theme.icon_pixmap(icon_name, theme.ACENTO, 20))
        name_label = field_label(f[label_name], title)
        name_label.setStyleSheet("font-weight:600;")
        grid.addWidget(icon_label, row, 0)
        grid.addLayout(vbox(name_label, hint_label(hint), spacing=0), row, 1)
        grid.addWidget(_wide(f[combo_name], 300), row, 2)
    grid.setColumnStretch(1, 1)
    services.addLayout(grid)
    body.addWidget(providers_card)
    body.addWidget(services_card)
    body.addStretch(1)


def arrange_eye(form: ModernForm, root: QWidget) -> None:
    f = form
    body = _page(f, root, "Rastreo ocular",
                 "Conecta un eye tracker para mover el puntero con la mirada y registrar los datos de la sesión.",
                 "pictureBox5")
    device_card, device = card(title_label=f.label8, title="Dispositivo", help_widget=make_help(f.pictureBox1))
    device.addWidget(field_label(f.label1, "Carpeta de plugins"))
    device.addLayout(hbox(f.pluginsRoute, _browse(f.pluginsRouteBrowse), spacing=6))
    device.addWidget(field_label(f.label2, "Eye tracker"))
    device.addWidget(f.trackingPlugins)
    device.addStretch(1)

    reticle_card, reticle = card(title_label=f.label10, title="Retícula", help_widget=make_help(f.pictureBox2))
    reticle.addWidget(field_label(f.label3, "Carpeta de retículas"))
    reticle.addLayout(hbox(f.reticlesRoute, _browse(f.reticlesRouteBrowse), spacing=6))
    reticle.addWidget(field_label(f.label4, "Retícula que sigue la mirada"))
    f.reticleExample.setFixedSize(40, 40)
    f.reticleExample.setScaledContents(True)
    f.reticleDimensions.setProperty("hint", True)
    reticle.addLayout(hbox(f.reticleSelected, f.reticleExample, f.reticleDimensions, spacing=10))
    reticle.addStretch(1)

    pointer_card, pointer = card(title_label=f.label11, title="Control del puntero",
                                 help_widget=make_help(f.pictureBox3))
    f.controlMouse.setText("Mover el puntero con la mirada")
    pointer.addWidget(f.controlMouse)
    f.clickTimer.setSuffix(" s")
    pointer.addLayout(hbox(field_label(f.label6, "Hacer clic al mirar un botón durante"), _wide(f.clickTimer, 80),
                           stretch_end=True))
    pointer.addWidget(hint_label("En la proyección, una barra en el botón muestra cuánto falta para el clic."))
    pointer.addStretch(1)

    data_card, data = card(title_label=f.label9, title="Registro de datos", help_widget=make_help(f.pictureBox4))
    f.saveData.setText("Guardar la mirada en un archivo CSV")
    data.addWidget(f.saveData)
    data.addWidget(field_label(f.label7, "Nombre del archivo"))
    f.fileNameTextBox.setPlaceholderText("p. ej. lector-01")
    data.addWidget(f.fileNameTextBox)
    data.addWidget(field_label(f.label5, "Carpeta"))
    data.addLayout(hbox(f.saveFileRoute, _browse(f.saveFileRouteBrowse), spacing=6))

    grid = QGridLayout()
    grid.setSpacing(14)
    grid.addWidget(device_card, 0, 0)
    grid.addWidget(reticle_card, 0, 1)
    grid.addWidget(pointer_card, 1, 0)
    grid.addWidget(data_card, 1, 1)
    body.addLayout(grid)
    body.addLayout(hbox(_action(f.buttonModified3, "Importar ajustes", "secondary", "upload"),
                        _action(f.buttonModified1, "Exportar ajustes", "secondary", "download"), None,
                        _action(f.buttonModified2, "Aplicar y conectar", "primary", "check")))
    body.addStretch(1)


def _view(view: FitFrameView, caption: str, placeholder: str, height: int = 230) -> QVBoxLayout:
    view.placeholder = placeholder
    view.setFixedHeight(height)
    return vbox(field_label(caption), view, spacing=6)


def arrange_text(form: ModernForm, root: QWidget) -> None:
    f = form
    body = _page(f, root, "Reconocimiento de texto",
                 "La cámara de texto mira la página. Cuando el lector resalta una palabra, EDDIE la recorta y la "
                 "lee con OCR.")
    camera_card, camera = card(title_label=f.labelRecTxt, title="Cámara de texto", help_widget=make_help(f.pictureBox2))
    camera.addLayout(hbox(vbox(field_label("Cámara"), _wide(f.ComboBoxCameraList1, 300), spacing=4), 24,
                          vbox(field_label("Resolución"), _resolution(f.numericUpDownResXText, f.label4,
                                                                      f.numericUpDownResYText), spacing=4),
                          stretch_end=True))
    camera.addWidget(hint_label("Usa una cámara distinta a la de gestos."))
    test_card, test = card("Probar el reconocimiento",
                           hint="Resalta una palabra en la hoja (o pasa el lápiz amarillo) y pulsa «Reconocer texto».")
    test.addLayout(hbox(_view(f.imageBox3, "Cámara en vivo (o el recorte que se leyó)", "Esperando imagen de la cámara…"),
                        _view(f.imageBox1, "Dónde se encontró el resaltado", "Aún no se detecta un resaltado"),
                        spacing=14))
    slot = hbox(spacing=10)
    f.slots["recognition"] = slot
    test.addLayout(slot)
    body.addWidget(camera_card)
    body.addWidget(test_card)
    body.addStretch(1)


def arrange_gesture(form: ModernForm, root: QWidget) -> None:
    f = form
    body = _page(f, root, "Reconocimiento gestual",
                 "Resalta y captura sobre la proyección con la mano, un lápiz de color o el mouse.")
    source_card, source = card("Cámara y complemento", help_widget=make_help(f.pictureBox2))
    source.addLayout(hbox(vbox(field_label(f.label1, "Cámara"), _wide(f.ComboBoxCameraList2, 260), spacing=4), 16,
                          vbox(field_label("Resolución"), _resolution(f.numericUpDownXGestual, f.label5,
                                                                      f.numericUpDownYGestual), spacing=4), 16,
                          vbox(field_label(f.label4, "Complemento"), _wide(f.comboBox1, 220), spacing=4),
                          stretch_end=True))
    f.checkBoxMouse.setText("Controlar el puntero con el gesto")
    options = hbox(f.checkBoxMouse, make_help(f.pictureBox1), 18, spacing=4)
    f.slots["gesture_options"] = options
    source.addLayout(hbox(_action(f.StartProjectionButtonModified, "Iniciar", "primary", "play"),
                          _action(f.buttonModified1, "Detener", "secondary", "square"), 18, options, None))

    view_card, view = card("Vista de la cámara")
    view.addLayout(hbox(_view(f.imageBox2, "Cámara gestual", "Pulsa «Iniciar» para ver la cámara", 210),
                        _view(f.imageBox4, "Última captura", "Sin capturas todavía", 210), spacing=14))
    view.addLayout(hbox(_action(f.buttonModified2, "Capturar selección", "secondary", "crop"), None))

    cal_card, cal = card(title_label=f.label6, title="Calibración", help_widget=make_help(f.pictureBox4),
                         hint="Apunta al centro de la cruz superior izquierda de la proyección y pulsa «Fijar inicio»; "
                              "luego a la cruz inferior derecha y pulsa «Fijar fin».")
    for box in (f.textBoxX, f.textBoxY):
        box.setReadOnly(True)
        box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _wide(box, 90)
    reading = hbox(field_label(f.label2, "Sensor X"), f.textBoxX, 12, field_label(f.label3, "Sensor Y"), f.textBoxY,
                   20, spacing=6)
    actions = hbox(spacing=8)
    f.slots["calibration_actions"] = actions
    reading.addLayout(actions)
    reading.addStretch(1)
    cal.addLayout(reading)
    grid = QGridLayout()
    grid.setHorizontalSpacing(12)
    grid.setVerticalSpacing(6)
    for col, title in enumerate(("", "Sensor inicio", "Sensor fin", "App inicio", "App fin", "Transformar"), start=0):
        if title:
            grid.addWidget(field_label(title), 0, col)
    for row, axis in enumerate(("X", "Y"), start=1):
        grid.addWidget(field_label(f"Eje {axis}"), row, 0)
        for col, prefix in enumerate(("numericUpDownSStart", "numericUpDownSEnd", "numericUpDownAStart",
                                      "numericUpDownAEnd"), start=1):
            grid.addWidget(_wide(f[f"{prefix}{axis}"], 120), row, col)
        check = f[f"checkBox{axis}"]
        check.setText("")
        check.setToolTip(f"Invierte el eje {axis} al convertir coordenadas del sensor a la pantalla.")
        grid.addWidget(check, row, 5, alignment=Qt.AlignmentFlag.AlignCenter)
    grid.setColumnStretch(6, 1)
    cal.addLayout(grid)
    cal.addLayout(hbox(None, _action(f.buttonModified3, "Guardar calibración", "secondary", "check")))

    body.addWidget(source_card)
    body.addWidget(view_card)
    body.addWidget(cal_card)
    body.addStretch(1)


def arrange_page(form: ModernForm, root: QWidget) -> None:
    f = form
    body = _page(f, root, "Documento PDF",
                 "El PDF del libro que se lee. EDDIE guarda en él los resaltados, marcadores y comentarios.")
    file_card, file = card(title_label=f.label1, title="Archivo", help_widget=make_help(f.pictureBox2))
    f.textBoxPathPDF.setPlaceholderText("Ningún PDF seleccionado")
    file.addLayout(hbox(f.textBoxPathPDF, _action(f.buttonModified1, "Elegir PDF…", "primary", "file-text")))
    file.addSpacing(6)
    file.addWidget(field_label("Tamaño de página del PDF (puntos)"))
    sep1 = QLabel("×")
    file.addLayout(hbox(_wide(f.numericUpDown5, 110), sep1, _wide(f.numericUpDown6, 110), stretch_end=True))
    file.addWidget(field_label(f.label8, "Tamaño de la hoja impresa (cm)"))
    sep2 = QLabel("×")
    file.addLayout(hbox(_wide(f.numericUpDown1, 110), sep2, _wide(f.numericUpDown2, 110), stretch_end=True))
    file.addSpacing(6)
    file.addWidget(field_label("Zona de resaltado en la proyección"))
    file.addWidget(hint_label("Esquina inferior derecha del área blanca, en píxeles de la proyección."))
    for spin in (f.FinalLocateX, f.FinalLocateY):
        spin.setSuffix(" px")
    sep3 = QLabel("×")
    file.addLayout(hbox(_wide(f.FinalLocateX, 110), sep3, _wide(f.FinalLocateY, 110), 10,
                        _action(f.buttonModified2, "Ajustar zona", "secondary", "crosshair"), stretch_end=True))
    file.addStretch(1)
    preview_card, preview = card("Vista previa")
    slot = vbox(spacing=8)
    f.slots["pdf_preview"] = slot
    preview.addLayout(slot)
    file_card.setMinimumWidth(470)
    body.addLayout(hbox(file_card, preview_card, spacing=14))
    body.addStretch(1)


# ============================================================================ ventana principal
NAV_ITEMS = [  # botón del original, rótulo, icono
    ("InteractionsButton", "Interacción", "mic"),
    ("WebSearchServicesButton", "Búsquedas", "globe"),
    ("EyeTrackingButton", "Rastreo ocular", "eye"),
    ("TextRecognitiionButton", "Texto (OCR)", "scan-text"),
    ("GestureRecognitionButton", "Gestos", "hand"),
    ("PageDetectionButton", "Documento PDF", "file-text"),
]


def _chrome(label: QLabel, icon_name: str, tip: str) -> QLabel:
    label.setPixmap(theme.icon_pixmap(icon_name, theme.APAGADO, 18))
    label.setScaledContents(False)
    label.setFixedSize(32, 32)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setCursor(Qt.CursorShape.PointingHandCursor)
    label.setToolTip(tip)
    return label


def arrange_menu(form: ModernForm, root: QWidget) -> None:
    f = form
    root.resize(1280, 720)
    outer = QHBoxLayout(root)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    nav = f.PanelNavBar
    nav.setParent(root)
    nav.setFixedWidth(248)
    side = QVBoxLayout(nav)
    side.setContentsMargins(14, 22, 14, 18)
    side.setSpacing(2)
    brand = f.add("brandTitle", ClickableLabel("EDDIE"))
    brand.setCursor(Qt.CursorShape.PointingHandCursor)
    brand_sub = f.add("brandSubtitle", QLabel("Lectura aumentada no obstructiva"))
    side.addLayout(vbox(brand, brand_sub, spacing=0))
    side.addSpacing(18)
    home = f.add("HomeButton", NavButton("Preparar sesión"))
    home.configure("Preparar sesión", "list-checks")
    home.show_status = False
    side.addWidget(home)
    section = f.add("navSection", QLabel("Módulos"))
    side.addWidget(section)
    for name, text, icon_name in NAV_ITEMS:
        button = f[name]
        button.configure(text, icon_name)
        side.addWidget(button)
    side.addStretch(1)
    status = f.add("systemStatus", QLabel(""))
    status.setWordWrap(True)
    side.addWidget(status)
    outer.addWidget(nav)

    content = QWidget()
    content.setObjectName("contentArea")
    col = QVBoxLayout(content)
    col.setContentsMargins(0, 0, 0, 0)
    col.setSpacing(0)
    bar = f.PanelBarraSuperior
    bar.setParent(content)
    bar.setFixedHeight(40)
    bar_row = QHBoxLayout(bar)
    bar_row.setContentsMargins(0, 4, 10, 0)
    bar_row.addStretch(1)
    bar_row.addWidget(_chrome(f.MinimizePictureBox, "minus", "Minimizar"))
    bar_row.addWidget(_chrome(f.ExitPictureBox, "x", "Cerrar EDDIE"))
    col.addWidget(bar)
    panel = f.PanelContenido
    panel.setParent(content)
    col.addWidget(panel, 1)
    footer = QFrame()
    footer.setObjectName("footer")
    footer.setFixedHeight(72)
    foot = QHBoxLayout(footer)
    foot.setContentsMargins(32, 0, 28, 0)
    foot.setSpacing(10)
    foot.addWidget(_action(f.ResetSettingsButtonModified, "Restaurar valores", "ghost", "refresh-ccw"))
    foot.addStretch(1)
    foot.addWidget(_action(f.SaveSettingsButtonModified, "Guardar", "secondary", "check"))
    start = _action(f.StartProjectionButtonModified, "Iniciar proyección", "primary", "play")
    start.setMinimumWidth(190)
    foot.addWidget(start)
    col.addWidget(footer)
    outer.addWidget(content, 1)


# ============================================================================ diálogos
def arrange_alert(form: ModernForm, root: QWidget) -> None:
    f = form
    outer = QVBoxLayout(root)
    outer.setContentsMargins(0, 0, 0, 0)
    frame = QFrame()
    frame.setObjectName("alertCard")
    outer.addWidget(frame)
    col = QVBoxLayout(frame)
    col.setContentsMargins(28, 22, 18, 22)
    col.setSpacing(10)
    f.label1.setObjectName("alertTitle")
    f.label2.setObjectName("alertText")
    for label in (f.label1, f.label2):
        label.setWordWrap(True)
    head = hbox(spacing=12)
    head.addWidget(f.label1, 1)
    head.addWidget(_chrome(f.ExitPictureBox, "x", "Cerrar"), 0, Qt.AlignmentFlag.AlignTop)
    col.addLayout(head)
    col.addWidget(f.label2)
    col.addStretch(1)
    col.addLayout(hbox(None, _action(f.buttonModified2, "Cancelar", "ghost"),
                       _action(f.buttonModified1, "Confirmar", "primary"),
                       _action(f.okButton, "Entendido", "primary"), 10, spacing=8))


def arrange_loading(form: ModernForm, root: QWidget) -> None:
    from ui.widgets import Spinner
    f = form
    outer = QVBoxLayout(root)
    outer.setContentsMargins(0, 0, 0, 0)
    pill = QFrame()
    pill.setObjectName("loadingPill")
    outer.addWidget(pill)
    row = QHBoxLayout(pill)
    row.setContentsMargins(18, 8, 22, 8)
    row.setSpacing(12)
    f.label2.setText("Buscando…")
    f.label2.setObjectName("loadingText")
    row.addWidget(f.add("spinner", Spinner(pill)))
    row.addWidget(f.label2)


def arrange_recent(form: ModernForm, root: QWidget) -> None:
    f = form
    col = QVBoxLayout(root)
    col.setContentsMargins(12, 8, 12, 8)
    col.setSpacing(2)
    f.lbl_palabraBuscada.setStyleSheet(f"color:{theme.TINTA};font-size:11pt;font-weight:600;")
    f.lbl_palabraBuscada.setWordWrap(True)
    f.lbl_Api.setStyleSheet(f"color:{theme.ACENTO};font-weight:600;")
    f.lbl_fecha_hora.setStyleSheet(f"color:{theme.APAGADO};")
    col.addWidget(f.lbl_palabraBuscada)
    col.addLayout(hbox(f.lbl_Api, None, f.lbl_fecha_hora))


# ============================================================================ proyección
# Geometría de la pantalla proyectada (1300 × 740). La zona de lectura (HighlightTool en
# 285,65 de 517×400) y las tres cruces de calibración NO se mueven: el montaje del proyector y la
# calibración gestual dependen de ellas. Todo lo interactivo pasa a la franja superior, donde
# Ibaceta (2023) midió 100 % de validez del eye tracker; abajo-centro queda libre.
PROJECTION_GEOMETRY = {
    # franja superior
    "btn_drawMenu": (12, 10, 86, 52), "textImageButton": (104, 10, 170, 52),
    "textBox1": (372, 14, 420, 44),
    "btn_buscarWeb": (880, 10, 116, 52), "btn_sincronizadorPdf": (1002, 10, 170, 52),
    "btn_turnOFF": (1216, 10, 72, 52),
    # segunda fila: servicios (búsqueda web) o herramientas del PDF (sincronizador)
    "btn_diccionario": (12, 70, 128, 52), "btn_traductor": (146, 70, 128, 52),
    "btn_enciclopedia": (880, 70, 132, 52), "btn_video": (1018, 70, 132, 52), "btn_imagen": (1156, 70, 132, 52),
    "syncButton": (12, 70, 128, 52), "buttonPDF": (146, 70, 128, 52),
    "buttonMarker": (880, 70, 132, 52), "buttonComments": (1018, 70, 132, 52), "buttonFiguresPD": (1156, 70, 132, 52),
    # paneles laterales
    "panel3": (12, 130, 262, 470), "panel_log": (12, 130, 262, 470), "historyLogPanel": (12, 130, 262, 470),
    "panel2": (880, 130, 408, 470), "syncCard": (880, 130, 408, 196),
    # cruces de calibración (sin cambios)
    "pictureBox3": (298, 20, 60, 60), "pictureBox4": (297, 570, 60, 60), "pictureBox5": (797, 570, 60, 60),
    "markButton": (1130, 692, 158, 36),
}
PROJECTION_BUTTONS = {  # nombre → (icono, rótulo)
    "btn_drawMenu": ("history", "Historial"), "textImageButton": ("highlighter", "Modo resaltar"),
    "btn_buscarWeb": ("search", "Buscar"), "btn_sincronizadorPdf": ("book-open-check", "Sincronizar PDF"),
    "btn_turnOFF": ("power", "Salir"),
    "btn_diccionario": ("book-a", "Definición"), "btn_traductor": ("languages", "Traducción"),
    "btn_enciclopedia": ("library", "Enciclopedia"), "btn_video": ("clapperboard", "Video"),
    "btn_imagen": ("image", "Imagen"),
    "syncButton": ("highlighter", "Guardar resaltado"), "buttonPDF": ("file-down", "Mostrar contenido"),
    "buttonMarker": ("bookmark", "Marcador"), "buttonComments": ("message-square", "Comentarios"),
    "buttonFiguresPD": ("shapes", "Figuras"),
    "btn_leerDefinicionTraduccion": ("volume-2", "Leer"), "btn_cerrarVentanaIzquierda": ("x", "Cerrar"),
    "btn_leerEnciclopedia": ("volume-2", "Leer"), "btn_cerrarVentanaDerecha": ("x", "Cerrar"),
    "btn_nav_atras": ("chevron-left", "Atrás"), "btn_nav_adelante": ("chevron-right", "Adelante"),
}
PROJECTION_TIPS = {
    "syncButton": "Guarda en el PDF el resaltado hecho sobre la hoja (página sincronizada).",
    "buttonPDF": "Proyecta sobre la hoja las figuras, marcadores y comentarios de la página indicada (PDF → papel).",
    "buttonMarker": "Detecta un marcador azul en la hoja y lo agrega al PDF (papel → PDF).",
    "buttonComments": "Detecta una nota adhesiva en la hoja y la agrega como comentario (papel → PDF).",
    "buttonFiguresPD": "Detecta figuras dibujadas en la hoja y las agrega al PDF (papel → PDF).",
    "textImageButton": "Alterna entre resaltar texto (OCR) y capturar una imagen con el gesto.",
}


def _note(frame: QFrame) -> QFrame:
    frame.setProperty("note", True)
    frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    return frame


def _small_tool(button: ToolButton, name: str) -> ToolButton:
    icon_name, label = PROJECTION_BUTTONS[name]
    button.configure(icon_name, label)
    button.setFixedSize(84, 56)
    return button


def arrange_projection(form: ModernForm, root: QWidget) -> None:
    f = form
    root.resize(1300, 740)
    for name, (icon_name, label) in PROJECTION_BUTTONS.items():
        button = f.controls.get(name)
        if isinstance(button, ToolButton):
            button.configure(icon_name, label)
    for name, tip in PROJECTION_TIPS.items():
        f[name].setToolTip(tip)

    # --- término capturado (el lector puede corregirlo antes de buscar)
    f.textBox1.setPlaceholderText("Resalta una palabra en la hoja")
    f.textBox1.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    caption = f.label2
    caption.setText("Término")
    caption.setObjectName("termCaption")
    f.controls["label2"] = caption

    # --- panel izquierdo: definición / traducción
    left = _note(f.panel3)
    col = QVBoxLayout(left)
    col.setContentsMargins(16, 14, 16, 12)
    col.setSpacing(8)
    f.lbl_datoBuscado_trad_def.setProperty("noteTitle", True)
    f.lbl_datoBuscado_trad_def.setWordWrap(True)
    f.lbl_datoBuscado_trad_def.setText("")
    col.addWidget(f.lbl_datoBuscado_trad_def)
    col.addWidget(f.rtb_result_definicion_traduccion, 1)
    col.addLayout(hbox(_small_tool(f.btn_leerDefinicionTraduccion, "btn_leerDefinicionTraduccion"), None,
                       _small_tool(f.btn_cerrarVentanaIzquierda, "btn_cerrarVentanaIzquierda")))

    # --- panel derecho: enciclopedia / video / imagen
    right = _note(f.panel2)
    col = QVBoxLayout(right)
    col.setContentsMargins(16, 14, 16, 12)
    col.setSpacing(8)
    f.lbl_PalabraBuscada.setProperty("noteTitle", True)
    f.lbl_PalabraBuscada.setWordWrap(True)
    col.addWidget(f.lbl_PalabraBuscada)
    nav = f.panel_navegador
    nav_col = QVBoxLayout(nav)
    nav_col.setContentsMargins(0, 0, 0, 0)
    nav_col.addWidget(f.rtb_ResultadosWikipedia)
    col.addWidget(nav, 1)
    col.addLayout(hbox(_small_tool(f.btn_nav_atras, "btn_nav_atras"), _small_tool(f.btn_nav_adelante, "btn_nav_adelante"),
                       None, _small_tool(f.btn_leerEnciclopedia, "btn_leerEnciclopedia"),
                       _small_tool(f.btn_cerrarVentanaDerecha, "btn_cerrarVentanaDerecha")))

    # --- panel izquierdo: contenido del PDF (sincronizador)
    log = _note(f.panel_log)
    col = QVBoxLayout(log)
    col.setContentsMargins(16, 14, 16, 12)
    col.setSpacing(6)
    title = f.groupBox1
    pdf_title = QLabel("Contenido del PDF")
    pdf_title.setProperty("noteTitle", True)
    col.addWidget(pdf_title)
    f.checkBox1.setText("Mostrar figuras sobre la hoja")
    col.addWidget(f.checkBox1)
    f.labelMarcadoresPDF.setText("Marcadores")
    f.comentariosPDF.setText("Comentarios")
    for label in (f.labelMarcadoresPDF, f.comentariosPDF):
        label.setProperty("noteHint", True)
    col.addWidget(f.labelMarcadoresPDF)
    col.addWidget(f.listBox1, 1)
    col.addWidget(_action(f.buttonEliminarMarcador2, "Eliminar marcador", "danger"))
    col.addWidget(f.comentariosPDF)
    col.addWidget(f.listBox2, 1)
    col.addWidget(_action(f.buttonEliminarComentario2, "Eliminar comentario", "danger"))
    title.setParent(f.spare)

    # --- historial
    history = _note(f.historyLogPanel)
    col = QVBoxLayout(history)
    col.setContentsMargins(16, 14, 12, 12)
    col.setSpacing(8)
    f.label1.setText("Búsquedas recientes")
    f.label1.setProperty("noteTitle", True)
    col.addWidget(f.label1)
    f.fl_busquedasRecientes.setStyleSheet("QScrollArea{background:transparent;border:none;}"
                                          "QWidget#flowInner{background:transparent;}")
    col.addWidget(f.fl_busquedasRecientes, 1)

    # --- tarjeta del sincronizador (columna derecha)
    sync = _note(f.add("syncCard", QFrame()))
    col = QVBoxLayout(sync)
    col.setContentsMargins(16, 12, 16, 12)
    col.setSpacing(8)
    sync_title = QLabel("Sincronización con el PDF")
    sync_title.setProperty("noteTitle", True)
    col.addWidget(sync_title)
    _action(f.backPageButton2, "", "secondary", "chevron-left").setFixedWidth(44)
    _action(f.nextPageButton2, "", "secondary", "chevron-right").setFixedWidth(44)
    f.syncPDFLabel.setText("Página 1 de 1")
    f.syncPDFLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
    col.addLayout(hbox(f.backPageButton2, f.syncPDFLabel, f.nextPageButton2))
    f.searchTextBox.setPlaceholderText("Número de página o texto a buscar")
    f.searchTextBox.setFixedHeight(36)
    f.searchTextBox.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    f.searchTextBox.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    col.addLayout(hbox(f.searchTextBox, _action(f.btnSearchPages2, "Buscar", "primary", "search")))
    f.Pages.setText("Aparece en las páginas:")
    f.Pages.setProperty("noteHint", True)
    f.PagesLabel.setText("—")
    col.addLayout(hbox(f.Pages, f.PagesLabel, None))
    sync.hide()

    _action(f.markButton, "Ocultar marcas", "projection", "crosshair")

    for name, (x, y, w, h) in PROJECTION_GEOMETRY.items():
        widget = f.controls[name]
        widget.setParent(root)
        widget.setGeometry(x, y, w, h)
    caption.setParent(root)
    caption.setGeometry(372, 0, 200, 14)
    caption.hide()                                  # el campo ya lo dice con su texto de ayuda
    # Visibilidad inicial (igual que el original): servicios y herramientas del PDF ocultos
    for name in ("btn_diccionario", "btn_traductor", "btn_enciclopedia", "btn_video", "btn_imagen", "syncButton",
                 "buttonPDF", "buttonMarker", "buttonComments", "buttonFiguresPD", "panel3", "panel2", "historyLogPanel",
                 "panel_log"):
        f[name].setVisible(False)
    for name in ("rtb_result_definicion_traduccion", "lbl_datoBuscado_trad_def", "btn_leerDefinicionTraduccion",
                 "btn_cerrarVentanaIzquierda", "rtb_ResultadosWikipedia", "lbl_PalabraBuscada", "btn_leerEnciclopedia",
                 "btn_cerrarVentanaDerecha", "btn_nav_atras", "btn_nav_adelante"):
        f[name].setVisible(False)
    for name in ("pictureBox3", "pictureBox4", "pictureBox5"):
        f[name].setPixmap(theme.target_pixmap(60))
        f[name].setScaledContents(False)
        f[name].setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)


ARRANGE: dict[str, Callable[[ModernForm, QWidget], None]] = {
    "SeleccionInteraccionPorVoz2": arrange_interactions,
    "SeleccionApis2": arrange_web,
    "EyeTrackingConfiguration2": arrange_eye,
    "TextRecognitionSettings": arrange_text,
    "GestureRecognitionSettings": arrange_gesture,
    "PageDetectionSettings": arrange_page,
    "MenuSettings": arrange_menu,
    "AlertBox": arrange_alert,
    "LoadingBox": arrange_loading,
    "busquedasRecientes2": arrange_recent,
    "ProjectionScreenActivity2": arrange_projection,
}
