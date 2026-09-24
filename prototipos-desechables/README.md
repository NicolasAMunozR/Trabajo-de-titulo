# Prototipos Desechables Granulares de Funciones EDDIE-2023

Esta carpeta contiene prototipos desechables rápidos, concisos y aislados (**"probar una función y era"**), diseñados para validar la factibilidad técnica de migrar cada función específica del MVP de EDDIE-2023 (C#/.NET) a Python.

Cada prototipo especifica los **componentes de hardware real necesarios**, ejecuta una **verificación estricta de conexión** antes de llamar a la función e incluye las tecnologías modernas recomendadas por el profesor guía (**Whisper** para audio-a-texto y **Ollama** para LLM local).

---

## 🛠️ Desglose de Prototipos de Funciones EDDIE-2023

| Script | Función EDDIE-2023 | Tecnología Propuesta | Hardware Real Requerido | Verificación de Hardware |
|---|---|---|---|---|
| [`proto_01_camara_texto_ocr.py`](file:///c:/Users/nicol/OneDrive/Documentos/GitHub/Trabajo-de-titulo/prototipos-desechables/proto_01_camara_texto_ocr.py) | Captura de texto impreso y OCR | OpenCV + Tesseract OCR | Cámara 1 (Texto) + `tesseract.exe` | Chequea apertura de Cámara 0 y versión Tesseract |
| [`proto_02_puntero_lapiz_color.py`](file:///c:/Users/nicol/OneDrive/Documentos/GitHub/Trabajo-de-titulo/prototipos-desechables/proto_02_puntero_lapiz_color.py) | Detección de marcador/lápiz de color | OpenCV HSV ColorPen | Cámara 2 (Gestos) | Chequea apertura de Cámara 1 |
| [`proto_03_reconocimiento_mano_dedo.py`](file:///c:/Users/nicol/OneDrive/Documentos/GitHub/Trabajo-de-titulo/prototipos-desechables/proto_03_reconocimiento_mano_dedo.py) | Segmentación de mano y dedo índice | OpenCV YCrCb HandSkin | Cámara 2 (Gestos) | Chequea apertura de Cámara 1 |
| [`proto_04_rastreo_ocular_socket.py`](file:///c:/Users/nicol/OneDrive/Documentos/GitHub/Trabajo-de-titulo/prototipos-desechables/proto_04_rastreo_ocular_socket.py) | Lectura de mirada *gaze point* | Sockets TCP / WebSocket | EyeTracker (EyeTribe / GazeCloud) | Chequea sockets en puertos 3000 / 6555 |
| [`proto_05_reconocimiento_voz_whisper.py`](file:///c:/Users/nicol/OneDrive/Documentos/GitHub/Trabajo-de-titulo/prototipos-desechables/proto_05_reconocimiento_voz_whisper.py) | Comandos de voz (Audio a Texto) | **Whisper STT** / SpeechRec | Micrófono Físico de Entrada | Chequea dispositivos de entrada de audio |
| [`proto_06_definiciones_ollama_llm.py`](file:///c:/Users/nicol/OneDrive/Documentos/GitHub/Trabajo-de-titulo/prototipos-desechables/proto_06_definiciones_ollama_llm.py) | Definición y resumen conceptual | **Ollama Local LLM** | Servidor Ollama `localhost:11434` | Consulta endpoint `/api/tags` |
| [`proto_07_destacado_pdf_pymupdf.py`](file:///c:/Users/nicol/OneDrive/Documentos/GitHub/Trabajo-de-titulo/prototipos-desechables/proto_07_destacado_pdf_pymupdf.py) | Resaltado amarillo en PDF | PyMuPDF QuadPoints | Archivo PDF objetivo | Chequea acceso a archivo PDF |
| [`proto_08_comentarios_postit_pymupdf.py`](file:///c:/Users/nicol/OneDrive/Documentos/GitHub/Trabajo-de-titulo/prototipos-desechables/proto_08_comentarios_postit_pymupdf.py) | Notas adhesivas Post-It en PDF | PyMuPDF Text Annotations | Archivo PDF objetivo | Chequea acceso a archivo PDF |
| [`proto_09_busqueda_video_youtube.py`](file:///c:/Users/nicol/OneDrive/Documentos/GitHub/Trabajo-de-titulo/prototipos-desechables/proto_09_busqueda_video_youtube.py) | Enlaces de video explicativo YouTube | REST Query + Regex (Error E34) | Conexión de Red / Internet | Chequea disponibilidad de red |

---

## 🚀 Cómo Ejecutar

```powershell
# Activar entorno virtual
.\eddie-python-venv\Scripts\Activate.ps1

# Ejecutar el diagnosticador y orquestador global de hardware y funciones:
python -X utf8 prototipos-desechables\evaluador_hardware_factibilidad.py
```
