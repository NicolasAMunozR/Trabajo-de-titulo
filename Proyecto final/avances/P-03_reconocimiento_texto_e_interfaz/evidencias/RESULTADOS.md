# Resultados — P-03_reconocimiento_texto_e_interfaz

Generado: 2026-11-08T13:56:54 · Python 3.13.18 · Linux 6.18.44-fc-v310 · dispositivos simulado

## Pruebas automatizadas

| Aprobadas | Fallidas | Omitidas | Fallo esperado (hallazgo documentado) | Cobertura de líneas | Umbral 80 % |
|---|---|---|---|---|---|
| 65 | 0 | 0 | 0 | 67 % | no cumple |

## Latencia del OrchestratorCore

500 ciclos medidos (tras 10 de calentamiento). Objetivo por plugin: ≤ 8.3 ms (50 % de una muestra a 60 Hz).

| Plugin | Media (ms) | p95 (ms) | Máx. (ms) | Ciclos > 8,3 ms |
|---|---|---|---|---|
| TextCamera | 0.104 | 0.146 | 0.25 | 0 |
| ImageProcessor | 0.0059 | 0.007 | 0.089 | 0 |
| ConsistencyProvider | 0.0097 | 0.01 | 0.426 | 0 |
| **Ciclo completo** | 0.1485 | 0.1974 | 0.5764 | 0 |

## Carga de plugins

| Plugin | Estado | Detalle |
|---|---|---|
| TextCamera | initialized |  |
| ImageProcessor | initialized |  |
| ConsistencyProvider | initialized |  |

## Capturas

- capturas/00_menu_settings.png
- capturas/01_text.png
- capturas/02_page.png
