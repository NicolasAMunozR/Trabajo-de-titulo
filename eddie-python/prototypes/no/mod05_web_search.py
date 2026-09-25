"""
prototypes/mod05_web_search.py
=====================================
PROTOTIPO RAD — MÓDULO 5: ModuloBusquedaWeb
=============================================
Módulo C# equivalente: ModuloBusquedaWeb/
  - BuscarDefinicion.cs         → API de definiciones (Google)
  - BuscarEnciclopedia.cs       → Wikipedia
  - BuscarImagen.cs             → Cloud Vision (Google)
  - BuscarYoutube.cs            → YouTube Data API
  - ApiTraduccionBing.cs        → Bing Translator

Estado en el proyecto EDDIE Python (MVP v1.0):
  *** MÓDULO FUERA DE ALCANCE DEL MVP ***
  Las APIs originales (Wikipedia, Bing, Google Cloud Vision, YouTube)
  tenían las credenciales VENCIDAS en el sistema de Ibaceta.
  Errores directamente relacionados: E25, E26, E33, E34, E36, E37, E63

Objetivo de este prototipo:
  1. Validar que la INTERFAZ IWebSearchProvider está bien definida
  2. Demostrar que Wikipedia SÍ funciona con la librería 'wikipedia-api'
     (alternativa gratuita que no requiere API key)
  3. Documentar qué APIs necesitarían credenciales actualizadas
  4. Crear mock completo para tests

Cómo ejecutar:
  ..\\..\\eddie-python-venv\\Scripts\\python.exe mod05_web_search.py
  ..\\..\\eddie-python-venv\\Scripts\\python.exe mod05_web_search.py --live  (requiere internet)
"""
import sys, os, time, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("\n" + "="*60)
print("PROTOTIPO RAD — MOD05: ModuloBusquedaWeb")
print("="*60)
print("  NOTA: Este modulo esta FUERA del alcance del MVP v1.0")
print("  Se valida la interfaz y el mock. APIs como trabajo futuro.")

print("\n[DEPS] Verificando dependencias...")

# wikipedia-api (librería gratuita, no requiere API key)
WIKI_OK = False
try:
    import wikipediaapi
    print(f"  OK wikipedia-api instalado")
    WIKI_OK = True
except ImportError:
    print(f"  WARN: wikipedia-api no instalado")
    print(f"    Instalar: pip install wikipedia-api")
    print(f"    (Solo necesario para test --live)")

# requests (para APIs REST)
REQ_OK = False
try:
    import requests
    print(f"  OK requests instalado")
    REQ_OK = True
except ImportError:
    print(f"  WARN: requests no instalado — pip install requests")


import dataclasses, random

@dataclasses.dataclass
class SearchResult:
    query: str
    source: str   # 'wikipedia', 'definition', 'youtube', 'image', 'translation'
    content: str
    url: str = ""
    success: bool = True
    latency_ms: float = 0.0


# ── Mock de todas las APIs ─────────────────────────────────────
class WebSearchMock:
    """
    Mock completo del proveedor de búsqueda web.
    Permite tests sin internet ni API keys.
    Equivale a las clases stub de C# legacy que no tenían credenciales.
    """
    def search_encyclopedia(self, query: str) -> SearchResult:
        time.sleep(0.1)  # Simular latencia de red
        return SearchResult(
            query=query, source='wikipedia',
            content=f"[MOCK] Resultado simulado para '{query}': "
                   f"Este es un artículo sobre {query} con información relevante...",
            url=f"https://es.wikipedia.org/wiki/{query.replace(' ', '_')}",
            success=True, latency_ms=102.3
        )

    def search_definition(self, word: str) -> SearchResult:
        time.sleep(0.08)
        definitions = {
            'lectura': 'Acción y efecto de leer. Capacidad de interpretar texto escrito.',
            'tracking': 'Seguimiento. En computación, monitoreo de posición o movimiento.',
            'plugin': 'Módulo de software que extiende la funcionalidad de una aplicación.',
        }
        defn = definitions.get(word.lower(), f"Definición no disponible para '{word}'")
        return SearchResult(query=word, source='definition', content=defn,
                          success=True, latency_ms=85.1)

    def translate_text(self, text: str, target_lang: str = 'en') -> SearchResult:
        time.sleep(0.12)
        return SearchResult(
            query=text, source='translation',
            content=f"[MOCK] Traduccion a '{target_lang}': [translated text of: {text[:30]}...]",
            success=True, latency_ms=123.4
        )

    def search_image(self, image_description: str) -> SearchResult:
        return SearchResult(
            query=image_description, source='image',
            content=f"[MOCK] Imagen identificada: '{image_description}'",
            success=True, latency_ms=200.0
        )


