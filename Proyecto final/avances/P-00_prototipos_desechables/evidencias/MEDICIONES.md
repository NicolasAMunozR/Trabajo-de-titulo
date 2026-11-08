# Mediciones de los prototipos desechables

Ejecutado el 2026-11-08T14:15:23 en Linux 6.18.44-fc-v310 (x86_64), Python 3.13.18, OpenCV 5.0.0, PyMuPDF 2.1. PDF: `borrador_tesis.pdf`. Semilla 2026.

Tipo: **pdf** = sobre el PDF real; **codigo** = sobre los módulos reales; **sintetico** = datos generados con verdad terreno conocida; **laboratorio** = requiere hardware o participantes (pendiente).

## F01 — Enumeración e inicialización de cámaras (laboratorio)

Se abre la cámara con OpenCV (MSMF y respaldo CAP_ANY, como prototipo_f01.py), se descartan 30 cuadros de calentamiento y se leen 300 cuadros a 640×480 midiendo cada cap.read(). Ejecutar con --camara <índice>.

Fórmula: `\mathrm{FPS}=N/\sum_{i=1}^{N}\Delta t_i`

- estado: pendiente

## F02 — Preprocesamiento y binarización (Otsu) (sintetico)

30 páginas del PDF renderizadas a 640 px de ancho; a cada una se le agrega un destello elíptico y una sombra lateral simulados más ruido gaussiano (σ = 4). La verdad terreno es la binarización de la página limpia. Se compara con un umbral adaptativo gaussiano (bloque 31, C = 10). Tiempo: 1 000 ejecuciones tras 10 de calentamiento.

Fórmula: `\mathrm{Eficacia}=\left(1-\frac{FP_{ruido}+FN_{corte}}{P_{afectados}}\right)\times 100\%`

- paginas: 30
- eficacia_pct: 25.8
- eficacia_sd: 2.7
- f1_tinta_pct: 32.2
- eficacia_adaptativo_pct: 96.8
- tiempo_ms: 0.67
- tiempo_sd_ms: 0.07

_Alcance:_ Mide el algoritmo con iluminación simulada; la eficacia con el proyector real se mide en el laboratorio.

## F03 — Reconocimiento óptico de caracteres (pdf)

Las tres primeras líneas de 60 párrafos de texto corrido del PDF (ancho ≥ 60 % de la página, sin tablas ni índices), renderizadas a 150 ppp, con el preprocesamiento de prototipo_f03.py (CLAHE, Otsu, apertura 2×2, escala ×2) y Tesseract «--oem 3 --psm 6 -l spa+eng». Verdad terreno: texto del PDF (get_text). «Degradado» agrega desenfoque, variación de brillo y ruido; «sin preproceso» entrega la imagen limpia directo a Tesseract.

Fórmula: `\mathrm{CER}=\frac{S_c+D_c+I_c}{N_c}\times 100\%,\quad \mathrm{WER}=\frac{S_w+D_w+I_w}{N_w}\times 100\%`

- bloques: 60
- cer_limpio_pct: 1.46
- wer_limpio_pct: 6.86
- cer_degradado_pct: 2.53
- wer_degradado_pct: 9.27
- cer_sin_preproceso_pct: 0.42
- wer_sin_preproceso_pct: 0.71
- caracteres: 16353
- palabras: 2405
- tiempo_ms: 381.1
- tiempo_sd_ms: 48.2

_Alcance:_ Es el límite superior (texto digital renderizado). La validez por palabra y posición con la cámara real se mide en el laboratorio, como Ibaceta (2023).

## F04 — Detección automática de páginas (sintetico)

80 escenas de 640×480: una página del PDF sobre un escritorio oscuro con textura, girada entre −15° y +15°, escala 0,9–1,25, leve perspectiva y brillo 0,75–1,1. Algoritmo de prototipo_f04.py (Canny 30/120, approxPolyDP 0,02·perímetro). Éxito: cuadrilátero con RMSE ≤ 10 px respecto de las esquinas reales.

Fórmula: `\mathrm{RMSE}=\sqrt{\frac{1}{4N}\sum_{i=1}^{N}\sum_{k=1}^{4}\left[(x_{k,i}-\hat{x}_{k,i})^2+(y_{k,i}-\hat{y}_{k,i})^2\right]}`

