# Plan Integral de Trabajo de Título — EDDIE
## Actualización del Núcleo Tecnológico: Migración de C# a Python

---

> [!IMPORTANT]
> El informe de seminario propone una **migración completa del núcleo tecnológico de C# (.NET) a Python**, adoptando una arquitectura de plugins desacoplados con un `OrchestratorCore` central. Esto es el corazón del trabajo de título.

---

## 📌 CONTEXTO DEL PROYECTO

**EDDIE** (*Empowering Digital Paper with Interactive Enhancements*) es una plataforma científica para estudiar lectura aumentada en papel físico. El sistema actual (C#/WinForms, `EDDIE-2023`) acumuló **67 errores documentados**, de los cuales **16 son errores arquitectónicos críticos** causados por 3 mecanismos de carga heterogéneos vía reflexión en C# (`Assembly.LoadFrom`, `AppDomain`, `Assembly.LoadFile`).

### Lo que propone el informe de seminario:
| Aspecto | C# Legacy (EDDIE-2023) | Python Nuevo (Trabajo de Título) |
|---------|----------------------|--------------------------------|
| Lenguaje | C# / .NET Framework | Python |
| Arquitectura | Monolito WinForms acoplado | Orquestador + Plugins desacoplados |
| Carga de plugins | 3 mecanismos de reflexión distintos | 1 único `PluginLoader` unificado |
| Visión computacional | Emgu.CV (binding C#) | OpenCV (nativo Python) |
| Procesamiento PDF | iTextSharp | PyMuPDF |
| Testing | Sin framework formal | pytest (cobertura ≥ 80%) |![alt text](image.png)
| Líneas de código | ~45.000 | ~8.000-10.000 (reducción del 80%) |

### Módulos a implementar (contratos de interfaz):
- `OrchestratorCore` — ciclo de vida de plugins (init, execute, release)
- `PluginLoader` — instancia plugins declarados en config
- `PluginBase` — contrato base común para todos los plugins
- `DeviceFactory` — abstracción de hardware (real vs simulado)
- `IImageProcessor` — reconocimiento de texto/OCR
- `IEyeTracker` — rastreo ocular (GazePoint, TheEyeTribe)
- `IGesturePlugin` — interacción gestual
- `IWebSearchProvider` — búsqueda web (solo interfaz en el MVP)
- `IConsistencyProvider` — consistencia bidireccional físico-digital

---

## 🗺️ PARTE 1 — PLAN GENERAL DE AVANCE (Paso a Paso)

### FASE 0 — Preparación y Diagnóstico *(Semana 1-2)*

**Paso 1.1 — Auditoría del código C# legacy (EDDIE-2023)**
- Revisar los **67 errores documentados** en el código C# existente
- Clasificar errores según la categoría descrita en el seminario (arquitectónicos vs funcionales)
- Verificar cuáles de los 16 errores críticos de reflexión son los más bloqueantes
- Crear una **matriz de trazabilidad de errores** (error → módulo afectado → prioridad)
- Documentar en `diagnostico_legacy.md`: qué funciona, qué falla, qué se migra

**Paso 1.2 — Validar prototipo de factibilidad (Throwaway Prototyping)**
- Confirmar que la migración de Emgu.CV → OpenCV es técnicamente factible
- Crear prototype mínimo en Python que:
  - Capture un frame de cámara con OpenCV
  - Aplique OCR con pytesseract o easyOCR
  - Detecte un gaze point simulado
- Documentar resultados del prototype en el informe (Objetivo Específico 1)

**Paso 1.3 — Configurar entorno de desarrollo Python**
- Instalar Python 3.11+ y crear entorno virtual (`venv` o `conda`)
- Instalar dependencias base: `opencv-python`, `pymupdf`, `pytest`, `numpy`
- Configurar Visual Studio Code con extensiones Python
- Inicializar nuevo repositorio Git con estructura de proyecto limpia

**Paso 1.4 — Hablar con el profesor guía**
- Confirmar el alcance exacto del Objetivo Específico 3 (qué módulos integrar en el MVP)
- Aclarar qué hardware físico estará disponible (GazePoint, TheEyeTribe, cámaras)
- Confirmar qué tests de aceptación se harán en el laboratorio InTeractiOn
- Acordar frecuencia de revisiones y fechas de entrega intermedias

---

### FASE 1 — Diseño de Arquitectura *(Semana 3-4)*

**Paso 2.1 — Diseñar el OrchestratorCore**
- Definir exactamente qué métodos tiene: `initialize()`, `execute_cycle()`, `release()`
- Definir cómo maneja errores de plugins sin crashear el sistema completo
- Definir el protocolo de comunicación: llamadas directas a métodos (no IPC/WebSocket en el MVP)
- Documentar en diagrama de secuencia y clases

**Paso 2.2 — Definir los contratos de interfaz (PluginBase y todos los IXxx)**
- Escribir la clase abstracta `PluginBase` con todos sus métodos obligatorios
- Escribir cada interfaz: `IImageProcessor`, `IEyeTracker`, `IGesturePlugin`, `IConsistencyProvider`, `IWebSearchProvider`
- Para cada interfaz: definir firma de métodos, tipos de retorno, y condiciones de error
- Esto es el **entregable del Objetivo Específico 2**

**Paso 2.3 — Diseñar el DeviceFactory (Hardware Abstraction Layer)**
- Definir la lista de dispositivos soportados: GazePoint, TheEyeTribe, cámaras
- Definir clases Mock para cada dispositivo (para desarrollo y testing sin hardware)
- Definir el mecanismo de selección real vs mock (flag de configuración)

**Paso 2.4 — Diseñar el PluginLoader**
- Definir formato de archivo de configuración (JSON o YAML)
- Definir cómo se declaran plugins en el config (nombre de clase, parámetros)
- Definir cómo el Loader instancia y registra cada plugin

---

### FASE 2 — Implementación Central *(Semana 5-10)*

**Paso 3.1 — Implementar OrchestratorCore y PluginLoader** *(Semana 5-6)*
- Código del orquestador con ciclo de vida completo
- PluginLoader con instanciación dinámica
- PluginBase clase abstracta
- Suite de tests unitarios para el orquestador (pytest)
- Lograr cobertura ≥ 80% en estos componentes

**Paso 3.2 — Implementar DeviceFactory y mocks** *(Semana 6)*
- Clases mock para: cámara, eye tracker, datos de gesto
- Generador de coordenadas simuladas para el eye tracker
- Inyección de dependencias vía DeviceFactory

**Paso 3.3 — Implementar IImageProcessor (OCR / Reconocimiento de texto)** *(Semana 7)*
- Captura de frame con OpenCV
- Preprocesamiento: conversión a escala de grises, binarización, filtros
- OCR con pytesseract o easyOCR
- Validar con precisión/recall en mínimo 10 palabras de prueba
- Tests: precisión ≥ umbral definido en el informe

**Paso 3.4 — Implementar IEyeTracker** *(Semana 8)*
- Driver para GazePoint (protocolo GazeAPI sobre TCP)
- Driver para TheEyeTribe (API REST o SDK)
- Mock que genera coordenadas simuladas con coeficiente de variación medible
- Validar latencia interna ≤ 8.3 ms (para dispositivo 60Hz)

**Paso 3.5 — Implementar IGesturePlugin** *(Semana 9)*
- Captura de video con OpenCV
- Detección de gestos básicos (ej: señalar, scroll gestual)
- Mock de gesto para testing
- Calcular tasa de error gestual

**Paso 3.6 — Implementar IConsistencyProvider** *(Semana 10)*
- Consistencia bidireccional físico-digital usando PyMuPDF
- Sincronización de anotaciones (highlight en PDF digital ↔ marca en papel)
- Detección de página actual mediante visión computacional
- Gestión de historial de anotaciones

---

### FASE 3 — Pruebas y Validación *(Semana 11-15)*

**Paso 4.1 — Software Testing (pytest)** *(Semana 11-12)*
- Ejecutar suite completa de tests
- Verificar cobertura ≥ 80%
- Corregir bugs encontrados
- Re-evaluar los 67 errores del legacy usando la matriz de trazabilidad
- Documentar qué errores se resolvieron y cuáles quedaron fuera de alcance

**Paso 4.2 — Verificación y Validación (MECIVA PS)** *(Semana 13)*
- Clasificar requerimientos en: críticos (100% sin bloqueos) vs secundarios
- Ejecutar mínimo 10 ejecuciones para variables continuas (coeficiente de variación)
- Documentar resultados en el informe de verificación y validación

**Paso 4.3 — Pruebas de aceptación en laboratorio InTeractiOn** *(Semana 14)*
- Llevar el sistema al laboratorio con hardware real
- Probar operación simultánea de todos los módulos integrados
- Probar recuperación ante falla parcial de sensores
- Documentar resultados

**Paso 4.4 — Análisis de resultados y correcciones** *(Semana 15)*
- Analizar los datos de todas las pruebas
- Priorizar correcciones críticas
- Implementar correcciones
- Re-ejecutar pruebas afectadas

---

### FASE 4 — Cierre y Entrega *(Semana 16-17)*

**Paso 5.1 — Documentación técnica del sistema**
- Docstrings completos en todo el código Python
- README.md con instrucciones de instalación, configuración y uso
- CHANGELOG.md con todos los cambios implementados
- Diagrama final de arquitectura actualizado

**Paso 5.2 — Empaquetar entregables**
- Repositorio Git limpio y ordenado (rama main taggeada)
- Reporte de software testing (pytest HTML report)
- Reporte de verificación y validación
- Artefactos de arquitectura (diagramas)

**Paso 5.3 — Redacción final del informe y defensa**
- Completar todos los capítulos pendientes
- Revisión completa del informe con el profesor guía
- Preparar presentación de defensa (20-30 slides)
- Ensayar defensa

---

## 💻 PARTE 2 — PLAN DE AVANCE DEL CÓDIGO (Paso a Paso)

### ETAPA A — Diagnóstico del legacy C# *(Días 1-7)*

**A.1 — Catalogar los 67 errores del código EDDIE-2023**
```
Objetivo: Tener claridad exacta de qué está roto en el legacy
Herramienta: SonarQube o análisis manual
Acción: Ejecutar análisis estático del código C#
Acción: Crear tabla: ID_Error | Módulo | Descripción | Tipo (arquitectónico/funcional) | Prioridad
Acción: Marcar los 16 errores críticos de reflexión (Assembly.LoadFrom, AppDomain, etc.)
Entregable: diagnostico_legacy.md con la tabla completa
```

**A.2 — Entender cada módulo C# a migrar**
```
Para cada módulo del EDDIE-2023 que será portado a Python:
  - ModuloProcesamientoImagenes → IImageProcessor (Python/OpenCV)
  - ModuloRastreoOcular → IEyeTracker (Python/SDK)
  - ModuloReconocimientoGestual → IGesturePlugin (Python/OpenCV)
  - ModuloConsistenciaDatos → IConsistencyProvider (Python/PyMuPDF)
  - ModuloBusquedaWeb → IWebSearchProvider (solo interfaz en MVP)

Acción: Para cada módulo C#, leer y documentar:
  - Qué clases existen y qué hacen
  - Qué parámetros de entrada y salida tienen sus métodos clave
  - Qué dependencias externas usan (SDK, DLL, API)
  - Equivalente Python que se usará
```

**A.3 — Crear el prototipo de factibilidad (Throwaway Prototype)**
```
Objetivo: Validar que OpenCV en Python puede reemplazar Emgu.CV
Crear archivo: prototype_factibilidad.py
Implementar:
  1. cap = cv2.VideoCapture(0)  → captura de cámara
  2. ret, frame = cap.read()    → leer frame
  3. gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) → escala de grises
  4. text = pytesseract.image_to_string(gray) → OCR básico
  5. Mostrar resultado en pantalla

Documentar: tiempo de ejecución, calidad del OCR, conclusión de factibilidad
Este resultado va directo al Capítulo de Implementación del informe
```

---

### ETAPA B — Diseño y estructura del proyecto Python *(Días 8-15)*

**B.1 — Estructura de directorios del proyecto**
```
eddie-python/
├── orchestrator/
│   ├── __init__.py
│   ├── orchestrator_core.py        ← OrchestratorCore
│   └── plugin_loader.py            ← PluginLoader
├── contracts/
│   ├── __init__.py
│   ├── plugin_base.py              ← PluginBase (clase abstracta)
│   ├── i_image_processor.py        ← IImageProcessor
│   ├── i_eye_tracker.py            ← IEyeTracker
│   ├── i_gesture_plugin.py         ← IGesturePlugin
│   ├── i_consistency_provider.py   ← IConsistencyProvider
│   └── i_web_search_provider.py    ← IWebSearchProvider (solo interfaz)
├── hardware/
│   ├── __init__.py
│   ├── device_factory.py           ← DeviceFactory
│   ├── real/                       ← Drivers hardware real
│   │   ├── gazepoint_driver.py
│   │   ├── eyetribe_driver.py
│   │   └── camera_driver.py
│   └── mock/                       ← Mocks para testing
│       ├── mock_eye_tracker.py
│       ├── mock_gesture.py
│       └── mock_camera.py
├── plugins/
│   ├── __init__.py
│   ├── image_processor_plugin.py   ← Implementa IImageProcessor
│   ├── eye_tracker_plugin.py       ← Implementa IEyeTracker
│   ├── gesture_plugin.py           ← Implementa IGesturePlugin
│   └── consistency_plugin.py       ← Implementa IConsistencyProvider
├── config/
│   └── plugins.json                ← Declaración de plugins activos
├── tests/
│   ├── test_orchestrator.py
│   ├── test_image_processor.py
│   ├── test_eye_tracker.py
│   ├── test_gesture_plugin.py
│   └── test_consistency.py
├── requirements.txt
├── README.md
└── main.py                         ← Punto de entrada
```

**B.2 — Definir PluginBase con todos los métodos requeridos**
```python
# contracts/plugin_base.py
from abc import ABC, abstractmethod

class PluginBase(ABC):
    @abstractmethod
    def initialize(self, config: dict) -> bool:
        """Inicializa el plugin con su configuración"""
        pass
    
    @abstractmethod  
    def execute(self) -> dict:
        """Ejecuta un ciclo del plugin, retorna datos"""
        pass
    
    @abstractmethod
    def release(self) -> None:
        """Libera recursos del plugin"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre único del plugin"""
        pass
```

**B.3 — Diseñar el archivo de configuración de plugins**
```json
// config/plugins.json
{
  "plugins": [
    {
      "name": "ImageProcessor",
      "class": "plugins.image_processor_plugin.ImageProcessorPlugin",
      "enabled": true,
      "config": {
        "camera_index": 0,
        "ocr_language": "spa",
        "use_mock": false
      }
    },
    {
      "name": "EyeTracker", 
      "class": "plugins.eye_tracker_plugin.EyeTrackerPlugin",
      "enabled": true,
      "config": {
        "device": "gazepoint",
        "use_mock": true
      }
    }
  ]
}
```

---

### ETAPA C — Implementación del OrchestratorCore *(Días 16-22)*

**C.1 — Implementar OrchestratorCore**
```
Métodos a implementar:
  initialize():
    - Leer config/plugins.json
    - Instanciar PluginLoader
    - Para cada plugin en config: cargar y llamar initialize()
    - Si un plugin falla su initialize(), loguear error y continuar (no crashear)
    
  execute_cycle():
    - Para cada plugin cargado: llamar execute()
    - Medir tiempo de ejecución de cada plugin
    - Si latencia > 8.3ms: loguear advertencia
    - Si plugin lanza excepción: capturar, loguear, continuar
    
  release():
    - Para cada plugin: llamar release() en orden inverso
    - Liberar recursos del sistema

Logging:
    - Cada evento tiene timestamp
    - Niveles: DEBUG, INFO, WARNING, ERROR
    - Guardar a archivo y mostrar en consola
```

**C.2 — Implementar PluginLoader**
```
Métodos a implementar:
  load_plugin(class_path: str, config: dict) -> PluginBase:
    - Separar module_path y class_name del class_path
    - Importar módulo dinámicamente: importlib.import_module()
    - Obtener clase: getattr(module, class_name)
    - Verificar que hereda de PluginBase
    - Instanciar y retornar

  load_all(config_path: str) -> List[PluginBase]:
    - Leer JSON de configuración
    - Para cada plugin enabled=true: llamar load_plugin()
    - Retornar lista de plugins instanciados
```

**C.3 — Tests del orquestador**
```
tests/test_orchestrator.py debe cubrir:
  - test_initialize_with_valid_config()
  - test_initialize_with_missing_plugin_class()  ← no debe crashear
  - test_execute_cycle_measures_latency()
  - test_execute_cycle_plugin_exception_isolation() ← un plugin falla, otros siguen
  - test_release_calls_all_plugins()
  - test_plugin_loader_valid_class()
  - test_plugin_loader_invalid_class()
  
Meta: cobertura ≥ 80% con pytest-cov
Comando: pytest tests/test_orchestrator.py -v --cov=orchestrator
```

---

### ETAPA D — Implementación de plugins *(Días 23-55)*

**D.1 — Plugin IImageProcessor (OCR)**
```
Archivo: plugins/image_processor_plugin.py
Dependencias: opencv-python, pytesseract (o easyocr)

execute() debe:
  1. Capturar frame de cámara (cv2.VideoCapture)
  2. Convertir a escala de grises
  3. Aplicar preprocesamiento (threshold, denoising)
  4. Extraer texto con OCR
  5. Filtrar stopwords del idioma
  6. Retornar: {"detected_words": [...], "raw_text": "...", "confidence": 0.85}

Métricas a medir:
  - Precisión y recall en dataset de 10 palabras de prueba
  - Tiempo de procesamiento por frame

Tests:
  - test_ocr_with_mock_image()
  - test_ocr_precision_minimum_10_words()
  - test_preprocessing_improves_accuracy()
```

**D.2 — Plugin IEyeTracker**
```
Archivo: plugins/eye_tracker_plugin.py
Dependencias: GazePoint SDK o TheEyeTribe SDK

Para GazePoint (protocolo TCP):
  - Conectar a socket TCP (IP:4242)
  - Enviar comando de calibración
  - Leer coordenadas de gaze en tiempo real
  - Calcular fijaciones (fixation detection)

Mock (mock/mock_eye_tracker.py):
  - Generar coordenadas aleatorias con distribución normal
  - Simular fijaciones de 200-500ms
  - Permitir configurar coeficiente de variación

Métricas:
  - Latencia de respuesta ≤ 8.3ms (para 60Hz)
  - Coeficiente de variación en ≥ 10 ejecuciones

Tests:
  - test_mock_eye_tracker_generates_coordinates()
  - test_eye_tracker_latency_within_bounds()
  - test_fixation_detection()
```

**D.3 — Plugin IGesturePlugin**
```
Archivo: plugins/gesture_plugin.py
Dependencias: opencv-python, mediapipe (opcional)

Gestos a implementar (según informe):
  - Señalar / apuntar con el dedo
  - Gesto de scroll (mano arriba/abajo)
  - Gesto de confirmación (pulgar arriba o similar)

execute() debe:
  1. Capturar frame de cámara
  2. Detectar mano con contornos (cv2.findContours) o MediaPipe
  3. Clasificar gesto detectado
  4. Retornar: {"gesture": "scroll_up", "confidence": 0.9, "position": (x, y)}

Métrica: tasa de error gestual (gestos incorrectos / total intentos)

Tests:
  - test_gesture_detection_with_mock_frame()
  - test_gesture_error_rate_within_bounds()
```

**D.4 — Plugin IConsistencyProvider**
```
Archivo: plugins/consistency_plugin.py
Dependencias: pymupdf (fitz)

Funcionalidades:
  1. Abrir PDF digital con PyMuPDF
  2. Detectar página actual del libro físico (OCR de número de página)
  3. Navegar al PDF digital en esa página
  4. Sincronizar subrayados:
     - Subrayado en físico → detectar con cámara → agregar highlight en PDF digital
     - Anotación en PDF digital → mostrar en overlay sobre cámara
  5. Guardar anotaciones en PDF (fitz.Annot)

Tests:
  - test_open_pdf()
  - test_add_highlight_annotation()
  - test_page_synchronization()
  - test_annotation_persistence()
```

---

### ETAPA E — Pruebas formales *(Días 56-70)*

**E.1 — Ejecutar suite completa de tests**
```
Comando: pytest tests/ -v --cov=. --cov-report=html
Objetivo: cobertura ≥ 80%
Si hay tests fallando: corregir el código (no los tests)

Reportes a generar:
  - pytest-html: reporte visual de tests
  - pytest-cov: reporte de cobertura
  - Guardar en /reports/testing/
```

**E.2 — Métricas de validación del informe (MECIVA PS)**
```
Para cada requerimiento crítico:
  - Ejecutar mínimo 10 veces el escenario
  - Registrar resultado en cada ejecución
  - Calcular coeficiente de variación para variables continuas
  - Verificar tasa de éxito = 100% sin bloqueos para críticos
  
Variables a medir:
  - Latencia del orquestador: media ± desv.std
  - Precisión OCR: media ± desv.std sobre 10 palabras
  - Coordenadas de gaze: coeficiente de variación
  - Tasa de error gestual: %
```

**E.3 — Prueba de aceptación en laboratorio**
```
Preparar:
  - Laptop/PC con sistema instalado y configurado
  - Hardware: GazePoint o TheEyeTribe conectado
  - Cámara para reconocimiento gestual y OCR
  - Documento físico de prueba (libro o texto impreso)
  - PDF digital correspondiente al documento físico

Ejecutar en laboratorio InTeractiOn:
  - Prueba 1: Todos los módulos corriendo simultáneamente por 5 minutos
  - Prueba 2: Desconectar eye tracker → sistema continúa sin crashear
  - Prueba 3: Señalar texto en libro físico → búsqueda web (si IWebSearchProvider tiene mock)
  - Registrar: logs del sistema, tiempos, errores, comportamiento
```

---

### ETAPA F — Cierre del código *(Días 71-80)*

**F.1 — Limpieza y documentación final**
```
Acción: Agregar docstrings a todas las clases y métodos públicos
  Formato: Google Style Docstrings
  """
  Breve descripción.
  
  Args:
      param1 (tipo): descripción
  
  Returns:
      tipo: descripción
  
  Raises:
      ExceptionType: cuándo se lanza
  """

Acción: Revisar que no haya código comentado sin uso
Acción: Verificar que todos los tests pasan
Acción: Actualizar README.md con:
  - Requisitos de sistema (OS, Python version, hardware)
  - Instrucciones de instalación paso a paso
  - Instrucciones de configuración (plugins.json)
  - Instrucciones de uso
  - Cómo ejecutar los tests
```

**F.2 — Commit y tag final**
```
git add .
git commit -m "feat: implementación completa del núcleo orquestador EDDIE Python"
git tag -a v1.0.0 -m "Versión final Trabajo de Título"
git push origin main --tags
```

---

## 📝 PARTE 3 — PLAN DE AVANCE DEL INFORME DE TESIS (Paso a Paso)

> [!TIP]
> Escribe el informe EN PARALELO con el código. Cada vez que implementas algo, documéntalo inmediatamente en el capítulo correspondiente.

### Estructura completa de la tesis:
```
Portada y datos formales
Resumen (Español)
Abstract (Inglés)
Tabla de contenidos / Figuras / Tablas / Abreviaciones
1. Introducción
2. Marco Teórico
3. Estado del Arte
4. Metodología
5. Análisis y Diseño del Sistema
6. Implementación
7. Evaluación y Resultados
8. Conclusiones y Trabajo Futuro
Referencias Bibliográficas
Anexos
```

---

### PASO T.1 — Configurar el documento *(Semana 1)*
```
Herramienta recomendada: Overleaf (LaTeX online, mencionado en el informe)
  - Crear proyecto en overleaf.com
  - Usar plantilla de tesis de tu institución o IEEE tesis template
  - Crear un archivo .tex por capítulo

Alternativa: Word con plantilla institucional
  - Configurar estilos: Título1, Título2, Normal, Código
  - Configurar numeración automática de páginas, figuras y tablas

Acción: Configurar gestor de referencias: Zotero (gratuito)
  - Instalar extensión Zotero para Overleaf o Word
  - Crear colección "Tesis EDDIE"
  - Empezar a agregar fuentes desde hoy
```

---

### PASO T.2 — Capítulo 1: Introducción *(Semana 1-2)*
```
1.1 Contexto y motivación
    - ¿Por qué el estudio de la lectura en papel sigue siendo relevante?
    - Importancia de las plataformas experimentales para investigación en HII
    - Problema de deuda técnica en software científico
    - (Citar: literatura sobre augmented reading y HCI)

1.2 Descripción del problema
    - EDDIE acumuló 67 errores documentados
    - Los 16 errores arquitectónicos críticos de reflexión en C#
    - Impacto: sistema inestable e inadecuado para mediciones científicas rigurosas
    - (Incluir aquí fragmento relevante del diagnóstico)

1.3 Objetivos
    1.3.1 Objetivo General:
          Actualizar el núcleo tecnológico de EDDIE mediante rediseño
          y reimplementación en Python, integrando módulos existentes
          para reducir la deuda técnica y asegurar compatibilidad
          con sensores físicos en un entorno de lectura aumentada no intrusivo.
    
    1.3.2 Objetivos Específicos:
          OE1: Diagnosticar la arquitectura C# legacy y evaluar
               factibilidad de migración mediante prototipos throwaway en Python.
          OE2: Diseñar el núcleo orquestador y definir contratos de
               interfaz para plugins desacoplados.
          OE3: Implementar el orquestador Python, la capa de abstracción
               de hardware, e integrar los módulos de consistencia,
               reconocimiento de texto, interacción gestual y rastreo ocular.
          OE4: Validar el sistema integrado mediante software testing,
               verificación funcional y pruebas de aceptación en laboratorio.

1.4 Hipótesis
    - La arquitectura propuesta (orquestador Python + plugins desacoplados)
      reducirá los errores críticos de 16 a 0 y reducirá el codebase de
      ~45.000 a ~10.000 líneas manteniendo funcionalidad equivalente.

1.5 Alcance
    - Incluye: orquestador, 4 plugins funcionales, HAL, suite de tests
    - Excluye: web dashboard, browser viewer, CLI de validación,
               WebSocket telemetry, validación multiplataforma Linux/macOS,
               implementación completa de IWebSearchProvider

1.6 Organización del documento
    - Breve descripción de cada capítulo (1 párrafo c/u)
```

---

### PASO T.3 — Capítulo 2: Marco Teórico *(Semana 2-4)*
```
2.1 Lectura Aumentada (Augmented Reading)
    - Definición y evolución del concepto
    - Diferencia con AR general
    - Plataformas experimentales para investigación HII
    - Citar: papers fundacionales del área

2.2 Seguimiento Ocular (Eye Tracking)
    - Principio de funcionamiento (corneal reflection, Purkinje images)
    - Dispositivos: GazePoint, TheEyeTribe
    - Métricas: fijaciones, sacadas, áreas de interés (AOI)
    - Aplicaciones en investigación de lectura

2.3 Reconocimiento Óptico de Caracteres (OCR)
    - Tesseract vs EasyOCR (comparar)
    - Preprocesamiento con OpenCV
    - Métricas: precisión, recall, CER, WER

2.4 Reconocimiento Gestual por Visión Computacional
    - Técnicas: contornos de mano, deep learning (MediaPipe)
    - Métricas: tasa de reconocimiento, tasa de error

2.5 Arquitecturas de Software Basadas en Plugins
    - Patrón Plugin/Extension Point
    - Inversion of Control (IoC) e Inyección de Dependencias
    - Comparar: reflexión C# (legacy) vs importlib Python (propuesto)

2.6 Deuda Técnica en Software Científico
    - Definición y taxonomía de deuda técnica
    - Impacto en reproducibilidad científica
    - Métricas de SonarQube

2.7 Testing en Software Científico
    - pytest: fixtures, cobertura, parametrización
    - MECIVA PS: metodología de verificación y validación
    - Hardware mocking y simulación de sensores

2.8 PyMuPDF (Fitz) para procesamiento de PDFs
    - Alternativa a iTextSharp
    - Anotaciones, highlights, extracción de texto

Nota: Para cada sección, buscar mínimo 3 referencias en IEEE Xplore, ACM, o Scholar
```

---

### PASO T.4 — Capítulo 3: Estado del Arte *(Semana 3-5)*
```
3.1 Sistemas de lectura aumentada
    - Buscar 5-8 sistemas similares publicados (últimos 7 años)
    - Para cada uno: autores, año, tecnologías, fortalezas, limitaciones

3.2 Plataformas de software científico para HCI
    - Sistemas experimentales para estudios de lectura y cognición
    - Software como PsychoPy, GazeParser, etc.

3.3 Arquitecturas de orquestación de plugins
    - Comparar enfoques: microservicios, IPC, llamadas directas en memoria
    - Justificar por qué se elige llamadas directas en memoria para EDDIE

3.4 Tabla comparativa
    | Sistema | Tecnología | Eye Tracking | Gestual | Consistencia | Limitaciones |
    |---------|-----------|-------------|---------|-------------|-------------|
    | EDDIE C# | C#/WinForms | Sí | Sí | Sí | 67 errores, monolito |
    | Sistema A | ... | ... | ... | ... | ... |
    | EDDIE Python | Python | Sí | Sí | Sí | Solo Windows 11 |

3.5 Brechas identificadas
    - Ningún sistema existente combina: eye tracking + OCR + gestual + consistencia
      físico-digital en una plataforma experimental de código abierto
    - La deuda técnica de EDDIE impide su uso para investigación rigurosa
    - Esta brecha justifica el trabajo de título
```

---

### PASO T.5 — Capítulo 4: Metodología *(Semana 4-5)*
```
4.1 Metodología de desarrollo: PDCA + RAD + Kanban
    - Describir el ciclo PDCA de 17 semanas
    - Describir el rol de RAD (Rapid Application Development):
      uso de throwaway prototyping para validar factibilidad OpenCV
    - Describir el tablero Kanban para gestión de tareas

4.2 Entorno de desarrollo
    - Hardware: procesador, GPU (NVIDIA RTX 5060), RAM
    - Software: Python 3.11+, VSCode, Git, pytest, SonarQube
    - Hardware de sensores: GazePoint, TheEyeTribe, cámaras digitales
    - SO: Windows 11

4.3 Metodología de evaluación
    4.3.1 Software Testing (pytest)
          - Cobertura de código (mínimo 80%)
          - Tipos de tests: unitarios, integración
          - Proceso de CI con pytest
    4.3.2 Verificación y Validación (MECIVA PS)
          - Clasificación: requerimientos críticos vs secundarios
          - Protocolo: mínimo 10 ejecuciones por variable continua
          - Métricas: coeficiente de variación, tasa de éxito
    4.3.3 Pruebas de aceptación en laboratorio
          - Contexto: laboratorio InTeractiOn
          - Escenarios: operación simultánea, fallo parcial de sensores

4.4 Criterios de éxito
    - Latencia ≤ 8.3ms por ciclo de orquestador
    - Cobertura de tests ≥ 80%
    - 0 errores arquitectónicos críticos (de los 16 originales)
    - Requerimientos críticos: 100% sin bloqueos
    - Reducción del codebase a 8.000-10.000 líneas
```

---

### PASO T.6 — Capítulo 5: Análisis y Diseño *(Semana 5-8, en paralelo con código)*
```
5.1 Requerimientos del sistema
    RF-01: El orquestador debe gestionar el ciclo de vida de todos los plugins
    RF-02: El sistema debe detectar texto en documentos físicos mediante OCR
    RF-03: El sistema debe registrar fijaciones del rastreo ocular
    RF-04: El sistema debe detectar gestos básicos del usuario
    RF-05: El sistema debe sincronizar anotaciones entre doc físico y digital
    RF-06: Un plugin que falle no debe crashear el sistema completo
    RF-07: La interfaz IWebSearchProvider debe estar definida (sin implementación)
    
    RNF-01: Latencia interna ≤ 8.3ms para dispositivos 60Hz
    RNF-02: Cobertura de tests ≥ 80%
    RNF-03: Reducir codebase de ~45.000 a ~10.000 líneas
    RNF-04: Compatible con Windows 11
    RNF-05: Los plugins se activan/desactivan vía archivo de configuración

5.2 Arquitectura del sistema
    - Diagrama de arquitectura: OrchestratorCore ↔ PluginLoader ↔ [Plugins]
    - DeviceFactory inyecta implementaciones real o mock
    - Diagrama de paquetes Python
    - Descripción de cada componente

5.3 Diseño de contratos de interfaz
    - Código de PluginBase (abstracto)
    - Código de cada IXxx con su firma completa
    - Justificación de las decisiones de diseño

5.4 Diseño de pruebas
    - Estrategia de testing (qué se testea en unitario vs integración)
    - Diseño de mocks para hardware
    - Plan de cobertura

5.5 Diagramas UML
    - Diagrama de clases completo
    - Diagrama de secuencia: ciclo de ejecución del orquestador
    - Diagrama de secuencia: carga de plugins al inicio
    - Diagrama de estados: ciclo de vida de un plugin
```

---

### PASO T.7 — Capítulo 6: Implementación *(Semana 8-14, en paralelo con código)*
```
6.1 Entorno de implementación
    - Versiones exactas: Python 3.x.x, opencv-python x.x, pymupdf x.x, etc.
    - requirements.txt comentado
    - Configuración de pytest y pytest-cov

6.2 OrchestratorCore y PluginLoader
    - Describir implementación
    - Mostrar fragmento de código del ciclo de ejecución
    - Describir el manejo de excepciones por plugin
    - Mostrar fragmento del cargador dinámico con importlib

6.3 DeviceFactory y sistema de mocks
    - Describir la inyección de dependencias
    - Mostrar cómo se selecciona real vs mock
    - Describir generación de datos simulados

6.4 Plugin IImageProcessor
    - Pipeline de procesamiento: captura → preprocesamiento → OCR → filtrado
    - Decisiones técnicas: ¿Tesseract o EasyOCR? ¿Por qué?
    - Captura de pantalla del OCR funcionando

6.5 Plugin IEyeTracker
    - Protocolo de comunicación con GazePoint o TheEyeTribe
    - Implementación del mock con distribución estadística

6.6 Plugin IGesturePlugin
    - Algoritmo de detección de gestos elegido (contornos o MediaPipe)
    - Justificación de la elección

6.7 Plugin IConsistencyProvider
    - Flujo de sincronización físico-digital
    - Uso de PyMuPDF para anotaciones

6.8 Dificultades técnicas y cómo se resolvieron
    - Problemas reales encontrados durante el desarrollo
    - Esto demuestra el trabajo real del estudiante

6.9 Decisiones de diseño importantes
    - Por qué llamadas directas en vez de IPC/WebSocket
    - Por qué Python y no C# moderno (ej: .NET 8)
    - Compromisos (trade-offs) tomados conscientemente
```

---

### PASO T.8 — Capítulo 7: Evaluación y Resultados *(Semana 14-16)*
```
7.1 Software Testing
    - Tabla de resultados de tests: Módulo | Tests | Pasados | Cobertura
    - Reporte de cobertura por módulo (gráfico de barras)
    - Matriz de trazabilidad: Error legacy → Estado actual (resuelto/pendiente)

7.2 Verificación y Validación (MECIVA PS)
    - Tabla de requerimientos críticos: RF | Intentos | Éxitos | Resultado
    - Tabla de variables continuas: Variable | Media | Desv.Std | CV
    - Gráficos de distribución de latencia

7.3 Pruebas de aceptación en laboratorio
    - Descripción del ambiente de prueba (fotos del laboratorio si es posible)
    - Resultados por escenario de prueba
    - Comportamiento ante fallos parciales de sensores

7.4 Análisis comparativo: C# legacy vs Python nuevo
    - Tabla: Métrica | EDDIE C# | EDDIE Python
    - Errores críticos: 16 vs 0
    - Líneas de código: ~45.000 vs ~X.000
    - Cobertura de tests: desconocida vs ≥80%
    - Latencia: no medida vs ≤8.3ms

7.5 Discusión
    - ¿Se cumplió el objetivo general?
    - OE1: ¿Se diagnóstico y validó factibilidad? → evidencia
    - OE2: ¿Se diseñaron los contratos? → evidencia
    - OE3: ¿Se implementó el orquestador e integración? → evidencia
    - OE4: ¿Se validó el sistema? → evidencia
    - Limitaciones del experimento (hardware disponible, tamaño de muestra)
```

---

### PASO T.9 — Capítulo 8: Conclusiones y Trabajo Futuro *(Semana 16-17)*
```
8.1 Conclusiones
    - Recapitular: el problema era la deuda técnica de EDDIE C#
    - La solución fue migrar a Python con arquitectura de plugins
    - Resultados obtenidos vs objetivos planteados
    - Impacto para la comunidad de investigación HII

8.2 Contribuciones
    - Núcleo orquestador reusable y extensible para investigación en HII
    - Contratos de interfaz bien definidos para 5 tipos de módulos
    - Suite de tests con ≥80% de cobertura
    - Reducción de ~35.000 líneas de código legacy

8.3 Limitaciones
    - Solo compatible con Windows 11 actualmente
    - IWebSearchProvider no implementado (APIs vencidas)
    - No se validó en Linux/macOS
    - Número limitado de gestos reconocidos

8.4 Trabajo Futuro
    - Implementar IWebSearchProvider con APIs actuales
    - Validar en Linux/macOS
    - Desarrollar web dashboard y CLI de validación
    - Integrar WebSocket para telemetría en tiempo real
    - Agregar reconocimiento de libro físico automático
    - Portear reconocimiento gestual a deep learning (YOLO, MediaPipe avanzado)
```

---

### PASO T.10 — Referencias *(Continuo desde el inicio)*
```
Gestor: Zotero con plugin para Overleaf (Zotero Better BibTeX)
Formato: IEEE (recomendado para ingeniería informática)

Fuentes clave a buscar:
  - IEEE Xplore: buscar "augmented reading", "eye tracking reading comprehension",
                 "plugin architecture scientific software", "OCR text recognition"
  - ACM DL: buscar "augmented paper", "gaze-based interaction", "technical debt"
  - Google Scholar: para acceso a PDFs de papers no-IEEE

Meta: mínimo 35-40 referencias en total
  - Marco Teórico: ~20 referencias
  - Estado del Arte: ~10 referencias (sistemas comparados)
  - Resto del documento: ~10 referencias adicionales
```

---

## 🗓️ CRONOGRAMA DE 17 SEMANAS

| Semana | Código (Python) | Informe (Tesis) |
|--------|----------------|-----------------|
| **1** | Diagnóstico C# legacy (67 errores) | Cap.1 Introducción, configurar Overleaf/Zotero |
| **2** | Prototipo throwaway (OpenCV factibilidad) | Cap.2 Marco Teórico inicio (2.1, 2.2) |
| **3** | Estructura de proyecto Python, PluginBase | Cap.2 Marco Teórico (2.3, 2.4, 2.5) |
| **4** | PluginLoader + config JSON | Cap.2 Marco Teórico (2.6, 2.7, 2.8) + Cap.3 inicio |
| **5** | OrchestratorCore (initialize, execute, release) | Cap.3 Estado del Arte completo |
| **6** | DeviceFactory + mocks | Cap.4 Metodología + Cap.5 inicio |
| **7** | Plugin IImageProcessor (OCR) | Cap.5 Análisis y Diseño (requisitos, arquitectura) |
| **8** | Plugin IEyeTracker | Cap.5 Análisis y Diseño (UML, contratos) |
| **9** | Plugin IGesturePlugin | Cap.6 Implementación (OrchestratorCore, PluginLoader) |
| **10** | Plugin IConsistencyProvider | Cap.6 Implementación (DeviceFactory, mocks) |
| **11** | Tests unitarios (pytest, cobertura ≥80%) | Cap.6 Implementación (plugins) |
| **12** | Tests de integración + corrección bugs | Cap.6 Implementación (dificultades, decisiones) |
| **13** | Verificación y Validación (MECIVA PS) | Cap.7 Evaluación inicio (resultados testing) |
| **14** | Pruebas de aceptación en laboratorio InTeractiOn | Cap.7 Evaluación (pruebas laboratorio) |
| **15** | Correcciones post-validación | Cap.7 Evaluación (análisis, comparativa, discusión) |
| **16** | Documentación final del código, tag v1.0.0 | Cap.8 Conclusiones + Referencias final |
| **17** | Build final, entregables | Revisión final completa + correcciones + entrega |

---

## ⚡ ACCIONES INMEDIATAS (Esta semana)

1. ✅ **Auditar los 67 errores** del código C# legacy → crear tabla de clasificación
2. ✅ **Instalar Python 3.11+** y las dependencias base (`pip install opencv-python pytesseract pymupdf pytest`)
3. ✅ **Crear el prototipo throwaway** (capture de cámara + OCR básico en Python)
4. ✅ **Crear proyecto en Overleaf** con la estructura de capítulos vacía
5. ✅ **Instalar Zotero** y empezar a guardar papers del marco teórico
6. ✅ **Hablar con el profesor guía** → confirmar alcance exacto y fechas
7. ✅ **Crear repositorio Git nuevo** `eddie-python` con la estructura de directorios propuesta
8. ✅ **Crear tablero Kanban** (GitHub Projects) con todas las tareas identificadas

---

> [!WARNING]
> **Punto crítico:** El informe de seminario menciona que `IWebSearchProvider` queda como **solo interfaz** en el MVP debido a APIs vencidas. Esto debe quedar documentado claramente en el alcance del trabajo de título para que no sea una observación de los evaluadores.

> [!CAUTION]
> **No desarrolles la UI todavía.** El informe de seminario indica que la web dashboard, browser viewer y CLI de validación quedan **fuera del alcance** del MVP. Enfócate primero en el núcleo orquestador y los 4 plugins.
