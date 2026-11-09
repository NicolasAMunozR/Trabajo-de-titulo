# Ventana principal de EDDIE (MenuSettings.cs), versión de avance para P-03, P-04 y P-05.
# Los módulos aún no integrados aparecen deshabilitados en el menú lateral con el avance en que llegan.
import importlib.util
import logging
import time
from typing import Optional

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtWidgets import QApplication, QGridLayout, QLabel, QStackedLayout, QVBoxLayout, QWidget

from contracts.i_web_search_provider import IWebSearchProvider
from ui.context import AppContext
from ui.dialogs import AlertBox, LoadingBox, message
from ui.modern_forms import build_modern
from ui import settings_pages
from ui.widgets import ActionButton, card, hint_label

logger = logging.getLogger(__name__)

NAV = {
    "InteractionsButton": "interactions",
    "WebSearchServicesButton": "web",
    "EyeTrackingButton": "eye",
    "TextRecognitiionButton": "text",
    "GestureRecognitionButton": "gesture",
    "PageDetectionButton": "page",
}
BUTTON_FOR = {key: button for button, key in NAV.items()}

# Página → (clase en ui/settings_pages.py, avance en que se integra)
PAGES = {
    "interactions": ("InteractionPage", "P-06"),
    "web": ("WebSearchPage", "P-06"),
    "eye": ("EyeTrackingPage", "P-05"),
    "text": ("TextRecognitionPage", "P-03"),
    "gesture": ("GestureRecognitionPage", "P-04"),
    "page": ("PageDetectionPage", "P-03"),
}


def projection_available() -> bool:
    return importlib.util.find_spec("ui.projection_screen") is not None


