# Guía Completa de Avance — Trabajo de Título EDDIE Python

---

## SECCIÓN 1 — Metodología Ibaceta: Cómo diagnosticar los 67 errores

### ¿Necesitas volver a ejecutar el proyecto C# para evaluar los errores?

**No necesariamente.** Ibaceta ya documentó los 67 errores con su metodología MECIVA PS. Tienes dos opciones:

| Opción | Cuándo usarla | Ventaja |
|--------|--------------|---------|
| **A) Usar el PDF de Ibaceta directamente** | Tu trabajo es la migración Python, no re-diagnosticar | Ahorras tiempo, la tabla ya existe |
| **B) Re-ejecutar el proyecto y re-evaluar** | Si quieres demostrar que identificas cuáles errores resuelves tú | Mayor rigor, pero requiere el hardware del lab |

> [!IMPORTANT]
> **Recomendación:** Usa la Opción A. Tu trabajo de título es la **solución** (migración a Python), no el diagnóstico (que ya hizo Ibaceta). Lo que SÍ debes hacer es construir una **matriz de trazabilidad** que vincule cada error de Ibaceta con el estado en tu nuevo sistema Python.

---

### Metodología MECIVA PS que usó Ibaceta (paso a paso)

Ibaceta **NO usó SonarQube ni herramientas automáticas**. Usó MECIVA PS con proceso manual:

**Paso 1 — Despliegue del sistema**
```
Acción: Instalar EDDIE-2023 en el computador del laboratorio
Acción: Registrar TODOS los errores que aparecen durante la instalación
Acción: Documentar qué dependencias faltan (DLLs, .NET version, etc.)
Registra: E1 al E20 aproximadamente
```

**Paso 2 — Reparación iterativa**
```
Acción: Para cada error de instalación, buscar solución
Acción: Documentar la solución aplicada
Acción: Clasificar: ¿Se resolvió totalmente (SF), parcialmente (SP), o sin solución (SS)?
```

**Paso 3 — Diagnóstico funcional (6 pasos MECIVA PS)**
```
3.1: Descomponer cada funcionalidad del sistema en sub-funciones
3.2: Identificar qué datos de entrada/salida necesita cada función
3.3: Definir qué tipos de resultados se esperan
3.4: Seleccionar método de verificación (pruebas no estadísticas, 10 iteraciones)
3.5: Ejecutar las pruebas de aceptación por funcionalidad
3.6: Obtener aprobación del jefe de proyecto (profesor guía)
```

**Paso 4 — Clasificar errores**
```
Categorías de Ibaceta:
  - Externo: problemas de hardware, red, laboratorio
  - Interno-consistencia: módulo de sincronización físico-digital
  - Interno-búsqueda: módulo de búsqueda web (APIs)
  - Interno-rastreoOcular: módulo eye tracking
  - Interno-interacción F/D: interacción física-digital
  - Interno-interfaz usuario: UI/UX
  - Interno-otro: setup, paths hardcodeados, dependencias

Estados:
  SS (0) = Sin Solución
  SP (1) = Solución Parcial
  SF (2) = Solución Final
```

---

### Tabla completa de los 67 errores de Ibaceta

> [!NOTE]
> Esta tabla fue extraída directamente de la Tabla A.1 de la tesis de Ibaceta Jaña, I. A. (2023).

