"""
Prototipo F01 Enumeración e Inicialización de Cámaras
Muestra todas las cámaras detectadas, con nombre real si Windows lo puede obtener,
permite elegir una, abre esa cámara en vivo durante 8 segundos y guarda el frame.

Presiona Q para salir antes de los 8 segundos.
"""

import cv2
import pathlib
import subprocess
import sys
import time

EVID = pathlib.Path(__file__).resolve().parent / "evidencias" / "real"
EVID.mkdir(parents=True, exist_ok=True)


def get_windows_camera_names():
    """Intenta obtener nombres reales de cámaras en Windows usando PowerShell."""
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_PnPEntity | Where-Object {$_.PNPClass -eq 'Camera'} | Select-Object -ExpandProperty Name"
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []

        names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return names
    except Exception:
        return []


def detect_cameras(max_index=10):
    backends = []

    if hasattr(cv2, "CAP_MSMF"):
        backends.append((cv2.CAP_MSMF, "MSMF"))

    backends.append((cv2.CAP_ANY, "ANY"))

    device_names = get_windows_camera_names()

    cameras = []
    for idx in range(max_index):
        for backend, bname in backends:
            try:
                cap = cv2.VideoCapture(idx, backend)
                if not cap.isOpened():
                    cap.release()
                    continue

                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)

                friendly = device_names[idx] if idx < len(device_names) else f"Cámara {idx}"
                cameras.append({
                    "idx": idx,
                    "backend": bname,
                    "w": w,
                    "h": h,
                    "fps": fps,
                    "name": friendly,
                    "cap": cap,
                })

                print(f"  [+] idx={idx} backend={bname}  {w}x{h} @ {fps:.0f} FPS  | nombre={friendly}")
                break

            except Exception:
                pass

    return cameras


def choose_camera(cameras):
    if not cameras:
        print("No se encontró ninguna cámara. Asegúrate de que esté activa.")
        sys.exit(1)

    print("\nCámaras detectadas:")
    for i, cam in enumerate(cameras, start=1):
        print(
            f"  [{i}] idx={cam['idx']} | nombre={cam['name']} | backend={cam['backend']} | "
            f"{cam['w']}x{cam['h']} | {cam['fps']:.0f} FPS"
        )

    while True:
        raw = input(f"\nElige una cámara (1-{len(cameras)}) o 0 para salir: ").strip()

        if raw == "0":
            print("No se seleccionó ninguna cámara.")
            sys.exit(0)

        try:
            option = int(raw)
        except ValueError:
            print("Entrada inválida. Debes escribir un número.")
            continue

        if 1 <= option <= len(cameras):
            return cameras[option - 1]

        print(f"Debes elegir un número entre 1 y {len(cameras)}.")


cameras = detect_cameras()

cam = choose_camera(cameras)
cap = cam["cap"]
saved = None

print(f"\nCámara seleccionada: idx={cam['idx']} | nombre={cam['name']} | ({cam['w']}x{cam['h']})")
print("Presiona  Q  para cerrar | S  para guardar frame ahora\n")

t_start = time.time()
DURATION = 8

while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo leer frame.")
        break

    elapsed = time.time() - t_start
    remaining = max(0, DURATION - elapsed)

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], 50), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    cv2.putText(
        frame,
        f"F01 | idx={cam['idx']} {cam['w']}x{cam['h']} {cam['fps']:.0f}fps",
        (8, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 220, 100),
        1,
    )
    cv2.putText(
        frame,
        f"Nombre: {cam['name']} | Backend: {cam['backend']} | Cierra en {remaining:.1f}s (Q=salir S=guardar)",
        (8, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (200, 200, 200),
        1,
    )

    cv2.imshow("F01 Camara en VIVO", frame)

    key = cv2.waitKey(30) & 0xFF
    if key == ord('q') or key == 27:
        break

    if key == ord('s') or elapsed >= DURATION:
        out = EVID / f"f01_camera.png"
        cv2.imwrite(str(out), frame)
        saved = out
        print(f"  [GUARDADO] {out}")
        if elapsed >= DURATION:
            break

cap.release()
cv2.destroyAllWindows()

if saved:
    print(f"\nEvidencia guardada: {saved}")
else:
    print("\nNo se guardó frame (cerraste antes).")

print("F01 COMPLETADO\n")