# P-05 — Rastreo ocular

Parte de la serie de avances de EDDIE en Python. La guía general (metodología, requisitos, hallazgos y cómo regenerar las evidencias) está en `../GUIA_AVANCES.md`.

Fase PDCA: **Do (implementación)** · Objetivo específico: **OE3** · Semanas del plan: **11–12** · Carpeta: `P-05_rastreo_ocular`

| | |
|---|---|
| **ID Prototipo** | P-05 |
| **Nombre** | Rastreo ocular |
| **Objetivos** | Unificar GazePoint (Open Gaze API), TheEyeTribe y GazeCloud bajo IEyeTracker, con EyeTrackerMock como contingencia (DeviceFactory).<br>Portar la sesión de mirada: control del mouse por mirada, clic por permanencia, retícula y registro CSV.<br>Agregar la página Rastreo ocular (exportar/importar configuración). |
| **Descripción** | Los tres protocolos se prueban con servidores falsos que emiten el mismo formato que los dispositivos reales. La sesión de mirada es un consumidor de resultados del ciclo: recibe la muestra del eye tracker en el mismo ciclo en que se produce. |
| **Requisitos Funcionales** | RO1–RO7, RFS4 |
| **Requisitos No Funcionales** | RNF-01, RNF-02, RNF-05 |

### Qué se revisa en este avance

1. Que cada protocolo (GazePoint, EyeTribe, GazeCloud) entregue GazePoint normalizados.
2. Que un eye tracker sin dispositivo falle la inicialización sin afectar al resto.
3. Que «Aplicar y conectar» con el eye tracker simulado muestre la retícula y escriba el CSV de la sesión.
4. Formato del archivo de configuración exportado (mismas claves que el C#).
5. Que los botones de carpeta, las casillas y los íconos de ayuda de Rastreo ocular no lancen excepciones (hallazgo H-03).

### Cómo ejecutarlo

```powershell
python main.py --sim
python -m pytest
python tools\generar_evidencias.py
```

### Resultados

Ejecución en `Linux 6.18.44-fc-v310`, Python 3.13.18, dispositivos simulados, 2026-11-08 13:57:18.

| Pruebas aprobadas | Fallo esperado (hallazgo) | Fallidas | Cobertura de líneas | Ciclo completo p95 | Ciclo completo máx. |
|---|---|---|---|---|---|
| 94 | 1 | 0 | 74 % | 1,41 ms | 3,53 ms |

Plugin con mayor latencia (p95): **ColorPenRecognition**, 0,92 ms (umbral 8,3 ms). Detalle por plugin en `evidencias/RESULTADOS.md`.

Figuras disponibles para la tesis:

- `evidencias/capturas/00_menu_settings.png` — Quinto prototipo: Ventana principal con «Preparar sesión» y el estado de cada módulo.
- `evidencias/capturas/01_text.png` — Quinto prototipo: Texto (OCR) con la cámara simulada y el texto reconocido.
- `evidencias/capturas/02_page.png` — Quinto prototipo: Documento PDF con la vista previa.
- `evidencias/capturas/03_gesture_mano.png` — Quinto prototipo: Gestos con Hand Skin (mano).
- `evidencias/capturas/03_gesture_lapiz.png` — Quinto prototipo: Gestos con Color Pen (lápiz).
- `evidencias/capturas/04_eye.png` — Quinto prototipo: Rastreo ocular.

Hallazgos relacionados: H-01, H-02, H-03 (corregido en este avance) (ver «Hallazgos de la verificación»).

