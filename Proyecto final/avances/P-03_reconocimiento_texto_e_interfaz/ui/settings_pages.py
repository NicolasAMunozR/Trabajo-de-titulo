# Páginas de configuración embebidas en la ventana principal de EDDIE.
# Cada página reemplaza un formulario del C# (Interacción, Búsqueda, Eye tracking, Texto, Gestos y PDF).
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import (QAbstractButton, QCheckBox, QFileDialog, QLabel, QLineEdit, QSizePolicy, QToolTip,
                               QWidget)
from contracts.i_speech_provider import ISpeechProvider

from contracts.i_eye_tracker import IEyeTracker
from contracts.i_gesture_plugin import GestureCalibration, IGesturePlugin
from contracts.i_web_search_provider import IWebSearchProvider
from hardware.camera_enumeration import list_cameras
from ui.context import AppContext
from ui.dialogs import message
from ui.form_builder import ImageButton
from ui.modern_forms import build_modern
from ui.widgets import ActionButton, FitFrameView

logger = logging.getLogger(__name__)
PROJECT_DIR = Path(__file__).resolve().parents[1]


class SettingsPage(QWidget):
    LAYOUT = ""
    TOOLTIPS: dict[str, str] = {}

    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.setObjectName(self.LAYOUT)
        self.form = build_modern(self.LAYOUT, self)
        for control, text in self.TOOLTIPS.items():
            widget = self.form.controls.get(control)
            if widget is not None:
                widget.setToolTip(text)
                # Iconos de información: un clic muestra la ayuda. Los botones (p. ej. los "Browse" de
                # Eye tracking) ya tienen su propia acción y muestran la ayuda al pasar el mouse.
                # Ojo: clicked(bool) de un botón entrega "checked"; si la lambda tuviera w=widget como
                # primer parámetro, Qt lo reemplazaría por False ("bool has no attribute mapToGlobal").
                if hasattr(widget, "clicked") and not isinstance(widget, QAbstractButton):
                    widget.clicked.connect(lambda *_, w=widget, t=text: QToolTip.showText(
                        w.mapToGlobal(QPoint(0, w.height())), t, w))

    def load_settings(self) -> None:
        # GetAllSettings (parte correspondiente a esta página).
        pass

    def save_settings(self) -> None:
        # SaveAllSettings (parte correspondiente a esta página).
        pass

    def on_cycle(self, results: dict) -> None:
        # Actualización periódica (vistas de cámara, coordenadas del sensor).
        pass


# ---------------------------------------------------------------------------- cámaras
def _fill_cameras(combo) -> list[tuple[int, str]]:
    from orchestrator.device_factory import DeviceFactory
    if DeviceFactory.global_mode() == "sim":
        cameras = [(0, "Simulated camera 0 (page)"), (1, "Simulated camera 1 (pen)")]
    else:
        cameras = list_cameras()
    combo.blockSignals(True)
    combo.clear()
    for index, name in cameras:
        combo.addItem(name, index)
    combo.blockSignals(False)
    return cameras


