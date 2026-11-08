# Equivalencias EDDIE-2023 (C#) → EDDIE Python

## 1. Carga de extensiones: de tres mecanismos de reflexión a uno

| C# | Mecanismo original | Python |
|---|---|---|
| `InteractionCoordinator/TextRecognitionSettings/GestureRecognitionSettings.LoadPlugins` (carpeta `Plugins`) | `Assembly.LoadFrom` | `PluginLoader` + entradas en `config/plugins.json` |
| `SeleccionApis2.obtenerListaApis*`, `ModuloBusquedaWeb/*` (carpeta `Apis`) | `Assembly.LoadFile` | idem (`plugins.llm_search_plugin.LLMSearchPlugin`) |
| `ModuloConsistenciaDatos/*` (carpeta `PluginsConsistencia`) | `Assembly.LoadFile` + `GetTypes()[0]` | idem (`plugins.consistency_plugin.ConsistencyPlugin`) |
| `ModuloRastreoOcular/IntermediateClass` (`Proxy`, `AppDomainPlugin`) | `AppDomain.CreateDomain` + `Assembly.LoadFrom` | idem (`hardware.eye_tracker.EyeTrackerPlugin` + `plugins.gaze_session_plugin`) |

Errores de la tabla de Ibaceta (2023) eliminados por diseño: carpetas inexistentes (`PluginsConsistencia`, E50),
DLL con tipo equivocado en `GetTypes()[0]`, plugins que no cargan por arquitectura x86/x64, y la salida forzada
de la aplicación cuando falta una cámara ("Connect 2 cameras to start EDDIE" → `Environment.Exit(1)`).
Ahora un plugin que falla queda registrado en `initialization_report` y el resto sigue funcionando.

## 2. Módulos

| C# | Python | Contrato |
|---|---|---|
| `CameraActivity.cs` (DirectShow) | `hardware/camera_enumeration.py` | — |
| `VideoCapture` de Emgu + `ImageGrabbed` | `hardware/camera_sensor.py` (hilo de captura) | `ICameraSensor` |
| `ColorRecognition.cs` + `OCRProcess.cs` | `plugins/image_processor_plugin.py` | `IImageProcessor` |
| `GestureRecognitionActivity.cs` | `plugins/gestures/base.py` | `IGesturePlugin` |
| `ColorPenRecognition`, `HandSkinRecognition`, `MouseRecognition` | `plugins/gestures/detectors.py` | `IGesturePlugin` |
| `DigitalDocSync.cs` | `plugins/consistency_plugin.py` (resaltados, búsqueda) | `IConsistencyProvider` |
| `ConsistencyLibraryPageMarkerDP/PD` | `get_bookmarks`, `delete_bookmark`, `sync_bookmark_from_frame` | `IConsistencyProvider` |
| `ConsistencyLibraryCommentsDP/PD` | `get_comments`, `delete_comment`, `sync_comments_from_frame` | `IConsistencyProvider` |
| `ConsistencyLibraryFiguresDP/PD` | `get_figures`, `sync_figures_from_frame` (filtros en `plugins/consistency/vision.py`) | `IConsistencyProvider` |
| `PluginGazeCloud`, `PluginEyeTribe` | `hardware/eye_tracker.py` (+ GazePoint Open Gaze API) | `IEyeTracker` |
| `IntermediateClass`, `MouseControl`, `StandardLogging` | `plugins/gaze_session_plugin.py` | `ICycleResultConsumer` |
| `ReticleDrawing.cs` | `ui/projection_widgets.ReticleOverlay` | — |
| `ButtonAlt.cs` (clic por permanencia de la mirada) | `ui/form_builder.ImageButton` (`dwell_ms`) | — |
| `ApiWikipedia`, `ApiDefinicionesGoogle`, `ApiTraduccionBing`, `ApiBuscarYoutube`, `ApiBusquedaImagenCloudVision` | `plugins/llm_search_plugin.py` (Google Gemini 2.5 Flash) | `IWebSearchProvider` |
| `System.Speech` (síntesis + gramática de comandos) | `plugins/speech_plugin.py` | `ISpeechProvider` |
| `HighlightTool.cs`, `FiguresDP.cs` (ModuloVisualizacionDatos) | `ui/projection_widgets.py` | — |
| `Properties.Settings2` / `App.config` | `app/settings_store.py` → `config/user_settings.json` (mismas claves) | — |

## 3. Interfaz

Cada pantalla se construye desde `ui/layouts/*.json`, generados automáticamente desde los `.Designer.cs`
originales con `tools/winforms_to_json.py` (posiciones, tamaños, textos, fuentes, colores, rangos de los
NumericUpDown). Las imágenes vienen de `Resources/` y de los `.resx` (`tools/extract_resx_images.py`).
La prueba `test_every_original_control_is_rebuilt_at_its_original_geometry` verifica que cada control del
original existe en la misma posición.

| Formulario C# | Python |
|---|---|
| `ReadingSession.Main` | `main.py` |
| `MenuSettings` | `ui/menu_settings.py` |
| `SeleccionInteraccionPorVoz2`, `SeleccionApis2`, `EyeTrackingConfiguration2`, `TextRecognitionSettings`, `GestureRecognitionSettings`, `PageDetectionSettings` | `ui/settings_pages.py` |
| `ProjectionScreenActivity2` | `ui/projection_screen.py` |
| `AlertBox`, `LoadingBox` | `ui/dialogs.py` |
| `busquedasRecientes2` | `ui/projection_widgets.RecentSearchItem` |

