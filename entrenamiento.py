"""Carga y ajuste supervisado de RoBERTuito para la copia experimental."""

import hashlib
import json
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from shutil import copytree

import pandas as pd
import torch
from datasets import Dataset
from pysentimiento.preprocessing import preprocess_tweet
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
    set_seed,
)

BASE = "pysentimiento/robertuito-sentiment-analysis"
REVISION = "a2cc0f67ebd705c55191e25a05ba23d885fcc09b"
CLASES = {0: "NEG", 1: "NEU", 2: "POS"}
BOLIVIA = {"negativa": 0, "neutral": 1, "positiva": 2}
PERU = {"negative": 0, "neutral": 1, "positive": 2}
SEMILLA = 42
MAX_TOKENS = 128


def sha256(ruta):
    with ruta.open("rb") as archivo:
        return hashlib.file_digest(archivo, "sha256").hexdigest()


def preparar_texto(texto):
    return preprocess_tweet(texto, lang="es")


def guardar(modelo, tokenizer, destino, evidencia, *, historial=None):
    destino.parent.mkdir(parents=True, exist_ok=True)
    evidencia["versiones"] = {
        paquete: version(paquete)
        for paquete in ("torch", "transformers", "datasets", "accelerate", "pysentimiento")
    }
    with TemporaryDirectory(dir=destino.parent) as carpeta:
        temporal = Path(carpeta) / destino.name
        modelo.save_pretrained(temporal)
        tokenizer.save_pretrained(temporal)
        if historial is not None:
            perdidas = [
                {"paso": registro["step"], "epoca": registro["epoch"], "perdida": registro["loss"]}
                for registro in historial if "loss" in registro
            ]
            pd.DataFrame(perdidas, columns=["paso", "epoca", "perdida"]).to_csv(
                temporal / "perdida_entrenamiento.csv", index=False
            )
        evidencia["artefactos_sha256"] = {
            archivo.name: sha256(archivo) for archivo in sorted(temporal.iterdir())
        }
        (temporal / "ejecucion.json").write_text(
            json.dumps(evidencia, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporal.rename(destino)
    print(f"Guardado: {destino}")


def cargar_modelo(origen):
    modelo = AutoModelForSequenceClassification.from_pretrained(origen, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(origen, local_files_only=True)
    if modelo.config.id2label != CLASES:
        raise ValueError(f"Correspondencia de clases inesperada: {modelo.config.id2label}")
    return modelo, tokenizer


def preparar_m0(destino):
    if destino.exists():
        raise FileExistsError(destino)
    origen = destino.parents[1] / "corrida_03_epocas/M0"
    if not (origen / "ejecucion.json").is_file():
        from huggingface_hub import snapshot_download

        publicado = Path(snapshot_download(
            BASE, revision=REVISION, token=False,
            allow_patterns=["config.json", "model.safetensors", "tokenizer.json",
                            "tokenizer_config.json", "special_tokens_map.json"],
        ))
        modelo, tokenizer = cargar_modelo(publicado)
        guardar(modelo, tokenizer, destino, {
            "modelo": "M0",
            "operacion": "copia del clasificador publicado, sin ajuste local",
            "origen": BASE,
            "revision": REVISION,
            "pesos_origen_sha256": sha256(publicado / "model.safetensors"),
            "clases": CLASES,
            "preprocesador": "preprocess_tweet(lang='es')",
            "pasos_optimizacion": 0,
        })
        return
    registro = json.loads((origen / "ejecucion.json").read_text(encoding="utf-8"))
    if registro["modelo"] != "M0" or registro["revision"] != REVISION or any(
        sha256(origen / nombre) != huella
        for nombre, huella in registro["artefactos_sha256"].items()
    ):
        raise ValueError("El modelo M0 incluido no coincide con la versión registrada.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destino.parent) as carpeta:
        copia = Path(carpeta) / "M0"
        copytree(origen, copia)
        copia.rename(destino)
    print(f"Guardado: {destino}")


def leer_peru(raiz):
    ruta = raiz / "insumos/smps_train.parquet"
    datos = pd.read_parquet(ruta)
    etiquetas = datos["label_name"].map(PERU)
    if etiquetas.isna().any() or not etiquetas.eq(datos["label"]).all():
        raise ValueError("Las etiquetas de SMPS no coinciden con su codificación publicada.")
    return datos.rename(columns={"text": "texto", "label": "labels"}), {
        "corpus": "pyupeu/social-media-peruvian-sentiment",
        "revision": "29c842ea9e189e5865925ac0ef6cb01b1388f4b6",
        "particion": "train",
        "archivo": ruta.relative_to(raiz).as_posix(),
        "sha256": sha256(ruta),
    }


def leer_bolivia(raiz, *, anotacion=None):
    if anotacion is None:
        anotacion = raiz / "TABLAS/06_clasificacion/clasificacion_asistida_v5_etiquetada.xlsx"
    particion = raiz / "insumos/particion_boliviana.xlsx"
    campos = ["id", "fuente", "texto_procesado", "etiqueta_humana"]
    humanos = pd.read_excel(anotacion, sheet_name="clasificacion", usecols=campos)
    divisiones = pd.read_excel(particion)
    if any(tabla["id"].isna().any() or not tabla["id"].is_unique for tabla in (humanos, divisiones)):
        raise ValueError("Hay identificadores vacíos o repetidos en el corpus boliviano.")
    if set(divisiones["particion"]) != {"entrenamiento", "validacion"}:
        raise ValueError("La partición boliviana contiene roles inesperados.")
    if divisiones["grupo_dependencia"].isna().any() or (
        divisiones.groupby("grupo_dependencia")["particion"].nunique().gt(1).any()
    ):
        raise ValueError("Hay grupos de publicaciones sin asignar o compartidos entre particiones.")
    if not set(humanos["etiqueta_humana"]) <= {*BOLIVIA, "inválida"}:
        raise ValueError("Hay etiquetas humanas ausentes o desconocidas.")
    validos = humanos.loc[humanos["etiqueta_humana"].isin(BOLIVIA), campos].set_index("id")
    registrados = divisiones.set_index("id")
    if set(validos.index) != set(registrados.index) or not validos.equals(
        registrados.loc[validos.index, validos.columns]
    ):
        raise ValueError("La partición no coincide con los textos y las etiquetas humanas.")
    entrenamiento = divisiones.loc[divisiones["particion"].eq("entrenamiento")].copy()
    entrenamiento["labels"] = entrenamiento["etiqueta_humana"].map(BOLIVIA)
    return entrenamiento.rename(columns={"texto_procesado": "texto"}), {
        "corpus": "Bolivia, anotación humana v5 de Telegram y Facebook",
        "particion": "entrenamiento",
        "archivos_sha256": {
            ruta.relative_to(raiz).as_posix(): sha256(ruta)
            for ruta in (anotacion, particion)
        },
        "excluidos_etiqueta_invalida": len(humanos) - len(validos),
        "reservados_validacion": len(divisiones) - len(entrenamiento),
    }


def codificar(datos, tokenizer):
    if datos["texto"].isna().any() or set(datos["labels"]) != set(CLASES):
        raise ValueError("Se requieren textos y ejemplos de las tres clases.")
    textos = datos["texto"].map(preparar_texto)
    if textos.str.strip().eq("").any():
        raise ValueError("El preprocesador produjo textos vacíos.")
    largos = tokenizer(textos.tolist(), return_length=True, verbose=False)["length"]
    tokens = tokenizer(textos.tolist(), truncation=True, max_length=MAX_TOKENS)
    dataset = Dataset.from_dict({**dict(tokens), "labels": datos["labels"].tolist()})
    return dataset, {
        "filas": len(dataset),
        "por_clase": {
            CLASES[clase]: int(cantidad)
            for clase, cantidad in datos["labels"].value_counts().items()
        },
        "repeticiones_texto_antes": int(datos["texto"].duplicated().sum()),
        "repeticiones_texto_preparado": int(textos.duplicated().sum()),
        "filas_truncadas": sum(longitud > MAX_TOKENS for longitud in largos),
    }


def ajustar(nombre, origen, destino, datos, evidencia, *, epocas, permitir=False):
    if not permitir:
        raise RuntimeError("El entrenamiento requiere activar ENTRENAR_MODELO explícitamente.")
    if destino.exists():
        raise FileExistsError(destino)
    if not torch.cuda.is_available():
        raise RuntimeError("Activa una GPU CUDA para ajustar RoBERTuito.")
    entrada = json.loads((origen / "ejecucion.json").read_text(encoding="utf-8"))
    antecesor = {"M1": "M0", "M2": "M1"}[nombre]
    if entrada["modelo"] != antecesor or any(
        sha256(origen / archivo) != huella
        for archivo, huella in entrada["artefactos_sha256"].items()
    ):
        raise ValueError(f"El ajuste requiere la salida verificada de {antecesor}.")
    set_seed(SEMILLA)
    modelo, tokenizer = cargar_modelo(origen)
    dataset, recuentos = codificar(datos, tokenizer)
    print(f"{nombre} | {len(dataset)} registros | {torch.cuda.get_device_name()} | {epocas} épocas")
    with TemporaryDirectory() as temporal:
        argumentos = TrainingArguments(
            output_dir=temporal,
            seed=SEMILLA,
            data_seed=SEMILLA,
            num_train_epochs=epocas,
            per_device_train_batch_size=16,
            learning_rate=2e-5,
            group_by_length=True,
            bf16=torch.cuda.is_bf16_supported(),
            eval_strategy="no",
            save_strategy="no",
            logging_steps=50,
            disable_tqdm=True,
            report_to=[],
        )
        entrenador = Trainer(
            model=modelo,
            args=argumentos,
            train_dataset=dataset,
            data_collator=DataCollatorWithPadding(tokenizer, pad_to_multiple_of=8),
            processing_class=tokenizer,
        )
        resultado = entrenador.train()
        guardar(modelo, tokenizer, destino, {
            "modelo": nombre,
            "operacion": "ajuste supervisado",
            "inicializacion": antecesor,
            "pesos_origen_sha256": entrada["artefactos_sha256"]["model.safetensors"],
            "datos": {**evidencia, **recuentos},
            "clases": CLASES,
            "preprocesador": "preprocess_tweet(lang='es')",
            "max_tokens": MAX_TOKENS,
            "semilla": SEMILLA,
            "gpu": torch.cuda.get_device_name(),
            "bf16": argumentos.bf16,
            "epocas": argumentos.num_train_epochs,
            "lote": argumentos.per_device_train_batch_size,
            "tasa_aprendizaje": argumentos.learning_rate,
            "optimizador": argumentos.optim.value,
            "programador": argumentos.lr_scheduler_type.value,
            "orden_por_longitud": argumentos.group_by_length,
            "funcion_perdida": "entropía cruzada sin ponderar",
            "pasos_optimizacion": resultado.global_step,
            "segundos_entrenamiento": resultado.metrics["train_runtime"],
        }, historial=entrenador.state.log_history)
