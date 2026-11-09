# Pruebas de la interfaz (Qt offscreen) del avance P-03: controles de cada formulario y flujos de los módulos integrados.
import json

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from ui.form_builder import LAYOUTS
from ui.modern_forms import build_modern

FORMS = ['MenuSettings', 'TextRecognitionSettings', 'PageDetectionSettings', 'AlertBox', 'LoadingBox']
PAGES = ['text', 'page']


def _nodes(nodes):
    for node in nodes:
        yield node
        yield from _nodes(node.get("children", []))


@pytest.mark.parametrize("name", FORMS)
def test_every_original_control_exists_in_the_new_interface(qapp, name):
    # Cada control del original sigue existiendo con su nombre, un tipo compatible y el mismo comportamiento.
    from PySide6.QtWidgets import (QAbstractButton, QAbstractSpinBox, QCheckBox, QComboBox, QLabel, QLineEdit,
                                   QListWidget, QRadioButton, QTextEdit, QWidget)
    from ui.widgets import FitFrameView
    expected = {"Label": QLabel, "PictureBox": QLabel, "ImageBox": FitFrameView, "ButtonModified": QAbstractButton,
                "Button": QAbstractButton, "ButtonAlt": QAbstractButton, "TextBox": (QLineEdit, QTextEdit),
                "RichTextBox": QTextEdit, "ComboBox": QComboBox, "NumericUpDown": QAbstractSpinBox,
                "CheckBox": QCheckBox, "RadioButton": QRadioButton, "ListBox": QListWidget}
    data = json.loads((LAYOUTS / f"{name}.json").read_text(encoding="utf-8"))
    root = QWidget()
    form = build_modern(name, root)
    for node in _nodes(data["controls"]):
        if node["type"] in ("Container",):
            continue
        widget = form.controls[node["name"]]
        if node["type"] in expected:
            assert isinstance(widget, expected[node["type"]]), node["name"]
        props = node["props"]
        if node["type"] == "NumericUpDown":
            assert widget.minimum() == props.get("Minimum", 0) and widget.maximum() == props.get("Maximum", 100)
            assert widget.value() == pytest.approx(props.get("Value", props.get("Minimum", 0))), node["name"]
        if props.get("Enabled") is False:
            assert not widget.isEnabled(), node["name"]


@pytest.fixture
def eddie(qapp, tmp_path, monkeypatch):
    # EDDIE del avance con dispositivos simulados (DeviceFactory).
    monkeypatch.setenv("EDDIE_DEVICE_MODE", "sim")
    messages = []
    import ui.dialogs as dialogs
    import ui.menu_settings as menu
    import ui.settings_pages as pages
    record = lambda parent, text, title="EDDIE": messages.append(text)
    for module in (dialogs, menu, pages):
        monkeypatch.setattr(module, "message", record)
    from app.runtime import EddieRuntime
    from app.settings_store import SettingsStore
    from ui.context import AppContext
    settings = SettingsStore(tmp_path / "user_settings.json")
    runtime = EddieRuntime(settings, trace_dir=tmp_path / "logs")
    runtime.start()
    ctx = AppContext(runtime=runtime, settings=settings)
    window = menu.MenuSettingsWindow(ctx)
    window.show()
    yield ctx, window, messages
    runtime.wait_for_jobs()
    window.close()
    runtime.stop()


def _settle(ctx, qapp, cycles=3):
    for _ in range(cycles):
        ctx.runtime._tick()
        ctx.runtime.wait_for_jobs()
        qapp.processEvents()


def test_integrated_plugins_start_and_only_their_pages_exist(eddie):
    ctx, window, _ = eddie
    report = ctx.runtime.orchestrator.initialization_report
    for name in ('TextCamera', 'ImageProcessor', 'ConsistencyProvider'):
        assert report[name]["status"] == "initialized", name
    assert set(ctx.pages) == set(PAGES)
    from ui.menu_settings import NAV
    for button, key in NAV.items():
        assert window.form[button].isEnabled() == (key in PAGES), button


def test_save_and_reset_text_settings_roundtrip(eddie, qapp):
    ctx, window, _ = eddie
    ctx.pages["text"].form.numericUpDownResXText.setValue(1280)
    window.save_all_settings()
    stored = json.loads(ctx.settings.path.read_text(encoding="utf-8"))
    assert stored["cameraTextWidth"] == 1280
    window.reset_all_settings()
    assert ctx.settings["cameraTextWidth"] == 640


def test_text_recognition_page_shows_the_simulated_camera(eddie, qapp):
    ctx, window, _ = eddie
    window.open_page("TextRecognitiionButton")
    _settle(ctx, qapp, 4)
    assert ctx.pages["text"].form.imageBox3.pixmap() is not None


def test_page_detection_opens_pdf_and_rejects_damaged_file(eddie, qapp, tmp_path, sample_pdf):
    ctx, window, messages = eddie
    assert ctx.pages["page"].open_pdf(str(sample_pdf))
    assert ctx.pages["page"].form.numericUpDown5.value() == 595
    damaged = tmp_path / "danado.pdf"
    damaged.write_bytes(sample_pdf.read_bytes().decode("latin-1").encode("utf-8")[:400])
    assert ctx.pages["page"].open_pdf(str(damaged)) is False
    assert messages, "debe avisar al usuario en vez de romper la aplicación"