- escenas: 80
- exito_pct: 97.5
- rmse_px: 2.26
- rmse_sd_px: 0.14

_Alcance:_ La detección automática del libro quedó fuera del alcance del MVP (sección de alcances); el resultado solo indica factibilidad.

## F05 — Seguimiento de lápiz de color (sintetico)

Dos series de 300 cuadros de 640×480 con una página del PDF, tres recuadros de color (contenido proyectado) y, en 4 de cada 5 cuadros, la punta roja de un lápiz (radio 12 px) en una posición conocida. Serie A: recuadros de cualquier tono salvo rojo; serie B: uno de ellos rojo. Algoritmo de prototipo_f05.py (rojo HSV H∈[0,10]∪[170,180], S≥120, V≥70; cierre y apertura elípticos 9×9; se toma el contorno rojo más grande). Acierto: centroide a ≤ 15 px del real.

Fórmula: `e=\sqrt{(x-\hat{x})^2+(y-\hat{y})^2};\quad \text{falsas}=\frac{N_{\text{detecciones erróneas}}}{N_{\text{cuadros}}}\times 100`

- cuadros: 600
- deteccion_pct: 100.0
- falsas_por_100: 0.0
- deteccion_rojo_pct: 0.0
- falsas_rojo_por_100: 99.7
- error_px: 0.73
- error_sd_px: 0.3
- tiempo_ms: 1.93

_Alcance:_ La serie B muestra el riesgo con contenido proyectado rojo: el algoritmo toma el objeto rojo más grande.

## F06 — Segmentación de mano y apuntado (sintetico)

200 cuadros con una silueta de mano (palma + índice) en tonos de piel aleatorios sobre una página del PDF. Máscara de prototipo_f06.py (YCrCb Cr∈[133,173], Cb∈[77,127] ∧ HSV H≤30). La punta se estima como el punto más alto de la máscara; acierto si está a ≤ 15 px de la real.

Fórmula: `\mathrm{IoU}=\frac{|M\cap G|}{|M\cup G|}\times 100\%`

- cuadros: 200
- iou_pct: 96.5
- punta_ok_pct: 96.5
- error_punta_px: 1.2
- tiempo_ms: 2.17

_Alcance:_ Siluetas sintéticas: la precisión con manos reales, distintos tonos de piel y distancias se mide en el laboratorio con participantes.

## F07 — Mapeo de coordenadas (homografía) (sintetico)

300 ensayos: una inclinación aleatoria de la cámara (esquinas desplazadas hasta ±80 px) y cuatro clics en las esquinas con error gaussiano σ = 1,5 px. Con la homografía estimada (findHomography, RANSAC) se reproyectan los 21 puntos interiores de una grilla 5×5 y se mide su distancia a la posición real.

Fórmula: `e_{\mathrm{reproy}}=\frac{1}{21}\sum_{j=1}^{21}\left\lVert H\,p_j-p_j^{\ast}\right\rVert_2`

- ensayos: 300
- error_px: 1.53
- error_sd_px: 0.51
- p95_px: 2.46

_Alcance:_ El error depende de la precisión del clic; con la cámara y la lámina patrón reales se mide en el laboratorio.

## F09 — Mouse como alternativa (laboratorio)

Ejecutar prototipo_f09.py y registrar 1 000 eventos (movimiento, clic, arrastre) con marcas de tiempo del callback; requiere la interfaz gráfica del PC.

Fórmula: `\Delta t=t_{\text{callback}}-t_{\text{evento}}`

- estado: pendiente

## F10 — Comunicación con el rastreador ocular (socket) (sintetico)

Un servidor local envía 3000 muestras de mirada a 60 Hz con el formato JSON del protocolo EyeTribe (TCP); el cliente las lee y decodifica como el prototipo. Se mide el intervalo entre recepciones.

Fórmula: `\mathrm{Jitter}=\sqrt{\frac{1}{M-1}\sum_{k=1}^{M}\left(\Delta t_k-\overline{\Delta t}\right)^2}`

- muestras: 3000
- recibidas: 3000
- perdida_pct: 0.0
- frecuencia_hz: 60.0
- jitter_ms: 0.45

