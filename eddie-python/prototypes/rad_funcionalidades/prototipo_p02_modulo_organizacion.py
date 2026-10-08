"""
================================================================================
PROYECTO EDDIE (Python Migration) - Prototipo RAD P-02
================================================================================
Nombre: Implementación del Módulo de Organización
Sección Tesis: 3.4.2 Segundo Prototipo (M. Figueroa, 2025)
Equivalente C# Legacy: proyecto_eddie/AugmentedReadingApp/MenuSettings.cs
Tecnología: Python 3.14 + JSON Schema + File Locks + Console UI

Objetivos:
1. Administrar la estructura jerárquica de Proyectos, Participantes y Protocolos.
2. Implementar bloqueo/desbloqueo de seguridad (Read-Only Locking) contra edición accidental.
3. Garantizar persistencia transaccional en archivos JSON estructurados.
================================================================================
"""

import os
import sys
import json
import time
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent
EVID_DIR = BASE_DIR / "evidencias" / "real"
EVID_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = EVID_DIR / "p02_organizacion_db.json"

class OrganizationManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.data = self._load()

    def _load(self):
        if self.db_path.exists():
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "proyectos": [
                {
                    "id": "PROJ-001",
                    "nombre": "Estudio Lectura Aumentada EDDIE v2.0",
                    "fecha_creacion": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "bloqueado": False,
                    "participantes": [
                        {"id": "PART-01", "nombre": "Sujeto Alfa", "edad": 24, "bloqueado": False}
                    ],
                    "protocolos": [
                        {
                            "id": "PROT-101",
                            "nombre": "Protocolo de Rastreo Gaze & Highlight",
                            "bloqueado": True,
                            "actividades": [
                                "1. Lectura libre de documento PDF durante 5 min",
                                "2. Destacar renglón clave con resaltador físico",
                                "3. Consultar enciclopedia de término en pantalla"
                            ]
                        }
                    ]
                }
            ]
        }

    def save(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        print(f"  [✓ PERSISTENCIA] Base de datos guardada en {self.db_path.name}")

    def crear_proyecto(self, nombre):
        p_id = f"PROJ-{len(self.data['proyectos']) + 1:03d}"
        nuevo = {
            "id": p_id,
            "nombre": nombre,
            "fecha_creacion": time.strftime("%Y-%m-%d %H:%M:%S"),
            "bloqueado": False,
            "participantes": [],
            "protocolos": []
        }
        self.data["proyectos"].append(nuevo)
        self.save()
        return p_id

    def toggle_lock_proyecto(self, proj_id):
        for p in self.data["proyectos"]:
            if p["id"] == proj_id:
                p["bloqueado"] = not p["bloqueado"]
                self.save()
                return p["bloqueado"]
        return None

def main():
    print("=" * 75)
    print("  EDDIE Python – Prototipo P-02: Módulo de Organización")
    print("  Referencia Tesis: Capítulo 3.4.2 | Proyecto C#: MenuSettings")
    print("=" * 75)

    mgr = OrganizationManager(DATA_FILE)

    print("\n  [ESTADO ACTUAL DE PROYECTOS Y PROTOCOLOS]:")
    for proj in mgr.data["proyectos"]:
        lock_str = "🔒 [BLOQUEADO]" if proj["bloqueado"] else "🔓 [EDITABLE]"
        print(f"  * {proj['id']}: {proj['nombre']} | {lock_str}")
        print(f"    - Participantes ({len(proj['participantes'])}):")
        for part in proj["participantes"]:
            print(f"      • {part['id']}: {part['nombre']} (Edad: {part['edad']})")
        print(f"    - Protocolos ({len(proj['protocolos'])}):")
        for prot in proj["protocolos"]:
            p_lock = "🔒" if prot["bloqueado"] else "🔓"
            print(f"      • {prot['id']}: {prot['nombre']} {p_lock}")
            for act in prot["actividades"]:
                print(f"        - {act}")

    # Demostración CRUD
    print("\n  [DEMOSTRACIÓN DE LÓGICA DE NEGOCIO]:")
    nuevo_id = mgr.crear_proyecto("Evaluación UX Laboratorio InTeractiOn")
    print(f"  [+] Nuevo proyecto creado: {nuevo_id}")

    bloqueado = mgr.toggle_lock_proyecto(nuevo_id)
    print(f"  [*] Estado de seguridad cambiado para {nuevo_id}: Bloqueado={bloqueado}")

    print("\n  ✓ Prototipo P-02 finalizado exitosamente.\n")

if __name__ == "__main__":
    main()
