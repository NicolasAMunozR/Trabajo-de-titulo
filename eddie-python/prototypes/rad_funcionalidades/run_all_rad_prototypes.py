"""
prototypes/rad_funcionalidades/run_all_rad_prototypes.py
===========================================================
EJECUTADOR MAESTRO DE PROTOTIPOS RAD (F1 a F28)
===========================================================
Ejecuta secuencialmente todos los 25 prototipos desechables RAD desarrollados en Python
y genera un reporte consolidado de factibilidad técnica para la migración de EDDIE-2023.
"""
import sys
import os
import time
import subprocess

os.environ['PYTHONIOENCODING'] = 'utf-8'

PROTOTYPES = [
    ("F1", "Enumeración de Cámaras", "f01_camera_enumeration.py"),
    ("F2", "Preprocesamiento y Binarización", "f02_image_preprocessing.py"),
    ("F3", "Reconocimiento OCR Tesseract", "f03_ocr_tesseract.py"),
    ("F4", "Detección de Páginas del Libro", "f04_book_page_detection.py"),
    ("F5", "Seguimiento Puntero ColorPen", "f05_color_pen_tracking.py"),
    ("F6", "Segmentación Mano HandSkin", "f06_hand_skin_segmentation.py"),
    ("F7", "Mapeo Coordenadas Gestos", "f07_gesture_coordinate_mapping.py"),
    ("F9", "Fallback Entrada Mouse", "f09_mouse_input_fallback.py"),
    ("F10", "Socket Server EyeTracker", "f10_eyetracker_socket_server.py"),
    ("F11", "Carga Dinámica Plugins importlib", "f11_plugin_dynamic_loading.py"),
    ("F12", "Detección Dwell Time Mirada", "f12_dwell_time_detection.py"),
    ("F13", "Overlay Retículo Mirada", "f13_gaze_reticle_overlay.py"),
    ("F14", "Búsqueda QuadPoints PDF", "f14_pdf_quadpoints_search.py"),
    ("F15", "Sincronización Highlight PDF", "f15_pdf_highlight_sync.py"),
    ("F16", "Sincronización Post-It PDF", "f16_pdf_postit_comments.py"),
    ("F17", "Sincronización Figuras PDF", "f17_pdf_geometric_figures.py"),
    ("F19", "Wikipedia REST API (Sanitizada E34)", "f19_wikipedia_rest_api.py"),
    ("F20", "Definiciones Conceptuales Ollama", "f20_ollama_definitions_connector.py"),
    ("F21", "Traducción de Texto REST", "f21_text_translation_api.py"),
    ("F22", "Cloud Vision Image Base64 Payload", "f22_cloud_vision_image_rec.py"),
    ("F23", "YouTube Video Query Embed", "f23_youtube_video_search.py"),
    ("F24", "Comandos por Voz STT Whisper", "f24_speech_to_text_whisper.py"),
    ("F25", "Síntesis de Voz TTS", "f25_text_to_speech_sapi.py"),
    ("F27", "HighlightTool Digital Proyectado", "f27_digital_highlight_tool.py"),
    ("F28", "Registro Asíncrono ModuloLog", "f28_async_event_logging.py")
]

def main():
    print("\n" + "="*80)
    print("EJECUCIÓN BATCH DE PROTOTIPOS RAD DESECHABLES (MIGRACIÓN EDDIE-2023 -> PYTHON)")
    print("="*80 + "\n")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable

    results_summary = []
    t_global = time.perf_counter()

    for fid, name, filename in PROTOTYPES:
        script_path = os.path.join(base_dir, filename)
        if not os.path.exists(script_path):
            results_summary.append((fid, name, "NO ENCONTRADO", 0.0))
            continue

        t0 = time.perf_counter()
        proc = subprocess.run([python_exe, script_path], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        elapsed = (time.perf_counter() - t0) * 1000

        status = "PASSED" if proc.returncode == 0 else "FAILED"
        results_summary.append((fid, name, status, round(elapsed, 1)))
        print(f" [{fid}] {name:<40} -> {status} ({elapsed:.1f} ms)")

    total_elapsed_s = time.perf_counter() - t_global

    print("\n" + "="*80)
    print("REPORTE CONSOLIDADO DE EVALUACIÓN DE FACTIBILIDAD TÉCNICA (RAD)")
    print("="*80)
    print(f" Total prototipos ejecutados : {len(PROTOTYPES)}")
    print(f" Prototipos exitosos (PASSED): {sum(1 for r in results_summary if r[2] == 'PASSED')}/{len(PROTOTYPES)}")
    print(f" Tiempo total de prueba      : {total_elapsed_s:.2f} s")
    print("-" * 80)
    print(" Funciones excluidas del MVP (No prototipar):")
    print("   - F8: Reconocimiento Gestual 3D (LeapMotion) -> Requiere hardware descontinuado")
    print("   - F18: Sincronización Marcapáginas PDF       -> Resuelto con PyMuPDF TOC")
    print("   - F26: Navegador CefSharp Embebido           -> Reemplazado por PyQt / WebEngine")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
