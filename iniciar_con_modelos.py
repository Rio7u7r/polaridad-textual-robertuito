"""Inicia la aplicación con los pesos descargados mediante Git LFS."""
import os
from pathlib import Path

root = Path(__file__).resolve().parent / "modelos"
for model in ("M0", "M1", "M2", "M3"):
    directory = root / model
    weights = directory / "model.safetensors"
    if not weights.is_file() or weights.stat().st_size < 1024:
        raise SystemExit(f"Faltan los pesos de {model}. Ejecuta git lfs pull en el repositorio.")
    os.environ.setdefault(f"{model}_LOCAL_PATH", str(directory))

os.environ.setdefault("DEFAULT_MODEL", "M1")

if __name__ == "__main__":
    from app import iniciar
    iniciar()