| ID | Categoría | Descripción | Estado |
|----|-----------|-------------|--------|
| E1 | Externo | Internet del laboratorio inestable | SP |
| E2 | Externo | Problemas compatibilidad GitKraken y permisos | SF |
| E3 | Interno-otro | No se pudo encontrar el dll leapC | SF |
| E4 | Externo | No se identifica la rama correcta del repositorio | SP |
| E5 | Interno-otro | Programa no inicializa por referencias VS erróneas | SF |
| E6 | Interno-otro | Programa no inicializa por falta de dll Serilog | SF |
| E7 | Interno-otro | Programa no inicializa sin cámara disponible | SF |
| E8 | Interno-otro | Mal funcionamiento sin 2 cámaras disponibles | SF |
| E9 | Externo | Falta de conexiones eléctricas en laboratorio | SP |
| E10 | Externo | Falta de seguridad en computador del laboratorio | SF |
| E11 | Interno-consistencia | Sincronización falla si no se ingresa PDF | SF |
| E12 | Externo | No existe manual de instalación para EDDIE | **SS** |
| E13 | Externo | No existe manual de uso para EDDIE | **SS** |
| E14 | Interno-otro | Mensajes de error en idioma distinto | SF |
| E15 | Externo | No se reconoce el eyetracker en el computador | SF |
| E16 | Externo | Conexión de cámara digital es inestable | SP |
| E17 | Interno-otro | No se encuentra paquete Netstantdart.library | SF |
| E18 | Interno-otro | No se encuentra .NET Framework v4.8 | SF |
| E19 | Interno-otro | No se procesan recursos por marca de zona restringida | SF |
| E20 | Interno-otro | Interfaz no tiene tamaño correcto con proyector | SF |
| E21 | Interno-consistencia | Botón de búsqueda falla si no hay PDF | SF |
| E22 | Interno-consistencia | Función revisar PDF falla si no hay PDF | SF |
| E23 | Interno-rastreoOcular | App falla al reabrir vista de rastreo ocular | SF |
| E24 | Interno-interacción F/D | No se reconoce el texto del documento físico | SF |
| E25 | Interno-búsqueda | Diccionario no busca palabras reconocidas | SP |
| E26 | Interno-búsqueda | Enciclopedia no muestra resultados | SP |
| E27 | Interno-otro | Faltan comentarios en el código | **SS** |
| E28 | Interno-otro | Variables y funciones sin nombres representativos | **SS** |
| E29 | Interno-consistencia | No se reconoce contenido del PDF ingresado | **SS** |
| E30 | Interno-consistencia | Función PDF falla si no se indica página | SF |
| E31 | Interno-interacción F/D | Cámara enfoca botones de interfaz al reconocer texto | SF |
| E32 | Interno-interacción F/D | OCR deja de funcionar tras uso prolongado | SF |
| E33 | Interno-búsqueda | No detecta cambio de selección de API de enciclopedia | SF |
| E34 | Interno-búsqueda | Símbolo '(' hace fallar la API de Wikipedia | **SS** |
| E35 | Interno-interacción F/D | OCR no reconoce correctamente en cada intento | SP |
| E36 | Interno-búsqueda | Sin internet, Wikipedia hace fallar el programa | SF |
| E37 | Interno-búsqueda | No se reconoce la API de traducción (Bing) | SP |
| E38 | Interno-consistencia | No se encuentra consistencyLibraryFiguresDP.dll | SF |
| E39 | Interno-búsqueda | Voz no accede a búsqueda de diccionario | SF |
| E40 | Interno-consistencia | Destacado físico→digital en posición/largo incorrectos | **SS** |
| E41 | Interno-consistencia | Destacado digital→físico en posición/largo incorrectos | **SS** |
| E42 | Interno-consistencia | Comentarios fallan si no se especifica página | SF |
| E43 | Interno-consistencia | Figuras fallan si no se especifica página | SF |
| E44 | Interno-consistencia | Marcapáginas fallan si no se especifica página | SF |
| E45 | Interno-consistencia | Contenido falla aun ingresando elementos correctos | SF |
| E46 | Interno-consistencia | Figuras fallan aun ingresando elementos correctos | SF |
| E47 | Interno-consistencia | Marcapáginas fallan aun ingresando correctamente | SF |
| E48 | Interno-consistencia | Comentarios fallan aun ingresando correctamente | SF |
| E49 | Externo | Eye Tribe no detecta parte inferior de la proyección | **SS** |
| E50 | Interno-consistencia | No se encuentra la carpeta Plugins-Consistencia | SF |
| E51 | Interno-rastreoOcular | No se encuentran plugins de rastreo ocular | SF |
| E52 | Interno-consistencia | Ruta hardcodeada al computador del desarrollador original | SP |
| E53 | Interno-interfaz | Botón 'save settings' no representa su funcionalidad | SF |
| E54 | Interno-consistencia | Variable auxcapture=null hace fallar Figuras | SF |
| E55 | Interno-consistencia | Variable auxcapture=null hace fallar Marcapáginas | SF |
| E56 | Interno-consistencia | Variable auxcapture=null hace fallar Comentarios | SF |
| E57 | Interno-consistencia | Ruta local de Dennise en marcapáginas físico→digital | SF |
| E58 | Interno-consistencia | Ruta local de Dennise en figuras físico→digital | SF |
| E59 | Interno-consistencia | Ruta local de Dennise en comentarios físico→digital | SF |
| E60 | Interno-consistencia | Ruta local de Dennise en FiguresDP | SF |
| E61 | Interno-consistencia | Enciclopedia falla si la palabra no se encuentra | SP |
| E62 | Interno-consistencia | Enciclopedia falla si palabra no es exacta en Wikipedia | SP |
| E63 | Interno-búsqueda | 'Búsqueda de figuras' no puede ejecutarse | SP |
| E64 | Interno-rastreoOcular | variable controller=null en controlar mouse | SF |
| E65 | Interno-rastreoOcular | variable logging=null en controlar mouse | SF |
| E66 | Interno-rastreoOcular | variable controller=null en guardar registro ocular | SF |
| E67 | Interno-rastreoOcular | variable logging=null en guardar registro ocular | SF |

