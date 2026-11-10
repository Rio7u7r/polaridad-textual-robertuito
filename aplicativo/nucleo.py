"""Inferencia CPU con el protocolo de 08 (fuente identificada en PROTOCOLO.md).

No escribe entradas, resultados ni excepciones de las bibliotecas en archivos.
La caché contiene exclusivamente pesos y tokenizadores; nunca textos.
"""
from __future__ import annotations

import gc
import hashlib
import json
import os
import threading
import time
from collections import OrderedDict
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")

CLASES = ("NEG", "NEU", "POS")
NOMBRES = {"NEG": "negativa", "NEU": "neutral", "POS": "positiva"}
MAX_CARACTERES = 2000
MAX_LENGTH = 128
STRIDE = 32
MODELOS = ("M2",) if os.getenv("TESIS_VARIANTE") == "m2" else ("M0", "M1", "M2")
RAIZ = Path(__file__).resolve().parent.parent
_CACHE: OrderedDict = OrderedDict()
_LOCK = threading.RLock()


class ErrorModelo(RuntimeError):
    """Mensaje público sin contenido de la entrada ni credenciales."""


def validar_texto(texto: str) -> str:
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("Escriba un texto antes de clasificar.")
    if len(texto) > MAX_CARACTERES:
        raise ValueError("El texto supera el límite de 2.000 caracteres. Acórtelo e intente de nuevo.")
    # No recortar silenciosamente: preprocess_tweet es la transformación de referencia.
    return texto


def corrida_actual():
    return json.loads((RAIZ / "corrida.json").read_text(encoding="utf-8"))["corrida"]


def _fuente(codigo):
    if codigo not in MODELOS:
        raise ErrorModelo("El modelo seleccionado no está disponible en esta edición.")
    ruta = RAIZ / "modelos" / corrida_actual() / codigo
    if not (ruta / "ejecucion.json").is_file():
        raise ErrorModelo(f"{codigo}: todavía faltan los pesos de la corrida elegida.")
    return ruta


def estado_modelos():
    estados = []
    for codigo in MODELOS:
        try:
            _fuente(codigo)
            estados.append({"codigo": codigo, "disponible": True})
        except ErrorModelo:
            estados.append({"codigo": codigo, "disponible": False})
    return estados

def indices_clases(config) -> dict[str, int]:
    aliases = {"NEG": "NEG", "NEGATIVA": "NEG", "NEGATIVE": "NEG",
               "NEU": "NEU", "NEUTRAL": "NEU", "POS": "POS",
               "POSITIVA": "POS", "POSITIVE": "POS"}
    salida = {}
    for indice, etiqueta in config.id2label.items():
        clase = aliases.get(str(etiqueta).upper())
        if clase is None or clase in salida:
            raise ErrorModelo("El modelo no contiene un mapa de clases NEG/NEU/POS inequívoco.")
        salida[clase] = int(indice)
    if set(salida) != set(CLASES) or set(salida.values()) != {0, 1, 2}:
        raise ErrorModelo("El modelo debe tener exactamente tres clases NEG/NEU/POS.")
    return salida


def liberar_cache() -> None:
    with _LOCK:
        _CACHE.clear()
        gc.collect()


def cargar_modelo(codigo: str):
    """Carga perezosa, un único modelo residente; comparaciones secuenciales."""
    with _LOCK:
        fuente = _fuente(codigo)
        # No conservar un secreto en la clave de la caché.
        clave = (fuente, (fuente / "model.safetensors").stat().st_mtime_ns)
        if clave in _CACHE:
            return _CACHE[clave]
        liberar_cache()
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            from transformers.utils import logging as tf_logging
            tf_logging.set_verbosity_error()
            torch.set_num_threads(max(1, min(4, int(os.getenv("TORCH_NUM_THREADS", "2")))))
            registro = json.loads((fuente / "ejecucion.json").read_text(encoding="utf-8"))
            if registro["modelo"] != codigo or any(
                huella_archivo(fuente / nombre) != huella
                for nombre, huella in registro["artefactos_sha256"].items()
            ):
                raise ErrorModelo(f"{codigo}: los archivos locales difieren de su registro.")
            opciones = dict(local_files_only=True, trust_remote_code=False, token=False)
            tokenizer = AutoTokenizer.from_pretrained(fuente, **opciones)
            model = AutoModelForSequenceClassification.from_pretrained(
                fuente, use_safetensors=True, torch_dtype=torch.float32, **opciones
            ).to("cpu").eval()
            indices_clases(model.config)
            _CACHE[clave] = (tokenizer, model)
            return tokenizer, model
        except ErrorModelo:
            raise
        except Exception:
            raise ErrorModelo(f"{codigo}: no se pudo cargar el modelo. Revise conexión, archivos, permisos y revisión configurada.") from None


def predecir(texto: str, modelo: str = "M2") -> dict:
    validar_texto(texto)
    # Serializar carga e inferencia entre usuarios evita tres modelos residentes.
    with _LOCK:
        inicio_carga = time.perf_counter()
        tokenizer, red = cargar_modelo(modelo)
        carga = time.perf_counter() - inicio_carga
        inicio = time.perf_counter()
        try:
            import torch
            from pysentimiento.preprocessing import preprocess_tweet
            mapa = indices_clases(red.config)
            preparado = preprocess_tweet(texto, lang="es")
            lote = tokenizer(preparado, return_tensors="pt", truncation=True,
                             max_length=MAX_LENGTH, stride=STRIDE,
                             return_overflowing_tokens=True, padding=True)
            lote.pop("overflow_to_sample_mapping", None)
            lote = {k: v.to("cpu") for k, v in lote.items()}
            with torch.inference_mode():
                tramos = torch.softmax(red(**lote).logits, dim=-1)
                promedio = tramos.mean(dim=0)
            probs = {c: float(promedio[mapa[c]].item()) * 100 for c in CLASES}
            filas = [{c: float(fila[mapa[c]].item()) * 100 for c in CLASES} for fila in tramos]
            ganador = max(CLASES, key=lambda c: probs[c])
            return {"modelo": modelo, "etiqueta": NOMBRES[ganador], "porcentajes": probs,
                    "n_tramos": len(filas), "porcentajes_por_tramo": filas,
                    "segundos": time.perf_counter() - inicio, "carga_segundos": carga,
                    "dispositivo": "cpu", "dtype": "float32"}
        except ErrorModelo:
            raise
        except Exception:
            raise ErrorModelo("No se pudo analizar el texto. Intente nuevamente con un texto más corto.") from None


def huella_archivo(ruta: str | Path) -> str:
    """Solo para auditar archivos de modelo; no recibe textos de la interfaz."""
    sha = hashlib.sha256()
    with Path(ruta).open("rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(bloque)
    return sha.hexdigest()
