# Contrato para el módulo de procesamiento de imágenes (OCR).
# Reemplaza OCRProcess.cs, ColorRecognition.cs y CameraActivity.cs.
from abc import abstractmethod
from contracts.i_camera_frame_consumer import ICameraFrameConsumer
from contracts.i_camera_sensor import CameraFrame, ImageArray
from contracts.plugin_base import PluginBase


class IImageProcessor(PluginBase, ICameraFrameConsumer):
    # Recibe frames BGR de un sensor y extrae texto con OCR; la captura pertenece a ICameraSensor.

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
        # Devuelve el texto OCR junto con las cajas de cada palabra y su confianza, en píxeles del frame.
        pass

    @abstractmethod
    def recognize_highlighted_text(self, frame: CameraFrame) -> dict:
        # Detecta la zona resaltada en el frame de cámara, la recorta y aplica OCR.
        # Devuelve un diccionario con el texto, el frame anotado, el recorte y la caja.
        pass

    @abstractmethod
    def get_precision_recall(self, expected_words: list[str]) -> dict:
        # Calcula la precisión, recall y F1-score del OCR comparando con las palabras esperadas.
        pass
