# Capítulo 3: Captura de Requerimientos y Prototipado del Sistema EDDIE (Python Migration)

---

## 3.2 CAPTURA DE REQUERIMIENTOS

El proceso de captura de requerimientos para la actualización del núcleo de la plataforma **EDDIE** (*Empowering Digital Paper with Interactive Enhancements*), a partir del sistema legacy monolítico en C# (ubicado en `EDDIE-2023/proyecto_eddie`), se llevó a cabo mediante un enfoque multifacético y defensivo, diseñado para asegurar una cobertura completa y actualizada de las necesidades científicas y operativas del proyecto.

Este proceso no solo se centró en la consolidación de las funcionalidades previas de interacción físico-digital en papel impreso, sino también en la resolución estructural de los **67 errores documentados por Ibaceta (2023)** y la adopción de una arquitectura extensible basada en plugins en **Python 3.14**.

A continuación, se detallan las fuentes de información y las etapas metodológicas utilizadas:

1. **Revisión de Requerimientos e Historial Legacy**: Se analizaron los requerimientos funcionales y no funcionales compilados en el desarrollo original de la plataforma (Gutiérrez Gálvez, 2016; Ibaceta, 2023). Esta revisión permitió establecer una línea base de las capacidades que debían ser mantenidas (como el trazado de destacan, lectura de QuadPoints y notas adhesivas) y aquellas que requerían una reestructuracióID	Requerimiento No Funcional	Criterio de Aceptación / Fuente
RNF-01	Multiplataforma	El sistema debe ser capaz de ejecutarse en sistemas operativos Windows 10/11, Linux (Ubuntu) y macOS utilizando un runtime estándar de Python 3.14 y paquetes multiplataforma PyPI. (Adaptado de Gutiérrez Gálvez, 2016)
RNF-02	Modularidad y Extensibilidad Estricta	El sistema debe permitir la integración de nuevas funcionalidades mediante plugins desacoplados que hereden de PluginBase, sin requerir modificaciones en el código fuente del núcleo.
RNF-03	Internacionalización (i18n)	La interfaz y los módulos deben soportar el cambio dinámico de idioma entre Español e Inglés mediante diccionarios JSON traducibles.
RNF-04	Documentación y Mantenibilidad	El código fuente debe contar con una cobertura del 100% de comentarios docstrings bajo el estándar PEP 8, e incluir guías claras para el desarrollo de nuevos plugins.
RNF-05	Carga Dinámica en Tiempo de Ejecución	El módulo PluginLoader debe ser capaz de instanciar, cargar y descargar plugins en tiempo de ejecución sin necesidad de recompilar la aplicación ni usar dominios de aplicación inestables (AppDomains).
RNF-06	Consistencia Espacio-Temporal Físico-Digital	La conversión de coordenadas entre la superficie de papel impreso y los documentos PDF digitales debe ser homotética y exacta, utilizando puntos tipográficos pt y QuadPoints de 8 vértices sin desalineación.
RNF-07	Eficiencia y Gestión de Memoria	El procesamiento de imágenes con OpenCV debe liberar explícitamente los buffers de memoria (NumPy arrays), evitando congelamientos o degradación del sistema por uso prolongado.
RNF-08	Resiliencia y Tolerancia a Fallos	La falla o excepción en la ejecución de un plugin no debe provocar la caída global del sistema; el orquestador debe aislar el error, registrar el evento en el log y continuar la ejecución defensiva.n crítica (como la carga dinámica de ensamblados DLL y la gestión de punteros nulos).
2. **Directrices del Profesor Guía y Diagnóstico Arquitectónico**: Se integraron las prioridades identificadas en el diagnóstico de la arquitectura C#, reclasificando los errores en 7 categorías formales. Se estableció como requisito obligatorio el desacoplamiento total del núcleo respecto a las librerías de terceros (reemplazando iTextSharp por PyMuPDF y Emgu.CV por OpenCV nativo) y la incorporación de un orquestador central (`OrchestratorCore`).
3. **Análisis del Estado del Arte**: Se estudiaron plataformas de captura y análisis multimodal como **NoldusHub**, **OpenSignals**, **Tobii Pro Lab** y **OBS Studio**. De este análisis se extrajeron los paradigmas de sincronización temporal multicanal, la estructuración de eventos en JSON y la separación entre plugins de captura (*Capture Plugins*) y plugins de reproducción (*Playback Views*).
4. **Estandarización y Especificación de Historias de Usuario**: Todos los requisitos recopilados fueron formalizados y categorizados por módulos funcionales, eliminando ambigüedades y asegurando que cada requisito fuera claramente verificable mediante pruebas unitarias (`pytest`) y prototipos funcionales (`RAD`).

