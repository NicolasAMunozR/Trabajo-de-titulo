"""
ui/menu_settings.py
===================
Ventana principal "EDDIE Menu Settings" (MenuSettings.cs): barra superior arrastrable,
menú lateral con las seis secciones, panel de contenido y los botones
Reset Settings / Save Settings / Start Projection.
"""
import logging

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QApplication, QStackedLayout, QWidget

from ui.context import AppContext
from ui.dialogs import AlertBox, LoadingBox, message
from ui.form_builder import build_form
from ui.settings_pages import (EyeTrackingPage, GestureRecognitionPage, InteractionPage, PageDetectionPage,
                               TextRecognitionPage, WebSearchPage)

logger = logging.getLogger(__name__)

NAV = {
    "InteractionsButton": "interactions",
    "WebSearchServicesButton": "web",
    "EyeTrackingButton": "eye",
    "TextRecognitiionButton": "text",
    "GestureRecognitionButton": "gesture",
    "PageDetectionButton": "page",
}


class MenuSettingsWindow(QWidget):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint)
        self.ctx = ctx
        self.setObjectName("MenuSettings")
        self.setWindowTitle("EDDIE Menu Settings")
        self.form = build_form("MenuSettings", self)
        self.setFixedSize(1280, 720)
        f = self.form
        f.textBox1.setStyleSheet("QLineEdit{border:none;background:#1c9dec;color:#f8f5fa;}")
        f.textBox3.setStyleSheet("QLineEdit{border:none;background:#f8f5fa;color:#00003c;}")
        for box in (f.textBox1, f.textBox3):
            box.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        f.LoadingPictureBox.setVisible(False)
        self._separator = _Separator(f.ContenidoNavBar)

        for button_name in NAV:
            button = f[button_name]
            button.setFlat(True)
            button.setStyleSheet("QPushButton{border:none;background:#f8f5fa;color:#00003c;text-align:left;}")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _=False, b=button_name: self.open_page(b))

        # Instancias de cada formulario de configuración (como en el constructor C#)
        ctx.pages = {
            "interactions": InteractionPage(ctx),
            "web": WebSearchPage(ctx),
            "eye": EyeTrackingPage(ctx),
            "text": TextRecognitionPage(ctx),
            "gesture": GestureRecognitionPage(ctx),
            "page": PageDetectionPage(ctx),
        }
        self._stack = QStackedLayout(f.PanelContenido)
        self._stack.setContentsMargins(0, 0, 0, 0)
        self._empty = QWidget()
        self._stack.addWidget(self._empty)
        for page in ctx.pages.values():
            self._stack.addWidget(page)

        f.ExitPictureBox.clicked.connect(self.exit_clicked)
        f.MinimizePictureBox.clicked.connect(self.showMinimized)
        f.SaveSettingsButtonModified.clicked.connect(self.save_clicked)
        f.ResetSettingsButtonModified.clicked.connect(self.reset_clicked)
        f.StartProjectionButtonModified.clicked.connect(self.start_projection)
        f.PanelBarraSuperior.installEventFilter(self)
        self._drag_from: QPoint | None = None
        self.alert = AlertBox(self)
        self.get_all_settings()
        ctx.runtime.cycle.connect(self._on_cycle)

    # ------------------------------------------------------------------ navegación
    def open_page(self, button_name: str) -> None:
        """AbrirFormEnPanel + changeAllToLightFont + negrita en el botón activo."""
        for name in NAV:
            font = QFont(self.form[name].font())
            font.setBold(name == button_name)
            self.form[name].setFont(font)
        self._stack.setCurrentWidget(self.ctx.pages[NAV[button_name]])

    def eventFilter(self, obj, event) -> bool:
        """PanelBarraSuperior_MouseMove: arrastrar la ventana desde la barra superior."""
        if obj is self.form.PanelBarraSuperior:
            if event.type() == event.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._drag_from = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            elif event.type() == event.Type.MouseMove and self._drag_from is not None:
                self.move(event.globalPosition().toPoint() - self._drag_from)
            elif event.type() == event.Type.MouseButtonRelease:
                self._drag_from = None
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------ ajustes
    def get_all_settings(self) -> None:
        for page in self.ctx.pages.values():
            page.load_settings()

    def save_all_settings(self) -> None:
        for page in self.ctx.pages.values():
            page.save_settings()
        self.ctx.settings.save()

    def reset_all_settings(self) -> None:
        self.ctx.pages["interactions"].reset()
        self.ctx.settings.reset()
        self.get_all_settings()

    def save_clicked(self) -> None:
        self.save_all_settings()
        self.alert.ask("¡Changes have been saved!", "The settings made will be saved for subsequent sessions",
                       confirm=False, over=self)

    def reset_clicked(self) -> None:
        if self.alert.ask("¿Are you sure to do this action?",
                          "If you reset the settings, the changes made to the settings so far will be lost",
                          confirm=True, over=self):
            self.reset_all_settings()

    def exit_clicked(self) -> None:
        self.save_all_settings()                       # el original guarda antes de preguntar
        if self.alert.ask("¿Are you sure you want to close the application?",
                          "If you have not saved any settings, they will be lost for the next session.",
                          confirm=True, over=self):
            QApplication.instance().quit()

    # ------------------------------------------------------------------ proyección
    def start_projection(self) -> None:
        """StartProjectionButtonModified_Click_1: abre la cámara de texto y muestra la proyección."""
        loading = LoadingBox(self, "menu").show_loading()
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
            message(self, f"No se pudo iniciar la proyección: {exc}", "Problem")
        finally:
            QTimer.singleShot(10, loading.close)

    def _on_cycle(self, results: dict) -> None:
        for page in self.ctx.pages.values():
            try:
                page.on_cycle(results)
            except Exception:
                logger.exception("Error actualizando %s", type(page).__name__)


class _Separator(QWidget):
    """ContenidoNavBar_Paint: línea negra bajo el título "Settings"."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setGeometry(0, 46, 213, 3)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.show()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawLine(0, 1, 213, 1)
