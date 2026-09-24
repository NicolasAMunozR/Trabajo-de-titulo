# Documentación Técnica y Arquitectónica Completa del Sistema EDDIE-2023

## 1. Visión General del Sistema

**EDDIE** (*Empowering Digital Paper with Interactive Enhancements* / *EDDIE Augmented Reading*) es un entorno de software científico y de Realidad Aumentada (RA) desarrollado en **C# / .NET Framework (x86)**. Su objetivo principal es asistir y enriquecer la lectura de documentos físicos (libros, artículos impresos) combinando la superficie de lectura en papel con proyecciones digitales enriquecidas e interactivas sobre el escritorio del usuario.

### Montaje Físico y Componentes de Hardware
1. **Documento Físico / Libro**: Ubicado en el escritorio de lectura.
2. **Proyector Superior (Overhead Projector)**: Proyecta la interfaz gráfica, capas de información y elementos visuales (subrayados, notas, resultados de búsqueda) directamente sobre el papel o el escritorio.
3. **Cámara de Texto / Documentos (Cámara 1)**: Orientada al papel para capturar imágenes del texto seleccionado por el usuario o para la detección de páginas.
4. **Cámara de Gestos (Cámara 2)**: Apuntada al área de trabajo para seguir la mano del usuario o un puntero de color (lápiz/marcador).
5. **Rastreador Ocular (Eye Tracker)**: Dispositivos como *The Eye Tribe*, *GazeCloudAPI* (vía webcam) o *Tobii*, que monitorean las coordenadas de la mirada (gaze point) del lector.
6. **Micrófono y Altavoz**: Para el reconocimiento de comandos de voz (*System.Speech*) y la síntesis de voz (Text-to-Speech / TTS) de definiciones y traducciones.

---

## 2. Arquitectura General y Flujo de Datos

La solución `AugmentedReadingApp32.sln` está compuesta por **21 proyectos en C#**, estructurados en capas bien definidas:

```
+-----------------------------------------------------------------------------------+
|                              Escritorio Físico / Libro                            |
|            [ Documento Impreso ] <=====> [ Proyección Digital sobre Escritorio ] |
+-----------------------------------------------------------------------------------+
       | (Captura Video 1)                                   ^ (Overlays Visuales)
       v                                                     |
+------------------------------+            +--------------------------------------+
| ModuloProcesamientoImagenes  |            |     ModuloVisualizacionDatos         |
| - CameraActivity (DirectShow)|            | - HighlightTool (Subrayado proyectado)|
| - ColorRecognition           |            | - FiguresDP (Formas geométricas)     |
| - OCRProcess (Tesseract)     |            +--------------------------------------+
+------------------------------+                             ^
       | (Texto / Imagen ROI)                                |
       v                                                     |
+-----------------------------------------------------------------------------------+
|                AugmentedReadingApp (ProjectionScreenActivity2.cs)                |
| - Orquestación GUI, Navegador CefSharp, Comandos de Voz, Coordinación Multimodal |
+-----------------------------------------------------------------------------------+
   |                    |                    |                        |
   v                    v                    v                        v
+------------+   +------------+   +-----------------------+   +---------------------+
|   Modulo   |   |   Modulo   |   |ModuloConsistenciaDatos|   | ModuloRastreoOcular |
|Reconocim.  |   |  Busqueda  |   | - DigitalDocSync      |   | - IntermediateClass |
|  Gestual   |   |    Web     |   |   (iTextSharp PDF)    |   | - ReticleDrawing    |
+------------+   +------------+   +-----------------------+   +---------------------+
   |                    |                    |                        |
   | (IPlugin)          | (Reflection APIs)  | (Plugins DP/PD)        | (IEyeTracking)
   v                    v                    v                        v
[ColorPen /       [Wikipedia / Bing /  [FiguresDP / PD,        [EyeTribe /
 HandSkin /        CloudVision /        CommentsDP / PD,        GazeCloud /
 LeapMotion /      GoogleDict /         PageMarkerDP / PD]      Tobii]
 Mouse]            YouTube]
```