---

### 3.2.1 Requerimientos Funcionales

En la **Tabla 3.1** se presenta el resumen estructurado de los requerimientos funcionales identificados para el sistema EDDIE. Estos definen las operaciones específicas que la plataforma debe realizar en sus componentes del Núcleo, Organización, Captura, Consistencia Físico-Digital, Visualización y Plugins.

#### Tabla 3.1: Resumen de requerimientos funcionales por módulo.

| Módulo | Cantidad de RF | Ejemplos de Requerimientos Representativos |
| :--- | :---: | :--- |
| **Organización y Gestión Experimental** | 12 | Crear, editar, eliminar, visualizar y proteger (bloqueo de lectura *Read-Only*) proyectos de investigación, participantes y protocolos experimentales. |
| **Núcleo y Orquestador Central** | 10 | Administrar el ciclo de vida de plugins (`initialize`, `execute`, `release`), gestionar la persistencia en `preferences.json`, soportar cambio dinámico de idioma (Español/Inglés) e integrar la bandeja del sistema (*System Tray*). |
| **Captura de Datos y Sensores** | 9 | Iniciar, pausar, reanudar y detener capturas síncronas de video de cámara y pantalla; registrar eventos de teclado y mouse en archivos estructurados JSON; gestionar sesiones de captura. |
| **Consistencia Físico-Digital (F14-F17)** | 11 | Búsqueda y mapeo de QuadPoints exactos en PDFs reales (F14); sincronización de destacado fluorescente físico $\leftrightarrow$ digital (F15); detección de Post-Its en papel con Tesseract OCR e inyección de anotaciones (F16); clasificación de figuras geométricas ($C = \frac{4\pi A}{P^2}$) y proyección de halos de luz (F17). |
| **Visualización y Reproducción Síncrona** | 7 | Reproducir sesiones capturadas en una línea de tiempo unificada (*Timeline Scrubber*); sincronizar video, trazo de cursor de mouse y reconstrucción de texto de teclado; organizar espacios de trabajo en ventanas independientes. |
| **Plugins de Captura y Hardware (HAL)** | 3 | Extender conectores de hardware para rastreo ocular (*EyeTracker*), sensores gestuales y procesadores de imagen mediante contratos estrictos de interfaz (`PluginBase`). |
| **Plugins de Visualización y Proyección** | 3 | Desplegar overlays de proyección sobre el papel físico y vistas en miniatura de canales de captura en tiempo real. |
| **TOTAL** | **55** | *Fuente: Elaboración propia, 2026.* |

---

### 3.2.2 Requerimientos No Funcionales

En la **Tabla 3.2** se especifican los requerimientos no funcionales que rigen el diseño y operación de la nueva arquitectura de EDDIE en Python, derivados de las restricciones de calidad, rendimiento y mantenibilidad establecidas para el proyecto de tesis.

#### Tabla 3.2: Requerimientos NO Funcionales.

