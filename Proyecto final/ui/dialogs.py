"""
ui/dialogs.py
=============
AlertBox.cs y LoadingBox.cs: diálogos con el mismo diseño del original.
"""
from typing import Optional

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDialog, QMessageBox, QWidget

from ui.form_builder import build_form


class _Dim(QWidget):
    """Fondo negro al 50 % que el original mostraba detrás del AlertBox."""

    def __init__(self, over: QWidget) -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
                         | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowOpacity(0.5)
        self.setStyleSheet("background:#000000;")
        self.setGeometry(over.frameGeometry())


class AlertBox(QDialog):
    """Alerta con título/subtítulo y botones Ok o Confirm/Cancel (bandera save|reset|exit)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setObjectName("AlertBox")
        self.form = build_form("AlertBox", self)
        self.setFixedSize(909, 382)
        self.form.okButton.clicked.connect(self.reject)
        self.form.buttonModified2.clicked.connect(self.reject)            # Cancel
        self.form.buttonModified1.clicked.connect(self.accept)            # Confirm
        self.form.ExitPictureBox.clicked.connect(self.reject)
        for label in (self.form.label1, self.form.label2):
            label.setWordWrap(False)

    def ask(self, title: str, subtitle: str, confirm: bool, over: Optional[QWidget] = None) -> bool:
        self.form.label1.setText(title)
        self.form.label2.setText(subtitle)
        self.form.label1.adjustSize()
        self.form.label2.adjustSize()
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
    """Animación "Loading..." posicionada como en LoadingBox.cs según el lado de la búsqueda."""

    def __init__(self, parent: QWidget, side: Optional[str] = None, background: str = "#f8f5fa") -> None:
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setObjectName("LoadingBox")
        self.form = build_form("LoadingBox", self)
        self.setFixedSize(225, 257)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(background))
        self.setPalette(pal)
        origin = parent.frameGeometry().topLeft()
        if side == "izquierda":
            self.move(origin + QPoint(30, 122))
        elif side == "derecha":
            self.move(origin + QPoint(980, 134))
        elif side == "menu":
            self.move(origin + QPoint(17, 420))

    def show_loading(self) -> "LoadingBox":
        self.show()
        self.raise_()
        return self


def message(parent: Optional[QWidget], text: str, title: str = "EDDIE") -> None:
    """MessageBox.Show del original."""
    QMessageBox.information(parent, title, text)