class MenuSettingsWindow(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint)
        self.ctx = ctx
        self.setObjectName("MenuSettings")
        self.setWindowTitle("EDDIE")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.form = build_modern("MenuSettings", self)
        self.setFixedSize(1280, 720)
        f = self.form

        # Instancias de cada formulario ya integrado (como en el constructor C#)
        ctx.pages = {key: getattr(settings_pages, cls)(ctx)
                     for key, (cls, _stage) in PAGES.items() if hasattr(settings_pages, cls)}
        for button_name, key in NAV.items():
            if key in ctx.pages:
                f[button_name].clicked.connect(lambda _=False, b=button_name: self.open_page(b))
            else:                                          # módulo aún no integrado en este avance
                f[button_name].set_pending(PAGES[key][1])
        f.HomeButton.clicked.connect(lambda: self.open_page(None))
        f.brandTitle.clicked.connect(lambda: self.open_page(None))

        self._stack = QStackedLayout(f.PanelContenido)
        self._stack.setContentsMargins(0, 0, 0, 0)
        self.home = SessionHome(self)
        self._empty = self.home
        self._stack.addWidget(self.home)
        for page in ctx.pages.values():
            self._stack.addWidget(page)

        f.ExitPictureBox.clicked.connect(self.exit_clicked)
        f.MinimizePictureBox.clicked.connect(self.showMinimized)
        f.SaveSettingsButtonModified.clicked.connect(self.save_clicked)
        f.ResetSettingsButtonModified.clicked.connect(self.reset_clicked)
        f.StartProjectionButtonModified.clicked.connect(self.start_projection)
        for drag_area in (f.PanelBarraSuperior, f.PanelNavBar):
            drag_area.installEventFilter(self)
        self._drag_from: QPoint | None = None
        self._last_status = 0.0
        self.alert = AlertBox(self)
        self.get_all_settings()
        self.open_page(None)
        self.refresh_status()
        self._status_timer = QTimer(self)
        self._status_timer.setInterval(1000)
        self._status_timer.timeout.connect(self.refresh_status)
        self._status_timer.start()
        ctx.runtime.cycle.connect(self._on_cycle)

    # ------------------------------------------------------------------ navegación
    def open_page(self, button_name: Optional[str]) -> None:
        # AbrirFormEnPanel: muestra la página y marca su botón; None abre «Preparar sesión».
        for name in NAV:
            self.form[name].set_selected(name == button_name)
        self.form.HomeButton.set_selected(button_name is None)
        if button_name is None:
            self.home.refresh()
            self._stack.setCurrentWidget(self.home)
        else:
            self._stack.setCurrentWidget(self.ctx.pages[NAV[button_name]])
        self.refresh_status()

    def current_page(self) -> Optional[str]:
        widget = self._stack.currentWidget()
        return next((key for key, page in self.ctx.pages.items() if page is widget), None)

    def eventFilter(self, obj, event) -> bool:
        # PanelBarraSuperior_MouseMove: arrastrar la ventana desde la barra superior o la lateral.
        if obj in (self.form.PanelBarraSuperior, self.form.PanelNavBar):
            if event.type() == event.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._drag_from = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            elif event.type() == event.Type.MouseMove and self._drag_from is not None:
                self.move(event.globalPosition().toPoint() - self._drag_from)
            elif event.type() == event.Type.MouseButtonRelease:
                self._drag_from = None
        return super().eventFilter(obj, event)

    def toast_anchor(self) -> tuple[int, int]:
        # Los avisos aparecen sobre la barra de acciones, a la derecha.
        return self.width() - 28, self.height() - 84

    # ------------------------------------------------------------------ estado de los módulos
    def module_status(self) -> dict[str, tuple[str, str]]:
        # Estado (ok | warn | off) y explicación de cada módulo, a partir de los plugins en ejecución.
        runtime, pages = self.ctx.runtime, self.ctx.pages
        report = runtime.orchestrator.initialization_report

        def ready(name: str) -> bool:
            return report.get(name, {}).get("status") == "initialized"

        status = {key: ("off", f"Se integra en el avance {stage}") for key, (_cls, stage) in PAGES.items()
                  if key not in pages}
        speech = ready("SpeechProvider")
        if "interactions" in pages:
            status["interactions"] = ("ok", "Reconocedor de voz listo") if speech else \
                ("off", "Sin reconocedor de voz: se usan los botones")
        if "web" in pages:
            providers = [p for p in runtime.plugins_for(IWebSearchProvider) if p["status"] == "initialized"]
            status["web"] = ("ok", f"Responde {providers[0]['label']}") if providers else \
                ("warn", "Ningún proveedor LLM disponible")
        if "eye" in pages:
            eye = pages["eye"].active_tracker
            status["eye"] = ("ok", "Eye tracker conectado") if eye else ("off", "Sin eye tracker (opcional)")
        text_ok = ready("TextCamera") and ready("ImageProcessor")
        status["text"] = ("ok", "Cámara de texto y OCR listos") if text_ok else \
            ("warn", "La cámara de texto o el OCR no están activos")
        if "gesture" in pages:
            gesture = pages["gesture"].active_plugin()
            active = gesture is not None and getattr(gesture, "recognition_active", False)
            status["gesture"] = ("ok", f"Reconociendo con {pages['gesture'].form.comboBox1.currentText()}") \
                if active else ("off", "Sin reconocimiento gestual (opcional)")
        consistency = runtime.plugin("ConsistencyProvider")
        loaded = consistency is not None and bool(consistency.execute().get("document_loaded"))
        status["page"] = ("ok", "PDF cargado") if loaded else ("warn", "Falta elegir el PDF del libro")
        return status

    def refresh_status(self) -> None:
        status = self.module_status()
        for key, (state, tip) in status.items():
            if key in self.ctx.pages:
                self.form[BUTTON_FOR[key]].set_status(state, tip)
        orch = self.ctx.runtime.orchestrator
        report = orch.initialization_report
        active = sum(1 for r in report.values() if r.get("status") == "initialized")
        history = orch._latency_history[-100:]
        cycle = f"\nCiclo del orquestador: {sum(history) / len(history):.1f} ms" if history else ""
        self.form.systemStatus.setText(f"{active} de {len(report)} plugins activos{cycle}")
        if self._stack.currentWidget() is self.home:
            self.home.refresh(status)

    # ------------------------------------------------------------------ ajustes
    def get_all_settings(self) -> None:
        for page in self.ctx.pages.values():
            page.load_settings()

    def save_all_settings(self) -> None:
        for page in self.ctx.pages.values():
            page.save_settings()
        self.ctx.settings.save()

    def reset_all_settings(self) -> None:
        if "interactions" in self.ctx.pages:
            self.ctx.pages["interactions"].reset()
        self.ctx.settings.reset()
        self.get_all_settings()

    def save_clicked(self) -> None:
        # Guardar ya no abre un cuadro que hay que cerrar: confirma con un aviso.
        self.save_all_settings()
        message(self, "Se usarán también en las próximas sesiones.", "Ajustes guardados")

    def reset_clicked(self) -> None:
        if self.alert.ask("¿Restaurar los valores iniciales?",
                          "Se perderán los cambios hechos en todas las páginas de configuración.",
                          confirm=True, over=self, confirm_text="Restaurar"):
            self.reset_all_settings()
            message(self, "Se restauraron los valores iniciales.", "Ajustes restaurados")

    def exit_clicked(self) -> None:
        self.save_all_settings()                       # el original guarda antes de preguntar
        if self.alert.ask("¿Cerrar EDDIE?", "Los ajustes ya quedaron guardados para la próxima sesión.",
                          confirm=True, over=self, confirm_text="Cerrar EDDIE"):
            QApplication.instance().quit()

    # ------------------------------------------------------------------ proyección
    def start_projection(self) -> None:
        # StartProjectionButtonModified_Click_1: abre la cámara de texto y muestra la proyección.
        if not projection_available():
            self.save_all_settings()
            message(self, "La pantalla de proyección se integra en el avance P-06. En este avance los módulos "
                          "se configuran y prueban desde esta ventana.", "EDDIE")
            return
        loading = LoadingBox(self, "menu", text="Abriendo proyección…").show_loading()
        QApplication.processEvents()
        try:
            self.save_all_settings()
            self.ctx.pages["text"].apply_camera()
            from ui.projection_screen import ProjectionScreen
            if self.ctx.projection is None:
                self.ctx.projection = ProjectionScreen(self.ctx)
            self.ctx.projection.start()
        except Exception as exc:                        # el C# tragaba la excepción (catch vacío)
            logger.exception("No se pudo iniciar la proyección")
            message(self, f"No se pudo iniciar la proyección: {exc}", "Problema")
        finally:
            QTimer.singleShot(10, loading.close)

    def _on_cycle(self, results: dict) -> None:
        now = time.monotonic()
        if now - self._last_status >= 0.25:              # estado de los módulos ~4 veces por segundo
            self._last_status = now
            self.refresh_status()
        for page in self.ctx.pages.values():
            try:
                page.on_cycle(results)
            except Exception:
                logger.exception("Error actualizando %s", type(page).__name__)


