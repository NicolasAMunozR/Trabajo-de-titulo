"""Tkinter dashboard for isolated plugin checks and complete pipeline runs."""
import json
import logging
import os
import queue
import tempfile
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
import pymupdf
from PIL import Image, ImageTk

from orchestrator.execution_trace import ExecutionTrace, json_safe, redact_sensitive
from orchestrator.orchestrator_core import OrchestratorCore
from plugins.spatial_calibration import SpatialCalibration

logger = logging.getLogger(__name__)


def render_pdf_page(
    pdf_path: str | Path,
    page_number: int,
    max_size: tuple[int, int] = (680, 580),
) -> tuple[Image.Image, int]:
    """Render one PDF page scaled to fit the embedded preview."""
    if page_number < 1:
        raise ValueError("La página del PDF debe ser 1 o mayor.")
    with pymupdf.open(pdf_path) as document:
        if page_number > document.page_count:
            raise ValueError(
                f"El PDF tiene {document.page_count} páginas; "
                f"la página {page_number} no existe."
            )
        page = document[page_number - 1]
        scale = min(
            max_size[0] / page.rect.width,
            max_size[1] / page.rect.height,
        )
        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(scale, scale),
            colorspace=pymupdf.csRGB,
            alpha=False,
        )
        image = Image.frombytes(
            "RGB",
            (pixmap.width, pixmap.height),
            pixmap.samples,
        )
        return image, document.page_count


