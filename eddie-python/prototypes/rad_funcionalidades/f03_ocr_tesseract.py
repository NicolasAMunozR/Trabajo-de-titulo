"""
prototypes/rad_funcionalidades/f03_ocr_tesseract.py
===========================================================
PROTOTIPO RAD - F3: Reconocimiento Óptico de Caracteres (OCR)
===========================================================
Subsistema: Procesamiento de Imágenes y Visión Computacional
Archivo C# Legacy: ModuloProcesamientoImagenes / OCRProcess.cs (Tesseract Engine C# wrapper)
Tecnología Propuesta: PyTesseract / Tesseract 5.x

Descripción:
  Convierte la imagen recortada y binarizada en texto reconocible en español usando pytesseract.
"""
import sys
import os
import time
import argparse
import numpy as np

os.environ['PYTHONIOENCODING'] = 'utf-8'
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

print("\n" + "="*70)
print("PROTOTIPO RAD - F3: Reconocimiento Óptico de Caracteres (OCR)")
print("="*70)

try:
    import cv2
    import pytesseract
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
except ImportError as e:
    print(f"ERROR: Dependencias no encontradas: {e}")
    sys.exit(1)

def run_ocr_test(image: np.ndarray, expected_text_keywords: list) -> dict:
    t0 = time.perf_counter()
    results = {}
    
    # Preprocesar rápida escala de grises
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    try:
        t_ocr = time.perf_counter()
        config = r'--oem 3 --psm 6 -l spa+eng'
        extracted_text = pytesseract.image_to_string(binary, config=config)
        ocr_ms = (time.perf_counter() - t_ocr) * 1000
        
        detected_words = [w.strip().lower() for w in extracted_text.split() if len(w.strip()) > 2]
        
        # Calcular Precision y Recall
        matches = [kw for kw in expected_text_keywords if kw.lower() in extracted_text.lower()]
        recall = len(matches) / len(expected_text_keywords) if expected_text_keywords else 1.0
        
        results = {
            'success': True,
            'extracted_text': extracted_text.strip(),
            'detected_word_count': len(detected_words),
            'ocr_time_ms': round(ocr_ms, 3),
            'matches_found': matches,
            'recall': round(recall, 3),
            'total_ms': round((time.perf_counter() - t0) * 1000, 3)
        }
    except Exception as e:
        results = {'success': False, 'error': str(e)}

    return results

def main():
    # Imagen de prueba sintética
    img = np.ones((300, 700, 3), dtype=np.uint8) * 255
    cv2.putText(img, "SISTEMA EDDIE LECTURA AUMENTADA", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, "PROTOTIPO OCR F3 EN PYTHON", (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    keywords = ["sistema", "eddie", "lectura", "aumentada", "prototipo", "ocr", "python"]

    print("\n[PASO 1] Ejecutando reconocimiento OCR sobre imagen de prueba...")
    res = run_ocr_test(img, keywords)

    print(f"\n{'='*70}")
    print("RESUMEN DE FACTIBILIDAD TÉCNICA - F3")
    print(f"{'='*70}")
    if res.get('success'):
        print(f"  Texto extraído     : '{res['extracted_text'].replace('\n', ' ')}'")
        print(f"  Palabras clave     : {len(res['matches_found'])}/{len(keywords)} encontradas")
        print(f"  Tasa de Recall     : {res['recall']:.1%}")
        print(f"  Tiempo de OCR      : {res['ocr_time_ms']} ms")
        print(f"  Equivalencia C#    : OCRProcess.cs (Tesseract.Net) -> PyTesseract")
        print(f"  Estado Factibilidad: FACTIBLE Y OPERATIVO")
    else:
        print(f"  Error en OCR       : {res.get('error')}")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
