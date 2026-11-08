"""Pruebas de la interfaz renovada (P-08, Qt offscreen): controles del original y flujos completos de EDDIE."""
import json
import os
import shutil

import pymupdf
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from ui.form_builder import LAYOUTS
from ui.modern_forms import build_modern

FORMS = ["MenuSettings", "SeleccionInteraccionPorVoz2", "SeleccionApis2", "EyeTrackingConfiguration2",
         "TextRecognitionSettings", "GestureRecognitionSettings", "PageDetectionSettings", "AlertBox",
         "ProjectionScreenActivity2", "LoadingBox", "busquedasRecientes2"]


def _nodes(nodes):
    for node in nodes:
        yield node
        yield from _nodes(node.get("children", []))


@pytest.mark.parametrize("name", FORMS)
def test_every_original_control_exists_in_the_new_interface(qapp, name):
    """P-08 cambia el diseño, pero cada control del original sigue existiendo con su nombre, un tipo
    compatible y el mismo comportamiento (rangos, valores, ítems), porque la lógica los usa por nombre."""
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
def eddie(qapp, tmp_path, monkeypatch, fake_llm):
    """EDDIE completo con dispositivos simulados y un LLM local falso."""
    monkeypatch.setenv("EDDIE_DEVICE_MODE", "sim")
    messages = []
    import ui.dialogs as dialogs
    import ui.menu_settings as menu
    import ui.projection_screen as projection
    import ui.settings_pages as pages
    record = lambda parent, text, title="EDDIE": messages.append(text)
    for module in (dialogs, menu, projection, pages):
        monkeypatch.setattr(module, "message", record)
    monkeypatch.setattr(projection, "PROJECT_DIR", tmp_path)
    (tmp_path / "logs").mkdir()
    from app.runtime import EddieRuntime
    from app.settings_store import SettingsStore
    from ui.context import AppContext
    settings = SettingsStore(tmp_path / "user_settings.json")
    runtime = EddieRuntime(settings, trace_dir=tmp_path / "logs")
    runtime.orchestrator._config_overrides["LLM-Gemini"] = {"config": {"base_url": fake_llm[0],
                                                                        "api_key": "test-key"}}
    runtime.start()
    ctx = AppContext(runtime=runtime, settings=settings)
    window = menu.MenuSettingsWindow(ctx)
    window.show()
    yield ctx, window, messages
    runtime.wait_for_jobs()
    if ctx.projection is not None:
        ctx.projection.close()
    window.close()
    runtime.stop()


def _settle(ctx, qapp, cycles=3):
    for _ in range(cycles):
        ctx.runtime._tick()
        ctx.runtime.wait_for_jobs()
        qapp.processEvents()


def _drag(widget, start, end):
    QTest.mousePress(widget, Qt.MouseButton.LeftButton, pos=QPoint(*start))
    QTest.mouseMove(widget, QPoint(*end))
    QTest.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=QPoint(*end))


def test_all_plugins_start_and_settings_pages_exist(eddie):
    ctx, window, _ = eddie
    report = ctx.runtime.orchestrator.initialization_report
    for name in ("TextCamera", "GestureCamera", "ImageProcessor", "ColorPenRecognition", "ConsistencyProvider",
                 "LLM-Gemini", "GazeSession"):
        assert report[name]["status"] == "initialized", name
    assert set(ctx.pages) == {"interactions", "web", "eye", "text", "gesture", "page"}
    assert ctx.pages["web"].provider_for("definition") == "LLM-Gemini"


def test_save_and_reset_settings_roundtrip(eddie, qapp):
    ctx, window, _ = eddie
    ctx.pages["interactions"].form.rbtn_voz_no.setChecked(True)
    ctx.pages["interactions"].form.rbtn_Si_botones.setChecked(True)
    ctx.pages["text"].form.numericUpDownResXText.setValue(1280)
    window.save_all_settings()
    stored = json.loads(ctx.settings.path.read_text(encoding="utf-8"))
    assert stored["voiceInteraction"] == "No" and stored["buttonDisplay"] == "Yes"
    assert stored["cameraTextWidth"] == 1280 and stored["definitionApi"] == "LLM-Gemini"
    window.reset_all_settings()
    assert ctx.settings["cameraTextWidth"] == 640
    assert not ctx.pages["interactions"].form.rbtn_voz_no.isChecked()


def test_highlight_ocr_then_llm_definition_flow(eddie, qapp, tmp_path):
    ctx, window, messages = eddie
    window.start_projection()
    screen = ctx.projection
    assert screen.isVisible()
    screen.toggle_mode()                                   # modo resaltado
    assert screen.highlight.highlight_on
    _drag(screen.highlight, (50, 100), (250, 100))         # el lector resalta
    _settle(ctx, qapp)
    assert ctx.pages["text"].form.imageBox1.pixmap() is not None       # imageBox1 con el rectángulo
    screen.form.textBox1.setPlainText("aumentada")         # (corrección manual del texto reconocido)
    screen.toggle_web_search()
    assert screen.form.btn_diccionario.isVisible()
    screen.search_definition()
    _settle(ctx, qapp)
    text = screen.form.rtb_result_definicion_traduccion.toPlainText()
    assert "Primera definición" in text and "Segunda definición" in text
    assert screen.form.panel3.isVisible() and screen.left_lines.segments
    screen.search_encyclopedia()
    _settle(ctx, qapp)
    assert "Segundo párrafo" in screen.form.rtb_ResultadosWikipedia.toPlainText()
    screen.close_right()
    assert not screen.form.panel2.isVisible() and not screen.right_lines.segments
    screen.write_activity_log()
    log = (tmp_path / "CSV_registro_actividades" / "log_actividades.csv").read_text(encoding="utf-8")
    assert "aumentada ; Diccionario" in log and "aumentada ; Enciclopedia" in log
    assert not messages