No se portaron las interfaces antiguas que el propio original ya no usaba (`InteractionCoordinator`,
`ProjectionScreen`, `ProjectionScreenActivity`, `SeleccionApis`, `SeleccionInteraccionPorVoz`,
`EyeTrackingConfiguration`): `ReadingSession.Main` arranca `MenuSettings`.

## 4. Cambios de comportamiento (correcciones)

| Original | Ahora | Motivo |
|---|---|---|
| Sin dos cámaras la app se cierra | Avisa y sigue; la cámara se puede elegir después | Aislamiento de fallos |
| El traductor no mostraba el panel izquierdo si antes no se usó el diccionario | Muestra el panel | Error de interfaz |
| `buttonPDF` provocaba el mensaje de depuración "FiguresDP is null…" | Mensaje para el usuario | Error de interfaz |
| Marcador físico siempre se creaba en la página 2 ("Esto es otro marcador") | Se crea en la página indicada | Valor fijo en el código |
| Comentarios y figuras físicos siempre en la página 1, con escalas 640×480→792×612 fijas | Página indicada, escala según el tamaño real del frame y del PDF (o calibración espacial) | Valores fijos |
| `FiguresDP` usaba una ruta absoluta de otro computador | Sin rutas absolutas | Error E-ruta |
| "Delete comment" solo quitaba el elemento de la lista | También lo elimina del PDF | Consistencia |
| El gesto hacía clic del sistema aunque *Recognition on* estuviera desactivado | Solo con *Recognition on* | Clics involuntarios |
| Captura en modo imagen sin plug-in → `NullReferenceException` | Se ignora sin error | Robustez |
| Enciclopedia, definiciones y traducción venían de Wikipedia, Google y Bing | Las genera Gemini 2.5 Flash con un prompt por servicio | Las APIs del original no se usan (requisito de la tesis: LLM) |
| Video: URL de la API de YouTube; imagen: etiquetas de Cloud Vision | Gemini propone la búsqueda de YouTube / reconoce la imagen (entrada multimodal) y se abre en el navegador embebido | Idem |
| El término a buscar solo venía del OCR | El lector puede corregirlo en *Captured content* | Errores de OCR |
| Cámara gestual por defecto en el índice 0 (igual que la de texto) | Índice 1 | Evita abrir la misma cámara dos veces |
| El texto reconocido solo se veía desde la pantalla de proyección (CaptureTxt) | Botón *Recognize text* y campo con el texto reconocido en *Text recognition*; el recorte queda visible 4 s | Probar el OCR sin abrir la proyección (avance P-03) |
| *Page detection* solo mostraba la ruta y el tamaño de página del PDF | Vista previa de la página con navegación ‹ › | Confirmar que se cargó el PDF correcto |
| El OCR devolvía las letras vecinas que toca el resaltador ("1 aumentada e") | Se descartan los fragmentos de 1–2 caracteres que tocan el borde del resaltado (si queda al menos una palabra) y el recorte se muestra derecho | Texto reconocido limpio para buscar |
| La ayuda de cada control se abría al hacer clic en cualquier control con `clicked`, incluidos botones y casillas | Solo los íconos de información la abren al hacer clic; los botones y casillas la muestran al pasar el mouse | Los botones entregaban `checked` a la lambda y fallaba con "'bool' object has no attribute 'mapToGlobal'" (hallazgo H-03) |
| — | La hoja de la cámara simulada se dibuja en `initialize()`, no en el primer ciclo | Evita un pico de ~20 ms en el primer ciclo |
| `HandSkinRecognition` rotaba siempre 180° la imagen (cámara del laboratorio montada invertida): con otra cámara la vista de calibración de la mano salía al revés y solo ese plug-in usaba coordenadas rotadas | La rotación es opcional y común a los tres plug-ins gestuales (casilla *Rotate 180°*, `rotate_180` en `plugins.json`); se aplica una vez al frame, así vista previa, coordenadas de calibración y recorte coinciden | Hallazgo de la verificación (avance P-07) |
| `ConsistencyPlugin._save` guardaba con `saveIncr()`; con PyMuPDF 2.x, desde el segundo guardado el PDF quedaba con la xref dañada y al reabrirlo se perdían resaltados, comentarios y marcadores anteriores | Cada guardado escribe una copia completa (temporal + reemplazo) y reabre el documento; si otro programa tiene el PDF bloqueado, se informa con un mensaje claro | Hallazgo H-02 de la verificación (avance P-07) |

## 5. Fuera de alcance

- **Leap Motion**: el plugin original estaba incompleto y depende del SDK de Leap; se puede agregar como
  otro `IGesturePlugin`.
- **Tobii** (DLL presente en el original pero sin plugin): se puede agregar como otro backend de `IEyeTracker`.
- La migración Emgu CV → OpenCV no es numéricamente idéntica; los umbrales están en `plugins.json`
  (`highlight_lower_bgr`, `lower_bgr`, `ycrcb_min`, …) para recalibrarlos en el laboratorio.