_Alcance:_ Enlace local (127.0.0.1): no incluye la latencia del dispositivo. Con GazePoint/EyeTribe reales se mide en el laboratorio.

## F11 — Carga dinámica de plugins (importlib) (codigo)

30 cargas de cada uno de los 8 módulos de plugins del código final con importlib.util.spec_from_file_location + exec_module (cada carga con un nombre nuevo, sin caché del módulo; las bibliotecas que importan ya están cargadas).

Fórmula: `\bar{t}=\frac{1}{N}\sum_{i=1}^{N}t_i`

- modulos: 8
- cargas: 240
- fallas: 0
- tiempo_ms: 0.36
- tiempo_sd_ms: 0.79

_Alcance:_ No hay telemetría de carga del C# para comparar; la comparación con AppDomain queda cualitativa.

## F12 — Clic por permanencia de la mirada (sintetico)

Traza de 10 min a 60 Hz que simula lectura (fijaciones log-normales de 150–450 ms, avances de 25–60 px, 12 % de regresiones) y una mirada voluntaria de 1,2 s sobre un botón cada 15–25 s, con ruido gaussiano σ = 10 px (y σ = 5 y 15 px para comparar). Algoritmo de modificar_demo_real_f12.py (zona de radio 45 px anclada al primer punto, 0,6 s) y barrido T × R con σ = 10 px.

Fórmula: `\text{accidentales/min}=\frac{N_{\text{disparos fuera de miradas voluntarias}}}{t_{\text{lectura}}}`

- umbral_s: 0.6
- radio_px: 45
- voluntarias_pct: 100.0
- accidentales_por_min: 3.5
- miradas_voluntarias: 30
- voluntarias_ruido_bajo_pct: 100.0
- accidentales_ruido_bajo: 7.9
- voluntarias_ruido_alto_pct: 50.0
- accidentales_ruido_alto: 0.3

| T (s) | R (px) | Voluntarias (%) | Accidentales/min |
|---|---|---|---|
| 0.4 | 25 | 33.3 | 1.0 |
| 0.4 | 35 | 76.7 | 10.5 |
| 0.4 | 45 | 100.0 | 29.3 |
| 0.5 | 25 | 26.7 | 0.0 |
| 0.5 | 35 | 76.7 | 1.4 |
| 0.5 | 45 | 100.0 | 9.6 |
| 0.6 | 25 | 13.3 | 0.0 |
| 0.6 | 35 | 66.7 | 0.4 |
| 0.6 | 45 | 100.0 | 3.5 |
| 0.8 | 25 | 3.3 | 0.0 |
| 0.8 | 35 | 50.0 | 0.0 |
| 0.8 | 45 | 93.3 | 0.3 |

_Alcance:_ Traza simulada: el umbral definitivo se calibra con lectores reales y el eye tracker del laboratorio.

## F13 — Retícula de mirada sobre la proyección (sintetico)

600 cuadros de 950×620 con el dibujo de la retícula de modificar_demo_real_f13.py (círculo con mezcla alfa y cruz) tras 10 de calentamiento. Mide solo el dibujo, no la presentación en el proyector.

Fórmula: `\mathrm{FPS}_{\max}=1000/\bar{t}_{\mathrm{ms}}`

- tiempo_ms: 0.82
- tiempo_sd_ms: 0.06
- fps_max: 1224.6

_Alcance:_ La latencia de extremo a extremo (dispositivo → proyector) se mide en el laboratorio.

## F14 — Búsqueda de coordenadas QuadPoints (pdf)

10 términos buscados 3 veces en las 64 páginas del PDF con page.search_for(term, quads=True). Coherencia: el texto extraído del rectángulo de cada QuadPoint (ampliado 2 pt para no cortar caracteres) contiene el término, sin distinguir tildes ni mayúsculas. Las palabras cortadas con guion al final de línea dan dos QuadPoints que no contienen el término completo.

Fórmula: `\mathrm{Coherencia}=\frac{N_{\text{QuadPoints cuyo texto contiene el término}}}{N_{\text{QuadPoints}}}\times 100\%`

- paginas: 64
- consultas: 1920
- coincidencias: 1836
- coherencia_pct: 82.0
- tiempo_ms: 1.028
- tiempo_sd_ms: 0.618

## F15 — Sincronización de resaltado (papel → PDF) (pdf)

