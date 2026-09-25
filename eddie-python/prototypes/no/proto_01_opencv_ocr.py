"""
prototypes/proto_01_opencv_ocr.py
=====================================
PROTOTIPO RAD #1: Factibilidad de migración Emgu.CV → OpenCV + OCR
====================================================================

PROPÓSITO (Objetivo Específico 1 del Seminario):
  Validar que OpenCV en Python puede reemplazar Emgu.CV (binding C#),
  específicamente para captura de cámara y preprocesamiento de imágenes
  para OCR (Optical Character Recognition).

METODOLOGÍA: Throwaway Prototyping (RAD)
  - Este prototipo NO es código de producción.
  - Se ejecuta una sola vez para demostrar factibilidad.
  - Sus resultados se documentan en el informe de tesis (Capítulo 4 y 6).
  - El código de producción real está en plugins/image_processor_plugin.py

EQUIVALENCIA CON C# LEGACY:
  C# (Emgu.CV)                    → Python (OpenCV)
  VideoCapture cap = new...        → cv2.VideoCapture(0)
  Mat frame = new Mat()            → ret, frame = cap.read()
  CvtColor(BGR2GRAY)              → cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  Threshold(...)                   → cv2.threshold(...)
  TesseractEngine.Process(bitmap)  → pytesseract.image_to_string(img)

REQUISITOS PREVIOS:
  1. Tesseract OCR instalado en el sistema:
     Windows: https://github.com/UB-Mannheim/tesseract/wiki
     → Instalar y agregar a PATH, o usar RUTA DE ABAJO
  2. Datos de idioma español: descargar 'spa.traineddata'
     → Colocar en la carpeta tessdata de Tesseract

CÓMO EJECUTAR:
  Desde la carpeta raíz del proyecto eddie-python:
  
  Con cámara física:
    .\\..\\eddie-python-venv\\Scripts\\python.exe prototypes/proto_01_opencv_ocr.py --camera
  
  Sin cámara (solo imagen de prueba):
    .\\..\\eddie-python-venv\\Scripts\\python.exe prototypes/proto_01_opencv_ocr.py
  
  Con una imagen específica:
    .\\..\\eddie-python-venv\\Scripts\\python.exe prototypes/proto_01_opencv_ocr.py --image ruta/imagen.jpg
"""

import sys
import time
import argparse
import os

# ─────────────────────────────────────────────────────────────────
# PASO 1: Verificar OpenCV (reemplaza Emgu.CV)
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PROTOTIPO RAD #1: Factibilidad OpenCV + OCR")
print("=" * 60)

print("\n[PASO 1] Verificando instalación de OpenCV...")
try:
    import cv2
    import numpy as np
    print(f"  ✓ OpenCV instalado correctamente: versión {cv2.__version__}")
    print(f"  ✓ NumPy instalado: versión {np.__version__}")
except ImportError as e:
    print(f"  ✗ ERROR: OpenCV no instalado. Ejecuta: pip install opencv-python")
    print(f"    Detalle: {e}")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────
# PASO 2: Verificar Tesseract OCR
# ─────────────────────────────────────────────────────────────────
print("\n[PASO 2] Verificando Tesseract OCR...")
try:
    import pytesseract
    
    # En Windows, Tesseract suele instalarse en esta ruta:
    TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSERACT_PATH_ALT = r'C:\Users\nicol\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
    
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        print(f"  ✓ Tesseract encontrado en: {TESSERACT_PATH}")
    elif os.path.exists(TESSERACT_PATH_ALT):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH_ALT
        print(f"  ✓ Tesseract encontrado en: {TESSERACT_PATH_ALT}")
    else:
        print(f"  ⚠ Tesseract no encontrado en rutas comunes.")
        print(f"    Si ya instalaste Tesseract, el OCR fallará pero el")
        print(f"    resto del prototipo (OpenCV) se puede validar igual.")
    
    # Verificar versión
    try:
        version = pytesseract.get_tesseract_version()
        print(f"  ✓ Versión de Tesseract: {version}")
        TESSERACT_OK = True
    except Exception as e:
        print(f"  ⚠ Tesseract instalado pero no accesible: {e}")
        print(f"    → El test de OCR será omitido, pero OpenCV se validará igual.")
        TESSERACT_OK = False
        
except ImportError:
    print(f"  ✗ pytesseract no instalado. Ejecuta: pip install pytesseract")
    TESSERACT_OK = False