| ID | Requerimiento No Funcional | Criterio de Aceptación / Fuente |
| :---: | :--- | :--- |
| **RNF-01** | **Multiplataforma** | El sistema debe ser capaz de ejecutarse en sistemas operativos Windows 10/11, Linux (Ubuntu) y macOS utilizando un runtime estándar de Python 3.14 y paquetes multiplataforma PyPI. *(Adaptado de Gutiérrez Gálvez, 2016)* |
| **RNF-02** | **Modularidad y Extensibilidad Estricta** | El sistema debe permitir la integración de nuevas funcionalidades mediante plugins desacoplados que hereden de `PluginBase`, sin requerir modificaciones en el código fuente del núcleo. |
| **RNF-03** | **Internacionalización (i18n)** | La interfaz y los módulos deben soportar el cambio dinámico de idioma entre Español e Inglés mediante diccionarios JSON traducibles. |
| **RNF-04** | **Documentación y Mantenibilidad** | El código fuente debe contar con una cobertura del 100% de comentarios docstrings bajo el estándar PEP 8, e incluir guías claras para el desarrollo de nuevos plugins. |
| **RNF-05** | **Carga Dinámica en Tiempo de Ejecución** | El módulo `PluginLoader` debe ser capaz de instanciar, cargar y descargar plugins en tiempo de ejecución sin necesidad de recompilar la aplicación ni usar dominios de aplicación inestables (*AppDomains*). |
| **RNF-06** | **Consistencia Espacio-Temporal Físico-Digital** | La conversión de coordenadas entre la superficie de papel impreso y los documentos PDF digitales debe ser homotética y exacta, utilizando puntos tipográficos `pt` y QuadPoints de 8 vértices sin desalineación. |
| **RNF-07** | **Eficiencia y Gestión de Memoria** | El procesamiento de imágenes con OpenCV debe liberar explícitamente los buffers de memoria (`NumPy arrays`), evitando congelamientos o degradación del sistema por uso prolongado. |
| **RNF-08** | **Resiliencia y Tolerancia a Fallos** | La falla o excepción en la ejecución de un plugin no debe provocar la caída global del sistema; el orquestador debe aislar el error, registrar el evento en el log y continuar la ejecución defensiva. |

*Fuente: Elaboración propia a partir de Gutiérrez Gálvez (2016) e Ibaceta (2023).*

---

## 3.4 PROTOTIPADO

En esta sección se presentan los prototipos elaborados para la plataforma **EDDIE**, estructurados en iteraciones de prototipado rápido (*Rapid Application Development / RAD*). Cada prototipo fue concebido como una iteración incremental que buscó cumplir con objetivos específicos, orientados a resolver las deficiencias del sistema monolítico legacy en C# (ubicado en `EDDIE-2023/proyecto_eddie`) y satisfacer los requisitos funcionales y no funcionales definidos para la nueva arquitectura en Python.

A continuación, se describen detalladamente los **6 prototipos desarrollados** (P-01 al P-06), detallando para cada uno sus objetivos, su equivalencia con la arquitectura legacy C#, los componentes en Python implementados en la carpeta `eddie-python/prototypes/rad_funcionalidades` y sus principales resultados.

---

### 3.4.1 Primer Prototipo (P-01): Replicación de Funcionalidades Críticas

El primer prototipo tuvo como objetivo principal determinar la viabilidad técnica de replicar las funcionalidades esenciales de EDDIE utilizando el nuevo núcleo tecnológico en Python 3.14 con OpenCV, PyMuPDF y Sockets, desacoplándolo del entorno monolítico WinForms/CefSharp.

#### Tabla 3.3: Primer prototipo - Replicación de funcionalidades críticas.

| Campo | Detalles |
| :--- | :--- |
| **ID Prototipo** | **P-01** |
| **Nombre** | Replicación de funcionalidades críticas |
| **Objetivos** | 1. Validar la viabilidad técnica de la nueva arquitectura desacoplada en Python.<br>2. Implementar captura síncrona multimodal (video, mouse, teclado, sockets UDP).<br>3. Replicar funcionalidades esenciales de `AugmentedReadingApp` sin acoplamiento gráfico monolítico. |
| **Descripción** | Prototipo orientado a la validación temprana mediante la construcción de scripts de captura atómica para eventos de mouse, teclado, video de cámara y comunicación por sockets UDP/TCP. Permite verificar que múltiples flujos de datos pueden operar de forma concurrente sin bloqueo del hilo principal. |
| **Requisitos Funcionales** | RF-22, RF-33, RF-36, RF-50, RF-51, RF-52, RF-53, RF-54, RF-55 |
| **Requisitos No Funcionales** | RNF-01 (Desacoplamiento), RNF-02 (Rendimiento), RNF-05 (Resiliencia), RNF-06 (Portabilidad) |
| **Fuente / Archivo Fuente** | Elaboración propia, 2026. Script: `eddie-python/prototypes/rad_funcionalidades/prototipo_p01_replicacion_critica.py` |