---

## 3. Desglose Detallado Módulo por Módulo

### 3.1. Aplicación Principal: `AugmentedReadingApp`
Es la capa de presentación y coordinación central de todo el sistema.

* **`ReadingSession.cs`**: Punto de entrada de la aplicación (`static void Main()`). Inicializa el entorno WinForms e invoca la pantalla de configuración principal (`MenuSettings`).
* **`MenuSettings.cs`**: Dashboard de configuración moderno con pestañas laterales. Permite al usuario:
  * Seleccionar las cámaras conectadas y resoluciones de trabajo.
  * Configurar el eye tracker a utilizar.
  * Seleccionar qué APIs de búsqueda web utilizar.
  * Ajustar parámetros de OCR y reconocimiento gestual.
  * Lanzar la pantalla de proyección principal.
* **`ProjectionScreenActivity2.cs`**: **El núcleo interactivo de Realidad Aumentada** (archivo de ~107 KB y >2.000 líneas de código). Se despliega a pantalla completa en el proyector. Contiene:
  * `ChromiumWebBrowser navegador` (*CefSharp*): Navegador embebido para mostrar resultados web y videos de YouTube.
  * `HighlightTool Highlight`: Control gráfico que permite trazar y proyectar franjas de subrayado amarillo sobre el texto físico.
  * `SpeechRecognitionEngine` y `SpeechSynthesizer`: Motor de escucha de voz en español para comandos ("buscar enciclopedia", "traducir", etc.) y lectura de textos en voz alta.
  * Paneles informativos laterales para mostrar definiciones, resúmenes de Wikipedia, traducciones y resultados de Google Cloud Vision.
* **Formularios de Configuración Secundarios**:
  * `PageDetectionSettings.cs`, `GestureRecognitionSettings.cs`, `TextRecognitionSettings.cs`, `EyeTrackingConfiguration2.cs`, `SeleccionApis2.cs`, `SeleccionInteraccionPorVoz2.cs`.
* **Clases de Apoyo UI**: `ButtonModified.cs`, `AlertBox.cs`, `LoadingBox.cs`.

---

### 3.2. Módulo de Procesamiento de Imágenes: `ModuloProcesamientoImagenes`
Se encarga del manejo de dispositivos de captura de video y del pipeline de OCR.

* **`CameraActivity.cs`**: Enamera y administra los dispositivos de video conectados usando la librería `DirectShowLib` (`DsDevice`).
* **`ColorRecognition.cs`**: Recibe los frames de la cámara de texto. Aplica procesamiento de imagen (conversión BGR a escala de grises, umbralización/binarización, filtrado de contornos con `Emgu.CV`) para aislar la región de interés (ROI) que contiene el texto.
* **`OCRProcess.cs`**: Envuelve el motor **Tesseract OCR** (`TesseractEngine` con `tessdata/spa` / `tessdata/eng`) para convertir los mapas de bits recortados en cadenas de texto legible.

---

### 3.3. Módulo de Reconocimiento Gestual: `ModuloReconocimientoGestual` y Plugins
Coordina la interacción sin contacto en el espacio de lectura.

* **`GestureRecognitionActivity.cs`**: Mapea las coordenadas del sensor de gestos `(SensorX, SensorY)` al sistema de coordenadas de la pantalla proyectada `(XFinal, YFinal)`. Simula la interacción del cursor del ratón e invoca clics usando llamadas P/Invoke a la API Win32 de Windows (`user32.dll`: `SetCursorPos`, `mouse_event`).
* **Plugins Gestuales (Complementos)**:
  * **`ColorPenRecognition`**: Detecta la punta de un lápiz o puntero de color específico filtrando por rangos en espacio de color RGB/HSV.
  * **`HandSkinRecognition`**: Realiza segmentación de piel en el espacio de color **YCrCb** (`YCrCbSkinDetector.cs`). Extrae contornos de la mano y calcula **defectos de convexidad** (`CvInvoke.ConvexityDefects`) para contar dedos levantados o identificar el dedo índice apuntando.
  * **`LeapMotionRecognition`**: Integra el sensor de gestos tridimensional Leap Motion.
  * **`MouseRecognition`**: Fallback que usa el puntero del mouse del sistema operativo.

