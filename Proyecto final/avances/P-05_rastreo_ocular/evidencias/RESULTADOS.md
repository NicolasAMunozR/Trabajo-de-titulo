# Resultados — P-05_rastreo_ocular

Generado: 2026-11-08T13:57:18 · Python 3.13.18 · Linux 6.18.44-fc-v310 · dispositivos simulado

## Pruebas automatizadas

| Aprobadas | Fallidas | Omitidas | Fallo esperado (hallazgo documentado) | Cobertura de líneas | Umbral 80 % |
|---|---|---|---|---|---|
| 94 | 0 | 0 | 1 | 74 % | no cumple |

## Latencia del OrchestratorCore

500 ciclos medidos (tras 10 de calentamiento). Objetivo por plugin: ≤ 8.3 ms (50 % de una muestra a 60 Hz). Gesto activo durante la medición: ColorPenRecognition.

| Plugin | Media (ms) | p95 (ms) | Máx. (ms) | Ciclos > 8,3 ms |
|---|---|---|---|---|
| TextCamera | 0.1143 | 0.165 | 0.381 | 0 |
| GestureCamera | 0.2665 | 0.341 | 3.346 | 0 |
| ImageProcessor | 0.0061 | 0.008 | 0.08 | 0 |
| ColorPenRecognition | 0.1202 | 0.924 | 1.283 | 0 |
| HandSkinRecognition | 0.0024 | 0.005 | 0.052 | 0 |
| MouseRecognition | 0.0028 | 0.003 | 0.063 | 0 |
| EyeTrackerMock | 0.0106 | 0.013 | 0.084 | 0 |
| GazeSession | 0.0047 | 0.006 | 0.056 | 0 |
| ConsistencyProvider | 0.01 | 0.011 | 0.474 | 0 |
| **Ciclo completo** | 0.5838 | 1.4146 | 3.5275 | 0 |

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

## Capturas

- capturas/00_menu_settings.png
- capturas/01_text.png
- capturas/02_page.png
- capturas/03_gesture_mano.png
- capturas/03_gesture_lapiz.png
- capturas/04_eye.png
