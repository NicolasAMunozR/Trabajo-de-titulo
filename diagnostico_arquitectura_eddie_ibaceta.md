# Diagnóstico de la Arquitectura C# de EDDIE mediante Reclasificación Oficial de Errores de Ibaceta (2023)

---

## 1. Visión General del Diagnóstico

El presente documento constituye el **Diagnóstico de la Arquitectura de Software del sistema EDDIE legacy en C#**, formulado a partir de la reclasificación completa de los **67 errores** documentados en la memoria de título de **Ibaceta (2023)**.

Para este estudio, la totalidad de los 67 errores se ha categorizado bajo la estructura formal de **7 Categorías de Análisis**:

```
+----------------------------------------------------------------------------------------------------+
|                DISTRIBUCIÓN DE ERRORES SEGÚN LAS 7 CATEGORÍAS ARQUITECTÓNICAS (N=67)               |
+----------------------------------------------------------------------------------------------------+
| Categoría                                            N° Errores   % Relativo   Barra de Frecuencia  |
+----------------------------------------------------------------------------------------------------+
| (a) Infraestructura técnica de carga y despliegue        16          23.9%     ██████████████████  |
| (b) Hardware/sensores                                     9          13.4%     ██████████          |
| (c) Documentación                                         2           3.0%     ██                |
| (d) Práctica de código/lógica interna                    26          38.8%     ████████████████████████████
| (e) UI/idioma                                             3           4.5%     ███                 |
| (f) Infraestructura de laboratorio                        3           4.5%     ███                 |
| (g) Servicios externos/APIs                               8          11.9%     █████████           |
+----------------------------------------------------------------------------------------------------+
| TOTAL                                                    67         100.0%                         |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Definición y Alcance de las 7 Categorías

### **(a) Infraestructura técnica de carga y despliegue (16 Errores / 23.9%)**
Engloba los fallos vinculados a la carga dinámica de ensamblados (`Assembly.LoadFrom`, `Assembly.LoadFile`), aislamiento inestable en dominios de aplicación (`AppDomain.CreateDomain`), DLLs externas faltantes o bloqueadas por seguridad Windows (`Zone.Identifier`), referencias desactualizadas en archivos `.csproj`, incompatibilidades de la versión `.NET Framework / NetStandard`, problemas de ramas/permisos Git, y **rutas absolutas localmente hardcodeadas** a computadores de desarrolladores anteriores (`C:\Users\Dennise\...`, `C:\Users\jose_ibaceta\...`).

### **(b) Hardware/sensores (9 Errores / 13.4%)**
Comprende fallos de detección, inicialización, reconexión e inestabilidad en dispositivos físicos: cámaras de documentos y de gestos, desconexión de sensores de rastreo ocular (*Eye Tribe / Tobii*), descalibración física en zonas de proyección, enfocado incorrecto de lentes sobre la interfaz y degradación por uso prolongado (buffers de imagen en blanco o negro).

### **(c) Documentación (2 Errores / 3.0%)**
Falta absoluta de artefactos de soporte al usuario y desarrollador: ausencia de manual de instalación y manual de usuario, lo que imposibilita la reproducibilidad y el despliegue autónomo del software.

### **(d) Práctica de código/lógica interna (26 Errores / 38.8%)**
Es la categoría más voluminosa. Incluye fallas en la lógica de negocio interna: desreferenciación de punteros nulos (`auxcapture=null`, `controller=null`, `logging=null`), excepciones al no cargar un PDF, fallas por falta de argumentos obligatorios (como número de página), desalineación espacial en las coordenadas de subrayado e interacción físico-digital (highlights $F \rightarrow D$ y $D \rightarrow F$), parsing incompatible de PDF, falta de comentarios de código y variables/funciones con nombres no representativos.

### **(e) UI/idioma (3 Errores / 4.5%)**
Inconvenientes relacionados con la capa de presentación WinForms: desajuste de resolución en proyector (escalado de UI), mensajes de error presentados en un idioma distinto (inglés) respecto a la aplicación, y etiquetas de botones que no reflejan su función real (`save settings`).

### **(f) Infraestructura de laboratorio (3 Errores / 4.5%)**
Condiciones del entorno físico de desarrollo y prueba: inestabilidad en la conexión de internet del laboratorio, falta de enchufes/conexiones eléctricas y restricciones de permisos/seguridad en los equipos locales.

### **(g) Servicios externos/APIs (8 Errores / 11.9%)**
Deficiencias en la integración con servicios web remotos: caídas por falta de conexión a internet durante consultas de Wikipedia/Diccionario, fallas al incluir caracteres especiales (como `(`) en URLs de enciclopedia, falta de detección de cambio de proveedor de API, vencimiento de credenciales (Bing Translation / Google Cloud Vision), y búsquedas que fallan si la palabra no es idéntica en la fuente.

---

## 3. Matriz Exhaustiva de Reclasificación de los 67 Errores de Ibaceta

| ID | Categoría Ibaceta | Descripción del Error | Estado Ibaceta | Categoría Formal | Causa Raíz en la Arquitectura C# | Solución en la Arquitectura Python |
|:---|:---|:---|:---:|:---:|:---|:---|
| **E1** | Externo | Internet del laboratorio inestable. | SP | **(f)** | Dependencia de red síncrona sin fallback offline en controladores. | Mocks locales y llamadas asíncronas tolerantes a fallos. |
| **E2** | Externo | Problemas de compatibilidad GitKraken y permisos del código. | SF | **(a)** | Estructura de permisos de repositorio desconfigurada en Git. | Entorno virtual `.venv` aislado e ignores estandarizados. |
| **E3** | Interno-otro | No se pudo encontrar el dll `leapC`. | SF | **(a)** | Carga implícita de DLL nativo en ruta del sistema sin verificación. | Interfaz `IGesturePlugin` con verificación pre-vuelo. |
| **E4** | Externo | No se identifica la rama correcta del código en Git. | SP | **(a)** | Gestión desestructurada de ramas de control de versiones. | Flujo Git estandarizado (branching strategy). |
| **E5** | Interno-otro | Falla inicialización por referencias Visual Studio erróneas. | SF | **(a)** | Referencias desactualizadas a ensamblados DLL en `.csproj`. | Gestión unificada de paquetes PyPI con `requirements.txt`. |
| **E6** | Interno-otro | Falla inicialización por falta de dll Serilog. | SF | **(a)** | Acoplamiento rígido a DLL de terceros para registros de log. | Reemplazo por biblioteca nativa `logging` de Python stdlib. |
| **E7** | Interno-otro | Falla inicialización por falta de cámara disponible. | SF | **(b)** | Ausencia de verificación de dispositivos en el arranque. | Comprobación defensiva `isOpened()` en `initialize()`. |
| **E8** | Interno-otro | Mal funcionamiento al no encontrarse 2 cámaras disponibles. | SF | **(b)** | Asunción rígida de doble cámara en flujo principal. | Capa de abstracción con mocks de cámara (`MockCamera`). |
| **E9** | Externo | Falta de conexiones eléctricas en el laboratorio. | SP | **(f)** | Restricción del espacio físico de trabajo. | Documentación de arquitectura de hardware en `hardware.json`. |
| **E10** | Externo | Falta de seguridad en el computador del laboratorio. | SF | **(f)** | Ausencia de aislamiento de permisos de usuario. | Ejecución aislada en entorno virtual `.venv`. |
| **E11** | Interno-consistencia | Sincronización falla si no se ingresa un archivo PDF. | SF | **(d)** | Invocación a iTextSharp sin validar nulidad de archivo de entrada. | Validación de parámetros en contrato `IConsistencyProvider`. |
| **E12** | Externo | No existe manual de instalación para EDDIE. | **SS** | **(c)** | Deuda técnica de documentación e instalación. | `README.md` autoguiado y scripts de despliegue. |
| **E13** | Externo | No existe manual de uso para EDDIE. | **SS** | **(c)** | Deuda técnica de documentación de usuario. | Documentación interactiva y especificación de contratos. |
| **E14** | Interno-otro | Mensajes de error en idioma distinto al resto de la app. | SF | **(e)** | Internacionalización inconsistente en captura de excepciones. | Mensajes de log estructurados en español. |
| **E15** | Externo | No se reconoce el eyetracker en el computador. | SF | **(b)** | Acoplamiento a drivers propietarios sin capa mock de pruebas. | `MockEyeTracker` con interfaz `IEyeTracker` unificada. |
| **E16** | Externo | Conexión de la cámara digital es inestable. | SP | **(b)** | Falta de reconexión automática en bucle de captura OpenCV. | Reintentos automáticos en `IImageProcessor`. |
| **E17** | Interno-otro | No se encuentra el paquete `Netstandard.library`. | SF | **(a)** | Conflicto de versiones de framework (.NET Framework vs NetStandard). | Runtime único Python 3.14. |
| **E18** | Interno-otro | No se encuentra `.NET Framework v4.8`. | SF | **(a)** | Deprecación / dependencia rígida de runtime de compilación. | Migración a Python interprets independiente del framework. |
| **E19** | Interno-otro | Recursos bloqueados por marca de la Web (Zone.Identifier). | SF | **(a)** | Bloqueo de seguridad de Windows en DLLs descargadas. | Eliminación total de DLLs externas compiladas. |
| **E20** | Interno-otro | La interfaz no tiene el tamaño correcto con el proyector. | SF | **(e)** | Coordenadas de resolución hardcodeadas en WinForms. | Parámetros de resolución en `config/hardware.json`. |
| **E21** | Interno-consistencia | Botón de búsqueda hace fallar el programa si no hay PDF. | SF | **(d)** | Acoplamiento directo de eventos GUI con invocación de motor. | Desacoplamiento Event-Driven en `OrchestratorCore`. |
| **E22** | Interno-consistencia | Revisar contenido PDF hace fallar programa si no existe PDF. | SF | **(d)** | Ausencia de verificación `File.Exists()` antes de procesar. | Verificación defensiva previa con `pathlib.Path`. |
| **E23** | Interno-rastreoOcular | App falla al reabrir vista de rastreo ocular tras parámetros. | SF | **(d)** | Fuga de recursos y falta de método `Dispose()` en WinForms. | Manejo imperativo de ciclo de vida `release()` en orquestador. |
| **E24** | Interno-interacción F/D | No se reconoce el texto del documento físico. | SF | **(b)** | Umbralización fija y falta de binarización adaptativa. | Pipeline OpenCV con binarización Otsu adaptativa. |
| **E25** | Interno-búsqueda | Función de diccionario no busca las palabras reconocidas. | SP | **(g)** | Fallo silencioso en cliente HTTP de diccionario. | Interfaz `IWebSearchProvider` desacoplada con mock. |
| **E26** | Interno-búsqueda | Enciclopedia no muestra resultados de palabras reconocidas. | SP | **(g)** | Excepción no capturada en parsing JSON de Wikipedia. | Integración de `wikipedia-api` con parsing robusto. |
| **E27** | Interno-otro | Faltan comentarios en el código para reconocer función. | **SS** | **(d)** | Deuda técnica de mantenibilidad de código. | Cobertura 100% de docstrings estilo Google. |
| **E28** | Interno-otro | Variables y funciones no cuentan con nombres representativos. | **SS** | **(d)** | Incumplimiento de estándares de código (nombres opacos). | Adopción estricta de convenciones PEP 8. |
| **E29** | Interno-consistencia | No se reconoce el contenido del archivo PDF ingresado. | **SS** | **(d)** | Incompatibilidad de iTextSharp con encodings de PDFs. | Reemplazo por `PyMuPDF` (`fitz`), nativamente UTF-8. |
| **E30** | Interno-consistencia | Función PDF falla si no se indica una página a analizar. | SF | **(d)** | Falta de argumentos opcionales / valores por defecto. | Firma con parámetro por defecto `page_num: int = 1`. |
| **E31** | Interno-interacción F/D | Cámara enfoca botones de la interfaz al reconocer texto. | SF | **(b)** | Solapamiento de coordenadas entre área proyectada y cámara. | Delimitación estricta de ROI (Region of Interest). |
| **E32** | Interno-interacción F/D | OCR deja de funcionar tras uso prolongado (imagen negra/blanca). | SF | **(b)** | Fuga de memoria en buffers `Emgu.CV.Mat` / `Bitmap`. | Gestión de memoria implícita en arreglos `NumPy`. |
| **E33** | Interno-búsqueda | No detecta el cambio de la selección de la API de enciclopedia. | SF | **(g)** | Ausencia de patrón Factory para cambio dinámico de API. | Carga declarativa desde `plugins.json`. |
| **E34** | Interno-búsqueda | Al detectar símbolos como `(`, la API de Wikipedia falla. | **SS** | **(g)** | Ausencia de sanitización / URL encoding en consultas HTTP. | Sanitización previa con `urllib.parse.quote`. |
| **E35** | Interno-interacción F/D | No se reconoce correctamente el texto en cada intento. | SP | **(b)** | Sensibilidad a variaciones de iluminación. | Normalización de contraste e histograma en `mod01`. |
| **E36** | Interno-búsqueda | Sin internet, búsqueda de Wikipedia hace fallar el programa. | SF | **(g)** | Falta de captura de `WebException` al consultar servidor. | Captura de `ConnectionError` retornando `SearchResult(success=False)`. |
| **E37** | Interno-búsqueda | No se reconoce la API para la función de traducción. | SP | **(g)** | Vencimiento / cambio de credencial en Bing Translator. | Abstracción en `IWebSearchProvider` para fácil actualización. |
| **E38** | Interno-consistencia | No se encuentra `consistencyLibraryFiguresDP.dll`. | SF | **(a)** | Carga dinámicamente fallida con `Assembly.LoadFile`. | Reemplazo por módulo nativo PyMuPDF sin DLLs externas. |
| **E39** | Interno-búsqueda | Comandos de voz no acceden a búsqueda de diccionario. | SF | **(d)** | Acoplamiento defectuoso entre `SpeechSynthesizer` y API. | Desacoplamiento mediante orquestador central. |
| **E40** | Interno-consistencia | Highlight F→D en posición/largo incorrecto. | **SS** | **(d)** | Bug en transformación de coordenadas iTextSharp-pantalla. | Sistema de coordenadas unificado normalizado `[0,1]`. |
| **E41** | Interno-consistencia | Highlight D→F en posición/largo incorrecto. | **SS** | **(d)** | Bug en mapeo inversivo proyector-papel. | Mapeo homotético normalizado mediante PyMuPDF. |
| **E42** | Interno-consistencia | Comentarios fallan si no se especifica página. | SF | **(d)** | Ausencia de validación de argumentos en DLL comentarios. | Argumento opcional `page_num: int = 1` en `add_comment()`. |
| **E43** | Interno-consistencia | Figuras fallan si no se especifica página. | SF | **(d)** | Ausencia de validación de argumentos en DLL figuras. | Argumento opcional con fallback a página activa. |
| **E44** | Interno-consistencia | Marcapáginas fallan si no se especifica página. | SF | **(d)** | Ausencia de validación de argumentos en DLL marcapáginas. | Argumento opcional en `add_bookmark()`. |
| **E45** | Interno-consistencia | Consistencia contenido falla con datos correctos. | SF | **(d)** | Bug interno en parseador iTextSharp. | Reemplazo total de motor por PyMuPDF. |
| **E46** | Interno-consistencia | Consistencia figuras falla con datos correctos. | SF | **(d)** | Puntero nulo en canvas de renderizado. | Inicialización defensiva de objetos de dibujo. |
| **E47** | Interno-consistencia | Consistencia marcapáginas falla con datos correctos. | SF | **(d)** | Error en formato de tabla de contenidos del PDF. | API limpia `doc.set_toc()` de PyMuPDF. |
| **E48** | Interno-consistencia | Consistencia comentarios falla con datos correctos. | SF | **(d)** | Instanciación fallida de objeto anotación iTextSharp. | API nativa `add_text_annot()` de PyMuPDF. |
| **E49** | Externo | Eye Tribe no detecta parte inferior de la proyección. | **SS** | **(b)** | Calibración incompleta de matriz de transformación. | Re-calibración y normalización en controlador de hardware. |
| **E50** | Interno-consistencia | No se encuentra carpeta `Plugins-Consistencia`. | SF | **(a)** | Dependencia de rutas relativas de carpetas DLL. | Import nativo de paquetes Python sin carpetas de DLLs. |
| **E51** | Interno-rastreoOcular | No se encuentran plugins de rastreo ocular. | SF | **(a)** | Incompatibilidad de `AppDomain.CreateDomain()` en runtime. | Cargador unificado `PluginLoader` sin AppDomains. |
| **E52** | Interno-consistencia | Ruta hardcodeada al computador de desarrollo original. | SP | **(a)** | Cadena de texto de ruta fija escrita en código C#. | Configuración externa en `config/plugins.json`. |
| **E53** | Interno-interfaz | Botón 'save settings' no representa su función. | SF | **(e)** | Evento de clic en GUI no vinculado al controlador. | Persistencia automática en gestor `ConfigManager`. |
| **E54** | Interno-consistencia | Variable `auxcapture=null` hace fallar Figuras. | SF | **(d)** | Ausencia de instanciación del buffer de captura. | Inicialización obligatoria en constructor de plugin. |
| **E55** | Interno-consistencia | Variable `auxcapture=null` hace fallar Marcapáginas. | SF | **(d)** | Puntero nulo no verificado antes de invocación. | Guardas explícitas `if self._capture is not None:`. |
| **E56** | Interno-consistencia | Variable `auxcapture=null` hace fallar Comentarios. | SF | **(d)** | Puntero nulo en gestor de eventos. | Inicialización garantizada en `initialize()`. |
| **E57** | Interno-consistencia | Ruta local de Dennise en marcapáginas F→D. | SF | **(a)** | Ruta fija `"C:\Users\Dennise\..."` escrita en código. | Rutas dinámicas temporales con `tempfile`. |
| **E58** | Interno-consistencia | Ruta local de Dennise en figuras F→D. | SF | **(a)** | Ruta fija a carpeta de desarrollador personal. | Parámetros de ruta centralizados en `hardware.json`. |
| **E59** | Interno-consistencia | Ruta local de Dennise en comentarios F→D. | SF | **(a)** | Ruta fija a directorio de imágenes personales. | Rutas relativas del proyecto. |
| **E60** | Interno-consistencia | Ruta local de Dennise en `FiguresDP`. | SF | **(a)** | Hardcoding de carpeta de salida de renders. | Rutas relativas configurables por el usuario. |
| **E61** | Interno-consistencia | Enciclopedia falla si palabra no se encuentra. | SP | **(g)** | Excepción `KeyError` no capturada al parsear JSON. | Retorno de objeto `SearchResult(success=False)`. |
| **E62** | Interno-consistencia | Enciclopedia falla si palabra no es exacta en Wikipedia. | SP | **(g)** | Falta de desambiguación en consulta HTTP. | Desambiguación automática en `wikipedia-api`. |
| **E63** | Interno-búsqueda | Funcionalidad 'búsqueda de figuras' no ejecutable. | SP | **(d)** | Método stub sin implementación en C#. | Interfaz declarada para implementación en v2.0. |
| **E64** | Interno-rastreoOcular | Variable `controller=null` en controlar mouse. | SF | **(d)** | Invocación de mouse antes de conectar tracker. | Verificación de estado `is_connected` previa. |
| **E65** | Interno-rastreoOcular | Variable `logging=null` en controlar mouse. | SF | **(d)** | Instancia de logger no inyectada en controlador. | Inyección de dependencias de `logging` en orquestador. |
| **E66** | Interno-rastreoOcular | Variable `controller=null` en guardar registro ocular. | SF | **(d)** | Acceso a controlador nulo durante guardado. | Manejo centralizado de datos en `OrchestratorCore`. |
| **E67** | Interno-rastreoOcular | Variable `logging=null` en guardar registro ocular. | SF | **(d)** | Logger desreferenciado en hilo de rastreo. | Sistema de métricas unificado `SessionMetrics`. |

---

## 4. Análisis Detallado por Categoría de Error

```
+----------------------------------------------------------------------------------------------------+
|                                    ANÁLISIS DE IMPACTO ARQUITECTÓNICO                              |
+----------------------------------------------------------------------------------------------------+

 1. CATEGORÍA (d): PRÁCTICA DE CÓDIGO / LÓGICA INTERNA (26 errores - 38.8%)
    - Concentra la mayor fragilidad del software legacy.
    - Causa: Falta de inicialización de objetos (variables null), falta de validación de argumentos y
      bugs en la lógica de conversión espacial de coordenadas físico-digitales.
    - Solución en Python: Ciclo de vida explícito (initialize -> execute -> release), tipos estrictos y
      reemplazo de iTextSharp por PyMuPDF (coordenadas homotéticas normalizadas).

 2. CATEGORÍA (a): INFRAESTRUCTURA TÉCNICA DE CARGA Y DESPLIEGUE (16 errores - 23.9%)
    - Es la causa principal de fallos de inicialización y despliegue del sistema C#.
    - Causa: Uso de 3 mecanismos de reflexión distintos (Assembly.LoadFrom, LoadFile, AppDomain) y
      rutas absolutas hardcodeadas a carpetas de desarrolladores (Dennise, jose_ibaceta).
    - Solución en Python: 1 solo mecanismo de carga dinámico (importlib.import_module) sobre PluginBase
      y configuración centralizada en JSON.

 3. CATEGORÍA (g): SERVICIOS EXTERNOS / APIS (8 errores - 11.9%)
    - Causa: Llamadas HTTP síncronas sin resiliencia, vencimiento de credenciales (Bing, Google Vision) y
      falta de sanitización de cadenas (caracteres especiales como '(').
    - Solución en Python: Capa IWebSearchProvider con resiliencia, sanitización de URLs y uso de
      wikipedia-api gratuita sin API key.

 4. CATEGORÍA (b): HARDWARE / SENSORES (9 errores - 13.4%)
    - Causa: Falta de verificaciones de estado en tiempo de ejecución para cámaras y eye trackers, y
      fugas de memoria en buffers Emgu.CV.
    - Solución en Python: Contratos IImageProcessor e IEyeTracker con inicialización defensiva y mocks.

 5. CATEGORÍAS (c), (e), (f): DOCUMENTACIÓN, UI/IDIOMA E INFRAESTRUCTURA LAB (8 errores - 12.0%)
    - Causa: Deuda de documentación (falta de manuales E12/E13) y acoplamiento de GUI WinForms.
    - Solución en Python: Documentación completa en Markdown, docstrings 100% y configuración de UI en JSON.
+----------------------------------------------------------------------------------------------------+
```

---

## 5. Conclusión para el Informe de Tesis

El diagnóstico basado en las **7 categorías requeridas** demuestra que:

1. **El 62.7% de los errores (42 de 67: categorías a + d)** corresponden a problemas de **arquitectura de software, carga dinámica y prácticas de código interno**, y no a limitaciones del hardware ni del laboratorio.
2. **Los 4 errores que Ibaceta dejó Sin Solución (SS)** en el sistema C# ($E12, E13, E27, E28, E29, E34, E40, E41$) pertenecen a las categorías **(a)**, **(c)**, **(d)** y **(g)**, todos los cuales quedan resueltos estructuralmente mediante la arquitectura de **Orquestador Central y Plugins en Python**.
