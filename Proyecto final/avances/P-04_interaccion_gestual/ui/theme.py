"""
ui/theme.py
===========
Sistema visual de la interfaz renovada (P-08).

La idea que ordena todo el diseño: EDDIE es un escritorio de lectura. En la ventana de
configuración el "lomo" del libro es la barra lateral en tinta azul; en la proyección el
fondo es negro (el proyector no emite luz ahí) y solo se iluminan la zona de lectura y las
notas que el lector pidió. El amarillo queda reservado para el resaltador, que es lo que la
cámara busca: ningún botón ni acento de la interfaz usa amarillo (hallazgo de Ibaceta, 2023).

Tokens
------
TINTA       #1B2440  barra lateral, títulos y texto principal
TINTA_2     #2A3558  estados hover sobre la tinta
LIENZO      #EEF1F6  fondo del área de trabajo
PAPEL       #FFFFFF  superficie de las tarjetas
LINEA       #D6DCE6  bordes y divisores
APAGADO     #5B6478  texto secundario
ACENTO      #0B7A87  acción principal y selección (verde azulado, nunca amarillo)
"""
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer

ICONS = Path(__file__).resolve().parent / "resources" / "icons"

TINTA = "#1B2440"
TINTA_2 = "#2A3558"
TINTA_TEXTO = "#C9D2E3"          # texto sobre la tinta
LIENZO = "#EEF1F6"
PAPEL = "#FFFFFF"
LINEA = "#D6DCE6"
APAGADO = "#5B6478"
ACENTO = "#0B7A87"
ACENTO_HOVER = "#086470"
ACENTO_SUAVE = "#DFF1F2"
OK = "#2F8F5B"
AVISO = "#B26A00"
INACTIVO = "#A0A8B8"
PELIGRO = "#B83A3A"

# Proyección (fondo sin luz)
PROY_FONDO = "#000000"
PROY_NOTA = "#EEF2F7"            # tarjetas de resultado: papel iluminado
PROY_TRAZO = "#8FA3BF"           # bordes de botones proyectados
PROY_TEXTO = "#E8EEF6"
PROY_ACTIVO = "#19A3B1"          # botón encendido (verde azulado, contrasta con el resaltado amarillo)

FONT_FAMILY = "IBM Plex Sans"
CHECK_ICON = (ICONS / "check-white.png").as_posix()
UP_ICON = (ICONS / "chevron-up-muted.png").as_posix()
DOWN_ICON = (ICONS / "chevron-down-muted.png").as_posix()


