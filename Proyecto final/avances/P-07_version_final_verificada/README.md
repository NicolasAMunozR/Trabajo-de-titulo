# EDDIE en Python — núcleo orquestador con arquitectura de plugins

Reimplementación de **EDDIE-2023** (C#/WinForms) sobre el `OrchestratorCore` en Python, con un
**único contrato de plugins** (`PluginBase`) y una capa de abstracción de hardware (`DeviceFactory`).
Conserva las configuraciones y funciones del original —ventana de configuración y pantalla
proyectada— con una interfaz rediseñada en español (justificación en
[`docs/DISENO_INTERFAZ.md`](docs/DISENO_INTERFAZ.md)). Las APIs web vencidas (Wikipedia, Google,
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
| Eye tracker | GazePoint Control / EyeTribe Server / página GazeCloud | Deben estar corriendo antes de pulsar **Aplicar y conectar** en *Rastreo ocular*. |

Los iconos son de Lucide (licencia ISC, `ui/resources/icons`). Las fuentes IBM Plex Sans (licencia OFL) vienen incluidas en `ui/resources/fonts`, así que la
interfaz se ve igual aunque no estén instaladas en el sistema.

## Ejecución

```powershell
python main.py            # EDDIE completo con el hardware real del laboratorio
python main.py --sim      # mismo sistema con cámaras y eye tracker simulados (DeviceFactory)
python main.py --sim --headless 300   # solo el orquestador, 300 ciclos, imprime latencias
python -m pytest          # 107 pruebas (unitarias, de contrato, de flujos de interfaz y de regresión)
```

En modo `--sim` la cámara de texto muestra una hoja con un resaltado amarillo (invertida, como la
cámara del montaje) y la cámara gestual un lápiz rojo en movimiento; el eye tracker simulado
(*EyeTrackerMock*) usa el cursor como mirada. Sirve para probar todo sin el laboratorio.

## Uso

Al abrir, **Preparar sesión** muestra los pasos y su estado real (PDF cargado, cámara de texto, proveedor
LLM, gesto, eye tracker, voz); cada paso tiene un botón que lleva a su página.

1. **Texto (OCR) / Gestos**: elegir cámara y resolución. En gestos, elegir el complemento (Color Pen,
   Hand Skin o Mouse), **Iniciar** y calibrar: apuntar a la cruz superior izquierda → **Fijar inicio**,
   a la inferior derecha → **Fijar fin** (o escribir los valores). *Controlar el puntero con el gesto*
   hace que el gesto mueva el cursor.
2. **Documento PDF**: **Elegir PDF…** con el documento digital del libro (se ve la vista previa).
3. **Búsquedas**: cada servicio (enciclopedia, definiciones, traducción, video, imágenes) lo responde
   *LLM · Google Gemini 2.5 Flash*; la tarjeta superior dice si el proveedor está listo.
4. **Interacción**: comandos de voz y botones de búsqueda.
5. **Rastreo ocular**: eye tracker, retícula, control del puntero por mirada, guardado CSV → **Aplicar y conectar**.
6. **Guardar** e **Iniciar proyección**. En la proyección (fondo negro, botones arriba): **Capturando /
   Resaltando** cambia el modo → resaltar una palabra → el OCR la escribe en el campo superior →
   **Buscar** → Definición, Traducción, Enciclopedia, Video o Imagen. **Sincronizar PDF** abre las
   herramientas papel ↔ PDF (resaltados, marcadores, comentarios, figuras, búsqueda de páginas).

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
ui/             Pantallas Qt: lógica (settings_pages, menu_settings, projection_screen) y capa visual
                (theme.py, widgets.py, modern_forms.py; los controles salen de ui/layouts/*.json)
tools/          Conversores WinForms → JSON y extractor de imágenes .resx (reproducibles)
config/         plugins.json (todos los plugins, un único mecanismo de carga)
tests/          Pruebas
```

Para agregar un plugin: crear una clase que implemente el contrato correspondiente y declararla en
`config/plugins.json`. Aparece automáticamente en el combobox de su categoría (gestos, eye trackers
o servicios de búsqueda).

Detalle de equivalencias C# → Python, cambios de comportamiento y lo que queda fuera de alcance:
[`docs/EQUIVALENCIAS.md`](docs/EQUIVALENCIAS.md).

## Avances de desarrollo (para la tesis)

La carpeta [`avances/`](avances/GUIA_AVANCES.md) contiene el código completo de cada iteración
(P-00 prototipos desechables → P-07 versión final verificada), sus pruebas y sus evidencias
(pruebas, cobertura, latencias, capturas). La guía está en `avances/GUIA_AVANCES.md` y las tablas
de prototipos para Overleaf en `avances/tabla_prototipos.tex`. Para regenerar las evidencias:
`python avances\generar_todo.py`. `pytest.ini` limita `python -m pytest` a `tests/` para que no
recorra las carpetas de avance.
