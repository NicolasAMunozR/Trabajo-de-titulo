# P-07 — Versión final verificada

Parte de la serie de avances de EDDIE en Python. La guía general (metodología, requisitos, hallazgos y cómo regenerar las evidencias) está en `../GUIA_AVANCES.md`.

Fase PDCA: **Check / Act** · Objetivo específico: **OE4** · Semanas del plan: **13–17** · Carpeta: `P-07_version_final_verificada`

| | |
|---|---|
| **ID Prototipo** | P-07 |
| **Nombre** | Versión final verificada |
| **Objetivos** | Verificar el sistema integrado: cobertura, latencia, trazabilidad de errores y pruebas de regresión.<br>Corregir los hallazgos de la verificación (H-01, H-02, H-03) y dejar una prueba que los detecte.<br>Cerrar la documentación técnica (README, EQUIVALENCIAS, DISENO_INTERFAZ). |
| **Descripción** | Es el contenido de «Proyecto final» con las correcciones de la verificación. Cada hallazgo tiene una prueba de regresión que falla con el código de P-06 y pasa con el de P-07. |
| **Requisitos Funcionales** | Todos los anteriores |
| **Requisitos No Funcionales** | RNF-01, RNF-02, RNF-03, RNF-04, RNF-05, RNF-06, RNF-07, RNF-08 |

### Qué se revisa en este avance

1. Las 107 pruebas (incluye regresiones de H-01, H-02 y H-03) y la cobertura ≥ 80 %.
2. Latencia del ciclo completo con todos los plugins ≤ 8,3 ms (p95).
3. Captura de Gestos con la mano en la orientación correcta y la casilla «Rotar la imagen 180°».
4. Demostración de consistencia: lo sincronizado se conserva al reabrir el PDF.
5. Pruebas de aceptación con el hardware del laboratorio (tools\generar_evidencias.py --real y MECIVA PS), que se completan en el laboratorio.

### Cómo ejecutarlo

```powershell
python main.py
python main.py --sim
python -m pytest
python tools\generar_evidencias.py  [--real]
```

### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:58:01.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 107 | 0 | 0 | 81 % | 1,48 ms | 2,31 ms |

Plugin con mayor latencia (p95): **ColorPenRecognition**, 0,93 ms (umbral 8,3 ms). Detalle por plugin en `evidencias/RESULTADOS.md`.

No se inicializó **LLM-Gemini** (initialization_failed): en la máquina donde se generó no había clave de Gemini; en tu PC se carga desde config/secrets.json o GEMINI_API_KEY.

Figuras disponibles para la tesis:

- `evidencias/capturas/00_menu_settings.png` — Séptimo prototipo: Ventana principal con «Preparar sesión» y el estado de cada módulo.
- `evidencias/capturas/01_text.png` — Séptimo prototipo: Texto (OCR) con la cámara simulada y el texto reconocido.
- `evidencias/capturas/02_page.png` — Séptimo prototipo: Documento PDF con la vista previa.
- `evidencias/capturas/03_gesture_mano.png` — Séptimo prototipo: Gestos con Hand Skin (mano).
- `evidencias/capturas/03_gesture_lapiz.png` — Séptimo prototipo: Gestos con Color Pen (lápiz).
- `evidencias/capturas/04_eye.png` — Séptimo prototipo: Rastreo ocular.
- `evidencias/capturas/05_web.png` — Séptimo prototipo: Búsquedas (proveedor LLM y servicio por tipo).
- `evidencias/capturas/06_interactions.png` — Séptimo prototipo: Interacción (voz y botones).
- `evidencias/capturas/10_proyeccion.png` — Séptimo prototipo: Pantalla de proyección renovada.
- `evidencias/capturas/11_proyeccion_busqueda.png` — Séptimo prototipo: Proyección con definición y enciclopedia (LLM local de prueba).
- `evidencias/capturas/12_proyeccion_pdf.png` — Séptimo prototipo: Proyección con el sincronizador del PDF.
- `evidencias/capturas/13_proyeccion_historial.png` — Séptimo prototipo: Proyección con el historial de búsquedas.

Demostración de consistencia (`evidencias/consistencia/`): 10/10 llamadas correctas. Al reabrir el PDF: anotaciones por página [1, 1, 2] (esperado [1, 1, 2]), 2 marcadores. Se conserva todo.

Hallazgos relacionados: H-01 (corregido), H-02 (corregido), H-03 (corregido) (ver «Hallazgos de la verificación»).

