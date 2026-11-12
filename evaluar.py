"""Evaluación de los modelos guardados en la partición boliviana de 454 filas."""

import json
from shutil import copyfile

import pandas as pd
import torch
from IPython.display import HTML, display
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from entrenamiento import BOLIVIA, MAX_TOKENS, cargar_modelo, preparar_texto, sha256


CLASES = list(BOLIVIA)
SOLAPAMIENTO = 32
FUENTE = "Partición boliviana de 454 publicaciones con etiqueta humana, corrida experimental."


def leer_particion(ruta):
    datos = pd.read_excel(ruta)
    ajuste = datos.loc[datos["particion"].eq("entrenamiento")]
    prueba = datos.loc[datos["particion"].eq("validacion")].copy()
    if len(ajuste) != 1809 or len(prueba) != 454 or not datos["id"].is_unique:
        raise ValueError("Se esperaba la partición histórica de 1.809 y 454 identificadores únicos.")
    if set(ajuste["grupo_dependencia"]) & set(prueba["grupo_dependencia"]):
        raise ValueError("Hay grupos de publicaciones compartidos entre ajuste y evaluación.")
    if prueba["texto_procesado"].isna().any() or set(prueba["etiqueta_humana"]) != set(CLASES):
        raise ValueError("Faltan textos o la etiqueta humana no coincide con las tres clases.")
    return prueba


@torch.inference_mode()
def predecir(textos, modelo, tokenizer, dispositivo):
    """Una predicción por publicación, aunque esta contenga varios tramos."""
    predicciones = []
    for texto in textos:
        entradas = tokenizer(
            preparar_texto(texto),
            max_length=MAX_TOKENS,
            stride=SOLAPAMIENTO,
            truncation=True,
            return_overflowing_tokens=True,
            padding=True,
            return_tensors="pt",
        )
        numero_tramos = len(entradas.pop("overflow_to_sample_mapping"))
        logits = modelo(**entradas.to(dispositivo)).logits
        probabilidades = logits.softmax(dim=-1).mean(dim=0)
        predicciones.append((CLASES[probabilidades.argmax().item()], numero_tramos))
    return predicciones


def evaluar_modelo(raiz, corrida, nombre, *, directorio_evaluacion=None, recalcular=False):
    particion = raiz / "insumos/particion_boliviana.xlsx"
    carpeta = raiz / "modelos" / corrida / nombre
    manifiesto = json.loads((carpeta / "ejecucion.json").read_text(encoding="utf-8"))
    huellas = manifiesto["artefactos_sha256"]
    if manifiesto["modelo"] != nombre or any(
        sha256(carpeta / archivo) != huella for archivo, huella in huellas.items()
    ):
        raise ValueError(f"Los archivos guardados no coinciden con el manifiesto de {nombre}.")

    prueba = leer_particion(particion)
    if not recalcular:
        archivo = raiz / "evaluacion" / corrida / f"{nombre}.json"
        if not archivo.is_file():
            raise FileNotFoundError(f"Falta la evaluación guardada de {nombre}. Restaura la copia o activa RECALCULAR_EVALUACION.")
        evidencia = json.loads(archivo.read_text(encoding="utf-8"))
        if (evidencia["modelo"], evidencia["corrida"], evidencia["subconjunto"],
            evidencia["pesos_sha256"], evidencia["particion_sha256"],
            evidencia["max_tokens"], evidencia["solapamiento"]) != (
                nombre, corrida, "validacion", huellas["model.safetensors"], sha256(particion),
                MAX_TOKENS, SOLAPAMIENTO):
            raise ValueError(f"La evaluación guardada de {nombre} difiere de esta corrida.")
        filas = pd.DataFrame(evidencia["predicciones"])
        referencia = prueba.set_index("id")["etiqueta_humana"].sort_index()
        if (not filas["id"].is_unique or
            not filas.set_index("id")["referencia"].sort_index().equals(referencia) or
            not set(filas["prediccion"]) <= set(CLASES)):
            raise ValueError(f"Las referencias guardadas de {nombre} difieren de la partición.")
        salida = (directorio_evaluacion or raiz / "evaluacion") / corrida / f"{nombre}.json"
        if salida.resolve() != archivo.resolve():
            salida.parent.mkdir(parents=True, exist_ok=True)
            copyfile(archivo, salida)
        print(f"{nombre}: se reutilizan las {len(filas)} predicciones de evaluación guardadas.")
        return filas
    dispositivo = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    modelo, tokenizer = cargar_modelo(carpeta)
    modelo.to(dispositivo).eval()
    resultados = predecir(prueba["texto_procesado"], modelo, tokenizer, dispositivo)

    filas = prueba[["id", "etiqueta_humana"]].rename(columns={"etiqueta_humana": "referencia"})
    filas[["prediccion", "tramos"]] = resultados
    if directorio_evaluacion is None:
        directorio_evaluacion = raiz / "evaluacion"
    destino = directorio_evaluacion / corrida / f"{nombre}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    evidencia = {
        "modelo": nombre,
        "corrida": corrida,
        "pesos_sha256": huellas["model.safetensors"],
        "particion_sha256": sha256(particion),
        "subconjunto": "validacion",
        "max_tokens": MAX_TOKENS,
        "solapamiento": SOLAPAMIENTO,
        "agregacion": "promedio de probabilidades softmax por publicación",
        "dispositivo": str(dispositivo),
        "predicciones": filas.to_dict(orient="records"),
    }
    destino.write_text(json.dumps(evidencia, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return filas


def resumir(filas):
    referencia = filas["referencia"]
    prediccion = filas["prediccion"]
    metricas = {
        "Exactitud": accuracy_score(referencia, prediccion),
        "F1 macro": f1_score(referencia, prediccion, labels=CLASES, average="macro", zero_division=0),
    }
    matriz = pd.DataFrame(
        confusion_matrix(referencia, prediccion, labels=CLASES),
        index=pd.Index(CLASES, name="Etiqueta humana"),
        columns=pd.Index(CLASES, name="Predicción"),
    )
    return metricas, matriz


def mostrar_cuadro(titulo, tabla):
    display(HTML(
        f'<div style="max-width:fit-content"><strong>{titulo}</strong>'
        '<div style="border:1px solid #667480;padding:8px 12px;margin-top:6px">'
        f'{tabla.to_html(float_format=lambda valor: f"{valor:.2%}")}'
        f'<small>Fuente. {FUENTE}</small></div></div>'
    ))