**Resumen:** SF=46 (68.7%), SP=17 (25.4%), SS=4 (5.9%)

---

### Cómo usar esta tabla en tu tesis

Debes construir una **Matriz de Trazabilidad** en tu Capítulo 7:

| ID Error | Descripción resumida | Estado Ibaceta | Estado en tu Python |
|----------|---------------------|----------------|---------------------|
| E3 | dll leapC no encontrado | SF (resuelto) | N/A — Leap Motion fuera de alcance MVP |
| E38 | consistencyLibraryFiguresDP.dll faltante | SF | **RESUELTO** — PyMuPDF no usa DLLs |
| E50 | Carpeta Plugins-Consistencia no encontrada | SF | **RESUELTO** — importlib unificado |
| E51 | Plugins rastreo ocular no encontrados | SF | **RESUELTO** — MockEyeTracker + IEyeTracker |
| E52 | Rutas hardcodeadas | SP | **RESUELTO** — config/plugins.json centraliza |
| E40 | Consistencia F→D posición incorrecta | SS | En progreso — IConsistencyProvider |
| E12 | Sin manual de instalación | SS | **RESUELTO** — README.md generado |
| ... | ... | ... | ... |

---

## SECCIÓN 2 — Validar Emgu.CV → OpenCV: Paso a paso + Código

### Paso 1: Verificar la instalación de OpenCV
```powershell
# En PowerShell, desde la raíz del proyecto:
.\eddie-python-venv\Scripts\python.exe -c "import cv2; print('OpenCV:', cv2.__version__)"
```
**Resultado esperado:** `OpenCV: 5.0.0`

### Paso 2: Instalar Tesseract OCR en Windows
```
1. Descargar instalador oficial:
   https://github.com/UB-Mannheim/tesseract/wiki
   → Buscar: "tesseract-ocr-w64-setup-5.x.x.exe"

2. Durante la instalación, marcar:
   [x] Additional language data (download)
   [x] Spanish (spa)

3. La ruta de instalación será:
   C:\Program Files\Tesseract-OCR\tesseract.exe

4. Verificar en PowerShell:
   & "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```