#### Implementación y Resultados de P-01
Se validó la captura síncrona en tiempo real mediante hilos independientes (`threading.Thread`) y la recepción de paquetes UDP en el puerto `9000`. Asimismo, los scripts `prototipo_f01.py` a `prototipo_f09.py` permitieron verificar la detección de hardware de video (DirectShow/MSMF) y el seguimiento de punteros en pantalla.

---

### 3.4.2 Segundo Prototipo (P-02): Implementación del Módulo de Organización

El segundo prototipo correspondió al desarrollo del módulo de administración de datos experimentales, guiando el flujo de trabajo del investigador mediante la gestión de proyectos, participantes y protocolos.

#### Tabla 3.4: Segundo prototipo - Implementación del módulo de organización.

| Campo | Detalles |
| :--- | :--- |
| **ID Prototipo** | **P-02** |
| **Nombre** | Implementación del módulo de organización |
| **Objetivos** | 1. Permitir la gestión estructural de proyectos de investigación, participantes y protocolos.<br>2. Implementar un mecanismo de bloqueo de seguridad (*Read-Only Locking*) para resguardar la integridad de los datos.<br>3. Garantizar la persistencia estructurada mediante formato JSON. |
| **Descripción** | Iteración enfocada en la creación de la lógica de negocio y almacenamiento de proyectos, participantes y secuencias de actividades experimentales. Evita modificaciones o eliminaciones accidentales mediante banderas de bloqueo en disco. |
| **Requisitos Funcionales** | RF-01 al RF-20 |
| **Requisitos No Funcionales** | RNF-01, RNF-02, RNF-04 (Persistencia) |
| **Fuente / Archivo Fuente** | Elaboración propia, 2026. Script: `eddie-python/prototypes/rad_funcionalidades/prototipo_p02_modulo_organizacion.py` |

#### Implementación y Resultados de P-02
Se logró una gestión limpia de datos persistidos en `p02_organizacion_db.json`. Reemplaza la lógica dispersa del formulario `MenuSettings.cs` de C#, habilitando el bloqueo transaccional de protocolos y participantes validados.

---

### 3.4.3 Tercer Prototipo (P-03): Módulo de Captura y Gestión de Plugins

El tercer prototipo abordó el corazón de la interacción físico-digital de EDDIE: la captura síncrona de datos y el motor de plugins de consistencia sobre documentos PDF reales.

#### Tabla 3.5: Tercer prototipo - Módulo de captura y gestión de plugins.

| Campo | Detalles |
| :--- | :--- |
| **ID Prototipo** | **P-03** |
| **Nombre** | Módulo de captura y gestión de plugins de consistencia |
| **Objetivos** | 1. Ejecutar sesiones de captura síncrona de video, eventos de teclado y mouse.<br>2. Implementar la sincronización físico-digital sobre documentos PDF reales (QuadPoints, Highlight, Post-It OCR y Figuras).<br>3. Almacenar eventos estructurados en archivos JSON y videos `.mp4`. |
| **Descripción** | Iteración centrada en la integración del motor de captura y la ejecución de algoritmos de visión por computador (OpenCV HSV, Tesseract OCR) y manipulación vectorial de PDFs (PyMuPDF). Contempla las funcionalidades de consistencia F14, F15, F16 y F17. |
| **Requisitos Funcionales** | RF-22 al RF-30, RF-33 al RF-39, RF-50 al RF-52 |
| **Requisitos No Funcionales** | RNF-01, RNF-02, RNF-04, RNF-05 |
| **Fuente / Archivo Fuente** | Elaboración propia, 2026. Scripts: `prototipo_p03_captura_plugins.py`, `demo_real_f14.py`, `demo_real_f15.py`, `demo_real_f16.py`, `demo_real_f17.py` |

