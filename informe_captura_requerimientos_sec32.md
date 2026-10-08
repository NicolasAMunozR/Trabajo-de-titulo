# Capítulo 3.2: Captura de Requerimientos del Sistema EDDIE (Python Migration)

---

## 3.2 CAPTURA DE REQUERIMIENTOS

El proceso de captura de requerimientos para la actualización del núcleo de la plataforma **EDDIE** (*Empowering Digital Paper with Interactive Enhancements*), a partir del sistema legacy monolítico en C# (ubicado en `EDDIE-2023/proyecto_eddie`), se llevó a cabo mediante un enfoque multifacético y defensivo, diseñado para asegurar una cobertura completa y actualizada de las necesidades científicas y operativas del proyecto.

Este proceso no solo se centró en la consolidación de las funcionalidades previas de interacción físico-digital en papel impreso, sino también en la resolución estructural de los **67 errores documentados por Ibaceta (2023)** y la adopción de una arquitectura extensible basada en plugins en **Python 3.14**.

A continuación, se detallan las fuentes de información y las etapas metodológicas utilizadas:

1. **Revisión de Requerimientos e Historial Legacy**: Se analizaron los requerimientos funcionales y no funcionales compilados en el desarrollo original de la plataforma (Gutiérrez Gálvez, 2016; Ibaceta, 2023). Esta revisión permitió establecer una línea base de las capacidades que debían ser mantenidas (como el trazado de destacan, lectura de QuadPoints y notas adhesivas) y aquellas que requerían una reestructuración crítica (como la carga dinámica de ensamblados DLL y la gestión de punteros nulos).
2. **Directrices del Profesor Guía y Diagnóstico Arquitectónico**: Se integraron las prioridades identificadas en el diagnóstico de la arquitectura C#, reclasificando los errores en 7 categorías formales. Se estableció como requisito obligatorio el desacoplamiento total del núcleo respecto a las librerías de terceros (reemplazando iTextSharp por PyMuPDF y Emgu.CV por OpenCV nativo) y la incorporación de un orquestador central (`OrchestratorCore`).
3. **Análisis del Estado del Arte**: Se estudiaron plataformas de captura y análisis multimodal como **NoldusHub**, **OpenSignals**, **Tobii Pro Lab** y **OBS Studio**. De este análisis se extrajeron los paradigmas de sincronización temporal multicanal, la estructuración de eventos en JSON y la separación entre plugins de captura (*Capture Plugins*) y plugins de reproducción (*Playback Views*).
4. **Estandarización y Específicación de Historias de Usuario**: Todos los requisitos recopilados fueron formalizados y categorizados por módulos funcionales, eliminando ambigüedades y asegurando que cada requisito fuera claramente verificable mediante pruebas unitarias (`pytest`) y prototipos funcionales (`RAD`).

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
| **Plugins de Captura y Hardware (HAL)** | 3 | Extender conectores de hardware para rastreo ocular (*EyeTracker*), sensores gestuales y procesadores de imagen mediante contratos strictly definidos de interfaz (`PluginBase`). |
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
