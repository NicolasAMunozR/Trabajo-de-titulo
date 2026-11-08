# Resultados — P-02_hal_y_consistencia

Generado: 2026-11-08T13:56:48 · Python 3.13.18 · Linux 6.18.44-fc-v310 · dispositivos simulado

## Pruebas automatizadas

| Aprobadas | Fallidas | Omitidas | Fallo esperado (hallazgo documentado) | Cobertura de líneas | Umbral 80 % |
|---|---|---|---|---|---|
| 41 | 0 | 0 | 1 | 73 % | no cumple |

## Latencia del OrchestratorCore

500 ciclos medidos (tras 10 de calentamiento). Objetivo por plugin: ≤ 8.3 ms (50 % de una muestra a 60 Hz).

| Plugin | Media (ms) | p95 (ms) | Máx. (ms) | Ciclos > 8,3 ms |
|---|---|---|---|---|
| TextCamera | 0.1133 | 0.151 | 2.451 | 0 |
| ConsistencyProvider | 0.0116 | 0.014 | 0.113 | 0 |
| **Ciclo completo** | 0.1547 | 0.2044 | 2.4865 | 0 |

## Carga de plugins

| Plugin | Estado | Detalle |
|---|---|---|
| TextCamera | initialized |  |
| ConsistencyProvider | initialized |  |

## Demostración de consistencia papel ↔ PDF (demos/demo_consistencia.py)

| Llamada (por OrchestratorCore.invoke) | Correcta | Latencia (ms) | Resultado |
|---|---|---|---|
| search_text | sí | 4.871 | [2] |
| add_highlight | sí | 1.572 | True |
| add_bookmark | sí | 0.618 | None |
| sync_bookmark_from_frame | sí | 3.786 | True |
| sync_comments_from_frame | sí | 2.709 | 1 |
| sync_figures_from_frame | sí | 3.828 | 2 |
| get_bookmarks | sí | 0.267 | ['Introducción Pag.1', 'Marcador físico página 2 Pag.2'] |
| get_comments | sí | 0.252 | [{'content': 'Comentario físico 1 (pág. 2)', 'page': 2, 'x': |
| get_figures | sí | 0.131 | {'rectangulos': [{'x': 234.327731092437, 'y': 108.2155603694 |
| search_text | sí | 0.002 | [] |

Al reabrir el PDF guardado: anotaciones por página [0, 0, 2] (esperado [1, 1, 2]), 0 marcadores (esperado 2), PDF reparado al abrir: True. **Se perdieron cambios (hallazgo H-02).**
