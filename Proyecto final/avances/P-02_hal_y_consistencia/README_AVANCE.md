# P-02 — Capa de abstracción de hardware y módulo de consistencia

Parte de la serie de avances de EDDIE en Python. La guía general (metodología, requisitos, hallazgos y cómo regenerar las evidencias) está en `../GUIA_AVANCES.md`.

Fase PDCA: **Do (implementación)** · Objetivo específico: **OE3** · Semanas del plan: **7–8** · Carpeta: `P-02_hal_y_consistencia`

| | |
|---|---|
| **ID Prototipo** | P-02 |
| **Nombre** | Capa de abstracción de hardware y módulo de consistencia |
| **Objetivos** | Incorporar DeviceFactory para conmutar cada dispositivo entre real y simulado sin cambiar código.<br>Implementar la cámara real (OpenCV, hilo de captura) y la enumeración de cámaras de Windows.<br>Integrar primero el módulo sin dependencia de hardware: la consistencia papel↔PDF como plugin IConsistencyProvider (PyMuPDF).<br>Extender el núcleo con overrides de configuración, invocación bajo demanda, reinicio en caliente y traza de ejecución. |
| **Descripción** | El núcleo pasa a su versión definitiva y se agrega la capa HAL. La consistencia (resaltados, marcadores, comentarios y figuras, búsqueda de texto) se ejecuta a través del orquestador con OrchestratorCore.invoke(). Sigue sin interfaz: se demuestra con demos/demo_consistencia.py, que sincroniza tres «fotos» sintéticas de la hoja con un PDF de prueba y guarda el PDF resultante y el render de cada página. |
| **Requisitos Funcionales** | N4, N5, N6, N8, C1, C2, C3, C7, C9, C10, C11 (parcial) |
| **Requisitos No Funcionales** | RNF-01, RNF-02, RNF-04, RNF-05 |

### Qué se revisa en este avance

1. Que con EDDIE_DEVICE_MODE=sim la cámara sea MockCameraSensor y con real la de OpenCV, sin tocar código.
2. Que una cámara inexistente falle de forma limpia (initialize → False) y no detenga el sistema.
3. Que invoke() devuelva errores legibles (por ejemplo «No hay un PDF cargado») en vez de excepciones.
4. Que marcador azul, nota amarilla y figuras magenta del papel se conviertan en marcador, comentario y figuras del PDF (evidencias/consistencia).
5. Que lo sincronizado siga en el PDF al reabrirlo (sección «Al reabrir el PDF guardado»).

### Cómo ejecutarlo

```powershell
python main.py --sim
python demos\demo_consistencia.py
python -m pytest
python tools\generar_evidencias.py
```

### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:56:48.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 41 | 1 | 0 | 73 % | 0,20 ms | 2,49 ms |

Plugin con mayor latencia (p95): **TextCamera**, 0,15 ms (umbral 8,3 ms). Detalle por plugin en `evidencias/RESULTADOS.md`.

Demostración de consistencia (`evidencias/consistencia/`): 10/10 llamadas correctas. Al reabrir el PDF: anotaciones por página [0, 0, 2] (esperado [1, 1, 2]), 0 marcadores. **Se pierden cambios → hallazgo H-02.**

Hallazgos relacionados: H-02 (ver «Hallazgos de la verificación»).

