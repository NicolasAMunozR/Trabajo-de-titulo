# Contrato para la consistencia bidireccional físico-digital.
# Reemplaza DigitalDocSync.cs y BibliotecaConsistencia usando PyMuPDF en lugar de iTextSharp.
from abc import abstractmethod
from dataclasses import dataclass
from contracts.i_camera_sensor import CameraFrame
from contracts.i_cycle_result_consumer import ICycleResultConsumer
from contracts.plugin_base import PluginBase


@dataclass
class Annotation:
    # Representa una anotación en el documento.
    page_number: int       # Página del documento (1-indexed)
    x0: float              # Coordenada izquierda normalizada [0,1]
    y0: float              # Coordenada superior normalizada [0,1]
    x1: float              # Coordenada derecha normalizada [0,1]
    y1: float              # Coordenada inferior normalizada [0,1]
    annotation_type: str   # 'highlight', 'comment', 'figure', 'bookmark'
    content: str = ""      # Texto del comentario (si aplica)


class IConsistencyProvider(PluginBase, ICycleResultConsumer):
    # Migra la lógica de iTextSharp (C#) a PyMuPDF (Python),
    # gestionando la sincronización entre el documento físico y el PDF digital.

    @abstractmethod
    def load_document(self, pdf_path: str) -> bool:
        # Carga el documento PDF digital. Devuelve True si se cargó correctamente.
        pass

    @abstractmethod
    def get_current_page(self) -> int:
        # Detecta la página actual del libro físico mediante visión computacional.
        # Devuelve el número de página actual (1-indexed), o -1 si no se detecta.
        pass

    @abstractmethod
    def add_highlight(self, annotation: Annotation) -> bool:
        # Agrega un subrayado al PDF digital (DigitalDocSync.SaveAnno). Devuelve True si se guardó.
        pass

    @abstractmethod
    def get_annotations(self, page_number: int) -> list:
        # Obtiene todas las anotaciones de una página del PDF (DigitalDocSync.GetRectAnno).
        pass

    # --- Operaciones de las 6 bibliotecas de consistencia del C# ---------------
    @abstractmethod
    def get_page_count(self) -> int:
        # Número de páginas del PDF cargado (DigitalDocSync.NPages).
        pass

    @abstractmethod
    def get_page_size(self) -> tuple[float, float]:
        # (ancho, alto) de la página en puntos PDF (DigitalDocSync.rectPage).
        pass

    @abstractmethod
    def search_text(self, query: str) -> list[int]:
        # Páginas (1-indexed) que contienen el texto (DigitalDocSync.SearchTxtPdf).
        pass

    @abstractmethod
    def get_bookmarks(self) -> list[str]:
        # Marcadores del PDF como 'Título Pag.N' (PageMarkerDP.GetPageMarker).
        pass

    @abstractmethod
    def delete_bookmark(self, label: str) -> bool:
        # Elimina un marcador 'Título Pag.N' (PageMarkerDP.DeleteMarker).
        pass

    @abstractmethod
    def get_comments(self) -> list[dict]:
        # Comentarios del PDF: {'content', 'page', 'x', 'y'} (CommentsDP.GetComments).
        pass

    @abstractmethod
    def delete_comment(self, content: str, page_number: int) -> bool:
        # Elimina un comentario del PDF.
        pass

    @abstractmethod
    def get_figures(self, page_number: int, view_size: tuple[int, int]) -> dict:
        # Obtiene las figuras digitales de la página escaladas a la vista (FiguresDP.ObtenerFiguras).
        # Devuelve {'rectangulos': [...], 'circulos': [...]}.
        pass

    @abstractmethod
    def sync_bookmark_from_frame(self, frame: CameraFrame, page_number: int) -> bool:
        # Detecta un marcador físico (azul) y crea el marcador digital (PageMarkerPD).
        pass

    @abstractmethod
    def sync_comments_from_frame(self, frame: CameraFrame, page_number: int) -> int:
        # Detecta notas físicas y las estampa en el PDF (CommentsPD). Retorna cuántas.
        pass

    @abstractmethod
    def sync_figures_from_frame(self, frame: CameraFrame, page_number: int) -> int:
        # Detecta figuras dibujadas a mano y las dibuja en el PDF (FiguresPD). Retorna cuántas.
        pass

    @abstractmethod
    def sync_physical_to_digital(self, frame: CameraFrame, page_number: int) -> list:
        # Detecta marcas físicas de lápiz desde un frame de cámara y las transfiere al PDF digital.
        # Devuelve la lista de anotaciones detectadas y sincronizadas.
        pass
