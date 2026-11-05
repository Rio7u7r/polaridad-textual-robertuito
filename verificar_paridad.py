"""Paridad independiente del cuaderno 08, con ejemplos sintéticos y CPU.

Las evidencias se escriben solamente en --salida; no incluyen textos ni rutas
personales. No utiliza corpus ni realiza entrenamiento o descargas de datos.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import platform
import statistics
import time

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")

from ejemplos import EJEMPLOS
import nucleo

REFERENCIA_08_SHA256 = "52e7c6343b65b5b9c2e16a8037e13dad27ad18994023300c5e4febdae747d053"
CLASES = ("NEG", "NEU", "POS")
ETIQUETAS = ("negativa", "neutral", "positiva")
UMBRAL_PROBABILIDAD = 0.001


def referencia_cuaderno_08(texto, tok, mod):
    """Transcripción independiente de celda 5 (índice cero) del 08 original.

    Únicas adaptaciones: CPU explícita y retorno de probabilidades/tramos,
    que el original calcula internamente pero no devuelve. No comparte
    preparación, tokenización, promedio ni mapa de clases con nucleo.py.
    """
    import torch
    from pysentimiento.preprocessing import preprocess_tweet

    entrada = preprocess_tweet(str(texto), lang="es")
    lote = tok(
        entrada, max_length=128, truncation=True, stride=32,
        return_overflowing_tokens=True, padding=True, return_tensors="pt"
    )
    lote.pop("overflow_to_sample_mapping", None)
    lote = {k: v.to("cpu") for k, v in lote.items()}
    with torch.inference_mode():
        tramos = torch.softmax(mod(**lote).logits, dim=-1)
        probabilidades = tramos.mean(dim=0)
    mapa = {0: "negativa", 1: "neutral", 2: "positiva"}
    return {
        "etiqueta": mapa[int(probabilidades.argmax())],
        "probabilidades": probabilidades.cpu().tolist(),
        "tramos": tramos.cpu().tolist(),
        "n_tramos": int(lote["input_ids"].shape[0]),
        "tokens_sin_especiales": len(tok(entrada, add_special_tokens=False,
                                        truncation=False, verbose=False)["input_ids"]),
    }


def sha256(ruta):
    h = hashlib.sha256()
    with Path(ruta).open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def argumentos():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--salida", type=Path, required=True,
                   help="Carpeta nueva fuera de space para evidencia JSON/CSV/Markdown.")
    p.add_argument("--config-local", type=Path,
                   help="JSON privado con M0_LOCAL_PATH ... M3_LOCAL_PATH; no se copia.")
    p.add_argument("--cuaderno-08", type=Path,
                   help="Cuaderno original opcional: se exige la huella auditada.")
    p.add_argument("--modelos", nargs="+", choices=["M0", "M1", "M2", "M3"],
                   default=["M0", "M1", "M2", "M3"])
    return p.parse_args()


def main():
    args = argumentos()
    destino = args.salida.resolve()
    carpeta_space = Path(__file__).resolve().parent
    if destino == carpeta_space or carpeta_space in destino.parents:
        raise SystemExit("La evidencia debe guardarse fuera de la carpeta que se subirá al Space.")
    if (destino / "paridad.json").exists():
        raise SystemExit("Ya existe una corrida en esa carpeta. Elija otra para conservarla.")
    if args.config_local:
        valores = json.loads(args.config_local.read_text(encoding="utf-8"))
        permitidas = {f"M{i}_LOCAL_PATH" for i in range(4)} | {"HF_HUB_OFFLINE", "TORCH_NUM_THREADS"}
        if not set(valores).issubset(permitidas):
            raise SystemExit("La configuración local debe contener solo rutas de modelos y opciones de CPU/offline.")
        for k, v in valores.items():
            os.environ[k] = str(v)
    comprobado = False
    if args.cuaderno_08:
        comprobado = sha256(args.cuaderno_08) == REFERENCIA_08_SHA256
        if not comprobado:
            raise SystemExit("El cuaderno 08 no coincide con la referencia auditada. Revise su versión.")
    import torch
    torch.set_num_threads(max(1, min(4, int(os.getenv("TORCH_NUM_THREADS", "2")))))
    destino.mkdir(parents=True, exist_ok=True)
    filas, detalles, cargas, huellas = [], [], [], {}
    ejemplos = [(nombre.split(" ")[0], texto) for nombre, texto in EJEMPLOS.items()]
    if [x[0] for x in ejemplos] != [f"E{i}" for i in range(1, 7)]:
        raise SystemExit("Se requieren los cinco textos E1–E5 y el texto largo E6.")
    for codigo in args.modelos:
        nucleo.liberar_cache()
        t0 = time.perf_counter()
        primera = nucleo.predecir(ejemplos[0][1], codigo)
        total_frio = time.perf_counter() - t0
        cargas.append({"modelo": codigo, "ejemplo": "E1", "carga_fria_segundos": primera["carga_segundos"],
                       "inferencia_primera_segundos": primera["segundos"],
                       "total_frio_segundos": total_frio})
        tok, mod = nucleo.cargar_modelo(codigo)
        if next(mod.parameters()).device.type != "cpu" or next(mod.parameters()).dtype != torch.float32:
            raise RuntimeError("La prueba requiere CPU y pesos float32.")
        if {int(k): v.upper() for k, v in mod.config.id2label.items()} != {0:"NEG",1:"NEU",2:"POS"}:
            raise RuntimeError("La referencia histórica requiere el mapa NEG/NEU/POS de 0 a 2.")
        origen = os.getenv(f"{codigo}_LOCAL_PATH")
        if origen:
            carpeta = Path(origen)
            huellas[codigo] = {p.name:sha256(p) for p in carpeta.iterdir()
                               if p.name in {"model.safetensors", "config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"}}
        else:
            huellas[codigo] = {"revision": nucleo.M0_REVISION if codigo == "M0" else os.getenv(f"{codigo}_REVISION", ""),
                               "nota": "Identidad por revisión; para huellas locales configure las rutas auditadas."}
        for identificador, texto in ejemplos:
            referencia = referencia_cuaderno_08(texto, tok, mod)
            t0 = time.perf_counter()
            actual = nucleo.predecir(texto, codigo)
            tiempo_total = time.perf_counter() - t0
            app_probs = [actual["porcentajes"][c] / 100 for c in CLASES]
            delta = max(abs(a-b) for a,b in zip(app_probs, referencia["probabilidades"]))
            delta_tramos = max(abs(actual["porcentajes_por_tramo"][i][c]/100 - referencia["tramos"][i][j])
                               for i in range(min(actual["n_tramos"], referencia["n_tramos"]))
                               for j,c in enumerate(CLASES))
            media = [sum(t[c]/100 for t in actual["porcentajes_por_tramo"])/actual["n_tramos"] for c in CLASES]
            delta_media = max(abs(a-b) for a,b in zip(app_probs, media))
            pasa = (delta < UMBRAL_PROBABILIDAD and delta_tramos < UMBRAL_PROBABILIDAD
                    and delta_media < UMBRAL_PROBABILIDAD
                    and actual["etiqueta"] == referencia["etiqueta"]
                    and actual["n_tramos"] == referencia["n_tramos"]
                    and (identificador != "E6" or (referencia["tokens_sin_especiales"] > 128 and actual["n_tramos"] > 1)))
            fila = {"modelo": codigo, "ejemplo": identificador, "caracteres":len(texto),
                    "tokens_sin_especiales":referencia["tokens_sin_especiales"],
                    "n_tramos_referencia":referencia["n_tramos"], "n_tramos_app":actual["n_tramos"],
                    "etiqueta_referencia":referencia["etiqueta"], "etiqueta_app":actual["etiqueta"],
                    "diferencia_max_probabilidad":delta, "diferencia_max_puntos_porcentuales":delta*100,
                    "diferencia_max_tramos_probabilidad":delta_tramos, "diferencia_media_probabilidad":delta_media,
                    "inferencia_caliente_segundos":actual["segundos"], "total_caliente_segundos":tiempo_total,
                    "cumple":pasa}
            for j,c in enumerate(CLASES):
                fila[f"referencia_{c}_porcentaje"] = referencia["probabilidades"][j]*100
                fila[f"app_{c}_porcentaje"] = actual["porcentajes"][c]
            filas.append(fila)
            detalles.append({"modelo":codigo,"ejemplo":identificador,"referencia_probabilidades_por_tramo":referencia["tramos"],
                             "app_porcentajes_por_tramo":actual["porcentajes_por_tramo"]})
            print(f"{codigo} {identificador}: {'OK' if pasa else 'FALLA'}; tramos={actual['n_tramos']}; diferencia={delta:.9g}", flush=True)
        del tok, mod
        nucleo.liberar_cache()
    versions = {p:importlib.metadata.version(p) for p in ["torch","transformers","pysentimiento","gradio","huggingface-hub","safetensors"]}
    resumen = {"fecha_utc":datetime.now(timezone.utc).isoformat(),"estado":"verificado" if all(f["cumple"] for f in filas) else "fallo",
               "alcance":"Paridad local sobre seis ejemplos sintéticos por modelo; no reevalúa el corpus ni valida el alojamiento.",
               "referencia":{"archivo":"COLAB/08_evaluacion_modelo.ipynb","celda_indice_cero":5,
                             "sha256":REFERENCIA_08_SHA256,"hash_original_comprobado":comprobado,
                             "adaptacion":"Retorno ampliado de la función original: probabilidades y tramos; CPU explícita.",
                             "sha256_funcion_transcrita":hashlib.sha256(inspect.getsource(referencia_cuaderno_08).encode()).hexdigest()},
               "umbrales":{"probabilidad_0_1_estrictamente_menor":UMBRAL_PROBABILIDAD,
                           "equivalencia_puntos_porcentuales":UMBRAL_PROBABILIDAD*100},
               "entorno":{"python":platform.python_version(),"sistema":platform.system(),"arquitectura":platform.machine(),
                          "cpu":platform.processor(),"cpu_logicas":os.cpu_count(),"hilos_torch":torch.get_num_threads(),
                          "dispositivo":"cpu","dtype":"float32","versiones":versions},
               "hashes_codigo":{n:sha256(carpeta_space/n) for n in ["nucleo.py","ejemplos.py","verificar_paridad.py"]},
               "huellas_modelos":huellas,"cargas_frias":cargas,"casos":filas,"detalle_tramos":detalles,
               "limitacion_tiempos":"Una carga fría de aplicación y una medición caliente por ejemplo; caché de disco del sistema no vaciada. No es benchmark de Hugging Face."}
    (destino/"paridad.json").write_text(json.dumps(resumen,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (destino/"paridad.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(filas[0]));w.writeheader();w.writerows(filas)
    with (destino/"tiempos_carga.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(cargas[0]));w.writeheader();w.writerows(cargas)
    texto = ["# Paridad y tiempos locales", "", f"Estado: **{resumen['estado']}**. Casos: {len(filas)}. Se utilizaron exclusivamente ejemplos sintéticos.", "",
             "Referencia: cuaderno 08 original, celda 5 (índice cero), transcripción con retorno ampliado de probabilidades y tramos. CPU float32 en ambos lados. El cuaderno original devuelve solo etiqueta.", "",
             "Criterio: diferencia estrictamente menor que 0,001 en probabilidad de 0 a 1, equivalente a 0,1 puntos porcentuales. Se informa también la diferencia en puntos porcentuales sin cambiar de escala silenciosamente.", "",
             "| Modelo | Ejemplo | Tokens | Tramos | Diferencia máxima (prob.) | Diferencia (pp) | Inferencia caliente (s) | Cumple |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |"]
    texto += [f"| {f['modelo']} | {f['ejemplo']} | {f['tokens_sin_especiales']} | {f['n_tramos_app']} | {f['diferencia_max_probabilidad']:.9g} | {f['diferencia_max_puntos_porcentuales']:.9g} | {f['inferencia_caliente_segundos']:.6f} | {'Sí' if f['cumple'] else 'No'} |" for f in filas]
    texto += ["", "| Modelo | Carga fría (s) | Primera inferencia (s) | Total primera llamada (s) | Mediana caliente (s) |", "| --- | ---: | ---: | ---: | ---: |"]
    for f in cargas:
        mediana=statistics.median(x['inferencia_caliente_segundos'] for x in filas if x['modelo']==f['modelo'])
        texto.append(f"| {f['modelo']} | {f['carga_fria_segundos']:.6f} | {f['inferencia_primera_segundos']:.6f} | {f['total_frio_segundos']:.6f} | {mediana:.6f} |")
    texto += ["", resumen["limitacion_tiempos"], "", "Las versiones, huellas y porcentajes completos se conservan en paridad.json y paridad.csv. Las salidas no contienen los textos introducidos ni rutas personales.", ""]
    (destino/"PARIDAD_Y_TIEMPOS.md").write_text("\n".join(texto),encoding="utf-8")
    return 0 if resumen['estado']=="verificado" else 1


if __name__ == "__main__":
    raise SystemExit(main())
