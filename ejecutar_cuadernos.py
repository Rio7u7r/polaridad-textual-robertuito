"""Ejecuta la secuencia 00–09 con un registro de salida por ejecución."""
import argparse
from datetime import datetime
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import nbformat
from ipykernel.kernelspec import install
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager


def ejecutar(salida):
    raiz = Path(__file__).resolve().parent
    salida = salida or raiz / "salidas" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    salida = salida.resolve()
    if not salida.is_relative_to(raiz / "salidas"):
        raise ValueError("Guarda la ejecución dentro de la carpeta salidas del proyecto.")
    ejecuciones = salida / "cuadernos"
    ejecuciones.mkdir(parents=True, exist_ok=False)
    notebooks = sorted(raiz.glob("0[0-9]_*.ipynb"))
    if [p.name[:2] for p in notebooks] != [f"{n:02}" for n in range(10)]:
        raise RuntimeError("La carpeta debe contener una copia de cada cuaderno 00–09.")

    kernel = "tesis-portatil"
    entorno = {**os.environ, "TESIS_SALIDAS": str(salida),
               "PYTHONDONTWRITEBYTECODE": "1", "TOKENIZERS_PARALLELISM": "false",
               "HF_HUB_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1"}
    with TemporaryDirectory() as temporal:
        spec = Path(install(prefix=temporal, kernel_name=kernel, display_name="Tesis portátil"))
        gestor = KernelSpecManager(kernel_dirs=[str(spec.parent)])
        for ruta in notebooks:
            print(f"Ejecutando {ruta.name}", flush=True)
            cuaderno = nbformat.read(ruta, as_version=4)
            try:
                km = KernelManager(kernel_name=kernel, kernel_spec_manager=gestor)
                NotebookClient(cuaderno, km=km, timeout=7200,
                               resources={"metadata": {"path": str(raiz)}}).execute(env=entorno, cleanup_kc=True)
            finally:
                nbformat.write(cuaderno, ejecuciones / ruta.name)
    print(f"Salidas guardadas en {salida}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--salida", type=Path)
    ejecutar(parser.parse_args().salida)
