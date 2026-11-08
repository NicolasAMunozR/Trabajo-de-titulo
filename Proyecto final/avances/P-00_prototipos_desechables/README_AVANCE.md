# P-00 — Prototipos desechables de factibilidad

Parte de la serie de avances de EDDIE en Python. La guía general (metodología, requisitos, hallazgos y cómo regenerar las evidencias) está en `../GUIA_AVANCES.md`.

Fase PDCA: **Plan** · Objetivo específico: **OE1** · Semanas del plan: **1–3** · Carpeta: `P-00_prototipos_desechables`

| | |
|---|---|
| **ID Prototipo** | P-00 |
| **Nombre** | Prototipos desechables de factibilidad |
| **Objetivos** | Comprobar, módulo por módulo, que cada funcionalidad del C# se puede migrar a Python con las bibliotecas propuestas (OpenCV, Tesseract, PyMuPDF, sockets/WebSocket, importlib, voz).<br>Detectar bloqueos de compatibilidad antes de diseñar el núcleo. |
| **Descripción** | Programas aislados y de bajo costo (throwaway prototyping de RAD), uno por capacidad técnica, que trabajan con la cámara, el PDF o el micrófono reales. No usan el núcleo ni los contratos: su único propósito es confirmar la factibilidad. Sus resultados alimentan el diseño de los contratos de P-01. |
| **Requisitos Funcionales** | — (factibilidad técnica) |
| **Requisitos No Funcionales** | RNF-07 |

### Qué se revisa en este avance

1. Que cada prototipo abra el dispositivo o archivo real y produzca el resultado esperado (frame, texto, contorno, coordenadas, anotación en el PDF, audio).
2. Qué biblioteca reemplaza a cada dependencia del C# (Emgu CV → OpenCV, iTextSharp → PyMuPDF, System.Speech → pyttsx3/SpeechRecognition, WatsonWebSocket → websockets).
3. Las evidencias que cada prototipo guarda con la tecla S (carpeta evidencias/real).

### Cómo ejecutarlo

```powershell
python prototipos\prototipo_f01.py   (cada prototipo se ejecuta por separado)
```

### Resultados

_Este avance no tiene evidencias automáticas: los prototipos se ejecutan con la cámara, el PDF o el micrófono reales y guardan su evidencia con la tecla S._

## Prototipos

| ID | Archivo | Qué valida | Contrato/módulo destino | Tecnología |
|---|---|---|---|---|
| F01 | `prototipos/prototipo_f01.py` | Enumeración e inicialización de cámaras (nombres reales vía PowerShell/DirectShow) | ICameraSensor | OpenCV |
| F02 | `prototipos/prototipo_f02.py` | Preprocesamiento y binarización (Otsu) de un frame real | IImageProcessor | OpenCV |
| F03 | `prototipos/prototipo_f03.py` | OCR con Tesseract sobre el frame de cámara | IImageProcessor | pytesseract |
| F04 | `prototipos/prototipo_f04.py` | Detección del contorno de la página/libro | IConsistencyProvider | OpenCV |
| F05 | `prototipos/prototipo_f05.py` | Seguimiento de lápiz de color (centroide y trayectoria) | IGesturePlugin | OpenCV |
| F06 | `prototipos/prototipo_f06.py` | Segmentación de piel/mano (YCrCb + HSV) | IGesturePlugin | OpenCV |
| F07 | `prototipos/prototipo_f07.py` | Homografía de 4 esquinas de la hoja (vista rectificada) | IConsistencyProvider | OpenCV |
| F09 | `prototipos/prototipo_f09.py` | Mouse como sustituto de la mirada y retícula | IEyeTracker | OpenCV |
| F10 | `prototipos/modificar_demo_real_f10.py` | Conexión con eye tracker real: GazeCloud (WebSocket) y EyeTribe (TCP) | IEyeTracker | websockets / socket |
| F11 | `prototipos/modificar_demo_real_f11.py` | Carga dinámica de módulos con importlib | PluginLoader | importlib |
| F12 | `prototipos/modificar_demo_real_f12.py` | Clic por permanencia de la mirada (dwell 600 ms) | IEyeTracker | OpenCV |
| F13 | `prototipos/modificar_demo_real_f13.py` | Retícula de mirada sobre la proyección | IEyeTracker | OpenCV |
| F14 | `prototipos/prototipo_f14.py` | Búsqueda de texto y QuadPoints en un PDF real | IConsistencyProvider | PyMuPDF |
| F15 | `prototipos/prototipo_f15.py` | Resaltado físico → PDF digital | IConsistencyProvider | OpenCV + PyMuPDF |
| F16 | `prototipos/prototipo_f16.py` | Notas adhesivas físicas ↔ comentarios del PDF (con OCR) | IConsistencyProvider | OpenCV + PyMuPDF + Tesseract |
| F17 | `prototipos/prototipo_f17.py` | Figuras geométricas PDF ↔ papel proyectado | IConsistencyProvider | OpenCV + PyMuPDF |
| F24 | `prototipos/prototipo_f24.py` | Comandos de voz en español | ISpeechProvider | SpeechRecognition + sounddevice |
| F25 | `prototipos/prototipo_f25.py` | Lectura en voz alta (SAPI5) | ISpeechProvider | pyttsx3 |
| F27 | `prototipos/prototipo_f27.py` | Banda de resaltado digital proyectada sobre la línea | Proyección | OpenCV |
