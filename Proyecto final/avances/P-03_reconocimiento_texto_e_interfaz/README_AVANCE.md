# P-03 — Reconocimiento de texto e interfaz de configuración

Parte de la serie de avances de EDDIE en Python. La guía general (metodología, requisitos, hallazgos y cómo regenerar las evidencias) está en `../GUIA_AVANCES.md`.

Fase PDCA: **Do (implementación)** · Objetivo específico: **OE3** · Semanas del plan: **9** · Carpeta: `P-03_reconocimiento_texto_e_interfaz`

| | |
|---|---|
| **ID Prototipo** | P-03 |
| **Nombre** | Reconocimiento de texto e interfaz de configuración |
| **Objetivos** | Integrar el reconocimiento del texto resaltado (IImageProcessor: segmentación del resaltado + Tesseract) sobre la cámara de texto declarada.<br>Construir la ventana de configuración a partir de los controles extraídos de los .Designer.cs, con un diseño propio en español (ui/theme.py, ui/modern_forms.py) y las páginas Texto (OCR) y Documento PDF.<br>Ejecutar el ciclo del orquestador dentro de Qt (EddieRuntime) y persistir los ajustes.<br>Poder probar el OCR y ver el PDF cargado desde estas páginas, sin esperar la pantalla de proyección. |
| **Descripción** | Aparece la interfaz. Conserva todos los controles del original (mismo nombre, tipo, rangos y estado inicial), ordenados en tarjetas con layouts de Qt, con un menú lateral que muestra el estado de cada módulo y una pantalla de inicio «Preparar sesión». Solo se construyen las páginas de los módulos ya integrados: las demás aparecen en el menú deshabilitadas con el avance en que se integran, y «Iniciar proyección» avisa que la proyección llega en P-06. Como en el C# el texto reconocido solo se veía desde la proyección, se agregan el botón «Reconocer texto» con el texto reconocido y una vista previa del PDF con navegación de páginas. Los mensajes son avisos no modales. |
| **Requisitos Funcionales** | FD1, N7, U1, U3, RFS3, RFS5, RFS6, RFS7, RFS8 |
| **Requisitos No Funcionales** | RNF-01, RNF-06, RNF-07 |

### Qué se revisa en este avance

1. Que «Reconocer texto» marque el resaltado amarillo en la imagen y muestre el texto leído por el OCR («aumentada» en la hoja simulada; con la cámara real, la palabra que resaltes en papel).
2. Que Documento PDF muestre la página del PDF cargado y permita recorrerlo.
3. Que cada control de los formularios incluidos exista con su nombre, tipo, rango y estado del C#.
4. Que «Preparar sesión» y el menú lateral cambien de estado al cargar el PDF.
5. Que Guardar y Restaurar valores persistan y restauren los ajustes (config/user_settings.json).
6. Que Documento PDF abra un PDF válido y rechace uno dañado con un aviso, sin cerrarse.
7. Capturas de la ventana principal, Texto (OCR) y Documento PDF (evidencias/capturas).

### Cómo ejecutarlo

```powershell
python main.py --sim
python -m pytest
python tools\generar_evidencias.py
```

### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:56:54.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 65 | 0 | 0 | 67 % | 0,20 ms | 0,58 ms |

Plugin con mayor latencia (p95): **TextCamera**, 0,15 ms (umbral 8,3 ms). Detalle por plugin en `evidencias/RESULTADOS.md`.

Figuras disponibles para la tesis:

- `evidencias/capturas/00_menu_settings.png` — Tercer prototipo: Ventana principal con «Preparar sesión» y el estado de cada módulo.
- `evidencias/capturas/01_text.png` — Tercer prototipo: Texto (OCR) con la cámara simulada y el texto reconocido.
- `evidencias/capturas/02_page.png` — Tercer prototipo: Documento PDF con la vista previa.

Hallazgos relacionados: H-02 (ver «Hallazgos de la verificación»).