def font(size: float = 10, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    f = QFont(FONT_FAMILY)
    f.setFamilies([FONT_FAMILY, "Segoe UI", "Arial"])
    f.setPointSizeF(size)
    f.setWeight(weight)
    return f


@lru_cache(maxsize=512)
def icon_pixmap(name: str, color: str = TINTA, size: int = 20) -> QPixmap:
    """Icono Lucide (ISC) pintado en `color`. Devuelve un pixmap vacío si no existe."""
    path = ICONS / f"{name}.svg"
    pm = QPixmap(QSize(size * 2, size * 2))
    pm.fill(Qt.GlobalColor.transparent)
    if not path.exists():
        return pm
    svg = path.read_text(encoding="utf-8").replace("currentColor", color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    painter = QPainter(pm)
    renderer.render(painter, QRectF(0, 0, size * 2, size * 2))
    painter.end()
    pm.setDevicePixelRatio(2.0)
    return pm


def icon(name: str, color: str = TINTA, size: int = 20) -> QIcon:
    return QIcon(icon_pixmap(name, color, size))


def target_pixmap(size: int = 60, color: str = PROY_TEXTO) -> QPixmap:
    """Cruz de calibración clara (sobre fondo negro la del original, azul oscuro, no se veía)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = p.pen()
    pen.setColor(QColor(color))
    pen.setWidthF(3)
    p.setPen(pen)
    c = size / 2
    p.drawEllipse(QRectF(c - size * 0.3, c - size * 0.3, size * 0.6, size * 0.6))
    p.drawEllipse(QRectF(c - size * 0.12, c - size * 0.12, size * 0.24, size * 0.24))
    p.drawLine(int(c), 2, int(c), size - 2)
    p.drawLine(2, int(c), size - 2, int(c))
    p.end()
    return pm


QSS = f"""
* {{ font-family: "{FONT_FAMILY}", "Segoe UI", Arial; }}
QWidget#MenuSettings {{ background: {LIENZO}; }}
QToolTip {{ background: {TINTA}; color: #FFFFFF; border: none; padding: 6px 8px; }}

/* ---------- barra lateral ---------- */
QFrame#PanelNavBar {{ background: {TINTA}; }}
QLabel#brandTitle {{ color: #FFFFFF; font-size: 20pt; font-weight: 600; }}
QLabel#brandSubtitle {{ color: {TINTA_TEXTO}; font-size: 9.5pt; }}
QLabel#navSection {{ color: #8C97B0; font-size: 9pt; padding: 14px 0 4px 4px; }}
QLabel#systemStatus {{ color: {TINTA_TEXTO}; font-size: 9pt; }}

/* ---------- área de contenido ---------- */
QFrame#PanelBarraSuperior {{ background: transparent; }}
QFrame#footer {{ background: {PAPEL}; border-top: 1px solid {LINEA}; }}
QLabel#pageTitle {{ color: {TINTA}; font-size: 20pt; font-weight: 600; }}
QLabel#pageSubtitle {{ color: {APAGADO}; font-size: 10pt; }}
QScrollArea#pageBody, QScrollArea#pageBody > QWidget > QWidget {{ background: transparent; border: none; }}

QFrame[card="true"] {{ background: {PAPEL}; border: 1px solid {LINEA}; border-radius: 10px; }}
QLabel[cardTitle="true"] {{ color: {TINTA}; font-size: 11.5pt; font-weight: 600; background: transparent; }}
QLabel[hint="true"] {{ color: {APAGADO}; font-size: 9pt; background: transparent; }}
QLabel[field="true"] {{ color: {TINTA}; font-size: 9.5pt; background: transparent; }}
QLabel[readout="true"] {{ color: {TINTA}; font-size: 15pt; font-weight: 600; background: transparent; }}
QLabel[help="true"] {{ background: transparent; }}
QLabel[stepNumber="true"] {{ color: {ACENTO}; font-size: 13pt; font-weight: 600; background: transparent; }}
QLabel[state="ok"] {{ color: {OK}; font-weight: 600; background: transparent; }}
QLabel[state="warn"] {{ color: {AVISO}; font-weight: 600; background: transparent; }}
QLabel[state="off"] {{ color: {APAGADO}; background: transparent; }}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QListWidget {{
    background: {PAPEL}; color: {TINTA}; border: 1px solid {LINEA}; border-radius: 6px;
    padding: 4px 8px; min-height: 22px; selection-background-color: {ACENTO}; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
    border: 1px solid {ACENTO}; }}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{ background: {LIENZO}; color: {INACTIVO}; }}
QLineEdit[readOnly="true"] {{ background: #F6F8FB; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{ image: url("{DOWN_ICON}"); width: 12px; height: 12px; }}
QSpinBox, QDoubleSpinBox {{ padding-right: 22px; }}
QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right;
    width: 20px; border: none; border-left: 1px solid {LINEA}; border-top-right-radius: 6px; background: #F6F8FB; }}
QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right;
    width: 20px; border: none; border-left: 1px solid {LINEA}; border-bottom-right-radius: 6px; background: #F6F8FB; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::up-button:hover,
QDoubleSpinBox::down-button:hover {{ background: {ACENTO_SUAVE}; }}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url("{UP_ICON}"); width: 10px; height: 10px; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url("{DOWN_ICON}"); width: 10px; height: 10px; }}
QComboBox QAbstractItemView {{ background: {PAPEL}; color: {TINTA}; selection-background-color: {ACENTO_SUAVE};
    selection-color: {TINTA}; border: 1px solid {LINEA}; }}
QCheckBox, QRadioButton {{ color: {TINTA}; background: transparent; spacing: 8px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid #8A93A6; border-radius: 4px;
    background: {PAPEL}; }}
QCheckBox::indicator:hover {{ border-color: {ACENTO}; }}
QCheckBox::indicator:checked {{ background: {ACENTO}; border-color: {ACENTO}; image: url("{CHECK_ICON}"); }}
QCheckBox::indicator:disabled {{ background: {LIENZO}; border-color: {LINEA}; }}

/* opciones Sí/No como selector segmentado */
QFrame[segmented="true"] {{ background: {LIENZO}; border-radius: 8px; }}
QRadioButton[segment="true"] {{ padding: 7px 16px; border-radius: 6px; color: {APAGADO}; }}
QRadioButton[segment="true"]::indicator {{ width: 0px; height: 0px; }}
QRadioButton[segment="true"]:checked {{ background: {PAPEL}; color: {ACENTO}; font-weight: 600;
    border: 1px solid {LINEA}; }}
QRadioButton[segment="true"]:hover:!checked {{ color: {TINTA}; }}

/* ---------- botones ---------- */
QPushButton[variant] {{ border-radius: 8px; padding: 8px 18px; font-size: 10pt; font-weight: 600; }}
QPushButton[variant="primary"] {{ background: {ACENTO}; color: #FFFFFF; border: 1px solid {ACENTO}; }}
QPushButton[variant="primary"]:hover {{ background: {ACENTO_HOVER}; }}
QPushButton[variant="primary"]:pressed {{ background: {TINTA}; border-color: {TINTA}; }}
QPushButton[variant="secondary"] {{ background: {PAPEL}; color: {TINTA}; border: 1px solid {LINEA}; }}
QPushButton[variant="secondary"]:hover {{ border-color: {ACENTO}; color: {ACENTO}; }}
QPushButton[variant="ghost"] {{ background: transparent; color: {APAGADO}; border: 1px solid transparent; }}
QPushButton[variant="ghost"]:hover {{ color: {TINTA}; background: {LIENZO}; }}
QPushButton[variant="danger"] {{ background: {PAPEL}; color: {PELIGRO}; border: 1px solid {LINEA}; }}
QPushButton[variant="danger"]:hover {{ border-color: {PELIGRO}; }}
QPushButton[variant]:disabled {{ background: {LIENZO}; color: {INACTIVO}; border-color: {LINEA}; }}
QPushButton[browse="true"] {{ background: {PAPEL}; border: 1px solid {LINEA}; border-radius: 6px; padding: 4px; }}
QPushButton[browse="true"]:hover {{ border-color: {ACENTO}; }}
QPushButton[browse="true"]:disabled {{ background: {LIENZO}; }}
QPushButton[chrome="true"] {{ background: transparent; border: none; border-radius: 6px; padding: 6px; }}
QPushButton[chrome="true"]:hover {{ background: {LINEA}; }}

/* ---------- diálogos ---------- */
QDialog#AlertBox {{ background: transparent; }}
QFrame#alertCard {{ background: {PAPEL}; border-radius: 12px; border: 1px solid {LINEA}; }}
QLabel#alertTitle {{ color: {TINTA}; font-size: 14pt; font-weight: 600; background: transparent; }}
QLabel#alertText {{ color: {APAGADO}; font-size: 10.5pt; background: transparent; }}
QFrame#toast {{ background: {TINTA}; border-radius: 10px; }}
QFrame#toast[kind="error"] {{ background: #5E1F1F; }}
QLabel#toastTitle {{ color: #FFFFFF; font-weight: 600; background: transparent; }}
QLabel#toastText {{ color: #E4E9F2; background: transparent; }}
QFrame#loadingPill {{ background: {TINTA}; border-radius: 22px; }}
QLabel#loadingText {{ color: #FFFFFF; font-weight: 600; background: transparent; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #C3CBD8; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""

# Hoja de estilo propia de la pantalla proyectada (se aplica sobre ProjectionScreen)
PROJECTION_QSS = f"""
QWidget#ProjectionScreenActivity2 {{ background: {PROY_FONDO}; }}
QFrame[note="true"] {{ background: {PROY_NOTA}; border-radius: 12px; border: none; }}
QFrame[note="true"] QLabel {{ color: {TINTA}; background: transparent; }}
QLabel[noteTitle="true"] {{ color: {TINTA}; font-size: 13pt; font-weight: 600; }}
QLabel[noteHint="true"] {{ color: {APAGADO}; font-size: 9pt; }}
QFrame[note="true"] QTextEdit, QFrame[note="true"] QListWidget {{ background: {PAPEL}; color: {TINTA};
    border: none; border-radius: 8px; padding: 6px; font-size: 11pt; }}
QFrame[note="true"] QLineEdit {{ background: {PAPEL}; color: {TINTA}; border: 1px solid {LINEA};
    border-radius: 6px; padding: 4px 8px; }}
QFrame[note="true"] QCheckBox {{ color: {TINTA}; }}
QTextEdit#textBox1 {{ background: transparent; color: {PROY_TEXTO}; border: 1px solid {PROY_TRAZO};
    border-radius: 10px; padding: 6px 12px; font-size: 14pt; }}
QLabel#termCaption {{ color: {PROY_TRAZO}; font-size: 9pt; background: transparent; }}
QPushButton[variant="projection"] {{ background: transparent; color: {PROY_TEXTO}; border: 1px solid {PROY_TRAZO};
    border-radius: 8px; padding: 6px 12px; font-weight: 600; }}
QPushButton[variant="projection"]:hover {{ border-color: {PROY_ACTIVO}; color: #FFFFFF; }}
QFrame[note="true"] QPushButton[variant] {{ border-radius: 8px; padding: 6px 12px; }}
QLabel#syncPDFLabel, QLabel#PagesLabel {{ color: {TINTA}; font-weight: 600; }}
"""


def apply_theme(app) -> None:
    """Paleta clara legible (también en Windows con modo oscuro) + estilo Fusion + QSS del sistema visual."""
    try:
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)          # Qt ≥ 6.8
    except AttributeError:
        pass
    app.setStyle("Fusion")                    # mismo aspecto en Windows y Linux; respeta el QSS completo
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: LIENZO, QPalette.ColorRole.WindowText: "#000000",
        QPalette.ColorRole.Base: "#ffffff", QPalette.ColorRole.AlternateBase: "#F6F8FB",
        QPalette.ColorRole.Text: "#000000", QPalette.ColorRole.Button: PAPEL,
        QPalette.ColorRole.ButtonText: TINTA, QPalette.ColorRole.BrightText: "#ffffff",
        QPalette.ColorRole.Highlight: ACENTO, QPalette.ColorRole.HighlightedText: "#ffffff",
        QPalette.ColorRole.ToolTipBase: TINTA, QPalette.ColorRole.ToolTipText: "#ffffff",
        QPalette.ColorRole.PlaceholderText: "#8A93A6", QPalette.ColorRole.Link: ACENTO,
        QPalette.ColorRole.Light: "#ffffff", QPalette.ColorRole.Midlight: "#E3E7EE",
        QPalette.ColorRole.Mid: "#A0A8B8", QPalette.ColorRole.Dark: "#5B6478",
        QPalette.ColorRole.Shadow: "#000000",
    }
    for role, value in roles.items():
        palette.setColor(role, QColor(value))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(INACTIVO))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(LIENZO))
    app.setPalette(palette)
    from ui.form_builder import load_fonts
    load_fonts()
    app.setFont(font(10))
    app.setStyleSheet(QSS)
