# Plugin de consistencia bidireccional físico-digital (IConsistencyProvider) con PyMuPDF.
# Reemplaza DigitalDocSync.cs y las bibliotecas de consistencia que se cargaban por reflexión.
# Escribe sobre el PDF elegido creando una copia de respaldo "<archivo>.pdf.bac" por sesión.
import logging
import re
import shutil
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pymupdf as fitz

from contracts.i_consistency_provider import Annotation, IConsistencyProvider
from plugins.consistency import vision
from plugins.spatial_calibration import SpatialCalibration

logger = logging.getLogger(__name__)

_YELLOW = (1.0, 1.0, 0.0)
_MAGENTA = (1.0, 0.0, 1.0)
_GREEN = (0.0, 0.8, 0.0)
_BOOKMARK_LABEL = re.compile(r"^(?P<title>.*) Pag\.(?P<page>\d+)$")


class ConsistencyPlugin(IConsistencyProvider):
    # Sincroniza resaltados, marcadores, comentarios y figuras entre papel y PDF.

    @property
    def name(self) -> str:
        return 'ConsistencyProvider'

    # ------------------------------------------------------------------ ciclo de vida
    def initialize(self, config: dict) -> bool:
        self._pdf_path = config.get('pdf_path', '')
        self._document = None
        self.last_load_error = ""
        self._backup_done = False
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
        self._camera_rotated = bool(config.get("camera_rotated_180", True))
        self._make_backup = bool(config.get("backup", True))
        self._calibration = None
        calibration_config = config.get("spatial_calibration")
        if calibration_config:
            self._calibration = SpatialCalibration.from_config(calibration_config)

        if self._pdf_path and not self.load_document(self._pdf_path):
            # Un PDF guardado que ya no se puede abrir no debe dejar sin consistencia al resto
            # del sistema: se sigue sin documento y el usuario elige otro en "Page detection".
            logger.warning("[ConsistencyProvider] No se cargó el PDF guardado (%s). Seleccione otro "
                           "en 'Page detection'.", self.last_load_error)
            self._pdf_path = ""
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
            logger.info("[ConsistencyProvider] Sin calibración espacial; los resaltados automáticos "
                        "por mirada quedan desactivados (los manuales funcionan).")
        return True

    def execute(self) -> dict:
        status = self._last_sync.get("status")
        if status != self._reported_sync_status:
            logger.debug("[ConsistencyProvider] estado=%s, página=%s", status, self._current_page)
            self._reported_sync_status = status
        return {
            'current_page': self._current_page,
            'annotation_count': len(self._annotations),
            'document_loaded': self._document is not None,
            'pdf_path': self._pdf_path,
            'calibrated': self._calibration is not None,
            'last_sync': dict(self._last_sync),
        }

    def release(self) -> None:
        try:
            if self._document is not None:
                self._document.close()
                self._document = None
        except Exception as exc:
            logger.warning("[ConsistencyPlugin] WARN en release: %s", exc)
        self._initialized = False

    # ------------------------------------------------------------------ correlación por ciclo
    def consume_cycle_results(self, results: dict[str, dict]) -> None:
        # Relaciona las salidas de OCR, mirada y gesto, y guarda el texto confirmado.
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
                float(region["x"]), float(region["y"]), float(region["width"]),
                float(region["height"]), frame_width, frame_height)
            if page_rect is not None:
                mapped_regions.append((region, page_rect))

        target = self._find_gaze_target(gaze_on_page, mapped_regions)
        if target is None:
            self._last_sync = {"status": "no_ocr_target", "gaze_page": gaze_on_page,
                               "mapped_ocr_regions": len(mapped_regions)}
            return
        if not rising_click:
            self._last_sync = {"status": "waiting_for_gesture_click", "gaze_page": gaze_on_page,
                               "text": target[0]["text"], "mapped_ocr_regions": len(mapped_regions)}
            return

        region, rect = target
        annotation = Annotation(page_number=self._current_page, x0=rect[0], y0=rect[1], x1=rect[2],
                                y1=rect[3], annotation_type="highlight", content=region["text"])
        self.add_highlight(annotation)
        self._last_sync = {"status": "annotated", "page_number": annotation.page_number,
                           "text": annotation.content, "gaze_page": gaze_on_page,
                           "rect": [annotation.x0, annotation.y0, annotation.x1, annotation.y1],
                           "mapped_ocr_regions": len(mapped_regions)}

    def _find_gaze_target(self, gaze, regions):
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

    # ------------------------------------------------------------------ documento
    def load_document(self, pdf_path: str) -> bool:
        # Carga el PDF (PageDetectionSettings → 'Select PDF' → new DigitalDocSync).
        self.last_load_error = ""
        try:
            document = self._open_valid_pdf(pdf_path)
        except Exception as exc:
            self.last_load_error = str(exc)
            logger.error("[ConsistencyPlugin] ERROR cargando PDF '%s': %s", pdf_path, exc)
            return False                                  # se conserva el documento anterior, si había
        if getattr(self, "_document", None) is not None:
            self._document.close()
        self._document = document
        self._pdf_path = str(pdf_path)
        self._backup_done = False
        self._current_page = 1
        logger.info("[ConsistencyPlugin] PDF cargado: %s (%s páginas)", pdf_path, document.page_count)
        return True

    @staticmethod
    def _open_valid_pdf(pdf_path: str) -> fitz.Document:
        # Abre el PDF y verifica que se pueda leer (PyMuPDF devuelve 0 páginas en vez de fallar si está dañado).
        if not Path(pdf_path).is_file():
            raise FileNotFoundError(f"No existe el archivo: {pdf_path}")
        damaged = ("El PDF está dañado o no tiene páginas legibles. Abra el archivo en un lector de PDF "
                   "para comprobarlo y use una copia sana (por ejemplo, descargándolo de nuevo).")
        try:
            document = fitz.open(pdf_path)
        except (fitz.FileDataError, RuntimeError) as exc:
            raise ValueError(damaged) from exc
        if document.needs_pass and not document.authenticate(""):
            document.close()
            raise ValueError("El PDF está protegido con contraseña. Use una copia sin contraseña.")
        if document.page_count == 0:
            document.close()
            raise ValueError(damaged)
        return document

    def _require_document(self) -> fitz.Document:
        if self._document is None:
            raise RuntimeError("No hay un PDF cargado. Selecciónelo en 'Page detection'.")
        return self._document

    def _page(self, page_number: int) -> fitz.Page:
        document = self._require_document()
        if not 1 <= page_number <= document.page_count:
            raise ValueError(f"Página fuera de rango: {page_number} (el PDF tiene {document.page_count}).")
        return document[page_number - 1]

    def _save(self) -> None:
        # Guarda los cambios en el mismo archivo, con respaldo .bac la primera vez.
        document = self._require_document()
        if self._make_backup and not self._backup_done and self._pdf_path:
            shutil.copyfile(self._pdf_path, self._pdf_path + ".bac")
            self._backup_done = True
        if document.can_save_incrementally():
            document.saveIncr()
        else:
            temp = self._pdf_path + ".tmp"
            document.save(temp, garbage=1)
            document.close()
            Path(temp).replace(self._pdf_path)
            self._document = fitz.open(self._pdf_path)

    @property
    def pdf_path(self) -> str:
        return self._pdf_path

    def get_current_page(self) -> int:
        return self._current_page

    def set_current_page(self, page_number: int) -> None:
        self._page(page_number)
        self._current_page = page_number

    def get_page_count(self) -> int:
        return self._require_document().page_count

    def get_page_size(self) -> tuple[float, float]:
        rect = self._page(self._current_page).rect
        return float(rect.width), float(rect.height)

    def render_page(self, page_number: int, width: int, height: int) -> np.ndarray:
        # Imagen BGR de la página (útil para la vista de proyección y la documentación).
        page = self._page(page_number)
        zoom = min(width / page.rect.width, height / page.rect.height)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        image = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # ------------------------------------------------------------------ resaltados (DigitalDocSync)
    def add_highlight(self, annotation: Annotation) -> bool:
        # DigitalDocSync.SaveAnno: crea una anotación Highlight amarilla en la página.
        if self._document is None:
            raise RuntimeError("No hay un PDF cargado para guardar la anotación.")
        page_idx = annotation.page_number - 1
        if not 0 <= page_idx < self._document.page_count:
            raise ValueError(f"Página fuera de rango: {annotation.page_number}.")
        if not (0 <= annotation.x0 < annotation.x1 <= 1 and 0 <= annotation.y0 < annotation.y1 <= 1):
            raise ValueError("Las coordenadas deben ser rectángulos normalizados válidos.")
        if annotation.annotation_type != 'highlight':
            raise NotImplementedError(f"Tipo de anotación no implementado: {annotation.annotation_type}")
        page = self._document[page_idx]
        rect = page.rect
        highlight_rect = fitz.Rect(annotation.x0 * rect.width, annotation.y0 * rect.height,
                                   annotation.x1 * rect.width, annotation.y1 * rect.height)
        annot = page.add_highlight_annot(highlight_rect)
        annot.set_colors(stroke=_YELLOW)
        if annotation.content:
            annot.set_info(content=annotation.content)
        annot.update()
        self._save()
        self._annotations.append(annotation)
        return True

    def get_annotations(self, page_number: int) -> list:
        # DigitalDocSync.GetRectAnno: todos los resaltados de la página, normalizados [0,1].
        page = self._page(page_number)
        width, height = page.rect.width, page.rect.height
        found = []
        for annot in page.annots(types=[fitz.PDF_ANNOT_HIGHLIGHT]) or []:
            vertices = annot.vertices or []                  # QuadPoints: área exacta resaltada
            r = fitz.Rect(min(v[0] for v in vertices), min(v[1] for v in vertices),
                          max(v[0] for v in vertices), max(v[1] for v in vertices)) if vertices else annot.rect
            found.append(Annotation(page_number, max(0.0, r.x0 / width), max(0.0, r.y0 / height),
                                    min(1.0, r.x1 / width), min(1.0, r.y1 / height), "highlight",
                                    annot.info.get("content", "")))
        return found

    def search_text(self, query: str) -> list[int]:
        # DigitalDocSync.SearchTxtPdf.
        document = self._require_document()
        query = (query or "").strip().lower()
        if not query:
            return []
        return [index + 1 for index, page in enumerate(document) if query in page.get_text().lower()]

    # ------------------------------------------------------------------ marcadores (PageMarkerDP/PD)
    def get_bookmarks(self) -> list[str]:
        return [f"{title} Pag.{page}" for _level, title, page, *_ in self._require_document().get_toc(simple=False)]

    def delete_bookmark(self, label: str) -> bool:
        match = _BOOKMARK_LABEL.match(label.strip())
        if not match:
            return False
        title, page = match.group("title").strip(), int(match.group("page"))
        document = self._require_document()
        toc = document.get_toc(simple=False)
        for index, (level, entry_title, entry_page, *_rest) in enumerate(toc):
            if entry_title.strip() == title and entry_page == page:
                del toc[index]
                document.set_toc(toc)
                self._save()
                return True
        return False

    def add_bookmark(self, title: str, page_number: int) -> None:
        self._page(page_number)
        document = self._require_document()
        toc = document.get_toc(simple=False)
        toc.append([1, title, page_number])
        document.set_toc(toc)
        self._save()

    def sync_bookmark_from_frame(self, frame: np.ndarray, page_number: int) -> bool:
        self._page(page_number)
        if not vision.detect_bookmark(self._oriented(frame)):
            return False
        self.add_bookmark(f"Marcador físico página {page_number}", page_number)
        return True

    # ------------------------------------------------------------------ comentarios (CommentsDP/PD)
    def get_comments(self) -> list[dict]:
        comments = []
        for index, page in enumerate(self._require_document()):
            for annot in page.annots(types=[fitz.PDF_ANNOT_TEXT, fitz.PDF_ANNOT_STAMP,
                                            fitz.PDF_ANNOT_FREE_TEXT]) or []:
                content = annot.info.get("content", "") or annot.info.get("subject", "")
                if annot.type[0] == fitz.PDF_ANNOT_STAMP and not content:
                    continue
                comments.append({"content": content, "page": index + 1,
                                 "x": float(annot.rect.x0), "y": float(annot.rect.y0)})
        return comments

    def delete_comment(self, content: str, page_number: int) -> bool:
        page = self._page(page_number)
        for annot in page.annots() or []:
            info = annot.info
            if (info.get("content", "") or info.get("subject", "")) == content:
                page.delete_annot(annot)
                self._save()
                return True
        return False

    def sync_comments_from_frame(self, frame: np.ndarray, page_number: int) -> int:
        page = self._page(page_number)
        oriented = self._oriented(frame)
        boxes = vision.detect_comments(oriented)
        if not boxes:
            return 0
        margin, y = 36.0, 36.0
        for count, (x, by, w, h) in enumerate(boxes, start=1):
            crop = oriented[by:by + h, x:x + w]
            ok, jpeg = cv2.imencode(".jpg", crop)
            if not ok:
                continue
            scale = min(0.5, (page.rect.width / 3) / max(w, 1))
            rect = fitz.Rect(margin, y, margin + w * scale, y + h * scale)
            label = f"Comentario físico {count} (pág. {page_number})"
            try:
                annot = page.add_stamp_annot(rect, stamp=jpeg.tobytes())
            except Exception:                         # PyMuPDF antiguo: imagen en el contenido
                page.insert_image(rect, stream=jpeg.tobytes())
                annot = page.add_text_annot(rect.tl, label)
            annot.set_info(content=label, subject=label)
            annot.update()
            y = rect.y1 + 8
        self._save()
        return len(boxes)

    # ------------------------------------------------------------------ figuras (FiguresDP/PD)
    def get_figures(self, page_number: int, view_size: tuple[int, int] = (400, 450)) -> dict:
        page = self._page(page_number)
        sx, sy = view_size[0] / page.rect.width, view_size[1] / page.rect.height
        figures = {"rectangulos": [], "circulos": []}
        for annot in page.annots(types=[fitz.PDF_ANNOT_SQUARE, fitz.PDF_ANNOT_CIRCLE]) or []:
            r = annot.rect
            item = {"x": r.x0 * sx, "y": r.y0 * sy, "width": r.width * sx, "height": r.height * sy}
            key = "rectangulos" if annot.type[0] == fitz.PDF_ANNOT_SQUARE else "circulos"
            figures[key].append(item)
        return figures

    def sync_figures_from_frame(self, frame: np.ndarray, page_number: int) -> int:
        page = self._page(page_number)
        oriented = self._oriented(frame)
        figures = vision.detect_figures(oriented)
        if not figures:
            return 0
        fh, fw = oriented.shape[:2]
        for figure in figures:
            rect = self._frame_rect_to_page(figure.x, figure.y, figure.width, figure.height, fw, fh, page)
            if rect.is_empty:
                continue
            if figure.kind == "rect":
                annot = page.add_rect_annot(rect)
                annot.set_colors(stroke=_YELLOW)
            else:
                annot = page.add_circle_annot(rect)
                annot.set_colors(stroke=_GREEN)
            annot.set_border(width=1.5)
            annot.set_info(content=f"Figura física ({figure.kind})")
            annot.update()
        self._save()
        return len(figures)

    def _frame_rect_to_page(self, x, y, w, h, fw, fh, page) -> fitz.Rect:
        if self._calibration is not None:
            mapped = self._calibration.map_camera_rect(x, y, w, h, fw, fh)
            if mapped is None:
                return fitz.Rect()
            x0, y0, x1, y1 = mapped
        else:
            x0, y0, x1, y1 = x / fw, y / fh, (x + w) / fw, (y + h) / fh
        pw, ph = page.rect.width, page.rect.height
        return fitz.Rect(x0 * pw, y0 * ph, x1 * pw, y1 * ph)

    def _oriented(self, frame: np.ndarray) -> np.ndarray:
        if frame is None:
            raise ValueError("Se requiere un frame de cámara para sincronizar anotaciones.")
        return cv2.rotate(frame, cv2.ROTATE_180) if self._camera_rotated else frame

    # ------------------------------------------------------------------ contrato general
    def sync_physical_to_digital(self, frame: object, page_number: int) -> list:
        # Ejecuta las tres sincronizaciones físico→digital y retorna lo creado.
        if frame is None:
            raise ValueError("Se requiere un frame de cámara para sincronizar anotaciones.")
        created = []
        if self.sync_bookmark_from_frame(frame, page_number):
            created.append(Annotation(page_number, 0, 0, 0, 0, "bookmark"))
        for _ in range(self.sync_comments_from_frame(frame, page_number)):
            created.append(Annotation(page_number, 0, 0, 0, 0, "comment"))
        for _ in range(self.sync_figures_from_frame(frame, page_number)):
            created.append(Annotation(page_number, 0, 0, 0, 0, "figure"))
        return created
