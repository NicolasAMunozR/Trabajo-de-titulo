# Búsqueda mediante un modelo de lenguaje (IWebSearchProvider): Google Gemini.
# Reemplaza las APIs del C#; cada servicio (enciclopedia, definición, traducción, video, imagen) lo responde el LLM.
# La clave se busca en config["api_key"], la variable GEMINI_API_KEY o config/secrets.json.
import base64
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from contracts.i_web_search_provider import IWebSearchProvider, SearchResult

logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).resolve().parent.parent
SECRETS_FILE = PROJECT_DIR / "config" / "secrets.json"

LANGUAGES = {"es": "español", "en": "inglés"}

SYSTEM_INSTRUCTION = (
    "Eres el asistente de búsqueda de EDDIE, una plataforma de lectura aumentada. "
    "El lector seleccionó un término en un libro físico. Responde exactamente en el "
    "formato pedido, sin saludos, sin markdown y sin texto adicional."
)

PROMPTS = {
    "encyclopedia": (
        "Actúa como una enciclopedia. Escribe un artículo breve y objetivo en español sobre "
        "\"{q}\": 3 a 5 párrafos cortos separados por una línea en blanco, sin títulos ni "
        "viñetas. Si el término es ambiguo, explica la acepción más común."
    ),
    "definition": (
        "Entrega entre 1 y 4 definiciones de diccionario en español para \"{q}\". "
        "Escribe una definición por línea, comenzando con la categoría gramatical entre "
        "paréntesis, sin numeración ni texto adicional."
    ),
    "translation": (
        "Traduce el siguiente texto al {lang}. Responde solo con la traducción, sin comillas "
        "ni explicaciones.\n\n{q}"
    ),
    "video": (
        "Propón la mejor consulta para encontrar en YouTube un video educativo que explique "
        "\"{q}\". Responde solo con la consulta, en una línea."
    ),
    "image": (
        "Identifica el objeto, concepto o texto principal de esta imagen capturada de un "
        "libro. Responde solo con 1 a 4 palabras en español, sin puntuación."
    ),
}


def _read_secret(key: str) -> str:
    try:
        return str(json.loads(SECRETS_FILE.read_text(encoding="utf-8")).get(key, "")).strip()
    except (OSError, ValueError):
        return ""