class TextRecognitionPage(SettingsPage):
    LAYOUT = "TextRecognitionSettings"
    TOOLTIPS = {"pictureBox2": "Cámara que mira la página para el reconocimiento de texto (OCR).\n"
                               "No debe ser la misma que la de reconocimiento gestual."}

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        self._last_preview = 0.0
        self._hold_preview_until = 0.0
        _fill_cameras(self.form.ComboBoxCameraList1)
        self.form.ComboBoxCameraList1.currentIndexChanged.connect(self._camera_changed)
        self._add_recognition_controls()

    def _add_recognition_controls(self) -> None:
        # Controles nuevos: probar el OCR desde esta página y ver el texto reconocido.
        button = ActionButton("Reconocer texto", variant="primary", icon="scan-text")
        button.setObjectName("buttonRecognizeText")
        button.setToolTip("Detecta el resaltado amarillo en la cámara de texto y aplica OCR (Tesseract).")
        button.clicked.connect(self.recognize_now)
        box = QLineEdit()
        box.setObjectName("textBoxRecognized")
        box.setReadOnly(True)
        box.setPlaceholderText("Aquí aparece el texto reconocido")
        self.form.place("recognition", button, box)

    def recognize_now(self) -> None:
        if self.ctx.runtime.plugin("ImageProcessor") is None:
            message(self, "El reconocimiento de texto (ImageProcessor) no está activo.", "Problema")
            return
        self.form.textBoxRecognized.setText("Reconociendo…")

        def done(result) -> None:
            if not result.ok:
                self.form.textBoxRecognized.setText(f"Error: {result.error}")
                return
            self.show_recognition(result.value)

        self.ctx.runtime.run_async("ImageProcessor", "recognize_highlighted_text", callback=done)

    def load_settings(self) -> None:
        s, f = self.ctx.settings, self.form
        f.ComboBoxCameraList1.blockSignals(True)
        index = f.ComboBoxCameraList1.findData(s["cameraTextIndex"])
        if index < 0 and f.ComboBoxCameraList1.count():
            logger.warning("La cámara de texto %s no está conectada.", s["cameraTextIndex"])
        f.ComboBoxCameraList1.setCurrentIndex(index)
        f.ComboBoxCameraList1.blockSignals(False)
        f.numericUpDownResXText.setValue(int(s["cameraTextWidth"]))
        f.numericUpDownResYText.setValue(int(s["cameraTextHeight"]))

    def save_settings(self) -> None:
        s, f = self.ctx.settings, self.form
        if f.ComboBoxCameraList1.currentIndex() >= 0:
            s["cameraTextIndex"] = int(f.ComboBoxCameraList1.currentData())
        s["cameraTextWidth"] = f.numericUpDownResXText.value()
        s["cameraTextHeight"] = f.numericUpDownResYText.value()

    def _camera_changed(self) -> None:
        self.save_settings()

    def apply_camera(self) -> None:
        # Abre la cámara elegida si cambió (ProyectionActivityBt: new VideoCapture(CameraNumber)).
        self.save_settings()
        s, sensor = self.ctx.settings, self.ctx.runtime.plugin("TextCamera")
        wanted = {"camera_index": int(s["cameraTextIndex"]), "width": int(s["cameraTextWidth"]),
                  "height": int(s["cameraTextHeight"])}
        if sensor is None or getattr(sensor, "camera_index", None) != wanted["camera_index"]:
            self.ctx.runtime.restart("TextCamera", wanted)

    def show_recognition(self, result: dict) -> None:
        # imageBox1 = frame con el rectángulo; imageBox3 = recorte reconocido (TextImage); texto abajo.
        if result.get("annotated") is not None:
            self.form.imageBox1.show_frame(result["annotated"])
        crop = result.get("upright_crop") if result.get("upright_crop") is not None else result.get("crop")
        if crop is not None:                                   # recorte derecho, como lo lee el OCR
            self.form.imageBox3.show_frame(crop)
            self._hold_preview_until = time.monotonic() + 4.0     # que el recorte no lo tape la vista en vivo
        if result.get("box") is None:
            text = "No se encontró un resaltado amarillo en la imagen de la cámara."
        elif not result.get("ocr_available", True):
            text = "Resaltado detectado, pero Tesseract-OCR no está instalado (ver README)."
        else:
            text = result.get("text", "").strip() or "Resaltado detectado, pero el OCR no reconoció texto."
        self.form.textBoxRecognized.setText(text)

    def on_cycle(self, results: dict) -> None:
        if not self.isVisible() or time.monotonic() - self._last_preview < 1 / 15:   # 15 FPS como el C#
            return
        if time.monotonic() < self._hold_preview_until:
            return
        self._last_preview = time.monotonic()
        sensor = self.ctx.runtime.plugin("TextCamera")
        if sensor is not None:
            self.form.imageBox3.show_frame(sensor.get_latest_frame())