### Paso 3: Ejecutar el Prototipo RAD #1 (sin cámara)
```powershell
# Desde la raíz del proyecto (Trabajo-de-titulo/):
.\eddie-python-venv\Scripts\python.exe -X utf8 eddie-python\prototypes\proto_01_opencv_ocr.py

# Con una imagen tuya:
.\eddie-python-venv\Scripts\python.exe -X utf8 eddie-python\prototypes\proto_01_opencv_ocr.py --image "ruta\a\tu\imagen.jpg"

# Con cámara en tiempo real:
.\eddie-python-venv\Scripts\python.exe -X utf8 eddie-python\prototypes\proto_01_opencv_ocr.py --camera
```

### Paso 4: Interpretar los resultados
El prototipo mostrará:
```
[4.1] Conversión a escala de grises: X.XXX ms
[4.2] Binarización (Otsu): X.XXX ms
[4.3] Reducción de ruido: X.XXX ms
[4.4] OCR (Tesseract): X.XXX ms
TOTAL PIPELINE: X.XXX ms

Precisión: XX.X%
Recall:    XX.X%
F1-Score:  XX.X%
```

### Equivalencias validadas para tu tesis

| C# Legacy (Emgu.CV) | Python (OpenCV) | Archivo |
|---------------------|-----------------|---------|
| `new VideoCapture(0)` | `cv2.VideoCapture(0)` | proto_01 |
| `CvtColor(BGR2GRAY)` | `cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)` | proto_01 |
| `Threshold(binary)` | `cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)` | proto_01 |
| `TesseractEngine.Process()` | `pytesseract.image_to_string()` | proto_01 |
| `PdfReader(path)` | `fitz.open(path)` | proto_02 |
| `PdfTextExtractor.GetText()` | `page.get_text()` | proto_02 |
| `PdfAnnotation.CreateMarkup()` | `page.add_highlight_annot()` | proto_02 |

---

## SECCIÓN 3 — Entorno Python: Resumen de lo realizado

### Estado actual del entorno (al ejecutar estas instrucciones)

```
c:\...\Trabajo-de-titulo\
├── eddie-python-venv\          ← Entorno virtual Python 3.14
│   └── Scripts\                ← python.exe, pip.exe, pytest.exe
├── eddie-python\               ← Proyecto nuevo (migración)
│   ├── contracts\              ← Interfaces (PluginBase, IImageProcessor, etc.)
│   ├── orchestrator\           ← OrchestratorCore + PluginLoader
│   ├── hardware\mock\          ← MockEyeTracker
│   ├── plugins\                ← (a implementar en siguientes etapas)
│   ├── config\plugins.json     ← Configuración de plugins
│   ├── tests\                  ← Test suite pytest
│   ├── prototypes\             ← Prototipos RAD ejecutados y validados
│   ├── requirements.txt
│   └── main.py
└── EDDIE-2023\                 ← Código C# legacy (referencia)
```

### Paquetes instalados en el venv
```
opencv-python  5.0.0.93  ← Reemplaza Emgu.CV
pytesseract    0.3.13    ← Interfaz Python para Tesseract OCR
pymupdf        1.28.2    ← Reemplaza iTextSharp
pytest         9.1.1     ← Framework de testing
pytest-cov     7.1.0     ← Medición de cobertura
numpy          2.5.2     ← Álgebra matricial
pillow         12.3.0    ← Procesamiento de imágenes auxiliar
```

### Comandos clave para usar el entorno

```powershell
# Activar el entorno virtual (necesario antes de ejecutar Python)
.\eddie-python-venv\Scripts\Activate.ps1

# Ejecutar prototipo PyMuPDF (VALIDADO: funciona)
python -X utf8 eddie-python\prototypes\proto_02_pymupdf.py

# Ejecutar prototipo Orquestador (VALIDADO: 3.71ms promedio)
python -X utf8 eddie-python\prototypes\proto_03_orchestrator.py

# Ejecutar tests con cobertura
cd eddie-python
..\eddie-python-venv\Scripts\pytest tests\ -v --cov=orchestrator --cov=contracts --cov-report=term-missing

# Ejecutar el sistema principal
python -X utf8 eddie-python\main.py --cycles 10
```