---

### 3.4. Módulo de Rastreo Ocular: `ModuloRastreoOcular` y Plugins
Gestiona el rastreo de la mirada del lector, el despliegue del retículo visual y el registro atencional.

* **`IntermediateClass.cs`**: Singleton thread-safe que administra el estado del eye tracker. Mantiene un proxy interno derivado de `MarshalByRefObject` para cargar/descargar DLLs de rastreo en dominios de aplicación aislados (`AppDomain`).
* **`ReticleDrawing.cs`**: Dibuja en pantalla un retículo visual proyectado sobre el punto donde el usuario fija la mirada.
* **`MouseControl.cs`**: Permite controlar el puntero del mouse utilizando la mirada (gaze control) mediante dwells (fijación prolongada en un punto).
* **`SettingsManager.cs`**: Guarda y recupera perfiles y calibraciones del tracker.
* **Plugins de Rastreo Ocular**:
  * **`PluginEyeTribe`**: Integra el SDK nativo de *The Eye Tribe* (`IGazeListener`).
  * **`PluginGazeCloud`**: Levanta un servidor WebSocket local (`WatsonWsServer`) en `127.0.0.1:3000` para recibir coordenadas de gaze desde la API web *GazeCloudAPI.js*.

---

### 3.5. Módulo de Consistencia Físico-Digital: `ModuloConsistenciaDatos` y Bibliotecas
Mantiene la sincronización bidireccional entre el libro impreso en papel y el archivo PDF digital correspondiente en el equipo.

* **`DigitalDocSync.cs`**: Utiliza **iTextSharp** para:
  * Extraer anotaciones, highlights y quadpoints existentes dentro del archivo PDF (`FilteredTextRenderListener`).
  * Insertar nuevas anotaciones de subrayado amarillo (`PdfStamper`, `PdfAnnotation.CreateMarkup`).
  * Extraer texto de zonas específicas usando filtros de región (`RegionTextRenderFilter`).
* **Bibliotecas de Consistencia**:
  * **`ConsistencyLibraryFiguresDP` / `FiguresPD`**: Sincroniza figuras geométricas (círculos, rectángulos) dibujadas en digital hacia la proyección física (DP: Digital-to-Physical) y viceversa (PD: Physical-to-Digital).
  * **`ConsistencyLibraryCommentsDP` / `CommentsPD`**: Sincroniza notas adhesivas (post-it / sticky notes) del PDF digital al escritorio o detecta post-it físicos colocados en el papel usando segmentación de color HSV para estamparlos como imágenes en el PDF.
  * **`ConsistencyLibraryPageMarkerDP` / `PageMarkerPD`**: Sincroniza marcapáginas o pestañas de separación entre la versión digital e impresa.

---

### 3.6. Módulo de Búsqueda Web: `ModuloBusquedaWeb` y Servicios API
Administra las consultas a servicios externos de conocimiento cuando el usuario selecciona una palabra o imagen.

* **`BuscarEnciclopedia.cs`**, **`BuscarDefinicion.cs`**, **`BuscarImagen.cs`**, **`BuscarVideo.cs`**, **`TraducirTexto.cs`**: Cargan dinámicamente mediante reflexión C# (`Assembly.LoadFile` / `Assembly.LoadFrom`) las librerías API ubicadas en el directorio `./Apis/`.
* **Proyectos de Servicios API**:
  * **`ApiWikipedia`**: Consulta la API REST de Wikipedia en español (`es.wikipedia.org/w/api.php`) y limpia el formato usando expresiones regulares.
  * **`ApiTraduccionBing`**: Consume el servicio Microsoft Azure Cognitive Services Translator API para detección e interpretación de idiomas.
  * **`ApiDefinicionesGoogle`**: Consulta endpoints de diccionario JSON para extraer definiciones conceptuales.
  * **`ApiBusquedaImagenCloudVision`**: Envía imágenes codificadas en Base64 a la API de **Google Cloud Vision** (`WEB_DETECTION`) para reconocer objetos, ilustraciones o diagramas impresos en el libro.
  * **`ApiBuscarYoutube`**: Genera consultas de búsqueda en YouTube y pasa las URLs al navegador CefSharp para reproducir videos explicativos en la proyección.

