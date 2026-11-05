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
M0_REVISION = "a2cc0f67ebd705c55191e25a05ba23d885fcc09b"
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


def _fuente(codigo: str) -> dict:
    if codigo not in ("M0", "M1", "M2", "M3"):
        raise ErrorModelo("Seleccione uno de los modelos M0, M1, M2 o M3.")
    local = os.getenv(f"{codigo}_LOCAL_PATH", "").strip()
    if local:
        if not Path(local).is_dir():
            raise ErrorModelo(f"{codigo}: la carpeta local configurada no está disponible.")
        return {"ruta": local, "local": True, "revision": None, "token": False}
    if codigo == "M0":
        return {"ruta": "pysentimiento/robertuito-sentiment-analysis", "local": False,
                "revision": M0_REVISION, "token": False}
    propietario = os.getenv("HF_MODEL_OWNER", "").strip()
    repo = os.getenv(f"{codigo}_REPO_ID", "").strip()
    if not repo and propietario:
        repo = f"{propietario}/robertuito-bol-{codigo.lower()}"
    if not repo:
        raise ErrorModelo(f"{codigo}: falta configurar el repositorio privado. M0 puede utilizarse por separado.")
    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        raise ErrorModelo(f"{codigo}: falta el Secret HF_TOKEN de lectura. No escriba el token en la caja de texto.")
    revision = os.getenv(f"{codigo}_REVISION", "").strip()
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision.lower()):
        raise ErrorModelo(f"{codigo}: configure la revisión de 40 caracteres del repositorio para fijar la versión.")
    return {"ruta": repo, "local": False, "revision": revision, "token": token}


def estado_modelos() -> list[dict]:
    estados = []
    for codigo in ("M0", "M1", "M2", "M3"):
        try:
            fuente = _fuente(codigo)
            detalle = "Carpeta local configurada." if fuente["local"] else "Repositorio configurado; se carga al primer uso."
            estados.append({"codigo": codigo, "disponible": True, "detalle": detalle})
        except ErrorModelo as exc:
            estados.append({"codigo": codigo, "disponible": False, "detalle": str(exc)})
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
        clave = (codigo, fuente["ruta"], fuente["revision"])
        if clave in _CACHE:
            return _CACHE[clave]
        liberar_cache()
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            from transformers.utils import logging as tf_logging
            tf_logging.set_verbosity_error()
            torch.set_num_threads(max(1, min(4, int(os.getenv("TORCH_NUM_THREADS", "2")))))
            opciones = dict(local_files_only=fuente["local"] or os.getenv("HF_HUB_OFFLINE") == "1",
                            trust_remote_code=False, token=fuente["token"])
            if fuente["revision"]:
                opciones["revision"] = fuente["revision"]
            tokenizer = AutoTokenizer.from_pretrained(fuente["ruta"], **opciones)
            model = AutoModelForSequenceClassification.from_pretrained(
                fuente["ruta"], use_safetensors=True, torch_dtype=torch.float32, **opciones
            ).to("cpu").eval()
            indices_clases(model.config)
            _CACHE[clave] = (tokenizer, model)
            return tokenizer, model
        except ErrorModelo:
            raise
        except Exception:
            raise ErrorModelo(f"{codigo}: no se pudo cargar el modelo. Revise conexión, archivos, permisos y revisión configurada.") from None


def predecir(texto: str, modelo: str = "M3") -> dict:
    validar_texto(texto)
    # Serializar carga e inferencia entre usuarios evita cuatro modelos residentes.
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
