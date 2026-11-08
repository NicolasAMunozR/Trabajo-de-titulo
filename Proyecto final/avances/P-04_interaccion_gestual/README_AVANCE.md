# P-04 — Interacción gestual

Parte de la serie de avances de EDDIE en Python. La guía general (metodología, requisitos, hallazgos y cómo regenerar las evidencias) está en `../GUIA_AVANCES.md`.

Fase PDCA: **Do (implementación)** · Objetivo específico: **OE3** · Semanas del plan: **10** · Carpeta: `P-04_interaccion_gestual`

| | |
|---|---|
| **ID Prototipo** | P-04 |
| **Nombre** | Interacción gestual |
| **Objetivos** | Integrar los plugins gestuales del C# (Color Pen, Hand Skin, Mouse) bajo IGesturePlugin, compartiendo la cámara gestual declarada.<br>Portar la calibración sensor→aplicación, el control del cursor («Recognition on»), la máquina de estados del clic y la captura automática de la selección.<br>Agregar la página Gestos, con calibración asistida («Fijar inicio» / «Fijar fin» desde la lectura del sensor). |
| **Descripción** | Los tres detectores heredan una base común (CalibratedGesturePlugin) que aplica la calibración y el clic; cada uno solo implementa su detección. Este avance porta el comportamiento del C# tal cual, incluida la rotación fija de 180° de Hand Skin, que después se detectó como defecto (H-01). |
| **Requisitos Funcionales** | G1, G2, G3, U2 |
| **Requisitos No Funcionales** | RNF-01, RNF-04, RNF-06 |

### Qué se revisa en este avance

1. Que el lápiz simulado mueva las coordenadas del sensor y la calibración las transforme al espacio de la aplicación.
2. Que al soltar el lápiz se capture la selección (imagen lista para la búsqueda por imagen).
3. Que los tres plugins aparezcan en el combobox por contrato y se reconecten al reiniciar la cámara.
4. Latencia del ciclo con el reconocimiento gestual activo.
5. Que «Fijar inicio» y «Fijar fin» copien la lectura del sensor a la calibración.
6. Captura de Gestos con la mano: la imagen aparece invertida (hallazgo H-01).

### Cómo ejecutarlo

```powershell
python main.py --sim
python -m pytest
python tools\generar_evidencias.py
```

### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:57:04.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 79 | 1 | 0 | 72 % | 1,50 ms | 1,76 ms |

Plugin con mayor latencia (p95): **ColorPenRecognition**, 1,00 ms (umbral 8,3 ms). Detalle por plugin en `evidencias/RESULTADOS.md`.

Figuras disponibles para la tesis:

- `evidencias/capturas/00_menu_settings.png` — Cuarto prototipo: Ventana principal con «Preparar sesión» y el estado de cada módulo.
- `evidencias/capturas/01_text.png` — Cuarto prototipo: Texto (OCR) con la cámara simulada y el texto reconocido.
- `evidencias/capturas/02_page.png` — Cuarto prototipo: Documento PDF con la vista previa.
- `evidencias/capturas/03_gesture_mano.png` — Cuarto prototipo: Gestos con Hand Skin (mano).
- `evidencias/capturas/03_gesture_lapiz.png` — Cuarto prototipo: Gestos con Color Pen (lápiz).

Hallazgos relacionados: H-01, H-02 (ver «Hallazgos de la verificación»).