class PluginDashboard:
    """Local operator UI for selecting, running and tracing EDDIE plugins."""

    def __init__(self, root: tk.Tk, config_path: str) -> None:
        self.root = root
        self.root.title("EDDIE — Pruebas de plugins")
        self.root.geometry("1180x820")
        self.config_path = Path(config_path).resolve()
        self.project_dir = self.config_path.parent.parent
        self.config = self._read_config()
        self.events: queue.Queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.latest_trace: Path | None = None
        self._preview_image = None
        self._pdf_preview_image = None
        self._pdf_page_count = 0
        self._camera_frame: np.ndarray | None = None
        self._camera_frame_size: tuple[int, int] | None = None
        self._display_image_bounds: tuple[int, int, int, int] | None = None
        self._calibration_points: list[tuple[float, float]] = []
        self.plugin_vars: dict[str, tk.BooleanVar] = {}

        self.pdf_path_var = tk.StringVar()
        self.page_var = tk.StringVar(value="1")
        self.corner_var = tk.StringVar()
        self.viewport_var = tk.StringVar()
        self.interval_var = tk.StringVar(value="0.25")
        self.status_var = tk.StringVar(value="Detenido")
        self.trace_var = tk.StringVar(value="Aún no se ha creado una traza.")

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self._drain_events)

    def _read_config(self) -> dict:
        try:
            with self.config_path.open("r", encoding="utf-8") as stream:
                config = json.load(stream)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"No se pudo leer {self.config_path}: {exc}") from exc
        if not isinstance(config.get("plugins"), list):
            raise ValueError("La configuración debe contener la lista 'plugins'.")
        return config

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        ttk.Label(
            self.root,
            text="Prueba individual de plugins y flujo integrado",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))

        notebook = ttk.Notebook(self.root)
        notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        run_tab = ttk.Frame(notebook, padding=10)
        pdf_tab = ttk.Frame(notebook, padding=10)
        notebook.add(run_tab, text="Plugins y ejecución")
        notebook.add(pdf_tab, text="PDF y calibración")
        self._build_run_tab(run_tab)
        self._build_pdf_tab(pdf_tab)

        footer = ttk.Frame(self.root, padding=(12, 4, 12, 12))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(1, weight=1)
        ttk.Label(footer, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        ttk.Label(footer, textvariable=self.trace_var).grid(
            row=0, column=1, sticky="w", padx=12
        )
        ttk.Button(footer, text="Abrir traza", command=self.open_trace).grid(
            row=0, column=2
        )

    def _build_run_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(1, weight=1)
        selection = ttk.LabelFrame(parent, text="Plugins activos para esta prueba", padding=8)
        selection.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 8))
        for index, plugin in enumerate(self.config["plugins"]):
            name = plugin.get("name", f"plugin-{index}")
            variable = tk.BooleanVar(value=bool(plugin.get("enabled", False)))
            self.plugin_vars[name] = variable
            ttk.Checkbutton(
                selection,
                text=name,
                variable=variable,
            ).grid(row=index, column=0, sticky="w")
        ttk.Label(
            selection,
            text="OCR y gestos requieren CameraSensor. Consistency necesita PDF, "
            "calibración, OCR, EyeTracker y GesturePlugin.",
            wraplength=290,
        ).grid(row=len(self.config["plugins"]), column=0, sticky="w", pady=(6, 0))
        ttk.Label(
            selection,
            text="La traza se guarda localmente e incluye texto OCR, puntos de "
            "mirada y ruta/configuración del PDF.",
            wraplength=290,
        ).grid(row=len(self.config["plugins"]) + 1, column=0, sticky="w", pady=(6, 0))
        presets = [
            ("Solo cámara", {"CameraSensor"}),
            ("OCR + cámara", {"CameraSensor", "ImageProcessor"}),
            ("Gestos + cámara", {"CameraSensor", "GesturePlugin"}),
            ("EyeTracker", {"EyeTracker"}),
            (
                "Flujo PDF",
                {
                    "CameraSensor",
                    "ImageProcessor",
                    "EyeTracker",
                    "GesturePlugin",
                    "ConsistencyProvider",
                },
            ),
        ]
        for offset, (label, selected) in enumerate(
            presets, start=len(self.config["plugins"]) + 2
        ):
            ttk.Button(
                selection,
                text=label,
                command=lambda names=selected: self._select_plugins(names),
            ).grid(row=offset, column=0, sticky="ew", pady=1)

        actions = ttk.LabelFrame(parent, text="Control", padding=8)
        actions.grid(row=1, column=0, sticky="new", padx=(0, 8))
        ttk.Button(actions, text="Probar un ciclo", command=self.run_one_cycle).grid(
            row=0, column=0, sticky="ew", pady=3
        )
        ttk.Button(actions, text="Iniciar ejecución continua", command=self.start_continuous).grid(
            row=1, column=0, sticky="ew", pady=3
        )
        ttk.Button(actions, text="Detener", command=self.stop).grid(
            row=2, column=0, sticky="ew", pady=3
        )
        ttk.Label(actions, text="Pausa entre ciclos (s):").grid(
            row=3, column=0, sticky="w", pady=(10, 0)
        )
        ttk.Entry(actions, textvariable=self.interval_var, width=10).grid(
            row=4, column=0, sticky="w"
        )

        display = ttk.Frame(parent)
        display.grid(row=0, column=1, rowspan=2, sticky="nsew")
        display.columnconfigure(0, weight=1)
        display.rowconfigure(1, weight=1)
        self.preview = tk.Canvas(
            display,
            width=720,
            height=360,
            background="#222222",
            highlightthickness=1,
            highlightbackground="#777777",
        )
        self.preview.grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.preview.create_text(
            360,
            180,
            text="Vista de cámara: ejecuta CameraSensor.",
            fill="white",
            tags="placeholder",
        )
        self.preview.bind("<Button-1>", self._calibration_click)
        ttk.Label(
            display,
            text="Calibración: haz clic en las esquinas de la página en orden "
                 "TL, TR, BR, BL.",
        ).grid(row=0, column=0, sticky="sw", padx=8, pady=8)
        output_box = ttk.LabelFrame(display, text="Resultados por plugin y ciclo", padding=6)
        output_box.grid(row=1, column=0, sticky="nsew")
        output_box.rowconfigure(0, weight=1)
        output_box.columnconfigure(0, weight=1)
        self.output = tk.Text(output_box, wrap="word", height=20, state="disabled")
        scrollbar = ttk.Scrollbar(output_box, command=self.output.yview)
        self.output.configure(yscrollcommand=scrollbar.set)
        self.output.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _build_pdf_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)
        settings = ttk.Frame(parent)
        settings.grid(row=0, column=0, sticky="nsw", padx=(0, 16))
        viewer = ttk.LabelFrame(parent, text="Vista previa del PDF", padding=8)
        viewer.grid(row=0, column=1, sticky="nsew")
        viewer.columnconfigure(0, weight=1)
        viewer.rowconfigure(1, weight=1)

        ttk.Label(
            settings,
            text="PDF de destino (usa una copia para pruebas):",
            wraplength=340,
        ).grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(settings, textvariable=self.pdf_path_var, width=42).grid(
            row=1, column=0, sticky="ew", pady=(0, 4)
        )
        ttk.Button(settings, text="Seleccionar PDF", command=self.select_pdf).grid(
            row=2, column=0, sticky="w"
        )
        ttk.Label(settings, text="Página (1-indexada):").grid(
            row=3, column=0, sticky="w", pady=(12, 4)
        )
        page_controls = ttk.Frame(settings)
        page_controls.grid(row=4, column=0, sticky="w")
        ttk.Button(
            page_controls, text="◀", width=3, command=self.previous_pdf_page
        ).grid(row=0, column=0)
        ttk.Entry(page_controls, textvariable=self.page_var, width=7).grid(
            row=0, column=1, padx=5
        )
        ttk.Button(
            page_controls, text="▶", width=3, command=self.next_pdf_page
        ).grid(row=0, column=2)
        ttk.Button(
            settings, text="Actualizar vista previa", command=self.refresh_pdf_preview
        ).grid(row=5, column=0, sticky="w", pady=(5, 0))

        ttk.Label(
            settings,
            text="Esquinas de página en el frame: JSON [TL, TR, BR, BL], "
            "cada punto [x,y] normalizado entre 0 y 1.",
            wraplength=340,
        ).grid(row=6, column=0, sticky="w", pady=(16, 4))
        ttk.Entry(settings, textvariable=self.corner_var, width=42).grid(
            row=7, column=0, sticky="ew"
        )
        ttk.Label(
            settings,
            text="Área del PDF en pantalla para mirada: JSON [x0,y0,x1,y1], "
            "coordenadas normalizadas. Déjalo vacío hasta medir/calibrar.",
            wraplength=340,
        ).grid(row=8, column=0, sticky="w", pady=(12, 4))
        ttk.Entry(settings, textvariable=self.viewport_var, width=42).grid(
            row=9, column=0, sticky="ew"
        )
        ttk.Label(
            settings,
            text=(
                "No uses coordenadas de ejemplo como calibración real. Sin ambos "
                "campos completos no se escribirán highlights. Este panel no modifica "
                "plugins.json: la configuración se aplica solo a la ejecución actual."
            ),
            wraplength=340,
            justify="left",
        ).grid(row=10, column=0, sticky="w", pady=(14, 0))
        ttk.Button(
            settings,
            text="Reiniciar puntos de cámara",
            command=self._reset_calibration_points,
        ).grid(row=11, column=0, sticky="w", pady=(12, 0))
        ttk.Label(
            viewer, text="Selecciona un PDF para mostrar la página."
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.pdf_preview = tk.Canvas(
            viewer,
            width=700,
            height=600,
            background="#555555",
            highlightthickness=0,
        )
        self.pdf_preview.grid(row=1, column=0, sticky="nsew")

    def select_pdf(self) -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar PDF para la prueba",
            filetypes=[("Documentos PDF", "*.pdf"), ("Todos los archivos", "*.*")],
        )
        if path:
            self.pdf_path_var.set(path)
            self.page_var.set("1")
            self.refresh_pdf_preview()

    def refresh_pdf_preview(self) -> None:
        pdf_path = self.pdf_path_var.get().strip()
        if not pdf_path:
            self.pdf_preview.delete("all")
            self._pdf_preview_image = None
            self._pdf_page_count = 0
            self.pdf_preview.create_text(
                350, 300, text="Selecciona un PDF para mostrar la página.",
                fill="white", width=600,
            )
            return
        try:
            page_number = int(self.page_var.get())
            image, self._pdf_page_count = render_pdf_page(pdf_path, page_number)
        except (OSError, ValueError, RuntimeError, pymupdf.FileDataError) as exc:
            self.pdf_preview.delete("all")
            self._pdf_preview_image = None
            self.pdf_preview.create_text(
                350, 300, text=f"No se pudo mostrar el PDF:\n{exc}",
                fill="white", width=620,
            )
            logger.warning("No se pudo renderizar la vista previa del PDF: %s", exc)
            return

        self._pdf_preview_image = ImageTk.PhotoImage(image)
        self.pdf_preview.delete("all")
        self.pdf_preview.create_image(350, 300, image=self._pdf_preview_image)
        self.pdf_preview.create_text(
            8,
            8,
            anchor="nw",
            text=f"Página {page_number} de {self._pdf_page_count}",
            fill="white",
        )

    def previous_pdf_page(self) -> None:
        try:
            page_number = max(1, int(self.page_var.get()) - 1)
        except ValueError:
            page_number = 1
        self.page_var.set(str(page_number))
        self.refresh_pdf_preview()

    def next_pdf_page(self) -> None:
        try:
            page_number = int(self.page_var.get()) + 1
        except ValueError:
            page_number = 1
        self.page_var.set(str(page_number))
        self.refresh_pdf_preview()

    def run_one_cycle(self) -> None:
        self._start_worker(continuous=False)

    def start_continuous(self) -> None:
        self._start_worker(continuous=True)

    def _start_worker(self, continuous: bool) -> None:
        if self.worker is not None and self.worker.is_alive():
            messagebox.showinfo("EDDIE", "Ya hay una ejecución activa.")
            return
        try:
            config = self._build_run_config()
            interval = float(self.interval_var.get())
            if interval < 0:
                raise ValueError("La pausa no puede ser negativa.")
        except (ValueError, json.JSONDecodeError, KeyError) as exc:
            messagebox.showerror("Configuración inválida", str(exc))
            return
        self.stop_event.clear()
        self.status_var.set("Iniciando plugins...")
        self.worker = threading.Thread(
            target=self._run_session,
            args=(config, continuous, interval),
            daemon=True,
        )
        self.worker.start()

    def _build_run_config(self) -> dict:
        config = json.loads(json.dumps(self.config))
        selected = {
            name for name, variable in self.plugin_vars.items() if variable.get()
        }
        by_name = {plugin["name"]: plugin for plugin in config["plugins"]}
        for plugin in config["plugins"]:
            plugin["enabled"] = plugin["name"] in selected

        for consumer_name in ("ImageProcessor", "GesturePlugin"):
            if consumer_name in selected:
                dependencies = by_name[consumer_name].get("dependencies", {})
                camera_name = dependencies.get("camera_sensor")
                if camera_name in by_name:
                    by_name[camera_name]["enabled"] = True

        if "ConsistencyProvider" in by_name:
            consistency = by_name["ConsistencyProvider"].setdefault("config", {})
            pdf_path = self.pdf_path_var.get().strip()
            consistency["pdf_path"] = pdf_path
            page_number = int(self.page_var.get())
            if page_number < 1:
                raise ValueError("La página del PDF debe ser 1 o mayor.")
            consistency["page_number"] = page_number
            corners = self.corner_var.get().strip()
            viewport = self.viewport_var.get().strip()
            if corners or viewport:
                if not corners or not viewport:
                    raise ValueError(
                        "Completa tanto las esquinas de la cámara como el área de mirada."
                    )
                calibration = {
                    "camera_page_corners": json.loads(corners),
                    "gaze_viewport": json.loads(viewport),
                }
                SpatialCalibration.from_config(calibration)
                consistency["spatial_calibration"] = calibration
            else:
                consistency.pop("spatial_calibration", None)

        return config

    def _run_session(self, config: dict, continuous: bool, interval: float) -> None:
        config_path = None
        orchestrator = None
        trace = None
        run_status = "completed"
        try:
            trace = ExecutionTrace(self.project_dir / "traces")
            self.latest_trace = trace.path
            trace.record("configuration", config=redact_sensitive(config))
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".json",
                prefix="eddie-ui-",
                encoding="utf-8",
                delete=False,
            ) as stream:
                json.dump(config, stream, ensure_ascii=False)
                config_path = stream.name
            orchestrator = OrchestratorCore(config_path)
            if not orchestrator.initialize():
                run_status = "initialization_failed"
                trace.record(
                    "initialization",
                    status=run_status,
                    active_plugins=[],
                    plugins=orchestrator.initialization_report,
                )
                self.events.put({
                    "kind": "status",
                    "text": "No se inicializó ningún plugin. Revisa resultados y traza.",
                })
                self.events.put({
                    "kind": "initialization_report",
                    "report": orchestrator.initialization_report,
                })
                return

            active_plugins = [plugin.instance_name for plugin in orchestrator.active_plugins]
            trace.record(
                "initialization",
                status="ok",
                active_plugins=active_plugins,
                plugins=orchestrator.initialization_report,
            )
            self.events.put({
                "kind": "status",
                "text": f"Plugins listos: {', '.join(active_plugins)}",
            })
            self.events.put({
                "kind": "initialization_report",
                "report": orchestrator.initialization_report,
            })
            cycle = 0
            while not self.stop_event.is_set():
                started = time.perf_counter()
                results = orchestrator.execute_cycle()
                cycle += 1
                metrics = orchestrator.last_cycle_metrics
                trace.record_cycle(cycle, results, metrics)
                camera = next(
                    (plugin for plugin in orchestrator.active_plugins
                     if hasattr(plugin, "get_latest_frame")),
                    None,
                )
                frame = camera.get_latest_frame().copy() if camera is not None and camera.get_latest_frame() is not None else None
                self.events.put({
                    "kind": "cycle",
                    "cycle": cycle,
                    "results": json_safe(results),
                    "metrics": metrics,
                    "frame": frame,
                    "trace_path": str(trace.path),
                })
                if not continuous:
                    break
                self.stop_event.wait(max(0.0, interval - (time.perf_counter() - started)))
        except Exception as exc:
            run_status = "error"
            logger.exception("Falló la ejecución desde el panel.")
            if trace is not None:
                trace.record("run_error", error=str(exc))
            self.events.put({"kind": "error", "text": str(exc)})
        finally:
            if orchestrator is not None:
                orchestrator.release()
            if config_path is not None:
                try:
                    os.unlink(config_path)
                except OSError:
                    logger.exception("No se pudo retirar la configuración temporal.")
            if trace is not None:
                trace.close(run_status)
                self.events.put({
                    "kind": "finished",
                    "trace_path": str(trace.path),
                    "status": run_status,
                })

    def stop(self) -> None:
        self.stop_event.set()
        self.status_var.set("Deteniendo después del ciclo actual...")

    def _drain_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                kind = event.get("kind")
                if kind == "status":
                    self.status_var.set(event["text"])
                elif kind == "cycle":
                    self._show_cycle(event)
                elif kind == "initialization_report":
                    self._append_output(
                        "=== INICIALIZACIÓN POR PLUGIN ===\n"
                        f"{json.dumps(event['report'], ensure_ascii=False, indent=2)}\n"
                    )
                elif kind == "error":
                    self.status_var.set(f"Error: {event['text']}")
                    self._append_output(f"ERROR DE EJECUCIÓN: {event['text']}\n")
                elif kind == "finished":
                    self.latest_trace = Path(event["trace_path"])
                    self.trace_var.set(f"Registro: {self.latest_trace}")
                    self.status_var.set(f"Terminado: {event['status']}")
                    self.refresh_pdf_preview()
        except queue.Empty:
            pass
        self.root.after(100, self._drain_events)

    def _show_cycle(self, event: dict) -> None:
        self._append_output(
            f"\n=== CICLO {event['cycle']} ===\n"
            f"{json.dumps(event['results'], ensure_ascii=False, indent=2)}\n"
            f"Latencias: {json.dumps(event['metrics'], ensure_ascii=False)}\n"
        )
        self.latest_trace = Path(event["trace_path"])
        self.trace_var.set(f"Registro: {self.latest_trace}")
        frame = event.get("frame")
        if isinstance(frame, np.ndarray):
            self._camera_frame = frame.copy()
            self._render_preview()

    def _render_preview(self) -> None:
        if self._camera_frame is None:
            return
        height, width = self._camera_frame.shape[:2]
        scale = min(720 / max(width, 1), 340 / max(height, 1), 1.0)
        resized = cv2.resize(
            self._camera_frame,
            (max(1, int(width * scale)), max(1, int(height * scale))),
        )
        display_height, display_width = resized.shape[:2]
        origin_x = (720 - display_width) // 2
        origin_y = (360 - display_height) // 2
        self._camera_frame_size = (width, height)
        self._display_image_bounds = (
            origin_x,
            origin_y,
            origin_x + display_width,
            origin_y + display_height,
        )
        for point_x, point_y in self._calibration_points:
            cv2.circle(
                resized,
                (int(point_x * display_width), int(point_y * display_height)),
                6,
                (0, 0, 255),
                -1,
            )
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        self._preview_image = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.preview.delete("all")
        self.preview.create_image(
            origin_x, origin_y, anchor="nw", image=self._preview_image
        )

    def _select_plugins(self, selected: set[str]) -> None:
        for name, variable in self.plugin_vars.items():
            variable.set(name in selected)

    def _calibration_click(self, event: tk.Event) -> None:
        if self._camera_frame_size is None or self._display_image_bounds is None:
            return
        if len(self._calibration_points) >= 4:
            return
        left, top, right, bottom = self._display_image_bounds
        if not left <= event.x <= right or not top <= event.y <= bottom:
            return
        frame_width, frame_height = self._camera_frame_size
        normalized_x = (event.x - left) / (right - left)
        normalized_y = (event.y - top) / (bottom - top)
        self._calibration_points.append((normalized_x, normalized_y))
        self.corner_var.set(json.dumps(self._calibration_points))
        self._render_preview()
        self._append_output(
            f"Calibración: esquina {len(self._calibration_points)}/4 = "
            f"[{normalized_x:.4f}, {normalized_y:.4f}] "
            f"en frame {frame_width}x{frame_height}.\n"
        )

    def _reset_calibration_points(self) -> None:
        self._calibration_points.clear()
        self.corner_var.set("")
        self._render_preview()
        self._append_output("Calibración de esquinas de cámara reiniciada.\n")

    def _append_output(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def open_trace(self) -> None:
        if self.latest_trace is None or not self.latest_trace.exists():
            messagebox.showinfo("EDDIE", "Todavía no hay un archivo de traza.")
            return
        os.startfile(self.latest_trace)

    def close(self) -> None:
        self.stop_event.set()
        if self.worker is not None and self.worker.is_alive():
            self.status_var.set("Cerrando después de liberar los plugins...")
            self.root.after(100, self._close_when_finished)
            return
        self.root.destroy()

    def _close_when_finished(self) -> None:
        if self.worker is not None and self.worker.is_alive():
            self.root.after(100, self._close_when_finished)
            return
        self.root.destroy()


def launch_dashboard(config_path: str) -> None:
    root = tk.Tk()
    try:
        PluginDashboard(root, config_path)
    except (OSError, ValueError, RuntimeError) as exc:
        messagebox.showerror("No se pudo abrir EDDIE", str(exc))
        root.destroy()
        raise
    root.mainloop()
