# Capítulo 3.4: Prototipado y Validación Incremental del Sistema EDDIE (Python Migration)

---

## 3.4 PROTOTIPADO

En esta sección se presentan los prototipos elaborados para la plataforma **EDDIE** (*Empowering Digital Paper with Interactive Enhancements*), estructurados en iteraciones de prototipado rápido (*Rapid Application Development / RAD*). Cada prototipo fue concebido como una iteración incremental que buscó cumplir con objetivos específicos, orientados a resolver las deficiencias del sistema monolítico legacy en C# (ubicado en `EDDIE-2023/proyecto_eddie`) y satisfacer los requisitos funcionales y no funcionales definidos para la nueva arquitectura en Python.

A diferencia del sistema C# heredado —que acumulaba **67 errores documentados** por problemas de acoplamiento rígido, fugas de memoria en OpenCV/Emgu.CV y reflexión inestable—, el proceso de prototipado se diseñó para verificar progresivamente la factibilidad técnica, modularidad, consistencia físico-digital y extensibilidad mediante un cargador único de plugins.

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
Se validó la captura síncrona en tiempo real mediante hilos independientes (`threading.Thread`) y la recepción de paquetes UDP en el puerto `9000`. Asimismo, los scripts `prototipo_f01.py` a `prototipo_f09.py` permitieron verificar la detección de hardware de video (DirectShow/MSMF) y el seguimiento de punteros en pantalla, demostrando una reducción del 80% en líneas de código respecto a `ProjectionScreenActivity2.cs` de C#.

---

### 3.4.2 Segundo Prototipo (P-02): Implementación del Módulo de Organización

El segundo prototipo correspondió al desarrollo del módulo de administración de datos experimentales, guiando el flujo de trabajo del investigador mediante la gestión de proyectos, participantes y protocolos.

#### Tabla 3.4: Segundo prototipo - Implementación del módulo de organización.

| Campo | Detalles |
| :--- | :--- |
| **ID Prototipo** | **P-02** |
| **Nombre** | Implementación del módulo de organización |
| **Objetivos** | 1. Permitir la gestión estructural de proyectos de investigación, participantes y protocolos.<br>2. Implementar un mecanismo de bloqueo de seguridad (*Read-Only Locking*) para resguardar la integridad de los datos.<br>3. Garantizar la persistencia estructurada mediante formato JSON. |
| **Descripción** | Iteración enfocada en la creación de la lógica de negocio y almacenamiento de proyectos, participantes y secuencias de actividades experimentales. Evita modificaciones o eliminaciones accidental mediante banderas de bloqueo en disco. |
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

## 3.5 RESUMEN Y MATRIZ DE COBERTURA

Para finalizar, la **Tabla 3.9** sintetiza los Requisitos Funcionales (RF) cubiertos por cada uno de los 6 prototipos desarrollados durante el proceso de migración:

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
