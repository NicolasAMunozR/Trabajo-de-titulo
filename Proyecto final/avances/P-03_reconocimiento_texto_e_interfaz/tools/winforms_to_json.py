# Convierte un archivo *.Designer.cs de WinForms en una descripción JSON del layout.
import json
import re
import sys
from pathlib import Path

DECL = re.compile(r"this\.(\w+)\s*=\s*new\s+([\w\.]+)\(\s*\)\s*;")
ASSIGN = re.compile(r"^\s*this\.(\w+)\.(\w+(?:\.\w+)?)\s*=\s*(.+?);\s*$")
SELF_ASSIGN = re.compile(r"^\s*this\.(\w+)\s*=\s*(.+?);\s*$")
ADD = re.compile(r"this\.(\w+)\.Controls\.Add\(this\.(\w+)\)")
SELF_ADD = re.compile(r"^\s*this\.Controls\.Add\(this\.(\w+)\)")
ITEMS = re.compile(r"this\.(\w+)\.Items\.AddRange\(new object\[\]\s*\{(.*?)\}\);", re.S)
EVENT = re.compile(r"this\.(\w+)\.(\w+)\s*\+=\s*new\s+[\w\.]+\(this\.(\w+)\);")
SELF_EVENT = re.compile(r"^\s*this\.(\w+)\s*\+=\s*new\s+[\w\.]+\(this\.(\w+)\);")
MENU_ITEMS = re.compile(r"this\.(\w+)\.(?:DropDownItems|Items)\.AddRange\(new System\.Windows\.Forms\.ToolStripItem\[\]\s*\{(.*?)\}\);", re.S)

BYTE = re.compile(r"\(\(int\)\(\(\(byte\)\((\d+)\)\)\)\)")


def parse_value(raw: str):
    raw = raw.strip()
    m = re.match(r"new System\.Drawing\.(Point|Size)\((-?\d+),\s*(-?\d+)\)", raw)
    if m:
        return [int(m.group(2)), int(m.group(3))]
    if raw.startswith("System.Drawing.Color.FromArgb"):
        nums = [int(n) for n in BYTE.findall(raw)] or [int(n) for n in re.findall(r"\d+", raw)]
        return "#" + "".join(f"{n:02x}" for n in nums[-3:])
    m = re.match(r"System\.Drawing\.(?:SystemColors|Color)\.(\w+)", raw)
    if m:
        return "@" + m.group(1)
    m = re.match(r'new System\.Drawing\.Font\("([^"]+)",\s*([\d\.]+)F(.*)\)', raw)
    if m:
        style = m.group(3)
        return {"family": m.group(1), "size": float(m.group(2)),
                "bold": "Bold" in style, "italic": "Italic" in style,
                "underline": "Underline" in style}
    m = re.match(r"global::[\w\.]+\.Properties\.Resources\.(\w+)", raw)
    if m:
        return {"resource": m.group(1)}
    m = re.match(r'\(\(System\.Drawing\.(?:Image|Icon)\)\(resources\.GetObject\("([^"]+)"\)\)\)', raw)
    if m:
        return {"resx": m.group(1)}
    if raw.startswith('"') and raw.endswith('"'):
        return bytes(raw[1:-1], "utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8", "ignore")
    if raw in ("true", "false"):
        return raw == "true"
    m = re.match(r"new decimal\(new int\[\]\s*\{\s*(-?\d+),\s*\d+,\s*\d+,\s*(-?\d+)\}\)", raw)
    if m:
        value, flags = int(m.group(1)), int(m.group(2))
        scale = (flags >> 16) & 0xFF
        sign = -1 if flags < 0 else 1
        number = sign * value / (10 ** scale)
        return int(number) if float(number).is_integer() else number
    m = re.match(r"^\(?\(?(?:float|int)?\)?\s*(-?[\d\.]+)D?F?\)?$", raw)
    if m:
        try:
            v = float(m.group(1))
            return int(v) if v.is_integer() else v
        except ValueError:
            pass
    m = re.match(r"System\.Windows\.Forms\.[\w]+\.(\w+)$", raw)
    if m:
        return m.group(1)
    m = re.match(r"\(\(System\.Windows\.Forms\.AnchorStyles\)(.*)\)$", raw)
    if m:
        return re.findall(r"AnchorStyles\.(\w+)", raw)
    if raw.startswith("System.Drawing.ContentAlignment."):
        return raw.rsplit(".", 1)[1]
    return {"raw": raw}


def convert(path: Path) -> dict:
    src = path.read_text(encoding="utf-8-sig", errors="ignore")
    # Une en una línea las constantes decimal multilínea (Maximum/Minimum/Value de NumericUpDown)
    src = re.sub(r"new decimal\(new int\[\]\s*\{([^}]*)\}\)",
                 lambda m: "new decimal(new int[] {" + " ".join(m.group(1).split()) + "})", src)
    controls, order, form = {}, [], {"props": {}, "events": {}, "children": []}
    for name, typ in DECL.findall(src):
        controls[name] = {"name": name, "type": typ.split(".")[-1], "props": {},
                          "children": [], "events": {}, "items": []}
        order.append(name)
    for line in src.splitlines():
        m = ASSIGN.match(line)
        if m and m.group(1) in controls:
            prop, val = m.group(2), m.group(3)
            if prop in ("Name",):
                continue
            controls[m.group(1)]["props"][prop] = parse_value(val)
            continue
        m = SELF_ASSIGN.match(line)
        if m and m.group(1) not in controls:
            form["props"][m.group(1)] = parse_value(m.group(2))
        m = ADD.search(line)
        if m and m.group(1) in controls:
            controls[m.group(1)]["children"].append(m.group(2))
        m = SELF_ADD.match(line)
        if m:
            form["children"].append(m.group(1))
        m = EVENT.search(line)
        if m and m.group(1) in controls:
            controls[m.group(1)]["events"][m.group(2)] = m.group(3)
        m = SELF_EVENT.match(line)
        if m:
            form["events"][m.group(1)] = m.group(2)
    for name, body in ITEMS.findall(src):
        if name in controls:
            controls[name]["items"] = [s for s in re.findall(r'"((?:[^"\\]|\\.)*)"', body)]
    for name, body in MENU_ITEMS.findall(src):
        if name in controls:
            controls[name]["children"].extend(re.findall(r"this\.(\w+)", body))
    for c in controls.values():
        if not c["items"]:
            del c["items"]
        if not c["events"]:
            del c["events"]

    def build(name):
        c = dict(controls[name])
        kids = c.pop("children")
        if kids:
            c["children"] = [build(k) for k in kids if k in controls]
        return c

    roots = [build(n) for n in form["children"] if n in controls]
    attached = set()

    def mark(n):
        attached.add(n["name"])
        for k in n.get("children", []):
            mark(k)
    for r in roots:
        mark(r)
    others = [build(n) for n in order if n not in attached
              and controls[n]["type"] not in ("ToolTip", "Timer", "BackgroundWorker", "ImageList", "ContextMenuStrip")
              and not any(n in controls[p]["children"] for p in controls)]
    return {"form": path.name.split(".")[0], "props": form["props"], "events": form["events"],
            "controls": roots, "detached": others,
            "components": [{"name": n, "type": controls[n]["type"], "props": controls[n]["props"]}
                           for n in order if controls[n]["type"] in ("ToolTip", "Timer", "BackgroundWorker", "ContextMenuStrip")]}


if __name__ == "__main__":
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for p in sys.argv[1].split(","):
        data = convert(Path(p))
        (out / f"{data['form']}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        print("ok", data["form"], len(json.dumps(data)))
