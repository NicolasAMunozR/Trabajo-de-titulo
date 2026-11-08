# Resultados — P-01_nucleo_orquestador

Generado: 2026-11-08T13:56:42 · Python 3.13.18 · Linux 6.18.44-fc-v310 · dispositivos simulado

## Pruebas automatizadas

| Aprobadas | Fallidas | Omitidas | Fallo esperado (hallazgo documentado) | Cobertura de líneas | Umbral 80 % |
|---|---|---|---|---|---|
| 34 | 0 | 0 | 0 | 81 % | cumple |

## Latencia del OrchestratorCore

500 ciclos medidos (tras 10 de calentamiento). Objetivo por plugin: ≤ 8.3 ms (50 % de una muestra a 60 Hz).

| Plugin | Media (ms) | p95 (ms) | Máx. (ms) | Ciclos > 8,3 ms |
|---|---|---|---|---|
| TextCamera | 0.0942 | 0.131 | 0.324 | 0 |
| FrameStatistics | 0.5757 | 0.776 | 2.351 | 0 |
| EyeTrackerMock | 0.0137 | 0.018 | 0.085 | 0 |
| FaultInjection | 0.0165 | 0.13 | 0.22 | 0 |
| CycleSummary | 0.0136 | 0.015 | 0.365 | 0 |
| **Ciclo completo** | 0.7488 | 0.9827 | 2.4958 | 0 |

## Carga de plugins

| Plugin | Estado | Detalle |
|---|---|---|
| TextCamera | initialized |  |
| FrameStatistics | initialized |  |
| EyeTrackerMock | initialized |  |
| FaultInjection | initialized |  |
| PluginInexistente | load_failed | El plugin no se pudo cargar; revisa el log del PluginLoader. |
| CycleSummary | initialized |  |
