"""Rutas del paquete portátil."""
import os
from pathlib import Path


def carpeta_salidas(raiz):
    ruta = os.environ.get("TESIS_SALIDAS")
    return Path(ruta) if ruta else raiz / "salidas/manual"