# ─────────────────────────────────────────────────────────────────
# PASO 3: Crear imagen de prueba (si no hay cámara)
# ─────────────────────────────────────────────────────────────────
def create_test_image_with_text() -> 'np.ndarray':
    """
    Crea una imagen de prueba con texto para validar el pipeline OCR.
    Esto permite testear sin cámara ni imagen externa.
    """
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    
    # Crear imagen blanca 640x480
    img_pil = Image.new('RGB', (640, 480), color=(255, 255, 255))
    draw = ImageDraw.Draw(img_pil)
    
    # Texto de prueba (palabras que el OCR debe detectar)
    test_text = (
        "PROTOTIPO RAD EDDIE Python\n\n"
        "Lectura aumentada\n"
        "Eye tracking\n"
        "Reconocimiento gestual\n"
        "Consistencia bidireccional\n"
        "OpenCV reemplaza Emgu.CV\n"
        "PyMuPDF reemplaza iTextSharp\n"
        "Python reemplaza C# legacy\n"
        "Arquitectura de plugins\n"
        "Orquestador centralizado"
    )
    
    # Usar fuente por defecto (sin necesidad de instalar fuentes externas)
    draw.text((50, 50), test_text, fill=(0, 0, 0))
    
    # Convertir de PIL a numpy array (formato OpenCV BGR)
    img_np = np.array(img_pil)
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    return img_bgr


# ─────────────────────────────────────────────────────────────────
# PASO 4: Pipeline de procesamiento OpenCV
# (equivale a ColorRecognition.cs + OCRProcess.cs en C# legacy)
# ─────────────────────────────────────────────────────────────────
def process_frame_pipeline(frame: 'np.ndarray') -> dict:
    """
    Pipeline completo de procesamiento de imagen para OCR.
    
    Equivalencias con el C# legacy:
    - Mat gray = CvInvoke.CvtColor(frame, BGR2GRAY)
      → gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    - CvInvoke.Threshold(gray, binary, 127, 255, ThresholdType.Binary)
      → _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    - TesseractEngine.Process(bitmap)
      → pytesseract.image_to_string(binary)
    
    Args:
        frame: numpy.ndarray BGR (formato nativo de OpenCV)
    
    Returns:
        dict con todas las métricas del procesamiento
    """
    results = {}
    
    # ── Paso 4.1: Convertir a escala de grises ──────────────────
    t0 = time.perf_counter()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_time_ms = (time.perf_counter() - t0) * 1000
    results['gray_time_ms'] = round(gray_time_ms, 3)
    print(f"\n  [4.1] Conversión a escala de grises: {gray_time_ms:.3f} ms")
    print(f"        Dimensiones: {frame.shape} → {gray.shape}")
    
    # ── Paso 4.2: Umbralización (binarización) ───────────────────
    t0 = time.perf_counter()
    # THRESH_BINARY + THRESH_OTSU: calcula el umbral automáticamente
    # (mejor que umbral fijo de 127 del C# legacy)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    binary_time_ms = (time.perf_counter() - t0) * 1000
    results['binary_time_ms'] = round(binary_time_ms, 3)
    print(f"  [4.2] Binarización (Otsu): {binary_time_ms:.3f} ms")
    
    # ── Paso 4.3: Reducción de ruido ─────────────────────────────
    t0 = time.perf_counter()
    denoised = cv2.GaussianBlur(binary, (3, 3), 0)
    denoise_time_ms = (time.perf_counter() - t0) * 1000
    results['denoise_time_ms'] = round(denoise_time_ms, 3)
    print(f"  [4.3] Reducción de ruido: {denoise_time_ms:.3f} ms")
    
    # ── Paso 4.4: OCR con Tesseract ──────────────────────────────
    if TESSERACT_OK:
        t0 = time.perf_counter()
        try:
            # Configuración: --oem 3 (LSTM), --psm 3 (auto detección)
            custom_config = r'--oem 3 --psm 3'
            raw_text = pytesseract.image_to_string(denoised, lang='spa', config=custom_config)
            ocr_time_ms = (time.perf_counter() - t0) * 1000
            
            # Limpiar el texto detectado
            detected_words = [
                w.strip().lower() 
                for w in raw_text.replace('\n', ' ').split() 
                if len(w.strip()) > 2  # filtrar palabras muy cortas
            ]
            
            results['ocr_time_ms'] = round(ocr_time_ms, 3)
            results['raw_text'] = raw_text.strip()
            results['detected_words'] = detected_words
            results['word_count'] = len(detected_words)
            
            print(f"  [4.4] OCR (Tesseract): {ocr_time_ms:.3f} ms")
            print(f"        Palabras detectadas: {len(detected_words)}")
            
        except Exception as e:
            results['ocr_error'] = str(e)
            results['ocr_time_ms'] = -1
            print(f"  [4.4] OCR: ERROR - {e}")
    else:
        results['ocr_time_ms'] = -1
        results['ocr_error'] = "Tesseract no disponible"
        print(f"  [4.4] OCR: OMITIDO (Tesseract no disponible)")
    
    # ── Paso 4.5: Tiempo total del pipeline ──────────────────────
    total_ms = sum([
        results.get('gray_time_ms', 0),
        results.get('binary_time_ms', 0),
        results.get('denoise_time_ms', 0),
        max(results.get('ocr_time_ms', 0), 0)
    ])
    results['total_pipeline_ms'] = round(total_ms, 3)
    
    return results


