# AlertBox, LoadingBox y avisos de la interfaz renovada.
# message() ahora muestra un aviso no modal en la ventana en vez de un cuadro que detiene la lectura.
from typing import Optional

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, QTimer
from PySide6.QtWidgets import QDialog, QFrame, QLabel, QMessageBox, QVBoxLayout, QWidget

from ui.modern_forms import build_modern


class _Dim(QWidget):
    # Fondo oscuro semitransparente detrás del AlertBox (como en el original).

    def __init__(self, over: QWidget) -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
                         | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowOpacity(0.45)
        self.setStyleSheet("background:#0B1020;")
        self.setGeometry(over.frameGeometry())


class AlertBox(QDialog):
    # Alerta con título/subtítulo y botones Entendido o Cancelar/Confirmar.

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setObjectName("AlertBox")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.form = build_modern("AlertBox", self)
        self.setFixedSize(500, 230)
        self.form.okButton.clicked.connect(self.reject)
        self.form.buttonModified2.clicked.connect(self.reject)            # Cancelar
        self.form.buttonModified1.clicked.connect(self.accept)            # Confirmar
        self.form.ExitPictureBox.clicked.connect(self.reject)

    def ask(self, title: str, subtitle: str, confirm: bool, over: Optional[QWidget] = None,
            confirm_text: str = "Confirmar") -> bool:
        self.form.label1.setText(title)
        self.form.label2.setText(subtitle)
        self.form.buttonModified1.setText(confirm_text)
        self.form.okButton.setVisible(not confirm)
        self.form.buttonModified1.setVisible(confirm)
        self.form.buttonModified2.setVisible(confirm)
        dim = _Dim(over) if over is not None else None
        if dim:
            dim.show()
            self.move(over.frameGeometry().center() - self.rect().center())
        try:
            return self.exec() == QDialog.DialogCode.Accepted
        finally:
            if dim:
                dim.close()


class LoadingBox(QDialog):
    # Indicador "Buscando…" junto al panel donde aparecerá el resultado.
    OFFSETS = {"izquierda": QPoint(48, 150), "derecha": QPoint(990, 150), "menu": QPoint(1010, 600)}

    def __init__(self, parent: QWidget, side: Optional[str] = None, background: str = "#f8f5fa",
                 text: str = "Buscando…") -> None:
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setObjectName("LoadingBox")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.form = build_modern("LoadingBox", self)
        self.form.label2.setText(text)
        self.setFixedSize(190, 46)
        origin = parent.frameGeometry().topLeft()
        if side in self.OFFSETS:
            self.move(origin + self.OFFSETS[side])

    def show_loading(self) -> "LoadingBox":
        self.show()
        self.raise_()
        return self


# ---------------------------------------------------------------------------- avisos no modales
TITLES = {"Problem": "Problema", "Problem found": "Problema", "Problema": "Problema", "Error": "Error",
          "EDDIE": ""}
ERROR_TITLES = {"Problema", "Error"}


class Toast(QFrame):
    def __init__(self, host: "ToastHost", title: str, text: str, error: bool) -> None:
        super().__init__(host.window)
        self.setObjectName("toast")
        self.setProperty("kind", "error" if error else "info")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(360)
        col = QVBoxLayout(self)
        col.setContentsMargins(16, 12, 16, 12)
        col.setSpacing(2)
        if title:
            head = QLabel(title)
            head.setObjectName("toastTitle")
            col.addWidget(head)
        body = QLabel(text)
        body.setObjectName("toastText")
        body.setWordWrap(True)
        col.addWidget(body)
        self.text = text
        self._host = host
        QTimer.singleShot(7000 if error else 4500, self.dismiss)

    def mousePressEvent(self, _event) -> None:
        self.dismiss()

    def dismiss(self) -> None:
        if self._host is not None:
            self._host.remove(self)
            self._host = None
        self.hide()
        self.deleteLater()


class ToastHost(QObject):
    # Pila de avisos de una ventana (esquina inferior derecha, o donde diga `toast_anchor`).
    MAX = 3

    def __init__(self, window: QWidget) -> None:
        super().__init__(window)
        self.window = window
        self.toasts: list[Toast] = []
        window.installEventFilter(self)

    @classmethod
    def for_window(cls, window: QWidget) -> "ToastHost":
        host = window.findChild(ToastHost, "toastHost", Qt.FindChildOption.FindDirectChildrenOnly)
        if host is None:
            host = cls(window)
            host.setObjectName("toastHost")
        return host

    def show_message(self, title: str, text: str) -> Toast:
        toast = Toast(self, title, text, title in ERROR_TITLES)
        self.toasts.append(toast)
        while len(self.toasts) > self.MAX:
            self.toasts[0].dismiss()
        toast.adjustSize()
        toast.show()
        toast.raise_()
        self._layout()
        return toast

    def remove(self, toast: Toast) -> None:
        if toast in self.toasts:
            self.toasts.remove(toast)
            self._layout()

    def _layout(self) -> None:
        anchor = getattr(self.window, "toast_anchor", None)
        x_right, bottom = anchor() if callable(anchor) else (self.window.width() - 24, self.window.height() - 92)
        y = bottom
        for toast in reversed(self.toasts):
            toast.adjustSize()
            y -= toast.height()
            toast.move(x_right - toast.width(), y)
            toast.raise_()
            y -= 8

    def eventFilter(self, obj, event) -> bool:
        if obj is self.window and event.type() == QEvent.Type.Resize:
            self._layout()
        return False


def message(parent: Optional[QWidget], text: str, title: str = "EDDIE") -> None:
    # MessageBox.Show del original, ahora como aviso no modal en la ventana del control.
    title = TITLES.get(title, title)
    window = parent.window() if parent is not None else None
    if window is not None and window.isVisible():
        ToastHost.for_window(window).show_message(title, text)
        return
    QMessageBox.information(parent, title or "EDDIE", text)