#### Implementación y Resultados de P-03
Se logró la paridad completa del 100% con los módulos C# originales (`DigitalDocSync.cs`, `PageMarkerPD.cs`, `CommentsPD.cs`, `FiguresPD.cs` en `EDDIE-2023/proyecto_eddie`):
* **F14 (QuadPoints)**: Extracción nativa de 8 coordenadas tipográficas QuadPoints ($TL, TR, BL, BR$) con `fitz.search_for(..., quads=True)`.
* **F15 (Highlight)**: Segmentación HSV de resaltadores fluorescentes en papel físico e inyección de anotaciones en PDF.
* **F16 (Post-It OCR)**: Detección de contornos de notas en papel + binarización Otsu + Tesseract OCR (`pytesseract spa+eng`) e inyección de anotaciones `Text/Note`.
* **F17 (Figuras Geométricas)**: Clasificación poligonal con la fórmula exacta de circularidad $C = \frac{4\pi A}{P^2}$ e inyección vectorial en el PDF.

---

### 3.4.4 Cuarto Prototipo (P-04): Módulo de Visualización y Reproducción Síncrona

El cuarto prototipo incorporó el módulo de reproducción multicanal (*Playback Views*), permitiendo revisar las sesiones capturadas en una línea de tiempo unificada.

#### Tabla 3.6: Cuarto prototipo - Módulo de visualización y reproducción síncrona.

| Campo | Detalles |
| :--- | :--- |
| **ID Prototipo** | **P-04** |
| **Nombre** | Módulo de visualización y reproducción síncrona (Playback Views) |
| **Objetivos** | 1. Proporcionar un reproductor multicanal sincronizado por línea de tiempo.<br>2. Sincronizar simultáneamente el video de la sesión, el texto ingresado y el recorrido del cursor del mouse.<br>3. Permitir desplazamiento temporal (*Scrubbing*), pausar y reanudar la reproducción. |
| **Descripción** | Iteración enfocada en la revisión visual de datos multimodales. Garantiza que los distintos canales de datos se mantengan alineados temporalmente durante la inspección. |
| **Requisitos Funcionales** | RF-42 a RF-49, RF-53 a RF-55 |
| **Requisitos No Funcionales** | RNF-01, RNF-02, RNF-04, RNF-05, RNF-06 |
| **Fuente / Archivo Fuente** | Elaboración propia, 2026. Script: `eddie-python/prototypes/rad_funcionalidades/prototipo_p04_visualizacion_playback.py` |

#### Implementación y Resultados de P-04
Reemplaza los componentes rígidos de `ModuloVisualizacionDatos` en C#. Ofrece una barra de tiempo interactiva con avance/retroceso de fotogramas y visualización del rastro del puntero sobre la imagen del documento.

---

### 3.4.5 Quinto Prototipo (P-05): Preferencias de Usuario y Ajustes de la Aplicación

El quinto prototipo se centró en la gestión de configuración del usuario, atajos de teclado (*Hotkeys*) e internacionalización (i18n).

#### Tabla 3.7: Quinto prototipo - Preferencias de usuario y ajustes.

| Campo | Detalles |
| :--- | :--- |
| **ID Prototipo** | **P-05** |
| **Nombre** | Preferencias de usuario y ajustes de la aplicación |
| **Objetivos** | 1. Persistir las preferencias generales del usuario en `preferences.json`.<br>2. Permitir el cambio dinámico de idioma (Español / Inglés).<br>3. Configurar atajos de teclado (*Hotkeys*) para el control de la captura. |
| **Descripción** | Iteración que implementa la persistencia de sesión, recordando el último proyecto, participante y estado de ventana al reiniciar el programa. |
| **Requisitos Funcionales** | RF-21, RF-31, RF-32, RF-40, RF-41 |
| **Requisitos No Funcionales** | RNF-01, RNF-02, RNF-03, RNF-04 |
| **Fuente / Archivo Fuente** | Elaboración propia, 2026. Script: `eddie-python/prototypes/rad_funcionalidades/prototipo_p05_preferencias_ajustes.py` |

#### Implementación y Resultados de P-05
Se implementó el diccionario i18n y la persistencia en `preferences.json`. Resuelve los errores de hardcoding de rutas y mensajes en inglés no traducidos presentes en el sistema C# legacy (errores E14 y E52).

---

### 3.4.6 Sexto Prototipo (P-06): Instalador del Núcleo y Conjunto de Plugins

El sexto prototipo resolvió la distribución y despliegue modular del software mediante un empaquetador de plugins y verificador de entorno.

