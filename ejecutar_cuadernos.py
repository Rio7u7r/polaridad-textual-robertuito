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
from gestion_modelos import preguntar_modelo


def ejecutar(salida, respuestas=None, entrenar=False):
    if not entrenar:
        if respuestas and any(respuesta != "si" for respuesta in respuestas):
            raise ValueError("Para solicitar modelos nuevos, activa --entrenar.")
        respuestas = ["si", "si", "si"]
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
               "TESIS_PERMITIR_ENTRENAMIENTO": "1" if entrenar else "0"}
    with TemporaryDirectory() as temporal:
        spec = Path(install(prefix=temporal, kernel_name=kernel, display_name="Tesis portátil"))
        gestor = KernelSpecManager(kernel_dirs=[str(spec.parent)])
        for ruta in notebooks:
            if ruta.name[:2] in ("06", "07", "08"):
                modelo = {"06": "M0", "07": "M1", "08": "M2"}[ruta.name[:2]]
                respuesta = respuestas[int(ruta.name[:2]) - 6] if respuestas else None
                cargar = preguntar_modelo(raiz, modelo, respuesta=respuesta, permitir_preparacion=entrenar)
                entorno[f"TESIS_RESPUESTA_{modelo}"] = "si" if cargar else "no"
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
    parser.add_argument("--respuestas", nargs=3, choices=("si", "no"), metavar=("M0", "M1", "M2"))
    parser.add_argument("--entrenar", action="store_true")
    argumentos = parser.parse_args()
    ejecutar(argumentos.salida, argumentos.respuestas, argumentos.entrenar)