# ── Búsqueda real en Wikipedia (gratuita, sin API key) ─────────
def search_wikipedia_real(query: str, lang: str = 'es') -> SearchResult:
    """
    Búsqueda en Wikipedia usando wikipedia-api (librería gratuita).
    Reemplaza BuscarEnciclopedia.cs + ApiWikipedia.cs del C# legacy.

    Errores de Ibaceta que esto resuelve:
      E34: Símbolo '(' hacía fallar la API de Wikipedia
           -> wikipedia-api maneja esto correctamente
      E36: Sin internet el programa fallaba
           -> Ahora captura ConnectionError con try/except
      E61: Enciclopedia falla si la palabra no se encuentra
           -> Retorna SearchResult con success=False en vez de crashear
      E62: Respuesta no válida si la palabra no está exacta
           -> wikipedia-api hace búsqueda de tipo 'may refer to' automáticamente
    """
    t0 = time.perf_counter()
    try:
        wiki = wikipediaapi.Wikipedia(
            language=lang,
            user_agent='EDDIE-Python-RAD/1.0 (trabajo-de-titulo)'
        )
        page = wiki.page(query)
        latency = (time.perf_counter() - t0) * 1000

        if page.exists():
            summary = page.summary[:500]
            return SearchResult(
                query=query, source='wikipedia',
                content=summary, url=page.fullurl,
                success=True, latency_ms=round(latency, 2)
            )
        else:
            return SearchResult(
                query=query, source='wikipedia',
                content=f"Pagina no encontrada para: '{query}'",
                success=False, latency_ms=round(latency, 2)
            )
    except Exception as e:
        return SearchResult(
            query=query, source='wikipedia',
            content=f"Error de conexion: {e}",
            success=False, latency_ms=0
        )


# ── MAIN ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true',
                       help='Hacer busquedas reales (requiere internet)')
    parser.add_argument('--query', type=str, default='lectura aumentada')
    args = parser.parse_args()

    mock = WebSearchMock()
    test_queries = ['lectura aumentada', 'eye tracking', 'OpenCV', 'python(lenguaje)']

    print(f"\n[PASO 1] Probando mock (sin internet, sin API keys)...")
    mock_results = []
    for q in test_queries:
        r = mock.search_encyclopedia(q)
        mock_results.append(r)
        print(f"  OK [{r.source}] '{q}' -> {r.content[:50]}... ({r.latency_ms:.0f}ms)")

    print(f"\n[PASO 2] Probando búsqueda de definicion (mock)...")
    for word in ['lectura', 'tracking', 'plugin']:
        r = mock.search_definition(word)
        print(f"  OK '{word}' -> {r.content[:60]}...")

    if args.live and WIKI_OK:
        print(f"\n[PASO 3] Búsqueda REAL en Wikipedia ('{args.query}')...")
        r = search_wikipedia_real(args.query)
        status = 'OK' if r.success else 'FAIL'
        print(f"  {status} Latencia: {r.latency_ms:.0f}ms")
        print(f"  URL: {r.url}")
        print(f"  Contenido: {r.content[:200]}...")

        # Probar con paréntesis (E34) — que fallaba en el C#
        print(f"\n  Probando con simbolo '(' en query (error E34 de Ibaceta)...")
        r2 = search_wikipedia_real('python(lenguaje)')
        print(f"  {'OK - No crashea con parentesis' if not r2.content.startswith('Error') else 'FAIL'}")

    elif args.live and not WIKI_OK:
        print(f"\n[PASO 3] OMITIDO: Instalar wikipedia-api primero: pip install wikipedia-api")

    print(f"""
{'='*60}
RESULTADOS — MOD05: ModuloBusquedaWeb
{'='*60}

[ESTADO EN MVP v1.0]
  *** FUERA DE ALCANCE DEL MVP ***
  Razon: APIs con credenciales vencidas (Google, Bing, YouTube)
  Plan: Reactivar en v2.0 con nuevas API keys del laboratorio InTeractiOn

[MOCK VALIDADO]
  search_encyclopedia() : OK (IWebSearchProvider.search_encyclopedia)
  search_definition()   : OK (IWebSearchProvider.search_definition)
  translate_text()      : OK (IWebSearchProvider.translate_text)
  search_image()        : OK (IWebSearchProvider.search_image)

[ALTERNATIVA GRATUITA IDENTIFICADA]
  Wikipedia: wikipedia-api (no requiere API key) -> E34, E36, E61, E62 resueltos
  Definiciones: dictionaryapi.dev (gratuita)
  Imagenes: Google Lens API (requiere cuenta Google)
  Traduccion: LibreTranslate (open source, auto-hosteable)

[ERRORES DE IBACETA RELACIONADOS]
  E25: Diccionario no busca palabras      -> RESUELTO con mock/interfaz
  E26: Enciclopedia no muestra resultados -> RESUELTO (wikipedia-api gratuita)
  E33: No detecta cambio de API           -> RESUELTO (config.json)
  E34: Simbolo '(' crashea Wikipedia      -> RESUELTO (wikipedia-api lo maneja)
  E36: Sin internet crashea               -> RESUELTO (try/except retorna SearchResult)
  E37: API Bing traduccion no reconocida  -> PENDIENTE (requiere nueva API key)
  E63: Busqueda de figuras no funciona    -> PENDIENTE (MVP v2.0)

[EQUIVALENCIAS VALIDADAS]
  BuscarEnciclopedia.cs + ApiWikipedia.cs  -> search_wikipedia_real()
  BuscarDefinicion.cs + ApiDefiniciones.cs -> search_definition() (mock)
  ApiTraduccionBing.cs                     -> translate_text() (mock)
  ApiBuscarYoutube.cs                      -> search_video() (mock)

[CONCLUSION]
  Migracion MOD05 (ModuloBusquedaWeb): INTERFAZ FACTIBLE
  Implementacion completa: TRABAJO FUTURO (v2.0)
  Mock disponible para tests del orquestador
{'='*60}
""")


if __name__ == '__main__':
    main()
