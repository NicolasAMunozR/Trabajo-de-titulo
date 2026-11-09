# Dependencias de contratos de inyección de dependencias para plugins que procesan imágenes y realizan OCR.
from abc import abstractmethod
from contracts.i_camera_frame_consumer import ICameraFrameConsumer
from contracts.i_camera_sensor import CameraFrame, ImageArray
from contracts.plugin_base import PluginBase

class IImageProcessor(PluginBase, ICameraFrameConsumer):
    # Recibe su fuente de frames desde el orquestador, nunca abre una cámara.
    @abstractmethod
    def preprocess(self, frame: CameraFrame) -> ImageArray:
        # Preprocesa el frame de cámara para mejorar la calidad de OCR.
        # Devuelve el frame preprocesado para OCR.
        pass

    @abstractmethod
    def extract_text(self, frame: ImageArray) -> str:
        # Extrae el texto del frame dado utilizando OCR.
        # Devuelve el texto detectado por OCR en el frame dado.
        pass

    @abstractmethod
    def extract_text_with_regions(self, frame: ImageArray) -> dict:
        # Extrae el texto del frame dado utilizando OCR y devuelve información adicional sobre las regiones de texto detectadas.
        pass

    @abstractmethod
    def recognize_highlighted_text(self, frame: CameraFrame) -> dict:
        # Detecta la zona resaltada en el frame de cámara, la recorta y aplica OCR.
        # Devuelve un diccionario con el texto detectado, el frame anotado, el
        pass

    @abstractmethod
    def get_precision_recall(self, expected_words: list[str]) -> dict:
        # Calcula la precisión, recall y F1-score del OCR comparando el texto detectado con las palabras esperadas.
        # Devuelve un diccionario con precisión, recall y F1-score del OCR comparado con las palabras esperadas.
        pass
