# Avances de desarrollo de EDDIE en Python

Esta carpeta reproduce, paso a paso, cómo se llegó desde EDDIE-2023 (C#) al código de «Proyecto final». Cada subcarpeta es el **código completo y ejecutable** de una iteración, con sus pruebas, su forma de ejecución y las evidencias que produce, para describirlas en la tesis como prototipos sucesivos.

## 1. Guía de trabajo (la misma de Figueroa Contreras, 2025)

Se usa el ciclo **PDCA** con **RAD** (prototipos funcionales iterativos) y **Kanban** para las tareas, igual que en la memoria de Matías Figueroa sobre Multimodal Observer y como se comprometió en el informe de seminario:

- **Plan (OE1)**: diagnóstico del C# y prototipos desechables de factibilidad → P-00.
- **Do (OE2, OE3)**: diseño del núcleo y los contratos, luego integración de un módulo por iteración, primero el que no depende de hardware (consistencia) y después los que sí → P-01 a P-06.
- **Check (OE4)**: pruebas automatizadas, cobertura, latencia, verificación funcional y aceptación → P-07.
- **Act (OE4)**: correcciones de lo encontrado en la verificación y cierre de la documentación → P-07.

Como en la sección 3.4 de Matías, cada prototipo se resume en una tabla con **ID, Nombre, Objetivos, Descripción, Requisitos Funcionales y Requisitos No Funcionales**. Al terminar cada iteración se documenta y valida: aquí eso queda en `README_AVANCE.md` de cada carpeta y en `evidencias/`, generado por `tools/generar_evidencias.py` (pruebas, cobertura, latencias, carga de plugins y capturas de pantalla).

## 2. Antes de usar los resultados en la tesis

- Las carpetas P-01 a P-06 se **reconstruyeron a partir del código final**. Cada una quita lo que todavía no estaba integrado y adapta lo mínimo (configuración, menú, pruebas) para que corra sola. P-01 usa la versión temprana del núcleo que estaba en la raíz del repositorio (`orchestrator_core.py`). No es el historial literal de commits. Si en la tesis los presentas como iteraciones, conviene que el orden y las fechas coincidan con tu Kanban o tus commits.
- Los números que trae cada `evidencias/` salieron de ejecutar ese avance en un entorno Linux con **dispositivos simulados**. Para la tesis, **vuelve a generarlos en tu computador** con el comando de la sección 8. Los de hardware real se toman en el laboratorio con `--real`, y son los que corresponden a las pruebas de aceptación.
- Los códigos de requisitos (N1…N8, G1…G3, RNF-01…RNF-08) son una **propuesta**. Los heredados (C, RO, B, FD, RFS, RFCO) usan la numeración de Ibaceta (2023) y de las memorias de origen. Ajústalos a la tabla de requisitos de tu capítulo 3.

## 3. Mapa de los avances

| Avance | Fase PDCA | OE | Semanas | Qué se integra | Pruebas | Cobertura | Ciclo p95 |
|---|---|---|---|---|---|---|---|
| P-00 | Plan | OE1 | 1–3 | Prototipos desechables de factibilidad | — | — | — |
| P-01 | Do (diseño) | OE2 | 4–6 | Núcleo orquestador y contratos de plugins | 34 | 81 % | 0,98 ms |
| P-02 | Do (implementación) | OE3 | 7–8 | Capa de abstracción de hardware y módulo de consistencia | 41 (+1 xfail) | 73 % | 0,20 ms |
| P-03 | Do (implementación) | OE3 | 9 | Reconocimiento de texto e interfaz de configuración | 65 | 67 % | 0,20 ms |
| P-04 | Do (implementación) | OE3 | 10 | Interacción gestual | 79 (+1 xfail) | 72 % | 1,50 ms |
| P-05 | Do (implementación) | OE3 | 11–12 | Rastreo ocular | 94 (+1 xfail) | 74 % | 1,41 ms |
| P-06 | Do (implementación) | OE3 | 12 | Pantalla de proyección, búsqueda con LLM y voz | 100 (+2 xfail) | 81 % | 1,49 ms |
| P-07 | Check / Act | OE4 | 13–17 | Versión final verificada | 107 | 81 % | 1,48 ms |

«xfail» es una prueba que documenta un defecto conocido de ese avance: se espera que falle y pasa a aprobada cuando el defecto se corrige en P-07.

## 4. Requisitos usados en las tablas

### Funcionales

| ID | Descripción | Origen |
|---|---|---|
| N1 | Cargar todos los plugins declarados en config/plugins.json con un único mecanismo (importlib). | Nuevo (núcleo) |
| N2 | Aislar las fallas de carga, inicialización y ejecución de un plugin sin detener el resto. | Nuevo (núcleo) |
| N3 | Inyectar el sensor de cámara declarado a los plugins que consumen frames. | Nuevo (núcleo) |
| N4 | Conmutar cada dispositivo entre implementación real y simulada (DeviceFactory). | Nuevo (HAL) |
| N5 | Invocar operaciones de un plugin bajo demanda, con aislamiento de errores y medición de latencia. | Nuevo (núcleo) |
| N6 | Reiniciar o detener un plugin en ejecución y reconectar a sus consumidores. | Nuevo (núcleo) |
| N7 | Registrar una traza de ejecución (JSONL) con cada acción y su latencia. | Nuevo (núcleo) |
| N8 | Persistir los ajustes del usuario con las mismas claves de Settings2 del C#. | Nuevo (núcleo) |
| RFCO12 | Arquitectura modular para incorporar nuevos módulos/dispositivos. | Contreras (2019) |
| FD1 | Reconocimiento del texto resaltado en el documento físico (OCR). | Carrasco (2017) RFCA2 |
| C1 | Figuras del documento físico reflejadas en el digital. | Pezoa (2020) RFP1 |
| C2 | Comentarios (nota adhesiva) del físico reflejados en el digital. | Pezoa (2020) RFP2 |
| C3 | Marcador físico (banderilla azul) reflejado en el digital. | Pezoa (2020) RFP3 |
| C5 | Figuras de una página digital reflejadas sobre el papel (proyección). | Pezoa (2020) RFP5 |
| C6 | Comentarios de una página digital reflejados sobre el papel. | Pezoa (2020) RFP6 |
| C7 | Listar los marcadores del documento digital. | Pezoa (2020) RFP7 |
| C8 | Activar/desactivar las figuras proyectadas sobre el papel. | Pezoa (2020) RFP8 |
| C9 | Eliminar un marcador del documento digital. | Pezoa (2020) RFP9 |
| C10 | Eliminar un comentario del documento digital. | Pezoa (2020) RFP10 |
| C11 | Resaltar en el papel y reflejarlo en el PDF. | Carrasco (2017) RFCA4 |
| C12 | Resaltar en el PDF y reflejarlo en el papel. | Carrasco (2017) RFCA5 |
| G1 | Reconocimiento gestual de la mano con cámara USB. | Contreras (2019) RFCO10 |
| G2 | Reconocimiento de la posición de un lápiz de color con cámara USB. | Contreras (2019) RFCO11 |
| G3 | Seleccionar con el gesto un fragmento y capturarlo. | Contreras (2019) RFCO5 |
| RO1–RO7 | Rastreo ocular: seguir la mirada, retícula, interacción por mirada, registro CSV, varios dispositivos, módulo de registro común y selección del dispositivo. | Estay (2020) RFE1–RFE7 |
| B1–B13 | Búsqueda: enciclopedia, definiciones, traducción, video, imágenes, selección de proveedor, visualizar/ocultar resultados, historial, voz y lector. | Montanares (2019) RFM1–RFM13 |
| RFS1–RFS8 | Interfaz: acceso a lectura aumentada, búsqueda, consistencia y rastreo; configurar, navegar, guardar y reiniciar ajustes. | Santibáñez (2020) |
| U1 | Mostrar al abrir los pasos para preparar la sesión de lectura con el estado real de cada módulo. | Nuevo (interfaz) |
| U2 | Fijar los puntos de calibración gestual desde la lectura actual del sensor. | Nuevo (interfaz) |
| U3 | Informar los mensajes con avisos no modales que no detienen la lectura. | Nuevo (interfaz) |

### No funcionales

| ID | Descripción |
|---|---|
| RNF-01 | Latencia orquestador→plugin ≤ 8,3 ms en el percentil 95 (50 % de una muestra a 60 Hz). |
| RNF-02 | Aislamiento de fallos: un plugin que falla no detiene el sistema y queda registrado. |
| RNF-03 | Cobertura de líneas de las pruebas automatizadas ≥ 80 %. |
| RNF-04 | Extensibilidad: un plugin nuevo se agrega con una clase y una entrada en plugins.json, sin tocar el núcleo. |
| RNF-05 | Validación sin laboratorio: todo el sistema se puede ejecutar y probar con dispositivos simulados. |
| RNF-06 | Interfaz: conserva todos los controles y flujos de EDDIE-2023 (mismo nombre y comportamiento), en español, con los botones de la proyección en la franja superior, la zona de lectura y las cruces en su posición original y sin amarillo fuera del resaltado (Ibaceta, 2023). |
| RNF-07 | Plataforma: Windows 11, Python ≥ 3.11, sin dependencias nativas de 32 bits. |
| RNF-08 | Sin APIs web vencidas: los servicios de búsqueda los responde un LLM (Gemini 2.5 Flash) y la clave no se versiona. |

## 5. Avances

### P-00 — Prototipos desechables de factibilidad

Fase PDCA: **Plan** · Objetivo específico: **OE1** · Semanas del plan: **1–3** · Carpeta: `P-00_prototipos_desechables`

| | |
|---|---|
| **ID Prototipo** | P-00 |
| **Nombre** | Prototipos desechables de factibilidad |
| **Objetivos** | Comprobar, módulo por módulo, que cada funcionalidad del C# se puede migrar a Python con las bibliotecas propuestas (OpenCV, Tesseract, PyMuPDF, sockets/WebSocket, importlib, voz).<br>Detectar bloqueos de compatibilidad antes de diseñar el núcleo. |
| **Descripción** | Programas aislados y de bajo costo (throwaway prototyping de RAD), uno por capacidad técnica, que trabajan con la cámara, el PDF o el micrófono reales. No usan el núcleo ni los contratos: su único propósito es confirmar la factibilidad. Sus resultados alimentan el diseño de los contratos de P-01. |
| **Requisitos Funcionales** | — (factibilidad técnica) |
| **Requisitos No Funcionales** | RNF-07 |

#### Qué se revisa en este avance

1. Que cada prototipo abra el dispositivo o archivo real y produzca el resultado esperado (frame, texto, contorno, coordenadas, anotación en el PDF, audio).
2. Qué biblioteca reemplaza a cada dependencia del C# (Emgu CV → OpenCV, iTextSharp → PyMuPDF, System.Speech → pyttsx3/SpeechRecognition, WatsonWebSocket → websockets).
3. Las evidencias que cada prototipo guarda con la tecla S (carpeta evidencias/real).

#### Cómo ejecutarlo

```powershell
python prototipos\prototipo_f01.py   (cada prototipo se ejecuta por separado)
```

#### Resultados

_Este avance no tiene evidencias automáticas: los prototipos se ejecutan con la cámara, el PDF o el micrófono reales y guardan su evidencia con la tecla S._

Prototipos incluidos (los números que faltan no existen en el repositorio):

| ID | Archivo | Qué valida | Contrato/módulo destino | Tecnología |
|---|---|---|---|---|
| F01 | `prototipo_f01.py` | Enumeración e inicialización de cámaras (nombres reales vía PowerShell/DirectShow) | ICameraSensor | OpenCV |
| F02 | `prototipo_f02.py` | Preprocesamiento y binarización (Otsu) de un frame real | IImageProcessor | OpenCV |
| F03 | `prototipo_f03.py` | OCR con Tesseract sobre el frame de cámara | IImageProcessor | pytesseract |
| F04 | `prototipo_f04.py` | Detección del contorno de la página/libro | IConsistencyProvider | OpenCV |
| F05 | `prototipo_f05.py` | Seguimiento de lápiz de color (centroide y trayectoria) | IGesturePlugin | OpenCV |
| F06 | `prototipo_f06.py` | Segmentación de piel/mano (YCrCb + HSV) | IGesturePlugin | OpenCV |
| F07 | `prototipo_f07.py` | Homografía de 4 esquinas de la hoja (vista rectificada) | IConsistencyProvider | OpenCV |
| F09 | `prototipo_f09.py` | Mouse como sustituto de la mirada y retícula | IEyeTracker | OpenCV |
| F10 | `modificar_demo_real_f10.py` | Conexión con eye tracker real: GazeCloud (WebSocket) y EyeTribe (TCP) | IEyeTracker | websockets / socket |
| F11 | `modificar_demo_real_f11.py` | Carga dinámica de módulos con importlib | PluginLoader | importlib |
| F12 | `modificar_demo_real_f12.py` | Clic por permanencia de la mirada (dwell 600 ms) | IEyeTracker | OpenCV |
| F13 | `modificar_demo_real_f13.py` | Retícula de mirada sobre la proyección | IEyeTracker | OpenCV |
| F14 | `prototipo_f14.py` | Búsqueda de texto y QuadPoints en un PDF real | IConsistencyProvider | PyMuPDF |
| F15 | `prototipo_f15.py` | Resaltado físico → PDF digital | IConsistencyProvider | OpenCV + PyMuPDF |
| F16 | `prototipo_f16.py` | Notas adhesivas físicas ↔ comentarios del PDF (con OCR) | IConsistencyProvider | OpenCV + PyMuPDF + Tesseract |
| F17 | `prototipo_f17.py` | Figuras geométricas PDF ↔ papel proyectado | IConsistencyProvider | OpenCV + PyMuPDF |
| F24 | `prototipo_f24.py` | Comandos de voz en español | ISpeechProvider | SpeechRecognition + sounddevice |
| F25 | `prototipo_f25.py` | Lectura en voz alta (SAPI5) | ISpeechProvider | pyttsx3 |
| F27 | `prototipo_f27.py` | Banda de resaltado digital proyectada sobre la línea | Proyección | OpenCV |

### P-01 — Núcleo orquestador y contratos de plugins

Fase PDCA: **Do (diseño)** · Objetivo específico: **OE2** · Semanas del plan: **4–6** · Carpeta: `P-01_nucleo_orquestador`

| | |
|---|---|
| **ID Prototipo** | P-01 |
| **Nombre** | Núcleo orquestador y contratos de plugins |
| **Objetivos** | Definir PluginBase y los contratos de cada módulo (ICameraSensor, IImageProcessor, IGesturePlugin, IEyeTracker, IConsistencyProvider, IWebSearchProvider, ISpeechProvider).<br>Implementar el OrchestratorCore (inicializar → ejecutar → liberar) y el PluginLoader con un único mecanismo de carga.<br>Validar la inyección de dependencias sensor→consumidor, el aislamiento de fallos y la latencia por ciclo. |
| **Descripción** | Primera versión del núcleo, sin interfaz. Se prueba con dispositivos simulados (MockCameraSensor, EyeTrackerMock) y con plugins de prueba: un consumidor de frames, un consumidor de resultados del ciclo, un plugin que falla cada 10 ciclos y una entrada con una clase inexistente (equivalente a la DLL faltante de los errores E38/E50). El OrchestratorCore de este avance es la versión temprana del repositorio (sin overrides, invoke ni reinicio en caliente). |
| **Requisitos Funcionales** | N1, N2, N3, RFCO12 |
| **Requisitos No Funcionales** | RNF-01, RNF-02, RNF-04, RNF-05 |

#### Qué se revisa en este avance

1. Que todos los plugins válidos queden «initialized» y la clase inexistente quede «load_failed» sin detener el arranque (inicializacion.json).
2. Que la falla inyectada en los ciclos 10, 20, … quede aislada: los demás plugins entregan resultado en todos los ciclos.
3. Que el consumidor reciba el sensor por inyección y no abra la cámara por su cuenta.
4. Que cada contrato herede de PluginBase y no pueda instanciarse sin implementar sus métodos.
5. Latencia por plugin y por ciclo frente al umbral de 8,3 ms (latencias.json).

#### Cómo ejecutarlo

```powershell
python main.py --cycles 300
python -m pytest
python tools\generar_evidencias.py
```

#### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:56:42.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 34 | 0 | 0 | 81 % | 0,98 ms | 2,50 ms |

Plugin con mayor latencia (p95): **FrameStatistics**, 0,78 ms (umbral 8,3 ms). Detalle por plugin en `P-01_nucleo_orquestador/evidencias/RESULTADOS.md`.

No se inicializó **PluginInexistente** (load_failed): entrada con clase inexistente, puesta a propósito para probar el aislamiento.

### P-02 — Capa de abstracción de hardware y módulo de consistencia

Fase PDCA: **Do (implementación)** · Objetivo específico: **OE3** · Semanas del plan: **7–8** · Carpeta: `P-02_hal_y_consistencia`

| | |
|---|---|
| **ID Prototipo** | P-02 |
| **Nombre** | Capa de abstracción de hardware y módulo de consistencia |
| **Objetivos** | Incorporar DeviceFactory para conmutar cada dispositivo entre real y simulado sin cambiar código.<br>Implementar la cámara real (OpenCV, hilo de captura) y la enumeración de cámaras de Windows.<br>Integrar primero el módulo sin dependencia de hardware: la consistencia papel↔PDF como plugin IConsistencyProvider (PyMuPDF).<br>Extender el núcleo con overrides de configuración, invocación bajo demanda, reinicio en caliente y traza de ejecución. |
| **Descripción** | El núcleo pasa a su versión definitiva y se agrega la capa HAL. La consistencia (resaltados, marcadores, comentarios y figuras, búsqueda de texto) se ejecuta a través del orquestador con OrchestratorCore.invoke(). Sigue sin interfaz: se demuestra con demos/demo_consistencia.py, que sincroniza tres «fotos» sintéticas de la hoja con un PDF de prueba y guarda el PDF resultante y el render de cada página. |
| **Requisitos Funcionales** | N4, N5, N6, N8, C1, C2, C3, C7, C9, C10, C11 (parcial) |
| **Requisitos No Funcionales** | RNF-01, RNF-02, RNF-04, RNF-05 |

#### Qué se revisa en este avance

1. Que con EDDIE_DEVICE_MODE=sim la cámara sea MockCameraSensor y con real la de OpenCV, sin tocar código.
2. Que una cámara inexistente falle de forma limpia (initialize → False) y no detenga el sistema.
3. Que invoke() devuelva errores legibles (por ejemplo «No hay un PDF cargado») en vez de excepciones.
4. Que marcador azul, nota amarilla y figuras magenta del papel se conviertan en marcador, comentario y figuras del PDF (evidencias/consistencia).
5. Que lo sincronizado siga en el PDF al reabrirlo (sección «Al reabrir el PDF guardado»).

#### Cómo ejecutarlo

```powershell
python main.py --sim
python demos\demo_consistencia.py
python -m pytest
python tools\generar_evidencias.py
```

#### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:56:48.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 41 | 1 | 0 | 73 % | 0,20 ms | 2,49 ms |

Plugin con mayor latencia (p95): **TextCamera**, 0,15 ms (umbral 8,3 ms). Detalle por plugin en `P-02_hal_y_consistencia/evidencias/RESULTADOS.md`.

Demostración de consistencia (`P-02_hal_y_consistencia/evidencias/consistencia/`): 10/10 llamadas correctas. Al reabrir el PDF: anotaciones por página [0, 0, 2] (esperado [1, 1, 2]), 0 marcadores. **Se pierden cambios → hallazgo H-02.**

Hallazgos relacionados: H-02 (ver «Hallazgos de la verificación»).

### P-03 — Reconocimiento de texto e interfaz de configuración

Fase PDCA: **Do (implementación)** · Objetivo específico: **OE3** · Semanas del plan: **9** · Carpeta: `P-03_reconocimiento_texto_e_interfaz`

| | |
|---|---|
| **ID Prototipo** | P-03 |
| **Nombre** | Reconocimiento de texto e interfaz de configuración |
| **Objetivos** | Integrar el reconocimiento del texto resaltado (IImageProcessor: segmentación del resaltado + Tesseract) sobre la cámara de texto declarada.<br>Construir la ventana de configuración a partir de los controles extraídos de los .Designer.cs, con un diseño propio en español (ui/theme.py, ui/modern_forms.py) y las páginas Texto (OCR) y Documento PDF.<br>Ejecutar el ciclo del orquestador dentro de Qt (EddieRuntime) y persistir los ajustes.<br>Poder probar el OCR y ver el PDF cargado desde estas páginas, sin esperar la pantalla de proyección. |
| **Descripción** | Aparece la interfaz. Conserva todos los controles del original (mismo nombre, tipo, rangos y estado inicial), ordenados en tarjetas con layouts de Qt, con un menú lateral que muestra el estado de cada módulo y una pantalla de inicio «Preparar sesión». Solo se construyen las páginas de los módulos ya integrados: las demás aparecen en el menú deshabilitadas con el avance en que se integran, y «Iniciar proyección» avisa que la proyección llega en P-06. Como en el C# el texto reconocido solo se veía desde la proyección, se agregan el botón «Reconocer texto» con el texto reconocido y una vista previa del PDF con navegación de páginas. Los mensajes son avisos no modales. |
| **Requisitos Funcionales** | FD1, N7, U1, U3, RFS3, RFS5, RFS6, RFS7, RFS8 |
| **Requisitos No Funcionales** | RNF-01, RNF-06, RNF-07 |

#### Qué se revisa en este avance

1. Que «Reconocer texto» marque el resaltado amarillo en la imagen y muestre el texto leído por el OCR («aumentada» en la hoja simulada; con la cámara real, la palabra que resaltes en papel).
2. Que Documento PDF muestre la página del PDF cargado y permita recorrerlo.
3. Que cada control de los formularios incluidos exista con su nombre, tipo, rango y estado del C#.
4. Que «Preparar sesión» y el menú lateral cambien de estado al cargar el PDF.
5. Que Guardar y Restaurar valores persistan y restauren los ajustes (config/user_settings.json).
6. Que Documento PDF abra un PDF válido y rechace uno dañado con un aviso, sin cerrarse.
7. Capturas de la ventana principal, Texto (OCR) y Documento PDF (evidencias/capturas).

#### Cómo ejecutarlo

```powershell
python main.py --sim
python -m pytest
python tools\generar_evidencias.py
```

#### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:56:54.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 65 | 0 | 0 | 67 % | 0,20 ms | 0,58 ms |

Plugin con mayor latencia (p95): **TextCamera**, 0,15 ms (umbral 8,3 ms). Detalle por plugin en `P-03_reconocimiento_texto_e_interfaz/evidencias/RESULTADOS.md`.

Figuras disponibles para la tesis:

- `P-03_reconocimiento_texto_e_interfaz/evidencias/capturas/00_menu_settings.png` — Tercer prototipo: Ventana principal con «Preparar sesión» y el estado de cada módulo.
- `P-03_reconocimiento_texto_e_interfaz/evidencias/capturas/01_text.png` — Tercer prototipo: Texto (OCR) con la cámara simulada y el texto reconocido.
- `P-03_reconocimiento_texto_e_interfaz/evidencias/capturas/02_page.png` — Tercer prototipo: Documento PDF con la vista previa.

Hallazgos relacionados: H-02 (ver «Hallazgos de la verificación»).

### P-04 — Interacción gestual

Fase PDCA: **Do (implementación)** · Objetivo específico: **OE3** · Semanas del plan: **10** · Carpeta: `P-04_interaccion_gestual`

| | |
|---|---|
| **ID Prototipo** | P-04 |
| **Nombre** | Interacción gestual |
| **Objetivos** | Integrar los plugins gestuales del C# (Color Pen, Hand Skin, Mouse) bajo IGesturePlugin, compartiendo la cámara gestual declarada.<br>Portar la calibración sensor→aplicación, el control del cursor («Recognition on»), la máquina de estados del clic y la captura automática de la selección.<br>Agregar la página Gestos, con calibración asistida («Fijar inicio» / «Fijar fin» desde la lectura del sensor). |
| **Descripción** | Los tres detectores heredan una base común (CalibratedGesturePlugin) que aplica la calibración y el clic; cada uno solo implementa su detección. Este avance porta el comportamiento del C# tal cual, incluida la rotación fija de 180° de Hand Skin, que después se detectó como defecto (H-01). |
| **Requisitos Funcionales** | G1, G2, G3, U2 |
| **Requisitos No Funcionales** | RNF-01, RNF-04, RNF-06 |

#### Qué se revisa en este avance

1. Que el lápiz simulado mueva las coordenadas del sensor y la calibración las transforme al espacio de la aplicación.
2. Que al soltar el lápiz se capture la selección (imagen lista para la búsqueda por imagen).
3. Que los tres plugins aparezcan en el combobox por contrato y se reconecten al reiniciar la cámara.
4. Latencia del ciclo con el reconocimiento gestual activo.
5. Que «Fijar inicio» y «Fijar fin» copien la lectura del sensor a la calibración.
6. Captura de Gestos con la mano: la imagen aparece invertida (hallazgo H-01).

#### Cómo ejecutarlo

```powershell
python main.py --sim
python -m pytest
python tools\generar_evidencias.py
```

#### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:57:04.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 79 | 1 | 0 | 72 % | 1,50 ms | 1,76 ms |

Plugin con mayor latencia (p95): **ColorPenRecognition**, 1,00 ms (umbral 8,3 ms). Detalle por plugin en `P-04_interaccion_gestual/evidencias/RESULTADOS.md`.

Figuras disponibles para la tesis:

- `P-04_interaccion_gestual/evidencias/capturas/00_menu_settings.png` — Cuarto prototipo: Ventana principal con «Preparar sesión» y el estado de cada módulo.
- `P-04_interaccion_gestual/evidencias/capturas/01_text.png` — Cuarto prototipo: Texto (OCR) con la cámara simulada y el texto reconocido.
- `P-04_interaccion_gestual/evidencias/capturas/02_page.png` — Cuarto prototipo: Documento PDF con la vista previa.
- `P-04_interaccion_gestual/evidencias/capturas/03_gesture_mano.png` — Cuarto prototipo: Gestos con Hand Skin (mano).
- `P-04_interaccion_gestual/evidencias/capturas/03_gesture_lapiz.png` — Cuarto prototipo: Gestos con Color Pen (lápiz).

Hallazgos relacionados: H-01, H-02 (ver «Hallazgos de la verificación»).

### P-05 — Rastreo ocular

Fase PDCA: **Do (implementación)** · Objetivo específico: **OE3** · Semanas del plan: **11–12** · Carpeta: `P-05_rastreo_ocular`

| | |
|---|---|
| **ID Prototipo** | P-05 |
| **Nombre** | Rastreo ocular |
| **Objetivos** | Unificar GazePoint (Open Gaze API), TheEyeTribe y GazeCloud bajo IEyeTracker, con EyeTrackerMock como contingencia (DeviceFactory).<br>Portar la sesión de mirada: control del mouse por mirada, clic por permanencia, retícula y registro CSV.<br>Agregar la página Rastreo ocular (exportar/importar configuración). |
| **Descripción** | Los tres protocolos se prueban con servidores falsos que emiten el mismo formato que los dispositivos reales. La sesión de mirada es un consumidor de resultados del ciclo: recibe la muestra del eye tracker en el mismo ciclo en que se produce. |
| **Requisitos Funcionales** | RO1–RO7, RFS4 |
| **Requisitos No Funcionales** | RNF-01, RNF-02, RNF-05 |

#### Qué se revisa en este avance

1. Que cada protocolo (GazePoint, EyeTribe, GazeCloud) entregue GazePoint normalizados.
2. Que un eye tracker sin dispositivo falle la inicialización sin afectar al resto.
3. Que «Aplicar y conectar» con el eye tracker simulado muestre la retícula y escriba el CSV de la sesión.
4. Formato del archivo de configuración exportado (mismas claves que el C#).
5. Que los botones de carpeta, las casillas y los íconos de ayuda de Rastreo ocular no lancen excepciones (hallazgo H-03).

#### Cómo ejecutarlo

```powershell
python main.py --sim
python -m pytest
python tools\generar_evidencias.py
```

#### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:57:18.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 94 | 1 | 0 | 74 % | 1,41 ms | 3,53 ms |

Plugin con mayor latencia (p95): **ColorPenRecognition**, 0,92 ms (umbral 8,3 ms). Detalle por plugin en `P-05_rastreo_ocular/evidencias/RESULTADOS.md`.

Figuras disponibles para la tesis:

- `P-05_rastreo_ocular/evidencias/capturas/00_menu_settings.png` — Quinto prototipo: Ventana principal con «Preparar sesión» y el estado de cada módulo.
- `P-05_rastreo_ocular/evidencias/capturas/01_text.png` — Quinto prototipo: Texto (OCR) con la cámara simulada y el texto reconocido.
- `P-05_rastreo_ocular/evidencias/capturas/02_page.png` — Quinto prototipo: Documento PDF con la vista previa.
- `P-05_rastreo_ocular/evidencias/capturas/03_gesture_mano.png` — Quinto prototipo: Gestos con Hand Skin (mano).
- `P-05_rastreo_ocular/evidencias/capturas/03_gesture_lapiz.png` — Quinto prototipo: Gestos con Color Pen (lápiz).
- `P-05_rastreo_ocular/evidencias/capturas/04_eye.png` — Quinto prototipo: Rastreo ocular.

Hallazgos relacionados: H-01, H-02, H-03 (corregido en este avance) (ver «Hallazgos de la verificación»).

### P-06 — Pantalla de proyección, búsqueda con LLM y voz

Fase PDCA: **Do (implementación)** · Objetivo específico: **OE3** · Semanas del plan: **12** · Carpeta: `P-06_proyeccion_busqueda_llm_y_voz`

| | |
|---|---|
| **ID Prototipo** | P-06 |
| **Nombre** | Pantalla de proyección, búsqueda con LLM y voz |
| **Objetivos** | Integrar la pantalla de proyección (ProjectionScreenActivity2): modo resaltado/captura, búsqueda y sincronización papel↔PDF, con los botones en la franja superior (zona de mayor validez del eye tracker según Ibaceta, 2023) y la zona de lectura y las cruces en su posición original.<br>Responder los cinco servicios de búsqueda con Gemini 2.5 Flash bajo IWebSearchProvider, en lugar de las APIs vencidas (Wikipedia, Google, Bing, YouTube, Cloud Vision).<br>Integrar lectura en voz alta y comandos de voz (ISpeechProvider) y las páginas Interacción y Búsquedas. |
| **Descripción** | Con este avance el sistema queda completo y equivale al código de «Proyecto final» antes de la verificación. Es una extensión respecto del alcance del seminario, donde IWebSearchProvider quedaba solo como interfaz. |
| **Requisitos Funcionales** | B1–B13, C5, C6, C8, C11, C12, RFS1, RFS2 |
| **Requisitos No Funcionales** | RNF-01, RNF-06, RNF-08 |

#### Qué se revisa en este avance

1. Flujo completo: resaltar → OCR → corregir el término → definición/enciclopedia (LLM local falso en las pruebas) → historial CSV.
2. Que el modo actual, el servicio que respondió y la tarjeta del sincronizador se vean en la proyección, y que ningún color de la interfaz sea amarillo.
3. Búsqueda por imagen con la captura del gesto.
4. Sincronizar un resaltado de la proyección con el PDF y buscar páginas.
5. Avisos cuando falta el término, la imagen o el PDF.

#### Cómo ejecutarlo

```powershell
python main.py --sim
python -m pytest
python tools\generar_evidencias.py
```

#### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:57:35.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 100 | 2 | 0 | 81 % | 1,49 ms | 10,28 ms |

Plugin con mayor latencia (p95): **ColorPenRecognition**, 0,97 ms (umbral 8,3 ms). Detalle por plugin en `P-06_proyeccion_busqueda_llm_y_voz/evidencias/RESULTADOS.md`.

No se inicializó **LLM-Gemini** (initialization_failed): en la máquina donde se generó no había clave de Gemini; en tu PC se carga desde config/secrets.json o GEMINI_API_KEY.

Figuras disponibles para la tesis:

- `P-06_proyeccion_busqueda_llm_y_voz/evidencias/capturas/00_menu_settings.png` — Sexto prototipo: Ventana principal con «Preparar sesión» y el estado de cada módulo.
- `P-06_proyeccion_busqueda_llm_y_voz/evidencias/capturas/01_text.png` — Sexto prototipo: Texto (OCR) con la cámara simulada y el texto reconocido.
- `P-06_proyeccion_busqueda_llm_y_voz/evidencias/capturas/02_page.png` — Sexto prototipo: Documento PDF con la vista previa.
- `P-06_proyeccion_busqueda_llm_y_voz/evidencias/capturas/03_gesture_mano.png` — Sexto prototipo: Gestos con Hand Skin (mano).
- `P-06_proyeccion_busqueda_llm_y_voz/evidencias/capturas/03_gesture_lapiz.png` — Sexto prototipo: Gestos con Color Pen (lápiz).
- `P-06_proyeccion_busqueda_llm_y_voz/evidencias/capturas/04_eye.png` — Sexto prototipo: Rastreo ocular.
- `P-06_proyeccion_busqueda_llm_y_voz/evidencias/capturas/05_web.png` — Sexto prototipo: Búsquedas (proveedor LLM y servicio por tipo).
- `P-06_proyeccion_busqueda_llm_y_voz/evidencias/capturas/06_interactions.png` — Sexto prototipo: Interacción (voz y botones).
- `P-06_proyeccion_busqueda_llm_y_voz/evidencias/capturas/10_proyeccion.png` — Sexto prototipo: Pantalla de proyección renovada.
- `P-06_proyeccion_busqueda_llm_y_voz/evidencias/capturas/11_proyeccion_busqueda.png` — Sexto prototipo: Proyección con definición y enciclopedia (LLM local de prueba).
- `P-06_proyeccion_busqueda_llm_y_voz/evidencias/capturas/12_proyeccion_pdf.png` — Sexto prototipo: Proyección con el sincronizador del PDF.
- `P-06_proyeccion_busqueda_llm_y_voz/evidencias/capturas/13_proyeccion_historial.png` — Sexto prototipo: Proyección con el historial de búsquedas.

Hallazgos relacionados: H-01, H-02 (ver «Hallazgos de la verificación»).

### P-07 — Versión final verificada

Fase PDCA: **Check / Act** · Objetivo específico: **OE4** · Semanas del plan: **13–17** · Carpeta: `P-07_version_final_verificada`

| | |
|---|---|
| **ID Prototipo** | P-07 |
| **Nombre** | Versión final verificada |
| **Objetivos** | Verificar el sistema integrado: cobertura, latencia, trazabilidad de errores y pruebas de regresión.<br>Corregir los hallazgos de la verificación (H-01, H-02, H-03) y dejar una prueba que los detecte.<br>Cerrar la documentación técnica (README, EQUIVALENCIAS, DISENO_INTERFAZ). |
| **Descripción** | Es el contenido de «Proyecto final» con las correcciones de la verificación. Cada hallazgo tiene una prueba de regresión que falla con el código de P-06 y pasa con el de P-07. |
| **Requisitos Funcionales** | Todos los anteriores |
| **Requisitos No Funcionales** | RNF-01, RNF-02, RNF-03, RNF-04, RNF-05, RNF-06, RNF-07, RNF-08 |

#### Qué se revisa en este avance

1. Las 107 pruebas (incluye regresiones de H-01, H-02 y H-03) y la cobertura ≥ 80 %.
2. Latencia del ciclo completo con todos los plugins ≤ 8,3 ms (p95).
3. Captura de Gestos con la mano en la orientación correcta y la casilla «Rotar la imagen 180°».
4. Demostración de consistencia: lo sincronizado se conserva al reabrir el PDF.
5. Pruebas de aceptación con el hardware del laboratorio (tools\generar_evidencias.py --real y MECIVA PS), que se completan en el laboratorio.

#### Cómo ejecutarlo

```powershell
python main.py
python main.py --sim
python -m pytest
python tools\generar_evidencias.py  [--real]
```

#### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:58:01.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 107 | 0 | 0 | 81 % | 1,48 ms | 2,31 ms |

Plugin con mayor latencia (p95): **ColorPenRecognition**, 0,93 ms (umbral 8,3 ms). Detalle por plugin en `P-07_version_final_verificada/evidencias/RESULTADOS.md`.

No se inicializó **LLM-Gemini** (initialization_failed): en la máquina donde se generó no había clave de Gemini; en tu PC se carga desde config/secrets.json o GEMINI_API_KEY.

Figuras disponibles para la tesis:

- `P-07_version_final_verificada/evidencias/capturas/00_menu_settings.png` — Séptimo prototipo: Ventana principal con «Preparar sesión» y el estado de cada módulo.
- `P-07_version_final_verificada/evidencias/capturas/01_text.png` — Séptimo prototipo: Texto (OCR) con la cámara simulada y el texto reconocido.
- `P-07_version_final_verificada/evidencias/capturas/02_page.png` — Séptimo prototipo: Documento PDF con la vista previa.
- `P-07_version_final_verificada/evidencias/capturas/03_gesture_mano.png` — Séptimo prototipo: Gestos con Hand Skin (mano).
- `P-07_version_final_verificada/evidencias/capturas/03_gesture_lapiz.png` — Séptimo prototipo: Gestos con Color Pen (lápiz).
- `P-07_version_final_verificada/evidencias/capturas/04_eye.png` — Séptimo prototipo: Rastreo ocular.
- `P-07_version_final_verificada/evidencias/capturas/05_web.png` — Séptimo prototipo: Búsquedas (proveedor LLM y servicio por tipo).
- `P-07_version_final_verificada/evidencias/capturas/06_interactions.png` — Séptimo prototipo: Interacción (voz y botones).
- `P-07_version_final_verificada/evidencias/capturas/10_proyeccion.png` — Séptimo prototipo: Pantalla de proyección renovada.
- `P-07_version_final_verificada/evidencias/capturas/11_proyeccion_busqueda.png` — Séptimo prototipo: Proyección con definición y enciclopedia (LLM local de prueba).
- `P-07_version_final_verificada/evidencias/capturas/12_proyeccion_pdf.png` — Séptimo prototipo: Proyección con el sincronizador del PDF.
- `P-07_version_final_verificada/evidencias/capturas/13_proyeccion_historial.png` — Séptimo prototipo: Proyección con el historial de búsquedas.

Demostración de consistencia (`P-07_version_final_verificada/evidencias/consistencia/`): 10/10 llamadas correctas. Al reabrir el PDF: anotaciones por página [1, 1, 2] (esperado [1, 1, 2]), 2 marcadores. Se conserva todo.

Hallazgos relacionados: H-01 (corregido), H-02 (corregido), H-03 (corregido) (ver «Hallazgos de la verificación»).

## 6. Hallazgos de la verificación

Formato de la fase de reparación de MECIVA PS (Ibaceta, 2023). Estados: SS sin solución, SP parcial, SF final.

| ID | Módulo | Descripción | Estado | Justificación o solución | Detectado en | Prueba de regresión |
|---|---|---|---|---|---|---|
| H-01 | Interacción gestual | Al calibrar con Hand Skin la vista de la cámara aparece rotada 180°. HandSkinRecognition.cs rotaba siempre la imagen porque la cámara del laboratorio estaba montada invertida; el port conservó esa rotación fija, solo en ese plug-in (Color Pen y Mouse no rotan), así que la vista previa y las coordenadas de calibración quedaban al revés con cualquier otra cámara. | SF | La rotación pasa a ser una opción común de los tres plug-ins (rotate_180, por defecto desactivada) que se aplica una sola vez al frame; vista previa, coordenadas y recorte comparten orientación. Casilla nueva «Rotar la imagen 180°» en Gestos para el montaje invertido del laboratorio. | Prueba de uso (calibración con la mano) | `test_gesture_preview_keeps_camera_orientation_by_default, test_rotate_180_is_optional_and_shared_by_preview_coordinates_and_capture, test_gesture_page_rotate_checkbox_controls_plugin_orientation` |
| H-02 | Consistencia | ConsistencyPlugin guardaba cada cambio con saveIncr(). Con PyMuPDF 2.1, desde el segundo guardado incremental el PDF queda con la xref dañada; al reabrirlo PyMuPDF lo «repara» y se pierden los resaltados, comentarios y marcadores guardados antes. En pantalla no se notaba porque el documento en memoria seguía correcto. | SF | Cada guardado escribe una copia completa en un archivo temporal, reemplaza el original y vuelve a abrirlo (se mantiene el respaldo .bac). Si otro programa tiene el PDF bloqueado (Windows), se reintenta y luego se informa con un mensaje claro. | Demostración del avance P-02 (reabrir el PDF guardado) | `test_successive_saves_keep_every_annotation_on_disk, test_locked_pdf_reports_a_clear_error_and_keeps_working, test_h02_demo_de_consistencia_conserva_todos_los_cambios_en_disco` |
| H-03 | Interfaz (Rastreo ocular) | Al pulsar los botones de carpeta o las casillas de Rastreo ocular aparecía «'bool' object has no attribute 'mapToGlobal'». La ayuda contextual se conectaba con lambda w=widget, t=text a la señal clicked; en los botones, clicked(bool) entrega checked y Qt lo pasaba como primer argumento, reemplazando w por False. La acción del botón sí se ejecutaba, pero cada clic dejaba una excepción. | SF | La ayuda por clic queda solo para los íconos de información; los botones y casillas la muestran al pasar el mouse. La lambda ignora los argumentos de la señal (lambda *_, w=widget, t=text). Se corrige desde P-05, primer avance con esos controles, hasta P-07. | Ejecución de P-05 en el PC (traceback en el log) | `test_info_icons_and_buttons_with_help_do_not_raise` |

## 7. Resumen de requisitos por prototipo

Equivale a las tablas 3.9 y 3.10 de Matías.

### Requisitos funcionales

| | P-01 | P-02 | P-03 | P-04 | P-05 | P-06 | P-07 |
|---|---|---|---|---|---|---|---|
| N1 | X |  |  |  |  |  | X |
| N2 | X |  |  |  |  |  | X |
| N3 | X |  |  |  |  |  | X |
| N4 |  | X |  |  |  |  | X |
| N5 |  | X |  |  |  |  | X |
| N6 |  | X |  |  |  |  | X |
| N7 |  |  | X |  |  |  | X |
| N8 |  | X |  |  |  |  | X |
| RFCO12 | X |  |  |  |  |  | X |
| FD1 |  |  | X |  |  |  | X |
| C1 |  | X |  |  |  |  | X |
| C2 |  | X |  |  |  |  | X |
| C3 |  | X |  |  |  |  | X |
| C5 |  |  |  |  |  | X | X |
| C6 |  |  |  |  |  | X | X |
| C7 |  | X |  |  |  |  | X |
| C8 |  |  |  |  |  | X | X |
| C9 |  | X |  |  |  |  | X |
| C10 |  | X |  |  |  |  | X |
| C11 |  | X |  |  |  | X | X |
| C12 |  |  |  |  |  | X | X |
| G1 |  |  |  | X |  |  | X |
| G2 |  |  |  | X |  |  | X |
| G3 |  |  |  | X |  |  | X |
| RO1–RO7 |  |  |  |  | X |  | X |
| B1–B13 |  |  |  |  |  | X | X |
| RFS1–RFS8 |  |  | X |  | X | X | X |
| U1 |  |  | X |  |  |  | X |
| U2 |  |  |  | X |  |  | X |
| U3 |  |  | X |  |  |  | X |

### Requisitos no funcionales

| | P-01 | P-02 | P-03 | P-04 | P-05 | P-06 | P-07 |
|---|---|---|---|---|---|---|---|
| RNF-01 | X | X | X | X | X | X | X |
| RNF-02 | X | X |  |  | X |  | X |
| RNF-03 |  |  |  |  |  |  | X |
| RNF-04 | X | X |  | X |  |  | X |
| RNF-05 | X | X |  |  | X |  | X |
| RNF-06 |  |  | X | X |  | X | X |
| RNF-07 |  |  | X |  |  |  | X |
| RNF-08 |  |  |  |  |  | X | X |

## 8. Cómo regenerar las evidencias en tu computador

```powershell
cd "C:\Users\nicol\OneDrive\Documentos\GitHub\Trabajo-de-titulo\Proyecto final"
.venv\Scripts\activate
python avances\generar_todo.py              # todos los avances, dispositivos simulados
cd "avances\P-04_interaccion_gestual"
python main.py --sim                         # abrir un avance concreto
python tools\generar_evidencias.py --real   # en el laboratorio, con cámaras y eye tracker
```

Cada avance usa el mismo `.venv` de «Proyecto final». Las capturas se toman con la cámara simulada para que sean comparables entre avances. Para la cámara gestual se usa una escena con una mano y el rótulo «ARRIBA», que deja ver de inmediato si la imagen está invertida (P-04 frente a P-07).

## 9. Cómo llevarlo a la tesis

- **Capítulo 3 (Análisis), sección Prototipado**: una subsección por avance con su tabla (están en `tabla_prototipos.tex`, listas para Overleaf), dos o tres capturas de `evidencias/capturas` y lo que se revisó. P-00 va como prototipos desechables de factibilidad (OE1).
- **Capítulo 3, Resumen**: las matrices de la sección 7.
- **Capítulo 5 (Evaluación)**: pruebas y cobertura de P-07, latencias (`latencias.csv` permite graficar), hallazgos H-01/H-02 en la matriz de trazabilidad, y las pruebas con `--real` del laboratorio.
