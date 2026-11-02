"""Extrae las imágenes embebidas (base64) de los archivos .resx de WinForms."""
import base64
import re
import sys
from pathlib import Path

PATTERN = re.compile(
    r'<data name="([^"]+)"[^>]*mimetype="application/x-microsoft\.net\.object\.bytearray\.base64"[^>]*>\s*<value>(.*?)</value>',
    re.S,
)


def extract(resx: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    form = resx.stem
    for name, payload in PATTERN.findall(resx.read_text(encoding="utf-8-sig")):
        raw = base64.b64decode("".join(payload.split()))
        ext = ".gif" if raw[:3] == b"GIF" else ".png" if raw[:4] == b"\x89PNG" else ".bmp" if raw[:2] == b"BM" else ".bin"
        target = out_dir / f"{form}.{name.replace('.Image', '')}{ext}"
        target.write_bytes(raw)
        written.append(target)
    return written


if __name__ == "__main__":
    for path in sys.argv[2:]:
        for item in extract(Path(path), Path(sys.argv[1])):
            print(item.name, item.stat().st_size)
