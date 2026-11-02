# EDDIE en Python — núcleo orquestador con arquitectura de plugins

Reimplementación de **EDDIE-2023** (C#/WinForms) sobre el `OrchestratorCore` en Python, con un
**único contrato de plugins** (`PluginBase`) y una capa de abstracción de hardware (`DeviceFactory`).
Al ejecutarlo se abre la **misma interfaz** del original —"EDDIE Menu Settings" y la pantalla
proyectada— con las mismas configuraciones y funciones. Las APIs web vencidas (Wikipedia, Google,
Bing, YouTube, Cloud Vision) **no se usan**: todos esos servicios los responde un **modelo de lenguaje
(LLM), Google Gemini 2.5 Flash**.

## Instalación (Windows 11)

```powershell
cd "Proyecto final"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Programas externos:

| Para | Instalar | Notas |
|---|---|---|
| OCR del texto resaltado | [Tesseract-OCR (UB Mannheim)](https://github.com/UB-Mannheim/tesseract/wiki) | Marcar el idioma *Spanish*. Se detecta solo en `C:\Program Files\Tesseract-OCR`; si está en otra ruta, poner `tesseract_path` en `config/plugins.json`. |
| Búsquedas con LLM (Gemini 2.5 Flash) | Clave gratuita de [Google AI Studio](https://aistudio.google.com/apikey) | Copiar `config/secrets.example.json` como `config/secrets.json` y pegar la clave (o definir la variable de entorno `GEMINI_API_KEY`). `secrets.json` está en `.gitignore`: **nunca subir la clave al repositorio**. |
| Eye tracker | GazePoint Control / EyeTribe Server / página GazeCloud | Deben estar corriendo antes de pulsar **Apply** en *Eye tracking*. |

Las fuentes IBM Plex Sans (licencia OFL) vienen incluidas en `ui/resources/fonts`, así que la
interfaz se ve igual aunque no estén instaladas en el sistema.

## Ejecución

```powershell
python main.py            # EDDIE completo con el hardware real del laboratorio
python main.py --sim      # mismo sistema con cámaras y eye tracker simulados (DeviceFactory)
python main.py --sim --headless 300   # solo el orquestador, 300 ciclos, imprime latencias
python -m pytest          # 86 pruebas (unitarias, de contrato y de flujos de interfaz)
```

En modo `--sim` la cámara de texto muestra una hoja con un resaltado amarillo (invertida, como la
cámara del montaje) y la cámara gestual un lápiz rojo en movimiento; el eye tracker simulado
(*EyeTrackerMock*) usa el cursor como mirada. Sirve para probar todo sin el laboratorio.

## Uso (igual que el original)

1. **Text Recognition / Gesture Recognition**: elegir cámara y resolución. En gestos, elegir el
   plug-in (Color Pen, Hand Skin o Mouse), **Start Recognition** y, si corresponde, calibrar
   (Sensor/App Start/End) y activar *Recognition on* para que el gesto mueva el cursor.
2. **Page detection**: *Select PDF* con el documento digital del libro.
3. **Web search services**: cada servicio (enciclopedia, definiciones, traducción, video, imágenes) lo
   responde *LLM · Google Gemini 2.5 Flash*; elegir el idioma de traducción.
4. **Interactions WS**: activar interacción por voz y/o botones.
5. **Eye tracking**: elegir el eye tracker, la retícula, control del mouse por mirada, guardado CSV → *Apply*.
6. **Save Settings** y **Start Projection**. En la proyección: botón amarillo para modo
   *Highlight* → resaltar una palabra → el OCR la escribe en *Captured content* → *Web Searcher* →
   diccionario, traductor, enciclopedia, video o imágenes. *Synchronizer* abre las herramientas
   papel ↔ PDF (resaltados, marcadores, comentarios, figuras, búsqueda de páginas).

Los ajustes se guardan en `config/user_settings.json` (mismas claves que `Settings2` del C#);
las búsquedas de la sesión en `CSV_registro_actividades/log_actividades.csv`; cada acción con su
latencia en `logs/plugin-flow-*.jsonl`.

## Estructura

```
contracts/      Contratos: PluginBase, ICameraSensor, IImageProcessor, IGesturePlugin, IEyeTracker,
                IConsistencyProvider, IWebSearchProvider, ISpeechProvider, ICycleResultConsumer
orchestrator/   OrchestratorCore (+ invoke/restart/stop por contrato), PluginLoader, DeviceFactory, trazas
hardware/       Cámara (hilo de captura), eye trackers (GazePoint, EyeTribe, GazeCloud), mouse del SO, simulados
plugins/        OCR resaltado, gestos (ColorPen, HandSkin, Mouse), consistencia PDF, LLM, voz, sesión de mirada
app/            Ajustes del usuario y runtime (ciclo del orquestador dentro de Qt)
ui/             Pantallas Qt construidas desde ui/layouts/*.json (extraídos de los .Designer.cs) y recursos
tools/          Conversores WinForms → JSON y extractor de imágenes .resx (reproducibles)
config/         plugins.json (todos los plugins, un único mecanismo de carga)
tests/          Pruebas
```

Para agregar un plugin: crear una clase que implemente el contrato correspondiente y declararla en
`config/plugins.json`. Aparece automáticamente en el combobox de su categoría (gestos, eye trackers
o servicios de búsqueda).

Detalle de equivalencias C# → Python, cambios de comportamiento y lo que queda fuera de alcance:
[`docs/EQUIVALENCIAS.md`](docs/EQUIVALENCIAS.md).
