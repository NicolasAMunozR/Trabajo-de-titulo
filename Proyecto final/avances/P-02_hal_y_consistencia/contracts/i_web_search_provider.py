"""
contracts/i_web_search_provider.py
=====================================
Contrato de interfaz para el módulo de búsqueda web.

Las APIs externas del C# (Google, Bing, Wikipedia, YouTube, Cloud Vision) NO se usan.
En esta versión el contrato se implementa con un modelo de lenguaje
(plugins/llm_search_plugin.py → Google Gemini 2.5 Flash). Cada servicio (enciclopedia,
definiciones, traducción, video, imagen) apunta a un plugin que cumple este contrato,
así que otro LLM se agrega como un plugin más sin cambiar la interfaz.

Documenta la intención de reemplazar:
  - ModuloBusquedaWeb/* (BuscarDefinicion, BuscarEnciclopedia, etc.)
  - ApiWikipedia, ApiTraduccionBing, ApiDefinicionesGoogle, etc.
"""
from abc import abstractmethod
from dataclasses import dataclass
from contracts.plugin_base import PluginBase


@dataclass
class SearchResult:
    """Resultado de una búsqueda web."""
    query: str          # Término buscado
    source: str         # 'wikipedia', 'definition', 'youtube', 'image', 'translation'
    content: str        # Contenido textual del resultado
    url: str = ""       # URL fuente (si aplica)
    media_url: str = "" # URL de imagen/video (si aplica)


class IWebSearchProvider(PluginBase):
    """
    Contrato para el proveedor de búsqueda web.

    Implementación de referencia: LLMSearchPlugin (sin APIs de terceros vencidas).

    Elimina el peligroso patrón de carga por reflexión de
    ModuloBusquedaWeb/*.cs que era uno de los 16 errores arquitectónicos.
    """

    @abstractmethod
    def search_encyclopedia(self, query: str) -> SearchResult:
        """Busca en Wikipedia. Reemplaza ApiWikipedia.cs"""
        pass

    @abstractmethod
    def search_definition(self, word: str) -> SearchResult:
        """Busca definición de una palabra. Reemplaza ApiDefinicionesGoogle.cs"""
        pass

    @abstractmethod
    def search_image(self, image_bytes: bytes) -> SearchResult:
        """Reconoce imagen con visión computacional. Reemplaza ApiBusquedaImagenCloudVision.cs"""
        pass

    @abstractmethod
    def translate_text(self, text: str, target_language: str) -> SearchResult:
        """Traduce texto. Reemplaza ApiTraduccionBing.cs"""
        pass

    @abstractmethod
    def search_video(self, query: str) -> SearchResult:
        """Busca video en YouTube. Reemplaza ApiBuscarYoutube.cs"""
        pass
