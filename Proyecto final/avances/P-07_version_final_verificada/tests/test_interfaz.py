# Pruebas del diseño de la interfaz: zona de lectura fija, botones arriba, sin amarillo y flujos asistidos.
import colorsys
import re

import pytest

from tests.test_ui_flows import _settle, eddie  # noqa: F401  (fixture compartida)


def _is_yellow(hex_color: str) -> bool:
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return 45 <= h * 360 <= 70 and s > 0.45 and v > 0.55


def test_interface_chrome_never_uses_yellow():
    # El amarillo queda solo para el resaltado; ningún color del sistema visual lo usa (Ibaceta, 2023).
    from ui import theme
    colors = set(re.findall(r"#[0-9A-Fa-f]{6}", theme.QSS + theme.PROJECTION_QSS))
    colors |= {value for name, value in vars(theme).items()
               if name.isupper() and isinstance(value, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", value)}
    assert colors and not [c for c in colors if _is_yellow(c)]


def test_projection_keeps_reading_area_and_moves_buttons_to_the_upper_band(eddie, qapp):
    # La zona de lectura y las cruces no se mueven; los botones van arriba y la franja inferior central queda libre.
    from ui.widgets import ToolButton
    ctx, window, _ = eddie
    window.start_projection()
    screen = ctx.projection
    f = screen.form
    assert screen.highlight.geometry().getRect() == (285, 65, 517, 400)
    assert [f[n].pos().toTuple() for n in ("pictureBox3", "pictureBox4", "pictureBox5")] == \
        [(298, 20), (297, 570), (797, 570)]
    top_level = [w for w in screen.findChildren(ToolButton) if w.parent() is screen]
    assert len(top_level) >= 15
    for button in top_level:
        assert button.geometry().bottom() < 130, button.objectName()
    assert f.markButton.geometry().top() > 680 and f.markButton.geometry().left() > 1100


def test_mode_button_tells_the_current_mode(eddie, qapp):
    ctx, window, _ = eddie
    window.start_projection()
    screen = ctx.projection
    button = screen.form.textImageButton
    assert button.label == "Capturando" and not button.active
    screen.toggle_mode()
    assert button.label == "Resaltando" and button.active and screen.highlight.highlight_on


def test_answered_service_is_marked_and_cleared_on_close(eddie, qapp):
    ctx, window, _ = eddie
    window.start_projection()
    screen = ctx.projection
    f = screen.form
    f.textBox1.setPlainText("aumentada")
    screen.toggle_web_search()
    assert f.btn_buscarWeb.active
    screen.search_definition()
    _settle(ctx, qapp)
    assert f.btn_diccionario.active and not f.btn_traductor.active
    screen.close_left()
    assert not f.btn_diccionario.active


def test_synchronizer_shows_its_card_and_keeps_one_panel_per_side(eddie, qapp, sample_pdf):
    ctx, window, _ = eddie
    ctx.pages["page"].open_pdf(str(sample_pdf))
    window.start_projection()
    screen = ctx.projection
    f = screen.form
    screen.search_encyclopedia()
    assert f.panel2.isVisible()
    screen.toggle_synchronizer()
    assert f.syncCard.isVisible() and f.btn_sincronizadorPdf.active
    assert not f.panel2.isVisible(), "la tarjeta del PDF y los resultados no se superponen"
    screen.change_page(+1)
    assert f.syncPDFLabel.text() == "Página 2 de 3"


def test_messages_are_non_blocking_notices(qapp, eddie, monkeypatch):
    # message() ya no abre un cuadro modal: muestra un aviso en la ventana y la ejecución sigue.
    import importlib
    from PySide6.QtWidgets import QMessageBox
    ctx, window, _ = eddie
    dialogs = importlib.reload(importlib.import_module("ui.dialogs"))
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: pytest.fail("no debe ser modal"))
    dialogs.message(ctx.pages["page"], "No se pudo abrir el PDF", "Problem found")
    host = dialogs.ToastHost.for_window(window)
    assert [t.text for t in host.toasts] == ["No se pudo abrir el PDF"]
    assert host.toasts[0].property("kind") == "error"
    for _ in range(5):
        dialogs.message(window, "aviso")
    assert len(host.toasts) == dialogs.ToastHost.MAX


def test_session_home_reflects_the_real_state(eddie, qapp, sample_pdf):
    ctx, window, _ = eddie
    window.open_page(None)
    assert window.current_page() is None
    state, _button = window.home.rows["page"]
    window.refresh_status()
    assert state.property("state") == "warn"
    assert window.form.PageDetectionButton.status == "warn"
    ctx.pages["page"].open_pdf(str(sample_pdf))
    window.refresh_status()
    assert state.property("state") == "ok" and window.form.PageDetectionButton.status == "ok"
    window.home.rows["gesture"][1].click()
    assert window.current_page() == "gesture"


def test_calibration_points_are_copied_from_the_sensor_reading(eddie, qapp):
    ctx, window, messages = eddie
    page = ctx.pages["gesture"]
    f = page.form
    f.textBoxX.setText("")
    assert page.set_calibration_point("start") is False
    assert "lectura del sensor" in messages[-1]
    f.textBoxX.setText("212")
    f.textBoxY.setText("48")
    f.buttonSetStart.click()
    assert (f.numericUpDownSStartX.value(), f.numericUpDownSStartY.value()) == (212, 48)
    f.textBoxX.setText("901")
    f.textBoxY.setText("655")
    f.buttonSetEnd.click()
    assert (f.numericUpDownSEndX.value(), f.numericUpDownSEndY.value()) == (901, 655)
    assert page.calibration().sensor_end_x == 901


def test_status_panel_reports_plugins_and_cycle_time(eddie, qapp):
    ctx, window, _ = eddie
    _settle(ctx, qapp, 3)
    window.refresh_status()
    text = window.form.systemStatus.text()
    assert re.search(r"\d+ de \d+ plugins activos", text) and "Ciclo del orquestador" in text