# ---------------------------------------------------------------------------- Page detection
class PageDetectionPage(SettingsPage):
    LAYOUT = "PageDetectionSettings"
    TOOLTIPS = {"pictureBox2": "PDF que se sincroniza con el libro físico."}

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        self.form.buttonModified1.clicked.connect(self.select_pdf)
        self.form.buttonModified2.clicked.connect(self.resize_highlight)
        self.form.textBoxPathPDF.setReadOnly(True)
        self._preview_page = 1
        self._page_count = 0
        self._add_preview_controls()

    PREVIEW_SIZE = (380, 420)                   # tamaño máximo con que se renderiza la página

    def _add_preview_controls(self) -> None:
        # Vista previa del PDF cargado (nueva: el C# solo mostraba la ruta y el tamaño de página).
        view = FitFrameView(placeholder="Elige un PDF para ver sus páginas")
        view.setObjectName("pdfPreview")
        view.setMinimumHeight(330)
        label = QLabel("Sin PDF")
        label.setObjectName("labelPreviewPage")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setProperty("field", True)
        previous = ActionButton("", variant="secondary", icon="chevron-left")
        following = ActionButton("", variant="secondary", icon="chevron-right")
        previous.setObjectName("buttonPreviewPrevious")
        following.setObjectName("buttonPreviewNext")
        for button in (previous, following):
            button.setFixedWidth(44)
        previous.clicked.connect(lambda: self.show_preview(self._preview_page - 1))
        following.clicked.connect(lambda: self.show_preview(self._preview_page + 1))
        from ui.widgets import hbox
        nav = QWidget()
        nav.setLayout(hbox(previous, label, following))
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.form.place("pdf_preview", view, nav)
        for name, widget in (("labelPreviewPage", label), ("buttonPreviewPrevious", previous),
                             ("buttonPreviewNext", following)):
            self.form.controls[name] = widget

    def show_preview(self, page: int) -> None:
        if not self._page_count:
            return
        page = max(1, min(self._page_count, page))
        w, h = self.PREVIEW_SIZE
        image = self.ctx.runtime.invoke("ConsistencyProvider", "render_page", page, w, h)
        if not image.ok:
            self.form.labelPreviewPage.setText("No se pudo mostrar")
            return
        self.form.pdfPreview.show_frame(image.value)
        self._preview_page = page
        self.form.labelPreviewPage.setText(f"Página {page} / {self._page_count}")

    def load_settings(self) -> None:
        path = self.ctx.settings["pdfPath"]
        consistency = self.ctx.runtime.plugin("ConsistencyProvider")
        if path and consistency is not None and getattr(consistency, "pdf_path", "") == path:
            self._show_document(path)

    def select_pdf(self) -> None:
        # PDFSelectBt_Click → new DigitalDocSync(file).
        path, _ = QFileDialog.getOpenFileName(self, "Elegir el PDF del libro", "", "PDF (*.pdf)")
        if path:
            self.open_pdf(path)

    def open_pdf(self, path: str) -> bool:
        result = self.ctx.runtime.invoke("ConsistencyProvider", "load_document", path)
        if not result.ok or not result.value:
            consistency = self.ctx.runtime.plugin("ConsistencyProvider")
            reason = result.error or getattr(consistency, "last_load_error", "") or path
            message(self, f"No se pudo abrir el PDF:\n{reason}", "Problema")
            return False
        self.ctx.settings["pdfPath"] = path
        self._show_document(path)
        return True

    def _show_document(self, path: str) -> None:
        self.form.textBoxPathPDF.setText(path)
        count = self.ctx.runtime.invoke("ConsistencyProvider", "get_page_count")
        self._page_count = count.value if count.ok else 0
        self.show_preview(1)
        size = self.ctx.runtime.invoke("ConsistencyProvider", "get_page_size")
        if size.ok:
            width, height = size.value
            self.form.numericUpDown5.setValue(int(width))
            self.form.numericUpDown6.setValue(int(height))
            if self.ctx.projection is not None:
                self.ctx.projection.highlight.page_size = (width, height)

    def resize_highlight(self) -> None:
        # Resize_Click → Highlight.RuntimeFinalLocation(FinalLocateX, FinalLocateY).
        if self.ctx.projection is not None:
            self.ctx.projection.highlight.runtime_final_location(self.form.FinalLocateX.value(),
                                                                 self.form.FinalLocateY.value())