---

### 3.7. Módulo de Visualización y Registro
* **`ModuloVisualizacionDatos`**:
  * `HighlightTool.cs`: Control `PictureBox` personalizado sobrepuesto en la proyección. Permite arrastrar y crear bandas amarillas translúcidas sobre las líneas de texto.
  * `FiguresDP.cs`: Canvas que renderiza figuras geométricas parseadas desde archivos JSON o anotaciones PDF.
* **`ModuloLog`**:
  * `StandardLogging.cs`: Utiliza **Serilog** con sinks asíncronos (`Serilog.Sinks.Async`, `Serilog.Sinks.File`) para registrar coordenadas de mirada, eventos de interacción y marcas de tiempo sin bloquear el hilo principal de la interfaz gráfica.

---

## 4. Contratos de Interfaz y Extensibilidad

El sistema define interfaces estrictas en proyectos dedicados para garantizar la extensibilidad mediante plugins cargados en tiempo de ejecución:

| Proyecto de Interfaz | Contratos Definidos | Propósito |
| :--- | :--- | :--- |
| `PluginFramework` | `IFilter.cs` (`IPlugin`) | Firma para plugins de reconocimiento gestual (`RunPlugin(VideoCapture src)`, `Point Center`, `DetectGesture`). |
| `InterfacesModuloWeb` | `IBusquedaEnciclopedia`, `IBusquedaImagenes`, `IBusquedaVideos`, `IDefiniciones`, `ITraducciones` | Firma para conectores de servicios web de conocimiento. |
| `InterfacesModuloConsistencia` | `IFiguresDP`, `IFiguresPD`, `ICommentsDP`, `ICommentsPD`, `IPageMarker`, `IPageMarkerPD` | Firma para plugins de sincronización de elementos físico-digitales. |
| `InterfazEyeTracking` | `IEyeTracking.cs` | Firma para controladores de hardware de rastreo ocular (`OpenConnection()`, evento `INotifyPropertyChanged`). |

---

## 5. Resumen de Tecnologías y Librerías Externas

| Componente | Tecnología / Librería | Plataforma / Protocolo |
| :--- | :--- | :--- |
| **Lenguaje y Framework** | C# 7.0+ / .NET Framework 4.5 - 4.7.2 | Arquitectura de compilación a 32 bits (x86) |
| **Interfaz Gráfica (GUI)** | Windows Forms (WinForms) | Win32 API (`user32.dll` P/Invoke) |
| **Navegador Web Embebido** | CefSharp.WinForms | Chromium Embedded Framework (CEF) |
| **Visión Computacional** | Emgu CV v3.x | Binding .NET para OpenCV, DirectShowLib |
| **Motor OCR** | Tesseract OCR (.NET wrapper) | `tessdata` (modelos de idioma en español e inglés) |
| **Manipulación de PDFs** | iTextSharp v5.x | Lectura de QuadPoints y estampado de anotaciones |
| **Voz y Audio** | `System.Speech.Recognition` & `Synthesis` | Motor SAPI nativo de Windows |
| **Rastreo Ocular** | The Eye Tribe SDK, GazeCloudAPI.js, Tobii Pro | WebSockets (`WatsonWebsocket` en puerto 3000), TCP Sockets |
| **Reconocimiento Gestual** | Custom YCrCb / HSV Color Segmenter, Leap Motion SDK | Defectos de convexidad de contornos en OpenCV |
| **Logging** | Serilog | Async File Sink (formato CSV / JSON) |