---

## SECCIÓN 4 — Etapa A completada: Resultados RAD

### Proto #1 — OpenCV + OCR
- **Estado:** ✅ OpenCV 5.0.0 instalado y funcionando
- **Pendiente:** Instalar Tesseract OCR para validar el OCR completo
- **Resultado parcial:** Pipeline de preprocesamiento funciona; OCR requiere Tesseract

### Proto #2 — PyMuPDF (iTextSharp → PyMuPDF) ✅ VALIDADO
```
Apertura PDF:           7.44 ms
Extracción de texto:    7.51 ms
Guardado con highlight: 3.59 ms
Lectura anotaciones:    7.16 ms
Conclusión: FACTIBLE — PyMuPDF reemplaza completamente iTextSharp
```

### Proto #3 — OrchestratorCore ✅ VALIDADO
```
Latencia promedio (10 ciclos, 3 plugins): 3.71 ms ≤ 8.3 ms ✓
Latencia máxima:                          4.03 ms ≤ 8.3 ms ✓
Aislamiento de fallos:                    CONFIRMADO
Carga dinámica importlib:                 CONFIRMADO
Ciclo de vida completo:                   CONFIRMADO
```

### Pendientes de la Etapa A
- [ ] Instalar Tesseract y ejecutar proto_01 con OCR completo
- [ ] proto_04: Validar MockEyeTracker (ejecutar hardware/mock/mock_eye_tracker.py)

---

## SECCIÓN 5 — Análisis del Cap. 2 (Taller de Investigación) y cómo continuar la tesis

### Lo que tiene tu Capítulo 2 (9 páginas — "Análisis de la Solución y Estado del Arte")

#### Estructura actual:
```
2.1 Estado del Arte
  2.1.1 Antecedentes del Proyecto EDDIE (Evolución histórica)
    2.1.1.1 Catálogo de funcionalidades y usabilidad previa
  2.1.2 Deuda Técnica y Reproducibilidad en Software Científico
  2.1.3 Lectura Aumentada y Coordinación Multimodal
  2.1.4 Arquitecturas Modulares y Patrones de Integración
  2.1.5 Metodologías de Evaluación de Software Científico
Referencias (34 fuentes)
```

#### ✅ Lo que está BIEN:
- Hilo conductor claro y lógico
- Deuda técnica bien fundamentada con literatura 2024-2025
- Justificación histórica de EDDIE sólida (6 memorias de título)
- Referencias a metodología MECIVA PS y SonarQube
- 34 referencias bibliográficas

#### ⚠️ Lo que FALTA (brechas identificadas):