48 resaltados agregados uno a uno sobre líneas de texto del PDF; cada uno se guarda con escritura completa a un archivo temporal y reemplazo (la corrección de H-02) y se vuelve a abrir. Persistencia: resaltados presentes al reabrir el archivo final.

Fórmula: `t=t_{\text{reapertura}}-t_{\text{inicio}}`

- anotaciones: 48
- persistidas: 48
- tiempo_ms: 13.8
- tiempo_sd_ms: 1.7

_Alcance:_ No mide la coincidencia en posición y largo con lo marcado en el papel (E40/E41 de Ibaceta, 2023): eso requiere la cámara y el proyector.

## F16 — Sincronización de notas adhesivas (sintetico)

40 notas amarillas cuadradas (70–110 px) en posiciones aleatorias sobre una página del PDF renderizada; detección de prototipo_f16.py (HSV H∈[18,38], área > 2 500, 4 vértices) y conversión del centro a puntos del PDF con la escala de la página (1 pt = 0,3528 mm).

Fórmula: `\Delta=\sqrt{(x_{\text{real}}-\hat{x}_{\text{pdf}})^2+(y_{\text{real}}-\hat{y}_{\text{pdf}})^2}`

- notas: 40
- detectadas_pct: 100.0
- error_pt: 0.68
- error_sd_pt: 0.0

_Alcance:_ Con la cámara real se agrega el error de la homografía cámara → página (F07) y la lectura de la nota manuscrita con OCR, que se miden en el laboratorio.

## F17 — Sincronización de figuras geométricas (sintetico)

60 figuras dibujadas con trazo de 3 px (20 círculos, 20 rectángulos, 20 triángulos de tamaño y posición aleatorios). Clasificador de prototipo_f17.py: compacidad C = 4πA/P² > 0,69 → círculo; 4 vértices → rectángulo; 3 → triángulo. IoU entre la primitiva reconstruida y la figura real (solo las bien clasificadas).

Fórmula: `C=\frac{4\pi A}{P^2},\qquad \mathrm{IoU}=\frac{|F_{\text{PDF}}\cap F_{\text{real}}|}{|F_{\text{PDF}}\cup F_{\text{real}}|}\times 100\%`

- figuras: 60
- exactitud_pct: 80.0
- iou_pct: 90.1
- iou_sd: 2.8

Matriz de confusión: {'circulo': {'circulo': 20}, 'rectangulo': {'circulo': 12, 'rectangulo': 8}, 'triangulo': {'triangulo': 20}}

_Alcance:_ Hallazgo: un cuadrado tiene compacidad π/4 ≈ 0,785 > 0,69, por lo que el prototipo, que evalúa la compacidad antes que el número de vértices, lo clasifica como círculo. Figuras dibujadas por computador; con trazos a mano y la cámara real se mide en el laboratorio.

## F24 — Comandos de voz (laboratorio)

Grabar los 8 comandos del módulo de búsqueda (Montanares, 2019) 10 veces cada uno con 3 personas en la sala del laboratorio; exactitud = comandos correctos / emitidos y tiempo desde el fin de la frase hasta el texto reconocido (SpeechRecognition, es-ES).

Fórmula: `\mathrm{Exactitud}=\frac{N_{\text{correctos}}}{N_{\text{emitidos}}}\times 100\%`

- estado: pendiente

## F25 — Síntesis de voz (laboratorio)

Leer 10 textos de 100 palabras con pyttsx3 (voz SAPI5 en español) en un hilo aparte; medir la duración de cada lectura (palabras por minuto) y que la interfaz no se bloquee.

Fórmula: `\mathrm{WPM}=N_{\text{palabras}}/t_{\text{min}}`

- estado: pendiente

## F27 — Banda de resaltado proyectada (sintetico)

600 cuadros de 900×600 con la banda de prototipo_f27.py (rectángulo amarillo y mezcla alfa 0,30). El contraste de Weber del texto bajo la luz proyectada se mide con luxómetro en el laboratorio.

Fórmula: `C_W=\frac{L_{\text{texto}}-L_{\text{fondo}}}{L_{\text{fondo}}}`

- alfa: 0.3
- tiempo_ms: 0.583
- tiempo_sd_ms: 0.065