#### Tabla 3.8: Sexto prototipo - Instalador del núcleo y conjunto de plugins.

| Campo | Detalles |
| :--- | :--- |
| **ID Prototipo** | **P-06** |
| **Nombre** | Instalador del núcleo y paquete de plugins |
| **Objetivos** | 1. Validar las dependencias del entorno virtual Python (`requirements.txt`).<br>2. Empaquetar y descompresión modular de plugins en formato `.zip`.<br>3. Garantizar un despliegue sin fallos de DLLs externas ni bloqueos de Windows (*Zone.Identifier*). |
| **Descripción** | Iteración orientada a automatizar la verificación del entorno y la instalación limpia de extensiones sin requerir compilación ni registros en el GAC. |
| **Requisitos Funcionales** | RF-22 |
| **Requisitos No Funcionales** | RNF-01, RNF-02 |
| **Fuente / Archivo Fuente** | Elaboración propia, 2026. Script: `eddie-python/prototypes/rad_funcionalidades/prototipo_p06_instalador_plugins.py` |

#### Implementación y Resultados de P-06
Soluciona estructuralmente los 16 errores de carga por reflexión de C# (errores E3, E5, E6, E17, E19 y E50), permitiendo instalar y actualizar plugins simplemente depositando un archivo `.zip` en la carpeta `plugins/`.

---

## 3.5 RESUMEN Y MATRIZ DE COBERTURA DE REQUERIMIENTOS

Para finalizar, la **Tabla 3.9** presenta un resumen de los requerimientos funcionales abordados por cada prototipo, mientras que la **Tabla 3.10** sintetiza los requerimientos no funcionales considerados durante su desarrollo.

#### Tabla 3.9: Resumen de requerimientos funcionales cubiertos por prototipo.

| Requerimiento Funcional (RF) | P-01 | P-02 | P-03 | P-04 | P-05 | P-06 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **RF-01 a RF-20** (Gestión de Proyectos, Participantes y Protocolos) | | **X** | | | | |
| **RF-21** (Persistencia de Preferencias e Idioma) | | | | | **X** | |
| **RF-22** (Sistema de Plugins e Instalación Modular) | **X** | | **X** | | | **X** |
| **RF-23 a RF-30** (Captura de Eventos Teclado, Mouse, Video) | | | **X** | | | |
| **RF-31 a RF-32** (Atajos Hotkeys y System Tray) | | | | | **X** | |
| **RF-33 a RF-39** (Consistencia Físico-Digital F14-F17) | **X** | | **X** | | | |
| **RF-40 a RF-41** (Minimización y Atajos de Captura) | | | | | **X** | |
| **RF-42 a RF-49** (Reproducción Síncrona y Playback Views) | | | | **X** | | |
| **RF-50 a RF-52** (Comunicación Sockets / API Python) | **X** | | **X** | | | |
| **RF-53 a RF-55** (Visualización Síncrona Multicanal) | **X** | | | **X** | | |

*Fuente: Elaboración propia, 2026.*

---

#### Tabla 3.10: Resumen de requerimientos NO funcionales considerados por prototipo.

| Requerimiento No Funcional (RNF) | P-01 | P-02 | P-03 | P-04 | P-05 | P-06 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **RNF-01** (Multiplataforma) | **X** | **X** | **X** | **X** | **X** | **X** |
| **RNF-02** (Modularidad y Extensibilidad) | **X** | **X** | **X** | **X** | **X** | **X** |
| **RNF-03** (Internacionalización i18n) | | | | | **X** | |
| **RNF-04** (Documentación PEP 8 / Docstrings) | **X** | **X** | **X** | **X** | **X** | **X** |
| **RNF-05** (Carga Dinámica en Runtime) | **X** | | **X** | **X** | | **X** |
| **RNF-06** (Consistencia Espacio-Temporal F14-F17) | **X** | | **X** | **X** | | |
| **RNF-07** (Bajo Consumo y Liberación OpenCV) | **X** | | **X** | **X** | | |
| **RNF-08** (Resiliencia y Aislamiento de Fallos) | **X** | | **X** | | **X** | |

*Fuente: Elaboración propia, 2026.*