def test_capture_mode_image_search(eddie, qapp):
    ctx, window, messages = eddie
    gesture = ctx.pages["gesture"]
    gesture.form.comboBox1.setCurrentIndex(gesture.form.comboBox1.findData("ColorPenRecognition"))
    gesture.start_recognition()
    _settle(ctx, qapp, 5)
    gesture.capture()
    assert ctx.capture_jpeg
    window.start_projection()
    screen = ctx.projection
    screen.toggle_web_search()
    screen.search_image()
    _settle(ctx, qapp)
    assert screen.form.lbl_PalabraBuscada.text() == "Libro abierto"


def test_search_without_term_and_without_image_shows_original_messages(eddie, qapp):
    ctx, window, messages = eddie
    window.start_projection()
    screen = ctx.projection
    screen.search_encyclopedia()
    assert screen.form.rtb_ResultadosWikipedia.toPlainText() == "Seleccione un término para buscar"
    screen.search_image()
    assert "Seleccione una imagen para buscar" in messages


def test_pdf_highlight_sync_and_content_flow(eddie, qapp, sample_pdf):
    ctx, window, messages = eddie
    assert ctx.pages["page"].open_pdf(str(sample_pdf))
    assert ctx.pages["page"].form.numericUpDown5.value() == 595
    window.start_projection()
    screen = ctx.projection
    screen.toggle_synchronizer()
    assert screen.form.panel_log.isVisible() and screen.form.syncButton.isVisible()
    screen.toggle_mode()
    _drag(screen.highlight, (50, 100), (300, 100))
    _settle(ctx, qapp)
    screen.sync_highlight()
    assert screen.form.syncPDFLabel.text() == "Página 1 de 3"
    assert len(screen.highlight.rectangles) == 1
    with pymupdf.open(sample_pdf) as document:
        assert len(list(document[0].annots())) == 1
    screen.form.searchTextBox.setText("homografia")
    screen.search_pages()
    assert screen.form.PagesLabel.text() == "2"
    screen.form.searchTextBox.setText("1")
    screen.load_pdf_content()
    assert screen.figures_overlay is not None and screen.figures_overlay.isVisible()
    screen.physical_sync("sync_bookmark_from_frame")       # la hoja simulada no tiene marcador azul
    _settle(ctx, qapp)
    assert messages[-1] == "No se encontró marcador"


def test_pdf_tools_require_pdf_and_page_number(eddie):
    ctx, window, messages = eddie
    window.start_projection()
    ctx.projection.sync_highlight()
    assert messages[-1].startswith("Primero elige el PDF del libro")


def test_eye_tracking_apply_with_simulated_tracker(eddie, qapp, tmp_path):
    ctx, window, messages = eddie
    page = ctx.pages["eye"]
    f = page.form
    f.trackingPlugins.setCurrentIndex(f.trackingPlugins.findData("EyeTrackerMock"))
    f.reticleSelected.setCurrentIndex(1)
    f.saveData.setChecked(True)
    f.fileNameTextBox.setText("prueba")
    page.save_route = str(tmp_path)
    page.apply()
    _settle(ctx, qapp, 3)
    assert messages[-1].startswith("Configuración seleccionada con éxito")
    assert page.overlay is not None
    assert ctx.runtime.latest["GazeSession"]["samples"] >= 1
    assert list(tmp_path.glob("prueba - *.csv"))
    page.overlay.close()


def test_eye_tracking_export_import_settings_format(eddie, tmp_path, monkeypatch):
    ctx, window, messages = eddie
    page = ctx.pages["eye"]
    target = tmp_path / "config.json"
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(target), ""))
    page.export_settings()
    data = json.loads(target.read_text(encoding="utf-8"))
    assert set(data) == {"pluginsRoute", "pluginName", "reticlesRoute", "reticleName", "mouseControl",
                         "clickTime", "saveData", "fileName", "fileRoute"}
    assert page.load_config_file(str(target))


def test_light_palette_keeps_text_readable(qapp):
    """En Windows con modo oscuro Qt pintaba texto blanco sobre los fondos claros del original."""
    from PySide6.QtGui import QPalette
    palette = qapp.palette()
    assert palette.color(QPalette.ColorRole.Text).name() == "#000000"
    assert palette.color(QPalette.ColorRole.Base).name() == "#ffffff"
    assert palette.color(QPalette.ColorRole.WindowText).name() == "#000000"


def test_damaged_pdf_shows_message_instead_of_breaking_projection(eddie, qapp, tmp_path, sample_pdf):
    ctx, window, messages = eddie
    damaged = tmp_path / "danado.pdf"
    damaged.write_bytes(_as_text_copy(sample_pdf))
    assert ctx.pages["page"].open_pdf(str(damaged)) is False
    assert "dañado" in messages[-1]
    assert ctx.settings["pdfPath"] != str(damaged)
    window.start_projection()
    assert ctx.projection is not None and ctx.projection.isVisible()


def _as_text_copy(pdf_path):
    """Reproduce el daño real: un PDF comprimido copiado como texto UTF-8 (bytes → U+FFFD)."""
    import pymupdf
    with pymupdf.open(pdf_path) as document:
        data = document.tobytes(deflate=True, garbage=3, use_objstms=1)
    return data.decode("utf-8", "replace").encode("utf-8")


def test_text_page_recognizes_the_highlighted_word(eddie, qapp):
    """Text recognition muestra el rectángulo detectado y el texto reconocido (antes solo desde la proyección)."""
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
    """Regresión: clicked(bool) de los botones "Browse" llegaba como w=False a la lambda de la ayuda
    ("'bool' object has no attribute 'mapToGlobal'")."""
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
