# Interfaz de realidad aumentada proyectada sobre el escritorio (ProjectionScreenActivity2.cs).
# Flujo: resaltar en el área blanca → OCR o captura → búsqueda con el LLM o sincronización con el PDF.
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QObject, QPoint, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QGuiApplication, QTextCursor, QTextListFormat
from PySide6.QtWidgets import QApplication, QWidget

from ui.context import AppContext
from ui.dialogs import AlertBox, LoadingBox, message
from ui import theme
from ui.modern_forms import build_modern
from ui.projection_widgets import FiguresOverlay, HighlightTool, LineCanvas, RecentSearchItem

logger = logging.getLogger(__name__)
PROJECT_DIR = Path(__file__).resolve().parents[1]

LEFT_SERVICES = ("btn_diccionario", "btn_traductor")
RIGHT_SERVICES = ("btn_enciclopedia", "btn_video", "btn_imagen")
VOICE_TARGETS = ["Video", "Enciclopedia", "Traducción", "Definición", "Imagen"]
MOBILE_UA = ("Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) "
             "Chrome/59.0.3071.125 Mobile Safari/537.36")


class _VoiceBridge(QObject):
    command = Signal(str)


class ProjectionScreen(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint)
        self.ctx = ctx
        self.setObjectName("ProjectionScreenActivity2")
        self.setWindowTitle("AR")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.form = build_modern("ProjectionScreenActivity2", self)
        self.setStyleSheet(theme.PROJECTION_QSS)
        self.setFixedSize(1300, 740)
        f = self.form
        self.concepto_buscar = ""                   # conceptoBuscar
        self.n_page, self.n_pages = 1, 1
        self.mark_point = False
        self.web_active = False                      # webSearchButtonActived
        self.sync_active = False                     # syncronizerButtonActived
        self.lado_busqueda: Optional[str] = None
        self.csv_lines = ["FECHA Y HORA ; PALABRA BUSCADA ; API UTILIZADA"]
        self.csv_path = PROJECT_DIR / "CSV_registro_actividades" / "log_actividades.csv"
        self.figures_overlay: Optional[FiguresOverlay] = None
        self.browser = None
        self._loading: Optional[LoadingBox] = None
        self._drag_from: Optional[QPoint] = None
        self._started = False

        # HighlightTool(30, 517, 400) en (285, 65), al frente
        self.highlight = HighlightTool(30, 517, 400, self)
        self.highlight.move(285, 65)
        self.highlight.raise_()
        self.highlight.on_first_click = self.first_click
        self.highlight.on_num_clicks = self.button_action

        self.left_lines = LineCanvas(f.leftLinePanel)
        self.right_lines = LineCanvas(f.rightLinePaper)
        f.panel_log.setVisible(False)
        self._show_mode()
        f.textBox1.textChanged.connect(self._concept_edited)
        self._wire()
        self.alert = AlertBox(self)
        self._voice = _VoiceBridge()
        self._voice.command.connect(self.voice_command)
        ctx.runtime.cycle.connect(self._on_cycle)

    # ------------------------------------------------------------------ conexiones
    def _wire(self) -> None:
        f = self.form
        f.markButton.clicked.connect(self.toggle_marks)
        f.textImageButton.clicked.connect(self.toggle_mode)
        f.btn_buscarWeb.clicked.connect(self.toggle_web_search)
        f.btn_sincronizadorPdf.clicked.connect(self.toggle_synchronizer)
        f.btn_enciclopedia.clicked.connect(self.search_encyclopedia)
        f.btn_video.clicked.connect(self.search_video)
        f.btn_traductor.clicked.connect(self.search_translation)
        f.btn_diccionario.clicked.connect(self.search_definition)
        f.btn_imagen.clicked.connect(self.search_image)
        f.btn_cerrarVentanaDerecha.clicked.connect(self.close_right)
        f.btn_cerrarVentanaIzquierda.clicked.connect(self.close_left)
        f.btn_leerDefinicionTraduccion.clicked.connect(lambda: self.read_aloud(f.rtb_result_definicion_traduccion))
        f.btn_leerEnciclopedia.clicked.connect(lambda: self.read_aloud(f.rtb_ResultadosWikipedia))
        f.btn_nav_atras.clicked.connect(lambda: self.browser and self.browser.back())
        f.btn_nav_adelante.clicked.connect(lambda: self.browser and self.browser.forward())
        f.btn_drawMenu.clicked.connect(self.toggle_history)
        f.btn_turnOFF.clicked.connect(self.turn_off)
        f.syncButton.clicked.connect(self.sync_highlight)
        f.nextPageButton2.clicked.connect(lambda: self.change_page(+1))
        f.backPageButton2.clicked.connect(lambda: self.change_page(-1))
        f.btnSearchPages2.clicked.connect(self.search_pages)
        f.buttonPDF.clicked.connect(self.load_pdf_content)
        f.buttonEliminarMarcador2.clicked.connect(self.delete_bookmark)
        f.buttonEliminarComentario2.clicked.connect(self.delete_comment)
        f.checkBox1.toggled.connect(self.toggle_figures)
        f.buttonMarker.clicked.connect(lambda: self.physical_sync("sync_bookmark_from_frame"))
        f.buttonComments.clicked.connect(lambda: self.physical_sync("sync_comments_from_frame"))
        f.buttonFiguresPD.clicked.connect(lambda: self.physical_sync("sync_figures_from_frame"))

    # ------------------------------------------------------------------ arranque (Form2_Load)
    def start(self) -> None:
        pages = self.ctx.pages
        voice, buttons = pages["interactions"].voice_enabled, pages["interactions"].show_buttons
        self.form.btn_buscarWeb.setVisible(not voice or buttons)
        if voice and not self._started:
            self.start_voice()
        consistency = self.ctx.runtime.plugin("ConsistencyProvider")
        if consistency is not None and consistency.execute().get("document_loaded"):
            size = self.ctx.runtime.invoke("ConsistencyProvider", "get_page_size")
            if size.ok:
                self.highlight.page_size = size.value
        if not self._started:
            screen = QGuiApplication.screens()[-1].availableGeometry()   # el proyector suele ser la última pantalla
            self.move(screen.center() - self.rect().center())
        self._started = True
        self.show()
        self.raise_()

    def _ensure_browser(self):
        # ChromiumWebBrowser (CefSharp) → QWebEngineView con el mismo user agent móvil.
        if self.browser is not None:
            return self.browser
        try:
            from PySide6.QtWebEngineCore import QWebEngineProfile
            from PySide6.QtWebEngineWidgets import QWebEngineView
        except ImportError:
            logger.warning("QtWebEngine no disponible: los videos e imágenes se abrirán en el navegador del sistema.")
            return None
        view = QWebEngineView(self.form.panel_navegador)
        view.page().profile().setHttpUserAgent(MOBILE_UA)
        self.form.panel_navegador.layout().addWidget(view)
        view.setVisible(False)
        self.browser = view
        return view

    def _load_url(self, url: str) -> None:
        browser = self._ensure_browser()
        if browser is None:
            QDesktopServices.openUrl(QUrl(url))
            return
        browser.setVisible(True)
        browser.raise_()
        browser.load(QUrl(url))

    # ------------------------------------------------------------------ resaltado / captura
    def toggle_marks(self) -> None:
        # button1_Click: muestra/oculta las cruces de calibración.
        for name in ("pictureBox3", "pictureBox4", "pictureBox5"):
            if self.mark_point:
                self.form[name].setPixmap(theme.target_pixmap(60))
            else:
                self.form[name].clear()
        self.mark_point = not self.mark_point

    def toggle_mode(self) -> None:
        # button3_Click: alterna modo resaltado (OCR) / modo captura (imagen).
        self.highlight.highlight_on = not self.highlight.highlight_on
        self._show_mode()
        self.highlight.update()
        self.capture_text(update_concept=False)

    def _show_mode(self) -> None:
        # El botón dice el modo actual (P-07 mostraba la imagen del modo al que se cambiaba).
        button = self.form.textImageButton
        if self.highlight.highlight_on:
            button.configure("highlighter", "Resaltando")
            button.setToolTip("Modo resaltado: lo que marques se lee con OCR. Pulsa para capturar una imagen.")
        else:
            button.configure("scan", "Capturando")
            button.setToolTip("Modo captura: lo que marques se recorta como imagen. Pulsa para resaltar texto.")
        button.set_active(self.highlight.highlight_on)

    def toast_anchor(self) -> tuple[int, int]:
        # Avisos bajo la zona de lectura, centrados, sin tapar el libro ni los paneles.
        return 285 + 517 // 2 + 180, 562

    def _mark_service(self, active: Optional[str], group: tuple[str, ...]) -> None:
        # Reemplaza las líneas guía del original: el servicio que respondió queda encendido.
        for name in group:
            self.form[name].set_active(name == active)

    def _gesture(self):
        name = self.ctx.active_gesture
        plugin = self.ctx.runtime.plugin(name) if name else None
        return plugin if plugin is not None and plugin.recognition_active else None

    def first_click(self) -> None:
        # FirstClick → recGestual.FinalToRectXY().
        gesture = self._gesture()
        if gesture is not None:
            gesture.mark_selection_start()

    def button_action(self) -> None:
        # ButtonAction: al terminar un resaltado (OCR) o una captura de imagen.
        if self.highlight.highlight_on:
            self.capture_text(update_concept=True)
            return
        gesture = self._gesture()
        if gesture is not None and gesture.auto_cam_capture:
            gesture_page = self.ctx.pages["gesture"]
            if not gesture_page.form.checkBoxMouse.isChecked():
                gesture.mark_selection_end()
            gesture_page.show_capture(gesture.capture_selection())

    def capture_text(self, update_concept: bool) -> None:
        # CaptureTxt + OCRProcess.TransformImage sobre la cámara de texto.
        def done(result) -> None:
            if not result.ok:
                if update_concept:
                    message(self, f"OCRProcess Resaltado: {result.error}")
                return
            self.ctx.pages["text"].show_recognition(result.value)
            if update_concept:
                text = result.value.get("text", "")
                self.form.textBox1.setPlainText(re.sub(r"\s*\n\s*", " ", text).strip())
                if result.value.get("box") is None:
                    self.form.textBox1.setPlaceholderText("No se detectó un resaltado en la cámara de texto")
        self.ctx.runtime.run_async("ImageProcessor", "recognize_highlighted_text", callback=done)

    def _concept_edited(self) -> None:
        # El lector puede corregir el texto reconocido antes de buscar.
        self.concepto_buscar = " ".join(self.form.textBox1.toPlainText().split())

    # ------------------------------------------------------------------ menús
    def toggle_web_search(self) -> None:
        f = self.form
        self.left_lines.clear()
        self.right_lines.clear()
        self.web_active = not self.web_active
        f.btn_buscarWeb.set_active(self.web_active)
        for name in ("btn_diccionario", "btn_enciclopedia", "btn_traductor", "btn_video", "btn_imagen"):
            f[name].setVisible(self.web_active)
        if self.web_active and self.sync_active:
            self._set_sync_tools(False)

    def toggle_synchronizer(self) -> None:
        self.left_lines.clear()
        self.right_lines.clear()
        self._set_sync_tools(not self.sync_active)
        if self.sync_active and self.form.panel2.isVisible():
            self.close_right()                      # un solo panel por lado: la tarjeta del PDF ocupa la derecha
        if self.sync_active and self.web_active:
            self.web_active = True
            self.toggle_web_search()

    def _set_sync_tools(self, on: bool) -> None:
        f = self.form
        self.sync_active = on
        f.panel_log.setVisible(on)
        if on:
            f.panel_log.raise_()
        f.btn_sincronizadorPdf.set_active(on)
        f.syncCard.setVisible(on)
        if on:
            f.syncCard.raise_()
        for name in ("buttonMarker", "buttonComments", "buttonFiguresPD", "buttonPDF", "syncButton", "backPageButton2",
                     "nextPageButton2", "btnSearchPages2", "searchTextBox", "syncPDFLabel", "Pages", "PagesLabel"):
            f[name].setVisible(on)

    def toggle_history(self) -> None:
        panel = self.form.historyLogPanel
        panel.setVisible(not panel.isVisible())
        f = self.form
        f.btn_drawMenu.set_active(panel.isVisible())
        if panel.isVisible():
            panel.raise_()

    # ------------------------------------------------------------------ búsquedas (LLM)
    def _provider(self, service: str) -> Optional[str]:
        return self.ctx.pages["web"].provider_for(service)

    def _record(self, term: str, service: str) -> None:
        # busquedasRecientes2 + línea del CSV de actividades.
        stamp = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        layout = self.form.fl_busquedasRecientes.property("flow_layout")
        layout.insertWidget(layout.count() - 1, RecentSearchItem(stamp, term, service))
        self.csv_lines.append(f"{stamp} ; {term} ; {service}")

    def _loading_show(self, side: str) -> None:
        self.lado_busqueda = side
        self._loading_close()
        self._loading = LoadingBox(self, side, background="#ffffff").show_loading()

    def _loading_close(self) -> None:
        if self._loading is not None:
            self._loading.close()
            self._loading = None

    def _run_search(self, service: str, method: str, args: tuple, side: str,
                    on_ok: Callable, missing_api: str) -> None:
        provider = self._provider(service)
        if not provider:
            message(self, missing_api)
            return
        self._loading_show(side)

        def done(result) -> None:
            self._loading_close()
            if result.ok:
                on_ok(result.value)
            else:
                on_ok(None, result.error)
        self.ctx.runtime.run_async(provider, method, *args, callback=done)

    def search_encyclopedia(self) -> None:
        f = self.form
        self.right_lines.clear()
        f.panel2.setVisible(True)
        f.panel2.raise_()
        self._close_browser()
        f.btn_cerrarVentanaDerecha.setVisible(True)
        f.rtb_ResultadosWikipedia.clear()
        f.lbl_PalabraBuscada.setVisible(True)
        f.rtb_ResultadosWikipedia.setVisible(True)
        f.btn_leerEnciclopedia.setVisible(True)
        self._hide_sync_card()
        self._mark_service("btn_enciclopedia", RIGHT_SERVICES)
        term = self.concepto_buscar
        if not term.strip():
            f.rtb_ResultadosWikipedia.setPlainText("Seleccione un término para buscar")
            return
        self._record(term, "Enciclopedia")
        f.lbl_PalabraBuscada.setText(term)

        def show(value, error=None) -> None:
            if value is None:
                f.rtb_ResultadosWikipedia.setPlainText(f"Problema detectado: {error}")
                return
            for paragraph in [p.strip() for p in value.content.split("\n\n") if p.strip()]:
                f.rtb_ResultadosWikipedia.append("\n" + paragraph)
            self.right_lines.draw((356, 45, 330, 45), (330, 45, 330, 170), (330, 170, 43, 170), (43, 170, 43, 163))
        self._run_search("encyclopedia", "search_encyclopedia", (term,), "derecha", show,
                         "Elige quién responde la enciclopedia en «Servicios de búsqueda».")

    def search_video(self) -> None:
        f = self.form
        self.right_lines.clear()
        f.panel2.setVisible(True)
        f.panel2.raise_()
        f.btn_leerEnciclopedia.setVisible(False)
        self._hide_sync_card()
        self._mark_service("btn_video", RIGHT_SERVICES)
        term = self.concepto_buscar
        f.lbl_PalabraBuscada.setVisible(True)
        f.lbl_PalabraBuscada.setText("Video: " + term)
        f.rtb_ResultadosWikipedia.setVisible(False)
        if not term.strip():
            message(self, "Seleccione un término para buscar en video")
            self._load_url("https://m.youtube.com")
            return
        for name in ("btn_nav_adelante", "btn_nav_atras", "btn_cerrarVentanaDerecha"):
            f[name].setVisible(True)
        self._record(term, "Video")

        def show(value, error=None) -> None:
            if value is None:
                message(self, f"No se pudo buscar el video: {error}")
                return
            self._load_url(value.url)
            self.right_lines.draw((356, 45, 330, 45), (330, 45, 330, 170), (330, 170, 129, 170), (129, 170, 129, 163))
        self._run_search("video", "search_video", (term,), "derecha", show,
                         "Elige quién responde la búsqueda de video en «Servicios de búsqueda».")

    def search_translation(self) -> None:
        f = self.form
        self.left_lines.clear()
        f.panel_log.setVisible(False)
        f.panel3.setVisible(True)
        f.panel3.raise_()
        f.rtb_result_definicion_traduccion.setVisible(True)
        f.rtb_result_definicion_traduccion.clear()
        f.btn_cerrarVentanaIzquierda.setVisible(True)
        f.btn_leerDefinicionTraduccion.setVisible(True)
        self._mark_service("btn_traductor", LEFT_SERVICES)
        term = self.concepto_buscar
        if not term.strip():
            f.rtb_result_definicion_traduccion.setPlainText("Seleccione un término para traducir")
            return
        f.lbl_datoBuscado_trad_def.setVisible(True)
        f.lbl_datoBuscado_trad_def.setText(term)
        self._record(term, "Traductor")
        language = self.ctx.pages["web"].target_language

        def show(value, error=None) -> None:
            if value is None:
                f.rtb_result_definicion_traduccion.setPlainText(f"No se pudo traducir: {error}")
                return
            f.rtb_result_definicion_traduccion.setPlainText(value.content)
            self.left_lines.draw((118, 3, 118, 170), (118, 170, 481, 170), (481, 170, 481, 163))
        self._run_search("translation", "translate_text", (term, language), "izquierda", show,
                         "Seleccione una api para búsqueda en traductor.")

    def search_definition(self) -> None:
        f = self.form
        self.left_lines.clear()
        f.panel_log.setVisible(False)
        f.panel3.setVisible(True)
        f.panel3.raise_()
        for name in ("btn_cerrarVentanaIzquierda", "lbl_datoBuscado_trad_def", "rtb_result_definicion_traduccion",
                     "btn_leerDefinicionTraduccion"):
            f[name].setVisible(True)
        f.rtb_result_definicion_traduccion.clear()
        self._mark_service("btn_diccionario", LEFT_SERVICES)
        term = self.concepto_buscar
        f.lbl_datoBuscado_trad_def.setText(term)
        if not term:
            f.rtb_result_definicion_traduccion.setPlainText("Seleccione un término para buscar")
            return
        self._record(term, "Diccionario")

        def show(value, error=None) -> None:
            rtb = f.rtb_result_definicion_traduccion
            if value is None:
                rtb.setPlainText("No se ha podido encontrar la palabra buscada")
                return
            cursor = rtb.textCursor()
            list_format = QTextListFormat()
            list_format.setStyle(QTextListFormat.Style.ListDisc)          # SelectionBullet = true
            cursor.insertList(list_format)
            lines = [line.strip(" -•\t") for line in value.content.splitlines() if line.strip()]
            for index, line in enumerate(lines):
                if index:
                    cursor.insertBlock()
                cursor.insertText(line)
            rtb.moveCursor(QTextCursor.MoveOperation.Start)
            self.left_lines.draw((118, 3, 118, 170), (118, 170, 386, 170), (386, 170, 386, 163))
        self._run_search("definition", "search_definition", (term,), "izquierda", show,
                         "Seleccionar Api para busqueda de definición")

    def search_image(self) -> None:
        f = self.form
        self.right_lines.clear()
        f.panel2.setVisible(True)
        f.panel2.raise_()
        f.btn_leerEnciclopedia.setVisible(False)
        self._hide_sync_card()
        self._mark_service("btn_imagen", RIGHT_SERVICES)
        image = self.ctx.capture_jpeg
        if image is None:
            message(self, "Seleccione una imagen para buscar")
            return
        for name in ("btn_cerrarVentanaDerecha", "btn_nav_adelante", "btn_nav_atras"):
            f[name].setVisible(True)
        f.rtb_ResultadosWikipedia.setVisible(False)

        def show(value, error=None) -> None:
            if value is None:
                message(self, f"No se pudo reconocer la imagen: {error}")
                return
            f.lbl_PalabraBuscada.setVisible(True)
            f.lbl_PalabraBuscada.setText(value.content)
            self._record(value.content, "Imagen")
            self._load_url(value.url)
            self.right_lines.draw((356, 45, 330, 45), (330, 45, 330, 170), (330, 170, 216, 170), (216, 170, 216, 163))
        self._run_search("image", "search_image", (image,), "derecha", show,
                         "Seleccione una api para búsqueda por imagen.")

    def _hide_sync_card(self) -> None:
        if self.sync_active:
            self.form.syncCard.setVisible(False)

    def _close_browser(self) -> None:
        if self.browser is not None:
            self.browser.setVisible(False)
        for name in ("btn_nav_adelante", "btn_nav_atras"):
            self.form[name].setVisible(False)

    def close_right(self) -> None:
        # btn_cerrarVentanaDerecha: cierra enciclopedia, video e imagen.
        f = self.form
        self.right_lines.clear()
        f.panel2.setVisible(False)
        f.rtb_ResultadosWikipedia.setVisible(False)
        f.rtb_ResultadosWikipedia.clear()
        f.lbl_PalabraBuscada.setVisible(False)
        f.btn_cerrarVentanaDerecha.setVisible(False)
        f.btn_leerEnciclopedia.setVisible(False)
        self._close_browser()
        self._stop_speaking()
        self._mark_service(None, RIGHT_SERVICES)
        if self.sync_active:
            self.form.syncCard.setVisible(True)

    def close_left(self) -> None:
        f = self.form
        self.left_lines.clear()
        for name in ("rtb_result_definicion_traduccion", "lbl_datoBuscado_trad_def", "btn_cerrarVentanaIzquierda",
                     "btn_leerDefinicionTraduccion"):
            f[name].setVisible(False)
        f.rtb_result_definicion_traduccion.clear()
        f.panel3.setVisible(False)
        self._stop_speaking()
        self._mark_service(None, LEFT_SERVICES)
        if self.sync_active:
            f.panel_log.setVisible(True)

    # ------------------------------------------------------------------ voz
    def read_aloud(self, widget) -> None:
        result = self.ctx.runtime.invoke("SpeechProvider", "speak", widget.toPlainText())
        if not result.ok:
            message(self, result.error or "La lectura en voz alta no está disponible.")

    def _stop_speaking(self) -> None:
        if self.ctx.runtime.plugin("SpeechProvider") is not None:
            self.ctx.runtime.invoke("SpeechProvider", "stop_speaking")

    def start_voice(self) -> None:
        # iniciarVR: gramática Buscar|Lectura|Cerrar + Video|Enciclopedia|Traducción|Definición|Imagen.
        commands = [f"{verb} {target}" for verb in ("Buscar", "Lectura", "Cerrar") for target in VOICE_TARGETS]
        result = self.ctx.runtime.invoke("SpeechProvider", "start_listening", commands, self._voice.command.emit)
        if not result.ok:
            message(self, result.error or "No hay reconocedor de voz instalado.", "Error")

    def voice_command(self, command: str) -> None:
        f = self.form
        actions = {
            "Cerrar Enciclopedia": self.close_right, "Cerrar Video": self.close_right,
            "Cerrar Imagen": self.close_right, "Cerrar Definición": self.close_left,
            "Cerrar Traducción": self.close_left,
            "Lectura Definición": lambda: self.read_aloud(f.rtb_result_definicion_traduccion),
            "Lectura Traducción": lambda: self.read_aloud(f.rtb_result_definicion_traduccion),
            "Lectura Enciclopedia": lambda: self.read_aloud(f.rtb_ResultadosWikipedia),
            "Buscar Traducción": self.search_translation, "Buscar Definición": self.search_definition,
            "Buscar Video": self.search_video, "Buscar Enciclopedia": self.search_encyclopedia,
            "Buscar Imagen": self.search_image,
        }
        action = actions.get(command)
        if action:
            action()

    # ------------------------------------------------------------------ PDF (consistencia)
    def _pdf_loaded(self) -> bool:
        plugin = self.ctx.runtime.plugin("ConsistencyProvider")
        if plugin is None or not plugin.execute().get("document_loaded"):
            message(self, "Primero elige el PDF del libro en «Documento PDF».", "Problema")
            return False
        return True

    def _page_from_box(self) -> Optional[int]:
        text = self.form.searchTextBox.text().strip()
        if not text.isdigit():
            message(self, "Escribe el número de página en la tarjeta de sincronización.", "Problema")
            return None
        return int(text)

    def _refresh_highlights(self) -> None:
        result = self.ctx.runtime.invoke("ConsistencyProvider", "get_annotations", self.n_page)
        if result.ok:
            self.highlight.set_page_rectangles([(a.x0, a.y0, a.x1, a.y1) for a in result.value])

    def sync_highlight(self) -> None:
        # syncPdfButton_Click: guarda el resaltado actual en la página n del PDF.
        if not self._pdf_loaded():
            return
        from contracts.i_consistency_provider import Annotation
        selection = self.highlight.normalized_selection()
        runtime = self.ctx.runtime
        if selection is not None:
            x0, y0, x1, y1 = selection
            text = self.concepto_buscar
            result = runtime.invoke("ConsistencyProvider", "add_highlight",
                                    Annotation(self.n_page, x0, y0, x1, y1, "highlight", text))
            if not result.ok:
                message(self, result.error, "Problem found")
        self.n_pages = runtime.invoke("ConsistencyProvider", "get_page_count").value or 1
        self._refresh_highlights()
        self._update_sync_label()

    def _update_sync_label(self) -> None:
        self.form.syncPDFLabel.setText(f"Página {self.n_page} de {self.n_pages}")
        self.form.syncPDFLabel.setVisible(True)

    def change_page(self, step: int) -> None:
        count = self.ctx.runtime.invoke("ConsistencyProvider", "get_page_count")
        if count.ok:
            self.n_pages = count.value
        self.n_page = min(max(1, self.n_page + step), self.n_pages)
        self._update_sync_label()
        if count.ok:
            self._refresh_highlights()

    def search_pages(self) -> None:
        if not self._pdf_loaded():
            return
        result = self.ctx.runtime.invoke("ConsistencyProvider", "search_text", self.form.searchTextBox.text())
        self.form.PagesLabel.setText(", ".join(str(p) for p in result.value or []) or "ninguna")

    def load_pdf_content(self) -> None:
        # buttonPDF_Click (Content, digital → papel): figuras, marcadores y comentarios.
        if not self._pdf_loaded():
            return
        page = self._page_from_box()
        if page is None:
            return
        f, runtime = self.form, self.ctx.runtime
        f.listBox1.clear()
        f.listBox2.clear()
        figures = runtime.invoke("ConsistencyProvider", "get_figures", page, (400, 450))
        if not figures.ok:
            message(self, figures.error, "Problem found")
            return
        if self.figures_overlay is not None:
            self.figures_overlay.deleteLater()
        self.figures_overlay = FiguresOverlay(figures.value, self)
        self.figures_overlay.move(285, 65)
        self.figures_overlay.show()
        self.figures_overlay.raise_()
        f.checkBox1.blockSignals(True)
        f.checkBox1.setChecked(True)
        f.checkBox1.blockSignals(False)
        f.checkBox1.setStyleSheet(f"QCheckBox{{color:{theme.OK};}}")
        f.listBox1.addItems(runtime.invoke("ConsistencyProvider", "get_bookmarks").value or [])
        comments = runtime.invoke("ConsistencyProvider", "get_comments").value or []
        f.listBox2.addItems([f"{c['content']} Pag.{c['page']}" for c in comments])
        f.buttonEliminarMarcador2.setEnabled(f.listBox1.count() > 0)
        f.buttonEliminarComentario2.setEnabled(f.listBox2.count() > 0)

    def toggle_figures(self, _checked: bool) -> None:
        if self.figures_overlay is None:
            message(self, "Primero proyecta el contenido del PDF con «Mostrar contenido».", "Problem found")
            return
        visible = not self.figures_overlay.isVisible()
        self.figures_overlay.setVisible(visible)
        self.form.checkBox1.setStyleSheet(f"QCheckBox{{color:{theme.OK if visible else theme.PELIGRO};}}")

    def delete_bookmark(self) -> None:
        item = self.form.listBox1.currentItem()
        if item is None:
            message(self, "No esta seleccionado")
            return
        message(self, "Item " + item.text())
        result = self.ctx.runtime.invoke("ConsistencyProvider", "delete_bookmark", item.text())
        if result.ok and result.value:
            message(self, "Marcador eliminado")
            self.form.listBox1.takeItem(self.form.listBox1.row(item))
        else:
            message(self, "No se pudo completar la operación")

    def delete_comment(self) -> None:
        item = self.form.listBox2.currentItem()
        if item is None:
            message(self, "No esta seleccionado")
            return
        match = re.match(r"^(.*) Pag\.(\d+)$", item.text())
        if match:
            self.ctx.runtime.invoke("ConsistencyProvider", "delete_comment", match.group(1), int(match.group(2)))
        message(self, "Comentario " + item.text() + " eliminado")
        self.form.listBox2.takeItem(self.form.listBox2.row(item))

    def physical_sync(self, method: str) -> None:
        # buttonMarker / buttonComments / buttonFiguresPD (papel → digital).
        if not self._pdf_loaded():
            return
        page = self._page_from_box()
        if page is None:
            return
        camera = self.ctx.runtime.plugin("TextCamera")
        frame = camera.capture_frame() if camera is not None else None
        if frame is None:
            message(self, "La cámara de reconocimiento de texto no entrega imágenes.", "Problem found")
            return
        texts = {
            "sync_bookmark_from_frame": ("Se sincronizó correctamente", "No se encontró marcador"),
            "sync_comments_from_frame": ("Se sincronizó el comentario", "No se encontró comentario para sincronizar"),
            "sync_figures_from_frame": ("Figuras sincronizadas", "No se encontraron figuras"),
        }[method]

        def done(result) -> None:
            if not result.ok:
                message(self, result.error, "Problem found")
                return
            if method == "sync_bookmark_from_frame" and result.value:
                with open(PROJECT_DIR / "logs" / "TiempoMarcadorFisico.txt", "a", encoding="utf-8") as log:
                    log.write(f"MarkerPD;{result.latency_ms} ms\n")
            message(self, texts[0] if result.value else texts[1])
        self.ctx.runtime.run_async("ConsistencyProvider", method, frame, page, callback=done)

    # ------------------------------------------------------------------ ventana
    def turn_off(self) -> None:
        if self.alert.ask("¿Cerrar EDDIE?", "Se cerrará la proyección y la ventana de configuración.",
                          confirm=True, over=self, confirm_text="Cerrar EDDIE"):
            QApplication.instance().quit()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_from = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_from is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_from)

    def mouseReleaseEvent(self, _event) -> None:
        self._drag_from = None

    def write_activity_log(self) -> None:
        # ProjectionScreenActivity_FormClosing: agrega las búsquedas de la sesión al CSV.
        if len(self.csv_lines) <= 1:
            return
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("a", encoding="utf-8") as stream:
            stream.write("\n".join(self.csv_lines) + "\n")
        self.csv_lines = self.csv_lines[:1]

    def closeEvent(self, event) -> None:
        self.write_activity_log()
        super().closeEvent(event)

    def _on_cycle(self, results: dict) -> None:
        pass
