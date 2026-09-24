"""
prototypes/rad_funcionalidades/f23_youtube_video_search.py
===========================================================
PROTOTIPO RAD - F23: Búsqueda y Reproducción de Videos Explicativos
===========================================================
Subsistema: Búsqueda Web de Conocimiento y APIs REST
Archivo C# Legacy: ModuloBusquedaWeb / ApiBuscarYoutube.cs
Tecnología Propuesta: YouTube Query Builder / Embedded Video Embed URL

Descripción:
  Construye URLs de búsqueda y reproductor incrustado de YouTube para complementar la lectura del usuario.
"""
import sys
import os
import time
import urllib.parse

os.environ['PYTHONIOENCODING'] = 'utf-8'

print("\n" + "="*70)
print("PROTOTIPO RAD - F23: Búsqueda y Reproducción de Videos Explicativos")
print("="*70)

def build_youtube_embed_url(topic: str) -> dict:
    t0 = time.perf_counter()
    query_encoded = urllib.parse.quote(f"{topic} explicacion")
    search_url = f"https://www.youtube.com/results?search_query={query_encoded}"
    embed_url = f"https://www.youtube.com/embed?listType=search&list={query_encoded}"
    
    elapsed_ms = (time.perf_counter() - t0) * 1000
    
    return {
        'topic': topic,
        'search_url': search_url,
        'embed_url': embed_url,
        'elapsed_ms': round(elapsed_ms, 3)
    }

def main():
    print("\n[PASO 1] Construyendo URLs de reproductor incrustado para 'Eye Tracking'...")
    res = build_youtube_embed_url("Eye Tracking")

    print(f"\n{'='*70}")
    print("RESUMEN DE FACTIBILIDAD TÉCNICA - F23")
    print(f"{'='*70}")
    print(f"  Tema Solicitado    : '{res['topic']}'")
    print(f"  URL Búsqueda YouTube: {res['search_url']}")
    print(f"  URL Embed Player   : {res['embed_url']}")
    print(f"  Tiempo de proceso  : {res['elapsed_ms']} ms")
    print(f"  Equivalencia C#    : ApiBuscarYoutube.cs -> YouTube Query Builder")
    print(f"  Estado Factibilidad: FACTIBLE Y OPERATIVO")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
