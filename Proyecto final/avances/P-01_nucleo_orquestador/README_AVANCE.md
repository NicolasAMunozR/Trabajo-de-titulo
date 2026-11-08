# P-01 — Núcleo orquestador y contratos de plugins

Parte de la serie de avances de EDDIE en Python. La guía general (metodología, requisitos, hallazgos y cómo regenerar las evidencias) está en `../GUIA_AVANCES.md`.

Fase PDCA: **Do (diseño)** · Objetivo específico: **OE2** · Semanas del plan: **4–6** · Carpeta: `P-01_nucleo_orquestador`

| | |
|---|---|
| **ID Prototipo** | P-01 |
| **Nombre** | Núcleo orquestador y contratos de plugins |
| **Objetivos** | Definir PluginBase y los contratos de cada módulo (ICameraSensor, IImageProcessor, IGesturePlugin, IEyeTracker, IConsistencyProvider, IWebSearchProvider, ISpeechProvider).<br>Implementar el OrchestratorCore (inicializar → ejecutar → liberar) y el PluginLoader con un único mecanismo de carga.<br>Validar la inyección de dependencias sensor→consumidor, el aislamiento de fallos y la latencia por ciclo. |
| **Descripción** | Primera versión del núcleo, sin interfaz. Se prueba con dispositivos simulados (MockCameraSensor, EyeTrackerMock) y con plugins de prueba: un consumidor de frames, un consumidor de resultados del ciclo, un plugin que falla cada 10 ciclos y una entrada con una clase inexistente (equivalente a la DLL faltante de los errores E38/E50). El OrchestratorCore de este avance es la versión temprana del repositorio (sin overrides, invoke ni reinicio en caliente). |
| **Requisitos Funcionales** | N1, N2, N3, RFCO12 |
| **Requisitos No Funcionales** | RNF-01, RNF-02, RNF-04, RNF-05 |

### Qué se revisa en este avance

1. Que todos los plugins válidos queden «initialized» y la clase inexistente quede «load_failed» sin detener el arranque (inicializacion.json).
2. Que la falla inyectada en los ciclos 10, 20, … quede aislada: los demás plugins entregan resultado en todos los ciclos.
3. Que el consumidor reciba el sensor por inyección y no abra la cámara por su cuenta.
4. Que cada contrato herede de PluginBase y no pueda instanciarse sin implementar sus métodos.
5. Latencia por plugin y por ciclo frente al umbral de 8,3 ms (latencias.json).

### Cómo ejecutarlo

```powershell
python main.py --cycles 300
python -m pytest
python tools\generar_evidencias.py
```

### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:56:42.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 34 | 0 | 0 | 81 % | 0,98 ms | 2,50 ms |

Plugin con mayor latencia (p95): **FrameStatistics**, 0,78 ms (umbral 8,3 ms). Detalle por plugin en `evidencias/RESULTADOS.md`.

No se inicializó **PluginInexistente** (load_failed): entrada con clase inexistente, puesta a propósito para probar el aislamiento.