class SessionHome(QWidget):
    # Pantalla de inicio: los pasos para preparar una sesión de lectura y su estado actual.
    STEPS = [  # (página, título, explicación, obligatorio)
        ("page", "Elige el PDF del libro", "Ahí se guardan los resaltados, marcadores y comentarios.", True),
        ("text", "Revisa la cámara de texto", "Debe ver la página completa; prueba resaltando una palabra.", True),
        ("web", "Elige quién responde las búsquedas", "Definición, traducción, enciclopedia, video e imagen.", True),
        ("gesture", "Activa un gesto", "Mano, lápiz de color o mouse para resaltar sobre la proyección.", False),
        ("eye", "Conecta el eye tracker", "Para mover el puntero con la mirada y registrar la sesión.", False),
        ("interactions", "Decide si usarás la voz", "Comandos como «Buscar definición».", False),
    ]

    def __init__(self, window: MenuSettingsWindow) -> None:
        super().__init__()
        self.window_ = window
        self.setObjectName("SessionHome")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 4, 32, 18)
        outer.setSpacing(4)
        title = QLabel("Preparar la sesión de lectura")
        title.setObjectName("pageTitle")
        outer.addWidget(title)
        sub = QLabel("Revisa estos pasos antes de iniciar la proyección. Los opcionales pueden quedar pendientes.")
        sub.setObjectName("pageSubtitle")
        outer.addWidget(sub)
        outer.addSpacing(14)
        frame, col = card()
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        self.rows: dict[str, tuple[QLabel, ActionButton]] = {}
        for row, (key, title_text, hint, required) in enumerate(self.STEPS):  # es una secuencia: van numerados
            number = QLabel(str(row + 1))
            number.setProperty("stepNumber", True)
            number.setFixedWidth(22)
            name = QLabel(title_text + ("" if required else "  (opcional)"))
            name.setProperty("field", True)
            name.setStyleSheet("font-weight:600;")
            state = QLabel("")
            state.setFixedWidth(300)
            state.setWordWrap(True)
            button = ActionButton("Configurar", variant="secondary")
            button.setObjectName(f"homeGo_{key}")
            button.clicked.connect(lambda _=False, k=key: window.open_page(BUTTON_FOR[k]))
            if key not in window.ctx.pages:
                button.setEnabled(False)
            grid.addWidget(number, row, 0, alignment=Qt.AlignmentFlag.AlignTop)
            text_col = QVBoxLayout()
            text_col.setSpacing(0)
            text_col.addWidget(name)
            text_col.addWidget(hint_label(hint))
            grid.addLayout(text_col, row, 1)
            grid.addWidget(state, row, 2)
            grid.addWidget(button, row, 3)
            self.rows[key] = (state, button)
        grid.setColumnStretch(1, 1)
        col.addLayout(grid)
        outer.addWidget(frame)
        outer.addStretch(1)

    def refresh(self, status: Optional[dict] = None) -> None:
        status = status or self.window_.module_status()
        for key, (label, button) in self.rows.items():
            state, tip = status.get(key, ("off", ""))
            label.setText(tip)
            label.setProperty("state", state)
            label.style().unpolish(label)
            label.style().polish(label)
            button.setText("Revisar" if state == "ok" else ("Configurar" if key in self.window_.ctx.pages
                                                             else PAGES[key][1]))

    def ready_to_start(self) -> bool:
        status = self.window_.module_status()
        return all(status[key][0] == "ok" for key, _t, _h, required in self.STEPS if required)