class LLMSearchPlugin(IWebSearchProvider):
    # Proveedor de búsqueda basado en Gemini.

    def __init__(self) -> None:
        self._model = "gemini-2.5-flash"
        self._base_url = "https://generativelanguage.googleapis.com"
        self._api_key = ""
        self._timeout = 60.0
        self._temperature = 0.2
        self._thinking_budget: Optional[int] = 0
        self._retries = 1
        self._label = ""
        self._last_latency_ms = -1.0
        self._last_error: Optional[str] = None
        self._initialized = False

    @property
    def name(self) -> str:
        return "LLMSearchProvider"

    @property
    def label(self) -> str:
        return self._label or f"LLM · Gemini ({self._model})"

    # ------------------------------------------------------------------ ciclo de vida
    def initialize(self, config: dict) -> bool:
        self._model = config.get("model", "gemini-2.5-flash")
        self._base_url = config.get("base_url", "https://generativelanguage.googleapis.com").rstrip("/")
        self._timeout = float(config.get("timeout_s", 60))
        self._temperature = float(config.get("temperature", 0.2))
        # gemini-2.5-flash "piensa" antes de responder; 0 lo desactiva y baja la latencia.
        budget = config.get("thinking_budget", 0)
        self._thinking_budget = None if budget is None else int(budget)
        self._retries = int(config.get("retries", 1))
        self._label = config.get("label", "")
        key_env = config.get("api_key_env", "GEMINI_API_KEY")
        self._api_key = (config.get("api_key") or os.environ.get(key_env, "") or _read_secret(key_env)).strip()
        if not self._api_key:
            logger.error("[%s] Falta la clave de Gemini: cree config/secrets.json con "
                         "{\"%s\": \"<clave>\"} o defina la variable de entorno %s.",
                         self.instance_name, key_env, key_env)
            return False
        self._initialized = True
        return True

    def execute(self) -> dict:
        return {"backend": "gemini", "model": self._model, "label": self.label,
                "last_latency_ms": self._last_latency_ms, "last_error": self._last_error}

    def release(self) -> None:
        self._initialized = False

    # ------------------------------------------------------------------ contrato
    def search_encyclopedia(self, query: str) -> SearchResult:
        text = self._complete(PROMPTS["encyclopedia"].format(q=self._clean(query)))
        return SearchResult(query=query, source="encyclopedia", content=text)

    def search_definition(self, word: str) -> SearchResult:
        text = self._complete(PROMPTS["definition"].format(q=self._clean(word)))
        return SearchResult(query=word, source="definition", content=text)

    def translate_text(self, text: str, target_language: str) -> SearchResult:
        language = LANGUAGES.get(target_language, target_language or "español")
        translated = self._complete(PROMPTS["translation"].format(q=text.strip(), lang=language))
        return SearchResult(query=text, source="translation", content=translated)

    def search_video(self, query: str) -> SearchResult:
        refined = self._complete(PROMPTS["video"].format(q=self._clean(query))).splitlines()[0].strip('" ')
        url = "https://m.youtube.com/results?search_query=" + urllib.parse.quote_plus(refined or query)
        return SearchResult(query=query, source="video", content=refined, url=url)

    def search_image(self, image_bytes: bytes) -> SearchResult:
        if not image_bytes:
            raise ValueError("No hay una imagen capturada para buscar.")
        label = self._complete(PROMPTS["image"], image=image_bytes).splitlines()[0].strip(" .\"")
        url = "https://www.ecosia.org/search?q=" + urllib.parse.quote_plus(label)
        return SearchResult(query=label, source="image", content=label, url=url)

    # ------------------------------------------------------------------ Gemini
    @staticmethod
    def _clean(query: str) -> str:
        query = " ".join((query or "").split())
        if not query:
            raise ValueError("Seleccione un término para buscar.")
        return query

    def _complete(self, prompt: str, image: Optional[bytes] = None) -> str:
        start = time.perf_counter()
        try:
            text = self._generate(prompt, image)
            self._last_error = None
            return text.strip()
        except RuntimeError as exc:
            self._last_error = str(exc)
            raise
        except urllib.error.URLError as exc:
            self._last_error = f"No se pudo contactar a Gemini: {exc.reason}"
            raise RuntimeError(self._last_error) from exc
        finally:
            self._last_latency_ms = round((time.perf_counter() - start) * 1000, 1)

    def _payload(self, prompt: str, image: Optional[bytes]) -> dict:
        parts: list[dict] = []
        if image:
            parts.append({"inline_data": {"mime_type": _mime_type(image),
                                          "data": base64.b64encode(image).decode()}})
        parts.append({"text": prompt})
        generation: dict = {"temperature": self._temperature, "maxOutputTokens": 1024}
        if self._thinking_budget is not None:
            generation["thinkingConfig"] = {"thinkingBudget": self._thinking_budget}
        return {"systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": generation}

    def _generate(self, prompt: str, image: Optional[bytes]) -> str:
        url = f"{self._base_url}/v1beta/models/{urllib.parse.quote(self._model)}:generateContent"
        data = self._post(url, self._payload(prompt, image))
        feedback = data.get("promptFeedback", {})
        if feedback.get("blockReason"):
            raise RuntimeError(f"Gemini bloqueó la consulta ({feedback['blockReason']}).")
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini no devolvió respuesta.")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        if not text.strip():
            reason = candidates[0].get("finishReason", "desconocido")
            raise RuntimeError(f"Gemini devolvió una respuesta vacía (finishReason={reason}).")
        return text

    def _post(self, url: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", "x-goog-api-key": self._api_key}
        for attempt in range(self._retries + 1):
            request = urllib.request.Request(url, data=body, method="POST", headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = _error_message(exc)
                if exc.code in (500, 503) and attempt < self._retries:   # modelo sobrecargado: reintentar
                    time.sleep(1.5 * (attempt + 1))
                    continue
                if exc.code == 429:
                    raise RuntimeError("Se alcanzó el límite de la capa gratuita de Gemini. "
                                       "Espere un minuto e intente de nuevo.") from exc
                if exc.code in (400, 401, 403) and "API key" in detail:
                    raise RuntimeError("La clave de Gemini no es válida. Revise config/secrets.json.") from exc
                raise RuntimeError(f"Gemini respondió HTTP {exc.code}: {detail}") from exc
        raise RuntimeError("Gemini no respondió.")


def _error_message(exc: urllib.error.HTTPError) -> str:
    raw = exc.read().decode("utf-8", "ignore")
    try:
        return json.loads(raw)["error"]["message"][:300]
    except (ValueError, KeyError, TypeError):
        return raw[:300]


def _mime_type(image: bytes) -> str:
    if image[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    return "image/jpeg"
