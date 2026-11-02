"""
ui/settings_pages.py
====================
Páginas de configuración embebidas en "EDDIE Menu Settings":

  InteractionPage        ← SeleccionInteraccionPorVoz2.cs ("Interactions WS")
  WebSearchPage          ← SeleccionApis2.cs ("Web search services"; ahora proveedores LLM)
  EyeTrackingPage        ← EyeTrackingConfiguration2.cs
  TextRecognitionPage    ← TextRecognitionSettings.cs
  GestureRecognitionPage ← GestureRecognitionSettings.cs
  PageDetectionPage      ← PageDetectionSettings.cs
"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QFileDialog, QToolTip, QWidget

from contracts.i_eye_tracker import IEyeTracker
from contracts.i_gesture_plugin import GestureCalibration, IGesturePlugin
from contracts.i_web_search_provider import IWebSearchProvider
from hardware.camera_enumeration import list_cameras
from ui.context import AppContext
from ui.dialogs import message
from ui.form_builder import ImageButton, build_form

logger = logging.getLogger(__name__)
PROJECT_DIR = Path(__file__).resolve().parents[1]


class SettingsPage(QWidget):
    LAYOUT = ""
    TOOLTIPS: dict[str, str] = {}

    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.setObjectName(self.LAYOUT)
        self.form = build_form(self.LAYOUT, self)
        for control, text in self.TOOLTIPS.items():
            widget = self.form.controls.get(control)
            if widget is not None:
                widget.setToolTip(text)
                if hasattr(widget, "clicked"):
                    widget.clicked.connect(lambda w=widget, t=text: QToolTip.showText(
                        w.mapToGlobal(QPoint(0, w.height())), t, w))

    def load_settings(self) -> None:
        """GetAllSettings (parte correspondiente a esta página)."""

    def save_settings(self) -> None:
        """SaveAllSettings (parte correspondiente a esta página)."""

    def on_cycle(self, results: dict) -> None:
        """Actualización periódica (vistas de cámara, coordenadas del sensor)."""


# ---------------------------------------------------------------------------- Interactions
class InteractionPage(SettingsPage):
    LAYOUT = "SeleccionInteraccionPorVoz2"
    TOOLTIPS = {
        "pictureBox1": "When activated it is possible to interact with the web search by means of voice prompts",
        "pictureBox2": "When activated, the web search buttons are displayed",
    }

    def load_settings(self) -> None:
        s = self.ctx.settings
        self.form.rbtn_Si_botones.setChecked(s["buttonDisplay"] == "Yes")
        self.form.rbtn_no_botones.setChecked(s["buttonDisplay"] == "No")
        self.form.rbtn_voz_si.setChecked(s["voiceInteraction"] == "Yes")
        self.form.rbtn_voz_no.setChecked(s["voiceInteraction"] == "No")

    def save_settings(self) -> None:
        s = self.ctx.settings
        if self.form.rbtn_Si_botones.isChecked():
            s["buttonDisplay"] = "Yes"
        if self.form.rbtn_no_botones.isChecked():
            s["buttonDisplay"] = "No"
        if self.form.rbtn_voz_si.isChecked():
            s["voiceInteraction"] = "Yes"
        if self.form.rbtn_voz_no.isChecked():
            s["voiceInteraction"] = "No"

    def reset(self) -> None:
        for radio in ("rbtn_Si_botones", "rbtn_no_botones", "rbtn_voz_si", "rbtn_voz_no"):
            widget = self.form[radio]
            widget.setAutoExclusive(False)
            widget.setChecked(False)
            widget.setAutoExclusive(True)

    @property
    def voice_enabled(self) -> bool:          # activarBusquedaVoz == "Yes"
        return self.form.rbtn_voz_si.isChecked()

    @property
    def show_buttons(self) -> bool:           # mostrarBotonesconVoz == "Yes"
        return self.form.rbtn_Si_botones.isChecked()


# ---------------------------------------------------------------------------- Web search services
class WebSearchPage(SettingsPage):
    LAYOUT = "SeleccionApis2"
    TOOLTIPS = {
        "pictureBox1": "Select the web search services for each type of search\n (encyclopedia, definitions, "
                       "images, video and translation),\n for translation select the language to translate into."
                       "\n\nEach service is answered by a language model (LLM) plugin.",
    }
    SERVICES = {
        "cbx_apisEnciclopedia": "encyclopediaApi",
        "cbx_apisDefiniciones": "definitionApi",
        "cbx_apisTraducciones": "translationApi",
        "cbx_apisVideos": "videoApi",
        "cbx_apisImagenes": "imageApi",
    }
    LANGUAGES = [("es", "Español"), ("en", "Inglés")]

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        self.refresh_providers()
        combo = self.form.cbx_idiomaTraducir
        combo.clear()
        for key, label in self.LANGUAGES:
            combo.addItem(label, key)
        combo.setCurrentIndex(-1)
        combo.setPlaceholderText("Select Service")

    def refresh_providers(self) -> None:
        """Equivale a obtenerListaApis*(): ahora los proveedores son plugins IWebSearchProvider."""
        providers = self.ctx.runtime.plugins_for(IWebSearchProvider)
        for combo_name in self.SERVICES:
            combo = self.form[combo_name]
            current = combo.currentData()
            combo.clear()
            combo.setEditable(False)
            combo.setPlaceholderText("Select Service")
            for provider in providers:
                ok = provider["status"] == "initialized"
                combo.addItem(provider["label"] + ("" if ok else "  (no disponible)"), provider["name"])
            index = combo.findData(current)
            combo.setCurrentIndex(index)

    def load_settings(self) -> None:
        s = self.ctx.settings
        available = [p["name"] for p in self.ctx.runtime.plugins_for(IWebSearchProvider)
                     if p["status"] == "initialized"]
        for combo_name, key in self.SERVICES.items():
            combo = self.form[combo_name]
            index = combo.findData(s[key])
            if index < 0 and available:                  # sin selección previa: primer LLM disponible
                index = combo.findData(available[0])
            combo.setCurrentIndex(index)
        lang = self.form.cbx_idiomaTraducir
        lang.setCurrentIndex(max(-1, lang.findText(s["languageTranslate"])) if s["languageTranslate"] else 0)

    def save_settings(self) -> None:
        s = self.ctx.settings
        for combo_name, key in self.SERVICES.items():
            s[key] = self.form[combo_name].currentData() or ""
        s["encyclopediaApiIndex"] = self.form.cbx_apisEnciclopedia.currentIndex()
        s["languageTranslate"] = self.form.cbx_idiomaTraducir.currentText()

    def provider_for(self, service: str) -> Optional[str]:
        """apiSeleccionada{Enciclopedia,Definicion,...} → nombre del plugin LLM."""
        combo = {"encyclopedia": "cbx_apisEnciclopedia", "definition": "cbx_apisDefiniciones",
                 "translation": "cbx_apisTraducciones", "video": "cbx_apisVideos",
                 "image": "cbx_apisImagenes"}[service]
        return self.form[combo].currentData()

    @property
    def target_language(self) -> str:
        return self.form.cbx_idiomaTraducir.currentData() or "es"


# ---------------------------------------------------------------------------- Eye tracking
class EyeTrackingPage(SettingsPage):
    LAYOUT = "EyeTrackingConfiguration2"
    TOOLTIPS = {
        "pictureBox1": "Select an available plugin,\nfirst select the path of your\ndirectory and select the plugin\navailable",
        "pictureBox2": "Select an available reticle,\nfirst select the path of your\ndirectory and select the reticle\navailable",
        "pictureBox3": "If selected it is possible to control the pointer with your gaze. Click(s) time is the number of "
                       "seconds that must elapse before a click is made when looking at a button.",
        "pictureBox4": "If selected, the data captured by the eye tracker are saved in a .csv file, you can give the "
                       "file a name and a save path.",
        "pictureBox5": "Select the eye tracking settings. The settings can be saved to a file using the 'Export Settings' "
                       "button and loaded with the 'Import Settings' button.",
        "pluginsRouteBrowse": "Presione el botón para seleccionar una carpeta desde la cual se cargarán\nlos plugins de "
                              "rastreo ocular (archivo plugins.json).",
        "reticlesRouteBrowse": "Presione el botón para seleccionar una carpeta desde la cual se cargarán\nlas distintas retículas.",
        "saveFileRouteBrowse": "Presione el botón para seleccionar una carpeta en la cual se guardarán los archivos\n"
                               "generados a partir de los datos capturados por el dispositivo de rastreo ocular.",
        "controlMouse": "Si se selecciona, el usuario podrá controlar el \npuntero con sus movimientos oculares.",
        "saveData": "Si se selecciona, los datos capturados por el eye tracker\nson guardados en un archivo .csv",
    }

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        f = self.form
        self.plugins_route = str(Path(ctx.runtime.config_path).resolve().parent)
        self.reticles_route = str(PROJECT_DIR / "ui" / "resources" / "reticles")
        self.save_route = str(PROJECT_DIR / "logs")
        Path(self.save_route).mkdir(exist_ok=True)
        self.active_tracker: Optional[str] = None
        self.overlay = None
        f.reticleExample.setScaledContents(True)
        f.reticleDimensions.setText("Ancho: 0px\nAlto: 0px")
        f.reticleDimensions.adjustSize()
        f.pluginsRoute.setText(self.plugins_route)
        f.reticlesRoute.setText(self.reticles_route)
        f.saveFileRoute.setText(self.save_route)
        f.clickTimer.setEnabled(False)
        f.fileNameTextBox.setEnabled(False)
        f.saveFileRouteBrowse.setEnabled(False)
        self._fill_trackers()
        self._fill_reticles()
        f.reticleSelected.currentIndexChanged.connect(self._reticle_changed)
        f.saveData.toggled.connect(lambda on: (f.fileNameTextBox.setEnabled(on), f.saveFileRouteBrowse.setEnabled(on)))
        f.controlMouse.toggled.connect(f.clickTimer.setEnabled)
        f.pluginsRouteBrowse.clicked.connect(self._browse_plugins)
        f.reticlesRouteBrowse.clicked.connect(self._browse_reticles)
        f.saveFileRouteBrowse.clicked.connect(self._browse_save)
        f.buttonModified2.clicked.connect(self.apply)                 # Apply
        f.buttonModified1.clicked.connect(self.export_settings)       # Export Settings
        f.buttonModified3.clicked.connect(self.import_settings)       # Import Settings

    def _fill_trackers(self) -> None:
        combo = self.form.trackingPlugins
        combo.clear()
        combo.addItem("None", None)
        for tracker in self.ctx.runtime.plugins_for(IEyeTracker):
            combo.addItem(tracker["label"], tracker["name"])
        combo.setCurrentIndex(0)

    def _fill_reticles(self) -> None:
        combo = self.form.reticleSelected
        combo.clear()
        combo.addItem("None")
        combo.addItems(sorted(p.name for p in Path(self.reticles_route).glob("*.png")))
        combo.setCurrentIndex(0)

    def _reticle_changed(self) -> None:
        name = self.form.reticleSelected.currentText()
        if name and name != "None":
            pm = QPixmap(str(Path(self.reticles_route) / name))
            self.form.reticleExample.setPixmap(pm)
            self.form.reticleDimensions.setText(f"Ancho: {pm.width()}px\nAlto: {pm.height()}px")
            self.form.reticleDimensions.adjustSize()

    def _browse_plugins(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Seleccione la carpeta con el plugins.json de rastreo ocular",
                                                  self.plugins_route)
        if folder:
            self.plugins_route = folder
            self.form.pluginsRoute.setText(folder)
            self._fill_trackers()

    def _browse_reticles(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Seleccione la carpeta donde se ubican las retículas",
                                                  self.reticles_route)
        if folder:
            self.reticles_route = folder
            self.form.reticlesRoute.setText(folder)
            self._fill_reticles()

    def _browse_save(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Seleccione la carpeta donde se desean almacenar los archivos con los datos generados por el eye tracker",
            self.save_route)
        if folder:
            self.save_route = folder
            self.form.saveFileRoute.setText(folder)

    def apply(self) -> None:
        """SaveChanges_MouseClick → IntermediateClass.InitializeClass(...)."""
        f, runtime = self.form, self.ctx.runtime
        tracker = f.trackingPlugins.currentData()
        if tracker is None:
            message(self, "No se ha seleccionado un plugin")
            return
        if self.active_tracker and self.active_tracker != tracker:
            runtime.orchestrator.stop_plugin(self.active_tracker)
        screen = QGuiApplication.primaryScreen().geometry()
        if not runtime.restart(tracker, {"screen_width": screen.width(), "screen_height": screen.height()}):
            report = runtime.orchestrator.initialization_report.get(tracker, {})
            message(self, f"No se pudo conectar el eye tracker '{f.trackingPlugins.currentText()}'.\n"
                          f"{report.get('error') or 'Verifique que el dispositivo y su servidor estén en ejecución.'}")
            return
        self.active_tracker = tracker
        csv_path = runtime.invoke("GazeSession", "configure_session", tracker, f.controlMouse.isChecked(),
                                  f.saveData.isChecked(), self.save_route, f.fileNameTextBox.text(),
                                  (screen.x(), screen.y(), screen.width(), screen.height())).value
        ImageButton.dwell_ms = f.clickTimer.value() * 1000 if f.controlMouse.isChecked() else 0
        self._set_overlay()
        extra = f"\nDatos en: {csv_path}" if csv_path else ""
        message(self, "Configuración seleccionada con éxito" + extra)

    def _set_overlay(self) -> None:
        from ui.projection_widgets import ReticleOverlay
        if self.overlay is not None:
            self.overlay.close()
            self.overlay = None
        name = self.form.reticleSelected.currentText()
        if name and name != "None":
            self.overlay = ReticleOverlay(str(Path(self.reticles_route) / name))
            self.overlay.show()

    def on_cycle(self, results: dict) -> None:
        if self.overlay is not None:
            point = results.get("GazeSession", {}).get("screen_point")
            if point:
                self.overlay.update_point(*point)

    def _config_values(self) -> dict:
        f = self.form
        return {"pluginsRoute": self.plugins_route, "pluginName": f.trackingPlugins.currentText(),
                "reticlesRoute": self.reticles_route, "reticleName": f.reticleSelected.currentText(),
                "mouseControl": f.controlMouse.isChecked(), "clickTime": f.clickTimer.value(),
                "saveData": f.saveData.isChecked(), "fileName": f.fileNameTextBox.text(),
                "fileRoute": self.save_route}

    def export_settings(self) -> None:
        """SettingsManager.SaveSettings: mismo formato JSON (FormAttributes) que el original."""
        default = f"config - {datetime.now():%d-%m-%Y_%H-%M-%S}.json"
        path, _ = QFileDialog.getSaveFileName(self, "Seleccione un directorio y un nombre para guardar su configuración",
                                              default, "Archivo JSON (*.json)")
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(self._config_values()), encoding="utf-8")
            message(self, "Configuración guardada con éxito")
        except OSError:
            message(self, "No se pudo guardar la configuración seleccionada.")

    def import_settings(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccione un archivo para cargar una configuración", "",
                                              "Archivo JSON (*.json)")
        if path:
            self.load_config_file(path)

    def load_config_file(self, path: str) -> bool:
        try:
            cfg = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cfg = None
        f = self.form
        valid = (cfg is not None and all(Path(cfg.get(k, "")).is_dir() for k in ("pluginsRoute", "reticlesRoute", "fileRoute"))
                 and (cfg.get("reticleName") == "None" or (Path(cfg["reticlesRoute"]) / cfg.get("reticleName", "")).is_file()))
        if valid:
            self.plugins_route, self.reticles_route, self.save_route = (cfg["pluginsRoute"], cfg["reticlesRoute"],
                                                                        cfg["fileRoute"])
            f.pluginsRoute.setText(self.plugins_route)
            f.reticlesRoute.setText(self.reticles_route)
            f.saveFileRoute.setText(self.save_route)
            f.controlMouse.setChecked(bool(cfg["mouseControl"]))
            f.clickTimer.setValue(int(cfg["clickTime"]))
            f.saveData.setChecked(bool(cfg["saveData"]))
            f.fileNameTextBox.setText(cfg.get("fileName", ""))
            self._fill_trackers()
            self._fill_reticles()
            index = f.trackingPlugins.findText(cfg["pluginName"])
            valid = index >= 0
            f.trackingPlugins.setCurrentIndex(max(0, index))
            f.reticleSelected.setCurrentIndex(max(0, f.reticleSelected.findText(cfg["reticleName"])))
        if valid:
            message(self, "Configuración cargada con éxito")
        else:
            message(self, "No se pudo cargar la configuración seleccionada.\nEl archivo pudo ser modificado o los "
                          "directorios\ny archivos señalados ya no existen o han sido   \nmovidos a otra ubicación.")
        return valid


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
    TOOLTIPS = {"pictureBox2": "Camera selection for OCR text recognition. The same camera must not be used for "
                               "gesture recognition."}

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        self._last_preview = 0.0
        _fill_cameras(self.form.ComboBoxCameraList1)
        self.form.ComboBoxCameraList1.currentIndexChanged.connect(self._camera_changed)

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
        """Abre la cámara elegida si cambió (ProyectionActivityBt: new VideoCapture(CameraNumber))."""
        self.save_settings()
        s, sensor = self.ctx.settings, self.ctx.runtime.plugin("TextCamera")
        wanted = {"camera_index": int(s["cameraTextIndex"]), "width": int(s["cameraTextWidth"]),
                  "height": int(s["cameraTextHeight"])}
        if sensor is None or getattr(sensor, "camera_index", None) != wanted["camera_index"]:
            self.ctx.runtime.restart("TextCamera", wanted)

    def show_recognition(self, result: dict) -> None:
        """imageBox1 = frame con el rectángulo; imageBox3 = recorte reconocido (TextImage)."""
        if result.get("annotated") is not None:
            self.form.imageBox1.show_frame(result["annotated"])
        if result.get("crop") is not None:
            self.form.imageBox3.show_frame(result["crop"])

    def on_cycle(self, results: dict) -> None:
        if not self.isVisible() or time.monotonic() - self._last_preview < 1 / 15:   # 15 FPS como el C#
            return
        self._last_preview = time.monotonic()
        sensor = self.ctx.runtime.plugin("TextCamera")
        if sensor is not None:
            self.form.imageBox3.show_frame(sensor.get_latest_frame())


class GestureRecognitionPage(SettingsPage):
    LAYOUT = "GestureRecognitionSettings"
    TOOLTIPS = {
        "pictureBox2": "Camera selection for gesture recognition. The same camera must not be used for text recognition. "
                       "Before starting the recognition you must select a plug-in.",
        "pictureBox1": "If the device is going to take control of the mouse such as the Hand Skin or Color Pen, activate "
                       "the Recognition on checkbox.",
        "pictureBox4": "'Sensor X' and 'Sensor Y' Displays the sensor information, relative coordinate in X and Y axis.\n "
                       "In 'Sensor start X' and 'Sensor start Y' the X and Y coordinates shown in the input 'Sensor X' and "
                       "'Sensor Y' must be entered when pointing the cursor to the center of the upper left calibration "
                       "cross.\n In 'Sensor end X' and 'Sensor end Y' the X and Y coordinates shown in the input 'Sensor X' "
                       "and 'Sensor Y' must be entered by pointing the cursor to the center of the lower right calibration "
                       "cross.",
    }
    CALIBRATION_FIELDS = ("numericUpDownSStartX", "numericUpDownSEndX", "numericUpDownAStartX", "numericUpDownAEndX",
                          "numericUpDownSStartY", "numericUpDownSEndY", "numericUpDownAStartY", "numericUpDownAEndY")

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        f = self.form
        _fill_cameras(f.ComboBoxCameraList2)
        f.comboBox1.clear()
        for plugin in ctx.runtime.plugins_for(IGesturePlugin):          # CreateFilterMenu()
            f.comboBox1.addItem(plugin["label"], plugin["name"])
        f.comboBox1.setCurrentIndex(-1)
        f.comboBox1.currentIndexChanged.connect(self._plugin_changed)
        f.StartProjectionButtonModified.clicked.connect(self.start_recognition)
        f.buttonModified1.clicked.connect(self.stop_recognition)
        f.buttonModified2.clicked.connect(self.capture)
        f.buttonModified3.clicked.connect(self.save_calibration)
        for field in self.CALIBRATION_FIELDS:
            f[field].valueChanged.connect(self._push_calibration)
        for check in ("checkBoxX", "checkBoxY", "checkBoxMouse"):
            f[check].toggled.connect(self._push_calibration)
        self._last_capture_seq = 0
        self.get_calibration_settings()

    # Properties.Settings.Default.ValorX1… (GetSettings / SaveSettings)
    def get_calibration_settings(self) -> None:
        s, f = self.ctx.settings, self.form
        f.numericUpDownSStartX.setValue(int(s["ValorX1"]))
        f.numericUpDownSStartY.setValue(int(s["ValorY1"]))
        f.numericUpDownSEndX.setValue(int(s["ValorX2"]))
        f.numericUpDownSEndY.setValue(int(s["ValorY2"]))

    def save_calibration(self) -> None:
        s, f = self.ctx.settings, self.form
        s["ValorX1"], s["ValorY1"] = f.numericUpDownSStartX.value(), f.numericUpDownSStartY.value()
        s["ValorX2"], s["ValorY2"] = f.numericUpDownSEndX.value(), f.numericUpDownSEndY.value()
        s.save()
        self.get_calibration_settings()

    def load_settings(self) -> None:
        s, f = self.ctx.settings, self.form
        f.ComboBoxCameraList2.setCurrentIndex(f.ComboBoxCameraList2.findData(s["cameraGestureIndex"]))
        f.numericUpDownXGestual.setValue(int(s["cameraGestureWidth"]))
        f.numericUpDownYGestual.setValue(int(s["cameraGestureHeight"]))
        f.comboBox1.setCurrentIndex(int(s["gestureComplementIndex"]) if f.comboBox1.count() else -1)
        f.numericUpDownSStartX.setValue(int(s["gestureValorX1"]))
        f.numericUpDownSStartY.setValue(int(s["gestureValorY1"]))
        f.numericUpDownSEndX.setValue(int(s["gestureValorX2"]))
        f.numericUpDownSEndY.setValue(int(s["gestureValorY2"]))
        f.checkBoxMouse.setChecked(bool(s["gestureRecognitionOnChecked"]))

    def save_settings(self) -> None:
        s, f = self.ctx.settings, self.form
        if f.ComboBoxCameraList2.currentIndex() >= 0:
            s["cameraGestureIndex"] = int(f.ComboBoxCameraList2.currentData())
        s["cameraGestureWidth"] = f.numericUpDownXGestual.value()
        s["cameraGestureHeight"] = f.numericUpDownYGestual.value()
        s["gestureComplementIndex"] = max(0, f.comboBox1.currentIndex())
        s["gestureValorX1"], s["gestureValorY1"] = f.numericUpDownSStartX.value(), f.numericUpDownSStartY.value()
        s["gestureValorX2"], s["gestureValorY2"] = f.numericUpDownSEndX.value(), f.numericUpDownSEndY.value()
        s["gestureRecognitionOnChecked"] = f.checkBoxMouse.isChecked()

    def _plugin_changed(self) -> None:
        was_active = self.active_plugin() is not None and self.active_plugin().recognition_active
        for name in self._gesture_names():
            plugin = self.ctx.runtime.plugin(name)
            if plugin is not None:
                plugin.set_recognition_active(False)
        self.ctx.active_gesture = self.form.comboBox1.currentData()
        if was_active:
            self.start_recognition()

    def _gesture_names(self) -> list[str]:
        return [self.form.comboBox1.itemData(i) for i in range(self.form.comboBox1.count())]

    def active_plugin(self):
        name = self.form.comboBox1.currentData()
        return self.ctx.runtime.plugin(name) if name else None

    def calibration(self) -> GestureCalibration:
        f = self.form
        return GestureCalibration(
            sensor_start_x=f.numericUpDownSStartX.value(), sensor_end_x=f.numericUpDownSEndX.value(),
            app_start_x=f.numericUpDownAStartX.value(), app_end_x=f.numericUpDownAEndX.value(),
            sensor_start_y=f.numericUpDownSStartY.value(), sensor_end_y=f.numericUpDownSEndY.value(),
            app_start_y=f.numericUpDownAStartY.value(), app_end_y=f.numericUpDownAEndY.value(),
            transform_x=f.checkBoxX.isChecked(), transform_y=f.checkBoxY.isChecked(),
            mouse_control=f.checkBoxMouse.isChecked())

    def _push_calibration(self) -> None:
        plugin = self.active_plugin()
        if plugin is not None:
            plugin.set_calibration(self.calibration())

    def start_recognition(self) -> None:
        """comenzarToolStripMenuItem_Click: abre la cámara gestual y activa el plug-in."""
        self.save_settings()
        if self.form.comboBox1.currentIndex() < 0:
            message(self, "Before starting the recognition you must select a plug-in.", "Problem")
            return
        s = self.ctx.settings
        sensor = self.ctx.runtime.plugin("GestureCamera")
        wanted = {"camera_index": int(s["cameraGestureIndex"]), "width": int(s["cameraGestureWidth"]),
                  "height": int(s["cameraGestureHeight"])}
        if sensor is None or getattr(sensor, "camera_index", None) != wanted["camera_index"]:
            if not self.ctx.runtime.restart("GestureCamera", wanted):
                message(self, "No se pudo abrir la cámara de reconocimiento gestual.", "Problem")
                return
        plugin = self.active_plugin()
        if plugin is None:
            message(self, f"El plug-in '{self.form.comboBox1.currentText()}' no está disponible.", "Problem")
            return
        self.ctx.active_gesture = self.form.comboBox1.currentData()
        plugin.set_calibration(self.calibration())
        plugin.set_recognition_active(True)

    def stop_recognition(self) -> None:
        plugin = self.active_plugin()
        if plugin is not None:
            plugin.set_recognition_active(False)

    def capture(self) -> None:
        """button4_Click → PutRectangle(RectangularSelection): recorta y guarda la imagen a buscar."""
        plugin = self.active_plugin()
        if plugin is None:
            message(self, "Before starting the recognition you must select a plug-in.", "Problem")
            return
        crop = plugin.capture_selection()
        self.show_capture(crop)

    def show_capture(self, crop) -> None:
        if crop is None:
            return
        self.form.imageBox4.show_frame(crop)
        ok, jpeg = cv2.imencode(".jpg", crop)
        if ok:
            self.ctx.capture_jpeg = jpeg.tobytes()             # byteImagenBuscada

    def on_cycle(self, results: dict) -> None:
        name = self.form.comboBox1.currentData()
        out = results.get(name, {}) if name else {}
        if not out.get("active"):
            return
        if out.get("capture_seq", 0) != self._last_capture_seq:          # selectedRectangle (AutoCamCapture)
            self._last_capture_seq = out["capture_seq"]
            plugin = self.active_plugin()
            if plugin is not None:
                self.show_capture(plugin.get_last_capture())
        if out.get("processed"):
            self.form.textBoxX.setText(str(out.get("sensor_x", 0)))
            self.form.textBoxY.setText(str(out.get("sensor_y", 0)))
            if self.isVisible():
                plugin = self.active_plugin()
                if plugin is not None:
                    self.form.imageBox2.show_frame(plugin.get_preview_frame())


# ---------------------------------------------------------------------------- Page detection
class PageDetectionPage(SettingsPage):
    LAYOUT = "PageDetectionSettings"
    TOOLTIPS = {"pictureBox2": "Select the PDF file to be synchronized with the physical book."}

    def __init__(self, ctx: AppContext) -> None:
        super().__init__(ctx)
        self.form.buttonModified1.clicked.connect(self.select_pdf)
        self.form.buttonModified2.clicked.connect(self.resize_highlight)
        self.form.textBoxPathPDF.setReadOnly(True)

    def load_settings(self) -> None:
        path = self.ctx.settings["pdfPath"]
        consistency = self.ctx.runtime.plugin("ConsistencyProvider")
        if path and consistency is not None and getattr(consistency, "pdf_path", "") == path:
            self._show_document(path)

    def select_pdf(self) -> None:
        """PDFSelectBt_Click → new DigitalDocSync(file)."""
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF (*.pdf)")
        if path:
            self.open_pdf(path)

    def open_pdf(self, path: str) -> bool:
        result = self.ctx.runtime.invoke("ConsistencyProvider", "load_document", path)
        if not result.ok or not result.value:
            consistency = self.ctx.runtime.plugin("ConsistencyProvider")
            reason = result.error or getattr(consistency, "last_load_error", "") or path
            message(self, f"No se pudo abrir el PDF:\n{reason}", "Problem found")
            return False
        self.ctx.settings["pdfPath"] = path
        self._show_document(path)
        return True

    def _show_document(self, path: str) -> None:
        self.form.textBoxPathPDF.setText(path)
        size = self.ctx.runtime.invoke("ConsistencyProvider", "get_page_size")
        if size.ok:
            width, height = size.value
            self.form.numericUpDown5.setValue(int(width))
            self.form.numericUpDown6.setValue(int(height))
            if self.ctx.projection is not None:
                self.ctx.projection.highlight.page_size = (width, height)

    def resize_highlight(self) -> None:
        """Resize_Click → Highlight.RuntimeFinalLocation(FinalLocateX, FinalLocateY)."""
        if self.ctx.projection is not None:
            self.ctx.projection.highlight.runtime_final_location(self.form.FinalLocateX.value(),
                                                                 self.form.FinalLocateY.value())
