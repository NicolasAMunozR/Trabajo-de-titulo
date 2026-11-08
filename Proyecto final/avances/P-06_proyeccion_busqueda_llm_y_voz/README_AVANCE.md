# P-06 — Pantalla de proyección, búsqueda con LLM y voz

Parte de la serie de avances de EDDIE en Python. La guía general (metodología, requisitos, hallazgos y cómo regenerar las evidencias) está en `../GUIA_AVANCES.md`.

Fase PDCA: **Do (implementación)** · Objetivo específico: **OE3** · Semanas del plan: **12** · Carpeta: `P-06_proyeccion_busqueda_llm_y_voz`

| | |
|---|---|
| **ID Prototipo** | P-06 |
| **Nombre** | Pantalla de proyección, búsqueda con LLM y voz |
| **Objetivos** | Integrar la pantalla de proyección (ProjectionScreenActivity2): modo resaltado/captura, búsqueda y sincronización papel↔PDF, con los botones en la franja superior (zona de mayor validez del eye tracker según Ibaceta, 2023) y la zona de lectura y las cruces en su posición original.<br>Responder los cinco servicios de búsqueda con Gemini 2.5 Flash bajo IWebSearchProvider, en lugar de las APIs vencidas (Wikipedia, Google, Bing, YouTube, Cloud Vision).<br>Integrar lectura en voz alta y comandos de voz (ISpeechProvider) y las páginas Interacción y Búsquedas. |
| **Descripción** | Con este avance el sistema queda completo y equivale al código de «Proyecto final» antes de la verificación. Es una extensión respecto del alcance del seminario, donde IWebSearchProvider quedaba solo como interfaz. |
| **Requisitos Funcionales** | B1–B13, C5, C6, C8, C11, C12, RFS1, RFS2 |
| **Requisitos No Funcionales** | RNF-01, RNF-06, RNF-08 |

### Qué se revisa en este avance

1. Flujo completo: resaltar → OCR → corregir el término → definición/enciclopedia (LLM local falso en las pruebas) → historial CSV.
2. Que el modo actual, el servicio que respondió y la tarjeta del sincronizador se vean en la proyección, y que ningún color de la interfaz sea amarillo.
3. Búsqueda por imagen con la captura del gesto.
4. Sincronizar un resaltado de la proyección con el PDF y buscar páginas.
5. Avisos cuando falta el término, la imagen o el PDF.

### Cómo ejecutarlo

```powershell
python main.py --sim
python -m pytest
python tools\generar_evidencias.py
```

### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:57:35.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 100 | 2 | 0 | 81 % | 1,49 ms | 10,28 ms |

Plugin con mayor latencia (p95): **ColorPenRecognition**, 0,97 ms (umbral 8,3 ms). Detalle por plugin en `evidencias/RESULTADOS.md`.

No se inicializó **LLM-Gemini** (initialization_failed): en la máquina donde se generó no había clave de Gemini; en tu PC se carga desde config/secrets.json o GEMINI_API_KEY.

Figuras disponibles para la tesis:

- `evidencias/capturas/00_menu_settings.png` — Sexto prototipo: Ventana principal con «Preparar sesión» y el estado de cada módulo.
- `evidencias/capturas/01_text.png` — Sexto prototipo: Texto (OCR) con la cámara simulada y el texto reconocido.
- `evidencias/capturas/02_page.png` — Sexto prototipo: Documento PDF con la vista previa.
- `evidencias/capturas/03_gesture_mano.png` — Sexto prototipo: Gestos con Hand Skin (mano).
- `evidencias/capturas/03_gesture_lapiz.png` — Sexto prototipo: Gestos con Color Pen (lápiz).
- `evidencias/capturas/04_eye.png` — Sexto prototipo: Rastreo ocular.
- `evidencias/capturas/05_web.png` — Sexto prototipo: Búsquedas (proveedor LLM y servicio por tipo).
- `evidencias/capturas/06_interactions.png` — Sexto prototipo: Interacción (voz y botones).
- `evidencias/capturas/10_proyeccion.png` — Sexto prototipo: Pantalla de proyección renovada.
- `evidencias/capturas/11_proyeccion_busqueda.png` — Sexto prototipo: Proyección con definición y enciclopedia (LLM local de prueba).
- `evidencias/capturas/12_proyeccion_pdf.png` — Sexto prototipo: Proyección con el sincronizador del PDF.
- `evidencias/capturas/13_proyeccion_historial.png` — Sexto prototipo: Proyección con el historial de búsquedas.

Hallazgos relacionados: H-01, H-02 (ver «Hallazgos de la verificación»).

