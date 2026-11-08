# Tesis EDDIE — versión preliminar en LaTeX

## Qué hay aquí

| Archivo / carpeta | Contenido |
|---|---|
| `main.tex` | Documento de prueba que compila todo (portada, resumen, capítulos 1–6, glosario, referencias, anexos y apéndices). |
| `comandos_eddie.tex` | Paquetes y comandos que usan los capítulos (`\ficha`, `\pendiente`, `\tipomed`, `\fuente`, `\figuraopcional`). |
| `capitulos/` | Un archivo por capítulo. |
| `datos/` | Números generados desde el código. **No se editan a mano.** |
| `figuras/` | Capturas de la interfaz y figuras del avance P-07. |
| `referencias.bib` | Bibliografía corregida (nombres y títulos verificados contra los PDF del proyecto). |

## Cómo llevarlo a tu Overleaf

1. Sube `capitulos/`, `datos/`, `figuras/`, `referencias.bib` y `comandos_eddie.tex` a tu proyecto.
2. En el preámbulo de tu plantilla del Departamento, después de sus paquetes, agrega `\input{comandos_eddie}`.
3. Reemplaza el cuerpo de tu `main` por los `\input{capitulos/...}` en el mismo orden que este `main.tex`.
4. Sube a `figuras/` las imágenes del estado del arte que ya tenías: `digitaldesk.png`, `enhanceddesk.png`, `arpapersync.png`, `enlight.png` y `multimodal_observer.png`. Mientras no estén, el PDF muestra un recuadro con el nombre que falta.
5. Si tu plantilla carga babel en español: no escribas `\,\%`; babel ya agrega el espacio antes de `%`.

## Cómo actualizar los números

Los resultados de los prototipos y de los avances están en `datos/*.tex` como macros (`\FDosEficaciaPct`, `\PSieteCobertura`, …). Para regenerarlos en tu PC:

```powershell
cd "Proyecto final\avances\P-00_prototipos_desechables"
python mediciones\medir_prototipos.py --pdf ruta\al\libro.pdf            # prototipos (agrega --camara 0 en el laboratorio)
cd ..
python generar_todo.py                                                    # pruebas, cobertura y latencias de P-01…P-07
python ruta\a\tesis\datos\actualizar_datos.py "C:\...\Proyecto final\avances"
```

Luego sube los `datos/*.tex` nuevos a Overleaf y recompila. Con `--camara`, la ficha de F1 pasa sola de «Pendiente» a los valores medidos.

## Lo que falta (marcado en naranja en el PDF como «Pendiente»)

- Mediciones con hardware: F1, F9, F24, F25 y la parte de sensor de F2–F17.
- Verificación MECIVA PS y pruebas de aceptación (capítulo 5, secciones 5.3 y 5.4).
- Ejecutar SonarQube (E27, E28).
- Verificar el identificador arXiv de Ernst et al. (2026): el borrador dice `2603.2041`, que no tiene el formato de arXiv.
