# Resultados — P-06_proyeccion_busqueda_llm_y_voz

Generado: 2026-11-08T13:57:35 · Python 3.13.18 · Linux 6.18.44-fc-v310 · dispositivos simulado

## Pruebas automatizadas

| Aprobadas | Fallidas | Omitidas | Fallo esperado (hallazgo documentado) | Cobertura de líneas | Umbral 80 % |
|---|---|---|---|---|---|
| 100 | 0 | 0 | 2 | 81 % | cumple |

## Latencia del OrchestratorCore

500 ciclos medidos (tras 10 de calentamiento). Objetivo por plugin: ≤ 8.3 ms (50 % de una muestra a 60 Hz). Gesto activo durante la medición: ColorPenRecognition.

| Plugin | Media (ms) | p95 (ms) | Máx. (ms) | Ciclos > 8,3 ms |
|---|---|---|---|---|
| TextCamera | 0.1221 | 0.174 | 2.001 | 0 |
| GestureCamera | 0.2828 | 0.372 | 2.537 | 0 |
| ImageProcessor | 0.0069 | 0.008 | 0.078 | 0 |
| ColorPenRecognition | 0.1467 | 0.97 | 9.062 | 1 |
| HandSkinRecognition | 0.0029 | 0.006 | 0.058 | 0 |
| MouseRecognition | 0.0025 | 0.003 | 0.031 | 0 |
| EyeTrackerMock | 0.0102 | 0.012 | 0.143 | 0 |
| SpeechProvider | 0.0036 | 0.004 | 0.058 | 0 |
| GazeSession | 0.0048 | 0.005 | 0.107 | 0 |
| ConsistencyProvider | 0.01 | 0.011 | 0.202 | 0 |
| **Ciclo completo** | 0.6566 | 1.492 | 10.2818 | 2 |

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
