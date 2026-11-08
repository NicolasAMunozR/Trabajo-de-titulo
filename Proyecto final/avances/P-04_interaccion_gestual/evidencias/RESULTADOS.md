# Resultados — P-04_interaccion_gestual

Generado: 2026-11-08T13:57:04 · Python 3.13.18 · Linux 6.18.44-fc-v310 · dispositivos simulado

## Pruebas automatizadas

| Aprobadas | Fallidas | Omitidas | Fallo esperado (hallazgo documentado) | Cobertura de líneas | Umbral 80 % |
|---|---|---|---|---|---|
| 79 | 0 | 0 | 1 | 72 % | no cumple |

## Latencia del OrchestratorCore

500 ciclos medidos (tras 10 de calentamiento). Objetivo por plugin: ≤ 8.3 ms (50 % de una muestra a 60 Hz). Gesto activo durante la medición: ColorPenRecognition.

| Plugin | Media (ms) | p95 (ms) | Máx. (ms) | Ciclos > 8,3 ms |
|---|---|---|---|---|
| TextCamera | 0.1204 | 0.168 | 0.32 | 0 |
| GestureCamera | 0.2894 | 0.375 | 1.053 | 0 |
| ImageProcessor | 0.0069 | 0.008 | 0.261 | 0 |
| ColorPenRecognition | 0.1285 | 0.997 | 1.289 | 0 |
| HandSkinRecognition | 0.003 | 0.006 | 0.167 | 0 |
| MouseRecognition | 0.0026 | 0.003 | 0.079 | 0 |
| ConsistencyProvider | 0.0093 | 0.011 | 0.068 | 0 |
| **Ciclo completo** | 0.6035 | 1.5031 | 1.7578 | 0 |

## Carga de plugins

| Plugin | Estado | Detalle |
|---|---|---|
| TextCamera | initialized |  |
| GestureCamera | initialized |  |
| ImageProcessor | initialized |  |
| ColorPenRecognition | initialized |  |
| HandSkinRecognition | initialized |  |
| MouseRecognition | initialized |  |
| ConsistencyProvider | initialized |  |

## Capturas

- capturas/00_menu_settings.png
- capturas/01_text.png
- capturas/02_page.png
- capturas/03_gesture_mano.png
- capturas/03_gesture_lapiz.png