def test_start_projection_is_announced_for_a_later_stage(eddie):
    ctx, window, messages = eddie
    window.start_projection()
    assert ctx.projection is None
    assert "P-06" in messages[-1]


def test_light_palette_keeps_text_readable(qapp):
    from PySide6.QtGui import QPalette
    palette = qapp.palette()
    assert palette.color(QPalette.ColorRole.Text).name() == "#000000"
    assert palette.color(QPalette.ColorRole.Base).name() == "#ffffff"


def test_text_page_recognizes_the_highlighted_word(eddie, qapp):
    # Text recognition muestra el rectángulo detectado y el texto reconocido (antes solo desde la proyección).
    ctx, window, messages = eddie
    page = ctx.pages["text"]
    window.open_page("TextRecognitiionButton")
    _settle(ctx, qapp)
    page.recognize_now()
    _settle(ctx, qapp)
    assert page.form.imageBox1.pixmap() is not None
    text = page.form.textBoxRecognized.text()
    import shutil
    if shutil.which("tesseract"):
        assert "aumentada" in text.lower()
    else:
        assert "Tesseract" in text


def test_page_detection_shows_a_preview_of_the_pdf(eddie, qapp, sample_pdf):
    ctx, window, messages = eddie
    page = ctx.pages["page"]
    assert page.open_pdf(str(sample_pdf))
    assert page.form.pdfPreview.pixmap() is not None
    assert page.form.labelPreviewPage.text() == "Página 1 / 3"
    page.show_preview(2)
    assert page.form.labelPreviewPage.text() == "Página 2 / 3"
    page.show_preview(99)                                   # fuera de rango: se queda en la última
    assert page.form.labelPreviewPage.text() == "Página 3 / 3"


def test_info_icons_and_buttons_with_help_do_not_raise(eddie, qapp, monkeypatch):
    # Regresión: el clic de los botones "Browse" llegaba como False a la ayuda y fallaba.
    import sys
    from PySide6.QtWidgets import QAbstractButton, QFileDialog
    ctx, window, messages = eddie
    errors = []
    monkeypatch.setattr(sys, "excepthook", lambda *exc: errors.append(exc[1]))
    for name in ("getExistingDirectory",):
        monkeypatch.setattr(QFileDialog, name, lambda *a, **k: "")
    for name in ("getOpenFileName", "getSaveFileName"):
        monkeypatch.setattr(QFileDialog, name, lambda *a, **k: ("", ""))
    for page in ctx.pages.values():
        for control in page.TOOLTIPS:
            widget = page.form.controls.get(control)
            if widget is None:
                continue
            if isinstance(widget, QAbstractButton):
                widget.click()                                  # emite clicked(checked=False), como el usuario
            else:
                widget.clicked.emit()
            qapp.processEvents()
    assert not errors, errors


# ---------------------------------------------------------------------------- diseño de la interfaz
def _is_yellow(hex_color: str) -> bool:
    import colorsys
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return 45 <= h * 360 <= 70 and s > 0.45 and v > 0.55


def test_interface_chrome_never_uses_yellow():
    # El botón de resaltado ya no es amarillo, para no confundirse con el resaltador (Ibaceta, 2023).
    import re
    from ui import theme
    colors = set(re.findall(r"#[0-9A-Fa-f]{6}", theme.QSS + theme.PROJECTION_QSS))
    colors |= {value for name, value in vars(theme).items()
               if name.isupper() and isinstance(value, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", value)}
    assert colors and not [c for c in colors if _is_yellow(c)]


def test_pending_modules_show_the_stage_where_they_arrive(eddie):
    ctx, window, _ = eddie
    from ui.menu_settings import NAV, PAGES
    for button, key in NAV.items():
        widget = window.form[button]
        if key in ctx.pages:
            assert widget.isEnabled() and widget.pending == ""
        else:
            assert not widget.isEnabled() and widget.pending == PAGES[key][1]


def test_messages_are_non_blocking_notices(qapp, eddie, monkeypatch):
    # message() muestra un aviso en la ventana en vez de un cuadro modal que detiene el uso.
    import importlib
    from PySide6.QtWidgets import QMessageBox
    ctx, window, _ = eddie
    dialogs = importlib.reload(importlib.import_module("ui.dialogs"))
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: pytest.fail("no debe ser modal"))
    dialogs.message(ctx.pages["page"], "No se pudo abrir el PDF", "Problem found")
    host = dialogs.ToastHost.for_window(window)
    assert [t.text for t in host.toasts] == ["No se pudo abrir el PDF"]
    assert host.toasts[0].property("kind") == "error"


def test_session_home_reflects_the_real_state(eddie, qapp, sample_pdf):
    ctx, window, _ = eddie
    window.open_page(None)
    state, _button = window.home.rows["page"]
    window.refresh_status()
    assert state.property("state") == "warn" and window.form.PageDetectionButton.status == "warn"
    ctx.pages["page"].open_pdf(str(sample_pdf))
    window.refresh_status()
    assert state.property("state") == "ok" and window.form.PageDetectionButton.status == "ok"
    window.home.rows["text"][1].click()
    assert window.current_page() == "text"


def test_status_panel_reports_plugins_and_cycle_time(eddie, qapp):
    import re
    ctx, window, _ = eddie
    _settle(ctx, qapp, 3)
    window.refresh_status()
    text = window.form.systemStatus.text()
    assert re.search(r"\d+ de \d+ plugins activos", text) and "Ciclo del orquestador" in text
