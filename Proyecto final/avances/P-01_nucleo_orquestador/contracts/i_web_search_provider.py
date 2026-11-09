# Contrato para el proveedor de búsqueda web.
from abc import abstractmethod
from dataclasses import dataclass
from contracts.plugin_base import PluginBase

@dataclass
class SearchResult:
    # El contrato IWebSearchProvider define métodos para buscar en Wikipedia, obtener definiciones de palabras, reconocer imágenes, traducir texto y buscar videos en YouTube. Cada método devuelve un objeto SearchResult que contiene información relevante sobre el resultado de la búsqueda, incluyendo el término buscado, la fuente, el contenido textual, y URLs asociadas si aplican.
    query: str          # Término buscado
    source: str         # 'wikipedia', 'definition', 'youtube', 'image', 'translation'
    content: str        # Contenido textual del resultado
    url: str = ""       # URL fuente (si aplica)
    media_url: str = "" # URL de imagen/video (si aplica)


class IWebSearchProvider(PluginBase):
    # Recibe su fuente de datos desde el orquestador, nunca abre un navegador ni hace scraping.
    @abstractmethod
    def search_encyclopedia(self, query: str) -> SearchResult:
        # Devuelve un objeto SearchResult con el contenido de la página de Wikipedia correspondiente al término buscado.
        pass

    @abstractmethod
    def search_definition(self, word: str) -> SearchResult:
        # Devuelve un objeto SearchResult con la definición de la palabra buscada.
        pass

    @abstractmethod
    def search_image(self, image_bytes: bytes) -> SearchResult:
        # Devuelve un objeto SearchResult con la descripción de la imagen reconocida mediante visión computacional.
        pass

    @abstractmethod
    def translate_text(self, text: str, target_language: str) -> SearchResult:
        # Devuelve un objeto SearchResult con la traducción del texto al idioma objetivo especificado.
        pass

    @abstractmethod
    def search_video(self, query: str) -> SearchResult:
        # Devuelve un objeto SearchResult con la información del video de YouTube correspondiente al término buscado.
        pass