# ─────────────────────────────────────────────────────────────────
# PASO 5: Calcular precisión y recall
# (Requerimiento del informe: validar con mínimo 10 palabras)
# ─────────────────────────────────────────────────────────────────
def calculate_precision_recall(detected_words: list, expected_words: list) -> dict:
    """
    Calcula métricas de precisión y recall del OCR.
    
    Precisión = palabras correctas detectadas / total palabras detectadas
    Recall    = palabras correctas detectadas / total palabras esperadas
    F1        = 2 * (Precisión * Recall) / (Precisión + Recall)
    
    El seminario exige validar con mínimo 10 palabras esperadas.
    """
    if not expected_words or not detected_words:
        return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'error': 'Sin datos'}
    
    expected_set = set(w.lower().strip() for w in expected_words)
    detected_set = set(w.lower().strip() for w in detected_words)
    
    true_positives = len(expected_set.intersection(detected_set))
    
    precision = true_positives / len(detected_set) if detected_set else 0.0
    recall = true_positives / len(expected_set) if expected_set else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    
    return {
        'precision': round(precision, 3),
        'recall': round(recall, 3),
        'f1': round(f1, 3),
        'true_positives': true_positives,
        'expected_count': len(expected_set),
        'detected_count': len(detected_set)
    }


# ─────────────────────────────────────────────────────────────────
# PASO 6: Prueba con cámara en tiempo real
# ─────────────────────────────────────────────────────────────────
def test_with_camera(camera_index: int = 0) -> None:
    """
    Prueba el pipeline con cámara en tiempo real.
    Presiona 'q' para salir, 's' para capturar y hacer OCR.
    """
    print(f"\n[PASO 6] Abriendo cámara #{camera_index}...")
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"  ✗ No se pudo abrir la cámara #{camera_index}")
        print(f"    Verifica que la cámara está conectada.")
        return
    
    # Obtener información de la cámara
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"  ✓ Cámara abierta: {width}x{height} @ {fps} FPS")
    
    print(f"\n  Mostrando vista previa. Presiona:")
    print(f"    [s] = capturar frame y hacer OCR")
    print(f"    [q] = salir")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("  ✗ Error al leer frame de la cámara")
            break
        
        # Mostrar preview (ventana de OpenCV)
        cv2.putText(
            frame,
            "Presiona 's' para OCR, 'q' para salir",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        cv2.imshow('EDDIE - Prototipo RAD #1 (OpenCV)', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\n  Saliendo de la cámara...")
            break
        elif key == ord('s'):
            print("\n  Capturando y procesando frame...")
            results = process_frame_pipeline(frame)
            if 'detected_words' in results:
                print(f"\n  Texto detectado:")
                print(f"  {results.get('raw_text', '')[:200]}")
    
    cap.release()
    cv2.destroyAllWindows()


# ─────────────────────────────────────────────────────────────────
# PROGRAMA PRINCIPAL
# ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description='Prototipo RAD #1: Factibilidad OpenCV + OCR para EDDIE Python'
    )
    parser.add_argument('--camera', action='store_true',
                        help='Usar cámara en tiempo real')
    parser.add_argument('--camera-index', type=int, default=0,
                        help='Índice de cámara (default: 0)')
    parser.add_argument('--image', type=str, default=None,
                        help='Ruta a imagen para procesar')
    args = parser.parse_args()
    
    # Palabras esperadas para test de precisión/recall (mínimo 10, según seminario)
    EXPECTED_WORDS = [
        'lectura', 'aumentada', 'tracking', 'gestual',
        'consistencia', 'opencv', 'arquitectura', 'plugins',
        'orquestador', 'python', 'prototipo', 'eddie'
    ]
    print(f"\n  Palabras de referencia para métricas ({len(EXPECTED_WORDS)} palabras):")
    print(f"  {EXPECTED_WORDS}")
    
    if args.camera:
        # ── Modo cámara en tiempo real ─────────────────────────────
        test_with_camera(args.camera_index)
        
    elif args.image:
        # ── Modo imagen externa ────────────────────────────────────
        print(f"\n[PASO 3] Cargando imagen: {args.image}")
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"  ✗ No se pudo cargar la imagen: {args.image}")
            sys.exit(1)
        print(f"  ✓ Imagen cargada: {frame.shape}")
        
        print("\n[PASO 4] Procesando pipeline OpenCV + OCR...")
        results = process_frame_pipeline(frame)
        
        if 'detected_words' in results:
            print(f"\n[PASO 5] Calculando métricas de precisión/recall...")
            metrics = calculate_precision_recall(results['detected_words'], EXPECTED_WORDS)
            print_results(results, metrics)
        
    else:
        # ── Modo imagen de prueba generada (sin cámara) ───────────
        print("\n[PASO 3] Generando imagen de prueba con texto...")
        try:
            frame = create_test_image_with_text()
            print(f"  ✓ Imagen de prueba creada: {frame.shape}")
        except Exception as e:
            print(f"  ✗ No se pudo crear imagen de prueba: {e}")
            # Crear imagen mínima sin PIL
            frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
            cv2.putText(frame, "LECTURA AUMENTADA OPENCV PYTHON", (30, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        print("\n[PASO 4] Ejecutando pipeline de procesamiento OpenCV...")
        results = process_frame_pipeline(frame)
        
        print("\n[PASO 5] Calculando métricas de precisión/recall...")
        detected = results.get('detected_words', [])
        metrics = calculate_precision_recall(detected, EXPECTED_WORDS)
        print_results(results, metrics)


def print_results(pipeline_results: dict, metrics: dict) -> None:
    """Imprime el resumen final del prototipo."""
    print("\n" + "=" * 60)
    print("RESUMEN DEL PROTOTIPO RAD #1")
    print("=" * 60)
    
    print("\n📊 TIEMPOS DEL PIPELINE:")
    print(f"   Escala de grises : {pipeline_results.get('gray_time_ms', 'N/A')} ms")
    print(f"   Binarización     : {pipeline_results.get('binary_time_ms', 'N/A')} ms")
    print(f"   Reducción ruido  : {pipeline_results.get('denoise_time_ms', 'N/A')} ms")
    print(f"   OCR Tesseract    : {pipeline_results.get('ocr_time_ms', 'N/A')} ms")
    print(f"   TOTAL PIPELINE   : {pipeline_results.get('total_pipeline_ms', 'N/A')} ms")
    
    print("\n🎯 MÉTRICAS OCR (mínimo 10 palabras de referencia):")
    if 'error' not in metrics:
        print(f"   Palabras detectadas  : {metrics.get('detected_count', 0)}")
        print(f"   Palabras correctas   : {metrics.get('true_positives', 0)}/{metrics.get('expected_count', 0)}")
        print(f"   Precisión            : {metrics.get('precision', 0):.1%}")
        print(f"   Recall               : {metrics.get('recall', 0):.1%}")
        print(f"   F1-Score             : {metrics.get('f1', 0):.1%}")
    
    print("\n✅ CONCLUSIÓN DE FACTIBILIDAD:")
    ocr_ok = pipeline_results.get('ocr_time_ms', -1) > 0
    total_ms = pipeline_results.get('total_pipeline_ms', 999)
    
    if ocr_ok and total_ms < 8300:  # objetivo: < 8.3 segundos por frame
        print("   ✓ OpenCV + Tesseract funcionan correctamente en Python")
        print("   ✓ La migración de Emgu.CV → OpenCV es TÉCNICAMENTE FACTIBLE")
        print("   ✓ Resultado: PROCEDER con la implementación del IImageProcessor")
    elif not ocr_ok:
        print("   ✓ OpenCV funciona correctamente (Emgu.CV → OpenCV: FACTIBLE)")
        print("   ⚠ OCR no validado (instalar Tesseract para validación completa)")
        print("   → Ver instrucciones al inicio del archivo para instalar Tesseract")
    else:
        print("   ⚠ Pipeline lento. Revisar hardware o reducir resolución.")
    
    print("\n📝 PARA TU TESIS:")
    print("   Este resultado documenta el Objetivo Específico 1 del seminario:")
    print("   'Validar factibilidad de migración mediante prototipos throwaway'")
    print("   → Incluir estos tiempos en el Capítulo 6 (Implementación)")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
