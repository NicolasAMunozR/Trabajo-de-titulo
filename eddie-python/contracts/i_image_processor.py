"""
contracts/i_image_processor.py
================================
Contrato de interfaz para el módulo de procesamiento de imágenes (OCR).

Reemplaza:
  - ModuloProcesamientoImagenes/OCRProcess.cs
  - ModuloProcesamientoImagenes/ColorRecognition.cs
  - ModuloProcesamientoImagenes/CameraActivity.cs
"""
from abc import abstractmethod
from typing import Optional
from contracts.plugin_base import PluginBase


class IImageProcessor(PluginBase):
    """
    Contrato para el procesador de imágenes y OCR.

    Implementaciones deben capturar frames de cámara,
    aplicar preprocesamiento y extraer texto mediante OCR.
    """

    @abstractmethod
    def capture_frame(self) -> Optional[object]:
        """
        Captura un frame de la cámara configurada.

        Returns:
            numpy.ndarray | None: Frame capturado o None si falla.
        """
        pass

    @abstractmethod
    def preprocess(self, frame: object) -> object:
        """
        Aplica preprocesamiento al frame para mejorar el OCR.
        (escala de grises, binarización, denoising)

        Args:
            frame: numpy.ndarray con el frame original.

        Returns:
            numpy.ndarray: Frame preprocesado listo para OCR.
        """
        pass

    @abstractmethod
    def extract_text(self, frame: object) -> str:
        """
        Aplica OCR al frame preprocesado y retorna el texto detectado.

        Args:
            frame: numpy.ndarray preprocesado.

        Returns:
            str: Texto detectado por el motor OCR.
        """
        pass

    @abstractmethod
    def get_precision_recall(self, expected_words: list[str]) -> dict:
        """
        Calcula precisión y recall del OCR contra un conjunto de palabras esperadas.
        Requerimiento del seminario: validar con mínimo 10 palabras.

        Args:
            expected_words (list[str]): Palabras esperadas en el texto.

        Returns:
            dict: {'precision': float, 'recall': float, 'f1': float}
        """
        pass
