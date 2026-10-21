"""
contracts/i_consistency_provider.py
=======================================
Contrato para el módulo de consistencia bidireccional físico-digital.

Reemplaza:
  - ModuloConsistenciaDatos/DigitalDocSync.cs (iTextSharp)
  - BibliotecaConsistencia/* (6 bibliotecas de consistencia)
  - InterfacesModuloConsistencia/* (6 interfaces fragmentadas)

Usa PyMuPDF (fitz) en lugar de iTextSharp.
"""
from abc import abstractmethod
from dataclasses import dataclass
from contracts.i_camera_sensor import CameraFrame
from contracts.i_cycle_result_consumer import ICycleResultConsumer
from contracts.plugin_base import PluginBase


@dataclass
class Annotation:
    """Representa una anotación en el documento."""
    page_number: int       # Página del documento (1-indexed)
    x0: float              # Coordenada izquierda normalizada [0,1]
    y0: float              # Coordenada superior normalizada [0,1]
    x1: float              # Coordenada derecha normalizada [0,1]
    y1: float              # Coordenada inferior normalizada [0,1]
    annotation_type: str   # 'highlight', 'comment', 'figure', 'bookmark'
    content: str = ""      # Texto del comentario (si aplica)


class IConsistencyProvider(PluginBase, ICycleResultConsumer):
    """
    Contrato para la consistencia bidireccional físico-digital.

    Migra la lógica de iTextSharp (C#) a PyMuPDF (Python),
    gestionando la sincronización entre el documento físico
    (capturado por cámara) y el PDF digital.
    """

    @abstractmethod
    def load_document(self, pdf_path: str) -> bool:
        """
        Carga el documento PDF digital.

        Args:
            pdf_path (str): Ruta al archivo PDF.

        Returns:
            bool: True si se cargó correctamente.
        """
        pass

    @abstractmethod
    def get_current_page(self) -> int:
        """
        Detecta la página actual del libro físico mediante visión computacional.
        (OCR del número de página o análisis de landmarks visuales)

        Returns:
            int: Número de página actual (1-indexed), o -1 si no se detecta.
        """
        pass

    @abstractmethod
    def add_highlight(self, annotation: Annotation) -> bool:
        """
        Agrega un subrayado/highlight al PDF digital.
        Equivalente a DigitalDocSync.SaveAnno() en C#.

        Args:
            annotation (Annotation): Datos de la anotación a agregar.

        Returns:
            bool: True si se guardó correctamente.
        """
        pass

    @abstractmethod
    def get_annotations(self, page_number: int) -> list:
        """
        Obtiene todas las anotaciones de una página del PDF.
        Equivalente a DigitalDocSync.GetRectAnno() en C#.

        Args:
            page_number (int): Número de página a consultar.

        Returns:
            list[Annotation]: Lista de anotaciones encontradas.
        """
        pass

    @abstractmethod
    def sync_physical_to_digital(self, frame: CameraFrame, page_number: int) -> list:
        """
        Detects physical pen marks from a camera frame and transfers them
        to the digital PDF. This is distinct from calibrated OCR/gaze
        selection, which is coordinated through consume_cycle_results().

        Args:
            frame: Frame BGR uint8 capturado por ICameraSensor.
            page_number (int): Página actual del documento.

        Returns:
            list[Annotation]: Anotaciones detectadas y sincronizadas.
        """
        pass
