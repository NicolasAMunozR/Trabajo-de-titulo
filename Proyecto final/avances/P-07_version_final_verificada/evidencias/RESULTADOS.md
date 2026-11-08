# Resultados — P-07_version_final_verificada

Generado: 2026-11-08T13:58:01 · Python 3.13.18 · Linux 6.18.44-fc-v310 · dispositivos simulado

## Pruebas automatizadas

| Aprobadas | Fallidas | Omitidas | Fallo esperado (hallazgo documentado) | Cobertura de líneas | Umbral 80 % |
|---|---|---|---|---|---|
| 107 | 0 | 0 | 0 | 81 % | cumple |

## Latencia del OrchestratorCore

500 ciclos medidos (tras 10 de calentamiento). Objetivo por plugin: ≤ 8.3 ms (50 % de una muestra a 60 Hz). Gesto activo durante la medición: ColorPenRecognition.

| Plugin | Media (ms) | p95 (ms) | Máx. (ms) | Ciclos > 8,3 ms |
|---|---|---|---|---|
| TextCamera | 0.1165 | 0.182 | 0.76 | 0 |
| GestureCamera | 0.2641 | 0.369 | 2.12 | 0 |
| ImageProcessor | 0.0061 | 0.008 | 0.057 | 0 |
| ColorPenRecognition | 0.1225 | 0.932 | 1.189 | 0 |
| HandSkinRecognition | 0.0025 | 0.005 | 0.046 | 0 |
| MouseRecognition | 0.0024 | 0.003 | 0.013 | 0 |
| EyeTrackerMock | 0.0104 | 0.015 | 0.16 | 0 |
| SpeechProvider | 0.0031 | 0.004 | 0.079 | 0 |
| GazeSession | 0.005 | 0.006 | 0.13 | 0 |
| ConsistencyProvider | 0.0091 | 0.011 | 0.074 | 0 |
| **Ciclo completo** | 0.5901 | 1.4824 | 2.3077 | 0 |

## Carga de plugins

| Plugin | Estado | Detalle |
|---|---|---|
| TextCamera | initialized |  |
| GestureCamera | initialized |  |
| ImageProcessor | initialized |  |
| ColorPenRecognition | initialized |  |
| HandSkinRecognition | initialized |  |
| MouseRecognition | initialized |  |
| EyeTracker-GazePoint | disabled |  |
| EyeTracker-EyeTribe | disabled |  |
| EyeTracker-GazeCloud | disabled |  |
| EyeTrackerMock | initialized |  |
| GazeSession | initialized |  |
| ConsistencyProvider | initialized |  |
| LLM-Gemini | initialization_failed | initialize() retornó False. |
| SpeechProvider | initialized |  |

## Demostración de consistencia papel ↔ PDF (demos/demo_consistencia.py)

| Llamada (por OrchestratorCore.invoke) | Correcta | Latencia (ms) | Resultado |
|---|---|---|---|
| search_text | sí | 5.65 | [2] |
| add_highlight | sí | 2.487 | True |
| add_bookmark | sí | 2.59 | None |
| sync_bookmark_from_frame | sí | 5.11 | True |
| sync_comments_from_frame | sí | 4.989 | 1 |
| sync_figures_from_frame | sí | 5.81 | 2 |
| get_bookmarks | sí | 0.32 | ['Introducción Pag.1', 'Marcador físico página 2 Pag.2'] |
| get_comments | sí | 0.51 | [{'content': 'Comentario físico 1 (pág. 2)', 'page': 2, 'x': |
| get_figures | sí | 0.189 | {'rectangulos': [{'x': 234.327731092437, 'y': 108.2155603694 |
| search_text | sí | 0.004 | [] |

Al reabrir el PDF guardado: anotaciones por página [1, 1, 2] (esperado [1, 1, 2]), 2 marcadores (esperado 2), PDF reparado al abrir: False. **Se conservan todos los cambios.**

## Capturas

- capturas/00_menu_settings.png
- capturas/01_text.png
- capturas/02_page.png
- capturas/03_gesture_mano.png
- capturas/03_gesture_lapiz.png
- capturas/04_eye.png
- capturas/05_web.png
- capturas/06_interactions.png
- capturas/10_proyeccion.png
- capturas/11_proyeccion_busqueda.png
- capturas/12_proyeccion_pdf.png
- capturas/13_proyeccion_historial.png
