# Diseño de la interfaz de EDDIE en Python

La interfaz de EDDIE en Python conserva **todos los controles y flujos** de EDDIE-2023 (ventana de configuración con seis módulos, pantalla proyectada, alertas e indicador de carga), con un diseño nuevo, en español, que corrige problemas de uso documentados por Ibaceta (2023). Las comparaciones con la interfaz WinForms original (reproducida a partir de sus `.Designer.cs`) están en `docs/comparacion_interfaz/`.

## 1. Cómo se construye

La lógica de cada pantalla (`ui/settings_pages.py`, `ui/menu_settings.py`, `ui/projection_screen.py`) accede a los controles por su nombre (`self.form.rbtn_voz_si`, `self.form.btn_diccionario`…), los mismos del C#. La capa visual está separada:

| Archivo | Qué hace |
|---|---|
| `ui/layouts/*.json` | Controles de cada formulario extraídos de los `.Designer.cs` (tipo, nombre, rangos, ítems, estado inicial). |
| `ui/modern_forms.py` | `build_modern`: crea esos controles con su nombre y comportamiento, y los ordena con layouts de Qt en tarjetas. Los que el diseño no muestra (rótulos de unidades, el GIF de carga) quedan en un contenedor oculto, de modo que ninguna referencia de la lógica se rompe. |
| `ui/theme.py` | Colores, tipografía (IBM Plex Sans), hoja de estilo de la ventana y de la proyección, e iconos Lucide (licencia ISC). |
| `ui/widgets.py` | Controles propios: `ActionButton`, `NavButton` (menú con estado del módulo), `ToolButton` (botón proyectado con estado y progreso del clic por mirada), `FitFrameView` (cámara sin deformar), `Spinner`. |

La prueba `test_every_original_control_exists_in_the_new_interface` revisa, en los 11 formularios, que cada control del original exista con un tipo compatible, el mismo rango, valor inicial y habilitación.

## 2. Ventana de configuración

| EDDIE-2023 | EDDIE en Python | Por qué |
|---|---|---|
| Al abrir, un panel vacío | **Preparar sesión**: pasos numerados (PDF, cámara de texto, proveedor LLM, gesto, eye tracker, voz) con su estado real y un botón a cada página | Se ve qué falta antes de proyectar; los pasos son una secuencia real de preparación |
| Menú de texto | Menú lateral con un **punto de estado** por módulo (verde listo, ámbar pendiente, gris opcional) | El estado de cada plugin (`initialization_report`) solo se veía en el log |
| — | Al pie del menú: plugins activos y **duración media del ciclo** del orquestador | Hace visible el requisito de latencia durante el uso |
| Ayudas solo al pasar el mouse por un icono | Tarjetas con título, icono de ayuda y una línea que explica cada opción | Menos pasos para entender cada ajuste |
| «Save Settings» abre un cuadro que hay que cerrar | **Guardar** confirma con un aviso que se cierra solo | Un paso menos |
| `MessageBox` modal | **Avisos no modales** (rojo oscuro si es un problema) | Un cuadro modal en la proyección detenía la lectura hasta pulsar «Aceptar» |
| Imagen de cámara estirada al control | La imagen conserva su proporción | El original deformaba la imagen 4:3 de la cámara |
| Calibración gestual: leer «Sensor X/Y» y escribir cuatro campos | **Fijar inicio / Fijar fin** copian la lectura del sensor | Calibrar era la tarea más propensa a errores de transcripción |
| Sin indicación de voz ni de proveedores | «Reconocedor listo / no disponible»; proveedores LLM con su estado | La falta de clave de Gemini solo se notaba al buscar |
| Textos en inglés y español | Español en toda la interfaz | Ibaceta (2023) registró mensajes en otro idioma (E14) |

## 3. Pantalla proyectada

Se diseñó con tres hallazgos de Ibaceta (2023) sobre EDDIE-2023:

1. **El eye tracker fue 100 % válido en la zona superior de la proyección** y bajo en la inferior y central. Por eso **todos los botones están en la franja superior** (primera fila: Historial, Modo, Buscar, Sincronizar PDF, Salir; segunda fila: servicios o herramientas del PDF) y la franja inferior central queda libre.
2. **El botón de resaltado era amarillo, como el resaltador**, y confundía al OCR. **Ningún color de la interfaz es amarillo** (`test_interface_chrome_never_uses_yellow`).
3. **La zona de lectura y las cruces de calibración no se mueven** respecto de EDDIE-2023 (HighlightTool en 285, 65 de 517 × 400; cruces en 298, 20 · 297, 570 · 797, 570): de ellas dependen el montaje del proyector y la calibración gestual.

Además: fondo negro (el proyector no emite luz donde no hay contenido), cruces claras, botón de modo que dice el modo actual («Capturando» / «Resaltando»), servicio que respondió marcado como encendido, barra de progreso del clic por mirada, tarjeta única para la sincronización con el PDF (un panel por lado), historial con el término destacado e indicador «Buscando…» junto al panel del resultado.

## 4. Pendiente de validar

El fondo negro y la franja superior son decisiones fundadas en Ibaceta (2023), no resultados medidos con esta versión. Deben validarse en el laboratorio con lectores y con el eye tracker (validez por zona de la proyección), como parte de las pruebas de aceptación.