| Sección faltante | Por qué es necesaria | Páginas estimadas |
|-----------------|---------------------|-------------------|
| Eye Tracking (métricas, hardware) | Tu sistema usa GazePoint/TheEyeTribe | 1.5 páginas |
| OCR (Tesseract, EasyOCR, DL-based) | Tu IImageProcessor usa OCR | 1.5 páginas |
| Reconocimiento gestual (OpenCV, MediaPipe) | Tu IGesturePlugin lo implementa | 1 página |
| Plugins en Python (importlib, pluggy) | Justifica tu elección técnica | 1 página |
| PyMuPDF vs iTextSharp (PDFs) | Justifica la migración técnica | 0.5 páginas |
| Diagramas (monolito C# vs Python plugins) | Apoyo visual ausente | 0.5 páginas |
| Corregir cita de Megargel et al. (2021) | Referencia incompleta señalada | inmediato |

---

### Plan paso a paso para completar y continuar la tesis

#### PASO T.A — Corregir el Capítulo 2 existente (Semana actual)

**T.A.1 — Agregar sección 2.1.6: Eye Tracking**
```
Contenido a redactar:
  - Principio de funcionamiento de rastreadores oculares
    (reflexión corneal, Purkinje images)
  - Tipos de dispositivos: infrarrojo remoto (GazePoint, TheEyeTribe),
    infrarrojo ocluido (Tobii), webcam-based (GazeCloudAPI)
  - Métricas atencionales:
    → Fijaciones (fixations): duración mínima ~100-200ms, indica procesamiento
    → Sacadas (saccades): movimientos rápidos entre fijaciones
    → Áreas de Interés (AOI): regiones del texto analizadas
  - Aplicaciones en investigación de lectura y cognición
  - Extensión objetivo: ~1.5 páginas

Fuentes a buscar en IEEE Xplore:
  - "eye tracking reading comprehension" → filtrar 2018-2025
  - "fixation saccade reading" → buscar papers fundacionales
  - Citar manual/paper de GazePoint: https://www.gazept.com/
```

**T.A.2 — Agregar sección 2.1.7: OCR y Procesamiento de Imágenes**
```
Contenido a redactar:
  - Tesseract OCR: historia, arquitectura LSTM, rendimiento
  - EasyOCR: alternativa basada en deep learning
  - Técnicas de preprocesamiento con OpenCV:
    → Escala de grises, binarización, umbralización (Otsu)
    → Reducción de ruido (GaussianBlur, medianBlur)
    → Dilatación/erosión para mejorar texto
  - Métricas de evaluación: WER (Word Error Rate), CER, Precisión/Recall
  - Extensión objetivo: ~1.5 páginas

Fuentes a buscar:
  - Paper original de Tesseract: Smith, R. (2007). IEEE ICDAR
  - "OCR preprocessing techniques" → IEEE Xplore
  - Documentación oficial Tesseract (citar como referencia técnica)
```

**T.A.3 — Agregar sección 2.1.8: Reconocimiento Gestual**
```
Contenido a redactar:
  - Detección de mano con visión computacional:
    → Segmentación por color (YCrCb — lo que usaba EDDIE C#)
    → Detección de contornos y defectos de convexidad
    → Deep learning: MediaPipe Hands (Google)
  - Comparativa: color-based vs ML-based
  - Métricas: tasa de reconocimiento, latencia de detección
  - Extensión objetivo: ~1 página

Fuentes:
  - Paper de MediaPipe Hands: Zhang et al. (2020) — Google Research
  - "hand gesture recognition OpenCV" → IEEE Xplore
```

**T.A.4 — Ampliar sección 2.1.4 con implementación Python de plugins**
```
Agregar subsección: "2.1.4.1 Implementación de Plugins en Ecosistemas Python"
  - importlib.import_module(): mecanismo nativo de Python
  - Patrón de entry points (setuptools)
  - Comparativa: Assembly.LoadFrom() (C#) vs importlib (Python)
    → Mostrar que 3 mecanismos distintos → 1 mecanismo unificado
  - Citar: documentación oficial de Python sobre importlib
```

**T.A.5 — Agregar diagrama de arquitectura**
```
Crear en draw.io o similar:
  Figura A: Arquitectura monolítica legacy (EDDIE C# / WinForms)
  Figura B: Arquitectura propuesta (OrchestratorCore + Plugins Python)

Insertar antes de la sección 2.1.4 o 2.1.5
```

**T.A.6 — Corregir referencia de Megargel et al. (2021)**
```
Buscar la referencia completa en Google Scholar:
  Autores: Megargel, Shankararaman, Walker (Singapur Management University)
  Título aproximado: algo relacionado con arquitecturas de software modulares
  Completar con: volumen, páginas, editorial, DOI
```

---

#### PASO T.B — Crear el Capítulo 3 (si no existe aún) o verificar la propuesta

**Verifica con tu profesor guía si tu documento de "Propuesta" (informe de seminario) YA sirve como Capítulo 1, o si necesita ser adaptado al formato de tesis.**

Si tu estructura es:
```
Capítulo 1 = Informe de Seminario (Propuesta) ← ya tienes esto
Capítulo 2 = Taller de Investigación (Estado del Arte) ← tienes esto (con brechas)
Capítulo 3 = ??? (Metodología o Análisis y Diseño)
```

Entonces el **próximo capítulo a escribir es el Capítulo 3: Metodología**, que incluye:

```
3.1 Metodología de desarrollo: PDCA + RAD + Kanban
    - Descripción de las 4 fases del PDCA
    - Cómo se usó RAD (throwaway prototyping): DOCUMENTAR los 3 prototipos
      que ya ejecutaste y sus resultados
    - Tablero Kanban: captura de pantalla de tu GitHub Projects

3.2 Entorno de desarrollo
    - Hardware disponible (PC, GPU NVIDIA RTX 5060, cámaras, GazePoint)
    - Software: Python 3.14, VS Code, Git, pytest
    - SO: Windows 11

3.3 Metodología de evaluación
    3.3.1 Software Testing (pytest): cobertura ≥ 80%
    3.3.2 Verificación y Validación (MECIVA PS)
    3.3.3 Pruebas de aceptación en laboratorio InTeractiOn

3.4 Criterios de éxito
    - Latencia ≤ 8.3 ms
    - Cobertura ≥ 80%
    - 0 errores de la categoría de Ibaceta sin resolver en el módulo equivalente
    - Reducción de codebase a ~10.000 líneas
```

---

#### PASO T.C — Escribir en paralelo con el código (desde ya)

**Regla de oro:** Cada vez que ejecutes un prototipo o implementes algo, escríbelo inmediatamente en el capítulo correspondiente.

```
Hoy ejecutaste proto_02 (PyMuPDF) → Escribe en Cap. 6:
  "La validación del prototipo throwaway de PyMuPDF demostró que la
  apertura de un PDF tarda 7.44 ms, la extracción de texto 7.51 ms,
  y la adición de un highlight 3.59 ms, confirmando la factibilidad
  de migrar de iTextSharp a PyMuPDF."

Hoy ejecutaste proto_03 (Orquestador) → Escribe en Cap. 6:
  "El prototipo del orquestador demostró latencias promedio de 3.71 ms
  por ciclo con 3 plugins activos, cumpliendo el requisito de ≤ 8.3 ms.
  Se confirmó el aislamiento de fallos: un plugin que lanzó RuntimeError
  en cada uno de los 10 ciclos no detuvo la ejecución de los demás plugins."
```

---

### Orden recomendado para continuar el informe

```
Semana actual:
  1. Corregir Cap. 2 (agregar secciones 2.1.6, 2.1.7, 2.1.8)
  2. Agregar diagramas de arquitectura
  3. Buscar y guardar en Zotero las referencias faltantes

Semanas 2-3:
  4. Escribir Cap. 3: Metodología (usando los resultados de los prototipos)
  5. Comenzar Cap. 5: Análisis y Diseño (contratos de interfaz ya definidos)

Semanas 4-8 (en paralelo con código):
  6. Escribir Cap. 6: Implementación (documenta cada módulo al implementarlo)

Semanas 9-12:
  7. Ejecutar pruebas formales → Cap. 7: Evaluación y Resultados

Semanas 13-14:
  8. Cap. 8: Conclusiones y trabajo futuro
  9. Revisión final completa
```

---

> [!TIP]
> **Usa Overleaf para LaTeX** (mencionado en tu informe de seminario). Si aún no tienes el proyecto creado, hazlo esta semana. La plantilla de tesis de tu institución debería estar disponible en el sitio web de la escuela o la secretaría académica.

> [!WARNING]
> **Endogamia bibliográfica:** El análisis del Cap. 2 muestra que cita casi exclusivamente tesis del propio laboratorio InTeractiOn. Incorpora papers internacionales de IEEE Xplore y ACM DL en las secciones técnicas nuevas (eye tracking, OCR, gestual).
