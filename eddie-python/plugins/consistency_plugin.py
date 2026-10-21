"""
plugins/consistency_plugin.py
=====================================
Implementación del plugin de consistencia bidireccional físico-digital.

Reemplaza:
  - ModuloConsistenciaDatos/DigitalDocSync.cs (iTextSharp)
  - BibliotecaConsistencia/* (6 bibliotecas de consistencia)
  - InterfacesModuloConsistencia/* (6 interfaces fragmentadas)

Migra la lógica de iTextSharp (C#) a PyMuPDF (Python), gestionando
la sincronización entre el documento físico (capturado por cámara)
y el PDF digital.

Dependencia:
  - pymupdf (fitz): lectura y anotación de PDFs
"""
import logging
from typing import Optional

from contracts.i_consistency_provider import IConsistencyProvider, Annotation
from plugins.spatial_calibration import SpatialCalibration

import pymupdf as fitz

logger = logging.getLogger(__name__)


class ConsistencyPlugin(IConsistencyProvider):
    """
    Plugin concreto para la consistencia bidireccional físico-digital.

    Gestiona la carga de PDFs, la detección de la página actual mediante
    visión computacional y la sincronización de anotaciones entre el
    documento físico y el PDF digital.

    Attributes:
        _pdf_path (str): Ruta al archivo PDF cargado.
        _document: Objeto fitz.Document (None si no hay PDF cargado).
        _current_page (int): Número de página actual (1-indexed).
        _annotations (list[Annotation]): Anotaciones acumuladas en sesión.
        _initialized (bool): Bandera del ciclo de vida.
    """

    @property
    def name(self) -> str:
        """Nombre identificador del plugin.

        Returns:
            str: 'ConsistencyProvider'
        """
        return 'ConsistencyProvider'

    def initialize(self, config: dict) -> bool:
        """
        Inicializa el plugin con la configuración provista.

        Args:
            config (dict): Parámetros de configuración. Claves relevantes:
                - 'pdf_path' (str): Ruta al PDF (default '').
                - 'pdf_path' (str): PDF a cargar. Se permite omitirlo
                  cuando el plugin solo se usa para gestionar la sesión.

        Returns:
            bool: True siempre (el plugin tolera ausencia de PDF).
        """
        self._pdf_path = config.get('pdf_path', '')
        self._document = None
        self._current_page = -1
        self._annotations: list[Annotation] = []
        self._cycle_results: dict[str, dict] = {}
        self._last_sync: dict = {"status": "waiting_for_cycle"}
        self._reported_sync_status = None
        self._previous_click = False
        self._ocr_plugin_name = config.get("ocr_plugin", "ImageProcessor")
        self._gaze_plugin_name = config.get("eye_tracker_plugin", "EyeTracker")
        self._gesture_plugin_name = config.get("gesture_plugin", "GesturePlugin")
        self._min_ocr_confidence = float(config.get("min_ocr_confidence", 0.6))
        self._selection_radius = float(config.get("selection_radius", 0.04))
        self._calibration = None
        calibration_config = config.get("spatial_calibration")
        if calibration_config:
            self._calibration = SpatialCalibration.from_config(calibration_config)

        if self._pdf_path and not self.load_document(self._pdf_path):
            return False
        if self._document is not None:
            page_number = int(config.get("page_number", 1))
            if not 1 <= page_number <= self._document.page_count:
                logger.error("Página configurada fuera del PDF: %s.", page_number)
                self._document.close()
                self._document = None
                return False
            self._current_page = page_number

        self._initialized = True
        if self._calibration is None:
            logger.warning(
                "[ConsistencyProvider] Sin calibración espacial; no se crearán "
                "anotaciones automáticas."
            )
        return True

    def execute(self) -> dict:
        """
        Ejecuta un ciclo del plugin de consistencia.

        Returns:
            dict: Diccionario con claves:
                - 'current_page' (int): Página actual del documento.
                - 'annotation_count' (int): Total de anotaciones en sesión.
                - 'document_loaded' (bool): True si hay un PDF cargado.
        """
        status = self._last_sync.get("status")
        if status != self._reported_sync_status:
            logger.info(
                "[ConsistencyProvider] Sincronización PDF: estado=%s, página=%s, "
                "anotaciones=%s.",
                status,
                self._current_page,
                len(self._annotations),
            )
            self._reported_sync_status = status
        return {
            'current_page': self._current_page,
            'annotation_count': len(self._annotations),
            'document_loaded': self._document is not None,
            'calibrated': self._calibration is not None,
            'last_sync': dict(self._last_sync),
        }

    def consume_cycle_results(self, results: dict[str, dict]) -> None:
        """Correlate OCR, gaze and gesture outputs and commit confirmed text."""
        self._cycle_results = dict(results)
        gesture = results.get(self._gesture_plugin_name, {})
        is_click = bool(gesture.get("is_click"))
        rising_click = is_click and not self._previous_click
        self._previous_click = is_click

        if self._calibration is None:
            self._last_sync = {"status": "calibration_missing"}
            return
        if self._document is None:
            self._last_sync = {"status": "pdf_not_loaded"}
            return

        gaze_result = results.get(self._gaze_plugin_name, {})
        gaze = gaze_result.get("gaze")
        if gaze is None:
            self._last_sync = {"status": "gaze_unavailable"}
            return
        gaze_on_page = self._calibration.map_gaze(gaze.x, gaze.y)
        if gaze_on_page is None:
            self._last_sync = {"status": "gaze_outside_page"}
            return

        ocr_result = results.get(self._ocr_plugin_name, {})
        frame_size = ocr_result.get("frame_size", {})
        frame_width = int(frame_size.get("width", 0))
        frame_height = int(frame_size.get("height", 0))
        mapped_regions = []
        for region in ocr_result.get("text_regions", []):
            if float(region.get("confidence", 0)) < self._min_ocr_confidence:
                continue
            page_rect = self._calibration.map_camera_rect(
                float(region["x"]),
                float(region["y"]),
                float(region["width"]),
                float(region["height"]),
                frame_width,
                frame_height,
            )
            if page_rect is not None:
                mapped_regions.append((region, page_rect))

        target = self._find_gaze_target(gaze_on_page, mapped_regions)
        if target is None:
            self._last_sync = {
                "status": "no_ocr_target",
                "gaze_page": gaze_on_page,
                "mapped_ocr_regions": len(mapped_regions),
            }
            return
        if not rising_click:
            self._last_sync = {
                "status": "waiting_for_gesture_click",
                "gaze_page": gaze_on_page,
                "text": target[0]["text"],
                "mapped_ocr_regions": len(mapped_regions),
            }
            return

        region, rect = target
        annotation = Annotation(
            page_number=self._current_page,
            x0=rect[0],
            y0=rect[1],
            x1=rect[2],
            y1=rect[3],
            annotation_type="highlight",
            content=region["text"],
        )
        self.add_highlight(annotation)
        self._last_sync = {
            "status": "annotated",
            "page_number": annotation.page_number,
            "text": annotation.content,
            "gaze_page": gaze_on_page,
            "rect": [annotation.x0, annotation.y0, annotation.x1, annotation.y1],
            "mapped_ocr_regions": len(mapped_regions),
        }

    def _find_gaze_target(
        self,
        gaze: tuple[float, float],
        regions: list[tuple[dict, tuple[float, float, float, float]]],
    ) -> Optional[tuple[dict, tuple[float, float, float, float]]]:
        gx, gy = gaze
        candidates = []
        for region, rect in regions:
            x0, y0, x1, y1 = rect
            dx = max(x0 - gx, 0.0, gx - x1)
            dy = max(y0 - gy, 0.0, gy - y1)
            distance = (dx * dx + dy * dy) ** 0.5
            if distance <= self._selection_radius:
                candidates.append((distance, region, rect))
        if not candidates:
            return None
        _, region, rect = min(candidates, key=lambda candidate: candidate[0])
        return region, rect

    def release(self) -> None:
        """
        Libera los recursos del plugin (cierra el documento PDF si está abierto).
        """
        try:
            if self._document is not None:
                self._document.close()
                self._document = None
        except Exception as exc:
            print(f"[ConsistencyPlugin] WARN en release: {exc}")
        self._initialized = False

    def load_document(self, pdf_path: str) -> bool:
        """
        Carga el documento PDF digital con PyMuPDF.

        Args:
            pdf_path (str): Ruta al archivo PDF.

        Returns:
            bool: True si el documento se cargó correctamente, False si falló.
        """
        try:
            self._document = fitz.open(pdf_path)
            self._current_page = 1
            print(f"[ConsistencyPlugin] PDF cargado: {pdf_path} ({self._document.page_count} páginas)")
            return True
        except Exception as exc:
            print(f"[ConsistencyPlugin] ERROR cargando PDF '{pdf_path}': {exc}")
            self._document = None
            return False

    def get_current_page(self) -> int:
        """
        Return the configured or selected PDF page, one-indexed.

        Returns:
            int: Número de página actual (1-indexed), o -1 si no detectado.
        """
        return self._current_page

    def add_highlight(self, annotation: Annotation) -> bool:
        """
        Agrega un highlight/subrayado al PDF digital y lo almacena en sesión.

        Equivalente a DigitalDocSync.SaveAnno() en C#.

        Args:
            annotation (Annotation): Datos de la anotación a agregar.
                Coordenadas normalizadas [0, 1] relativas a la página.

        Returns:
            bool: True si la anotación se registró correctamente.
        """
        if self._document is None:
            raise RuntimeError("No hay un PDF cargado para guardar la anotación.")
        page_idx = annotation.page_number - 1
        if not 0 <= page_idx < self._document.page_count:
            raise ValueError(f"Página fuera de rango: {annotation.page_number}.")
        if not (0 <= annotation.x0 < annotation.x1 <= 1
                and 0 <= annotation.y0 < annotation.y1 <= 1):
            raise ValueError("Las coordenadas deben ser rectángulos normalizados válidos.")
        if annotation.annotation_type != 'highlight':
            raise NotImplementedError(
                f"Tipo de anotación no implementado: {annotation.annotation_type}"
            )

        page = self._document[page_idx]
        rect = page.rect
        highlight_rect = fitz.Rect(
            annotation.x0 * rect.width,
            annotation.y0 * rect.height,
            annotation.x1 * rect.width,
            annotation.y1 * rect.height
        )
        annot = page.add_highlight_annot(highlight_rect)
        if annotation.content:
            annot.set_info(content=annotation.content)
        annot.update()
        self._document.saveIncr()
        self._annotations.append(annotation)
        return True

    def get_annotations(self, page_number: int) -> list:
        """
        Obtiene todas las anotaciones de una página específica.

        Equivalente a DigitalDocSync.GetRectAnno() en C#.

        Args:
            page_number (int): Número de página a consultar (1-indexed).

        Returns:
            list[Annotation]: Lista de anotaciones en la página indicada.
        """
        return [a for a in self._annotations if a.page_number == page_number]

    def sync_physical_to_digital(self, frame: object, page_number: int) -> list:
        """
        Detecta anotaciones físicas desde un frame y las transfiere al PDF.

        Args:
            frame: numpy.ndarray con imagen del documento físico.
            page_number (int): Página actual del documento.

        Returns:
            list[Annotation]: Anotaciones detectadas y sincronizadas.
        """
        if frame is None:
            raise ValueError("Se requiere un frame de cámara para sincronizar anotaciones.")
        raise NotImplementedError(
            "La detección automática de anotaciones físicas aún no está implementada."
        )
