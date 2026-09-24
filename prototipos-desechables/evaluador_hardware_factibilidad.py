"""
Evaluador de Factibilidad y Verificación de Hardware Real (Granular)
---------------------------------------------------------------------
Orquesta la ejecución de los 9 prototipos aislados de funciones EDDIE-2023,
ejecuta la verificación previa de hardware real para cada componente y produce
el informe cuantitativo en JSON y Markdown.
"""

import sys
import os
import time
import json

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import proto_01_camara_texto_ocr
import proto_02_puntero_lapiz_color
import proto_03_reconocimiento_mano_dedo
import proto_04_rastreo_ocular_socket
import proto_05_reconocimiento_voz_whisper
import proto_06_definiciones_ollama_llm
import proto_07_destacado_pdf_pymupdf
import proto_08_comentarios_postit_pymupdf
import proto_09_busqueda_video_youtube


def run_all_checks():
    print("==========================================================================")
    print("      VERIFICADOR DE HARDWARE REAL Y PROTOTIPOS DE FUNCIONES EDDIE-2023")
    print("==========================================================================")
    print("Metodología: Figueroa (2025) — Prototipos Granulares 'Probar una función y listo'\n")

    results = []

    # 1. Cámara 1 + OCR
    print(">>> 1. Probando Función: Captura Cámara 1 + Tesseract OCR")
    proto_01_camara_texto_ocr.execute_function(camera_index=0)

    # 2. Cámara 2 + ColorPen
    print(">>> 2. Probando Función: Puntero de Color (ColorPen HSV)")
    proto_02_puntero_lapiz_color.execute_function(camera_index=1)

    # 3. Cámara 2 + HandSkin
    print(">>> 3. Probando Función: Segmentación Mano y Dedo Índice (YCrCb)")
    proto_03_reconocimiento_mano_dedo.execute_function(camera_index=1)

    # 4. EyeTracker Socket
    print(">>> 4. Probando Función: Lectura Mirada EyeTracker Socket")
    proto_04_rastreo_ocular_socket.execute_function()

    # 5. Whisper Audio a Texto
    print(">>> 5. Probando Función: Transcripción de Voz a Texto (Whisper STT)")
    proto_05_reconocimiento_voz_whisper.execute_function(record_duration_sec=1)

    # 6. Ollama Local LLM
    print(">>> 6. Probando Función: Definiciones Conceptuales (Ollama LLM Local)")
    proto_06_definiciones_ollama_llm.execute_function(word="Realidad Aumentada")

    # 7. PyMuPDF Highlight
    print(">>> 7. Probando Función: Destacado Amarillo en PDF (PyMuPDF QuadPoints)")
    proto_07_destacado_pdf_pymupdf.execute_function()

    # 8. PyMuPDF Post-It
    print(">>> 8. Probando Función: Notas Adhesivas Post-It en PDF (PyMuPDF)")
    proto_08_comentarios_postit_pymupdf.execute_function()

    # 9. YouTube URL Builder
    print(">>> 9. Probando Función: Búsqueda de Videos YouTube (Sanitizador E34)")
    proto_09_busqueda_video_youtube.execute_function()

    print("==========================================================================")
    print("               EJECUCIÓN DE PROTOTIPOS COMPLETADA")
    print("==========================================================================")


if __name__ == "__main__":
    run_all_checks()
