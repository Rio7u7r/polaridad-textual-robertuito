"""Exporta modelos por lista permitida. No accede a la red ni sube archivos."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

PERMITIDOS = ("config.json", "model.safetensors", "tokenizer.json",
              "tokenizer_config.json", "special_tokens_map.json")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sanear(obj):
    if isinstance(obj, dict):
        return {k: sanear(v) for k, v in obj.items()
                if k not in {"_name_or_path", "name_or_path", "token", "use_auth_token", "cache_dir"}}
    if isinstance(obj, list):
        return [sanear(v) for v in obj]
    return obj


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for code in ("m1", "m2", "m3"):
        parser.add_argument(f"--{code}", type=Path, required=True)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    destino = args.salida.resolve()
    if destino.exists():
        parser.error("La salida debe ser una carpeta nueva para preservar exportaciones anteriores.")
    manifest = json.loads(Path(__file__).with_name("checkpoint_manifest.json").read_text(encoding="utf-8"))
    fichas = json.loads(Path(__file__).with_name("ficha_modelos.json").read_text(encoding="utf-8"))
    # Verificar todo antes de copiar; no elegir el checkpoint por su nombre.
    for code in ("M1", "M2", "M3"):
        origen = getattr(args, code.lower()).resolve()
        for name in PERMITIDOS:
            if not (origen / name).is_file():
                parser.error(f"{code}: falta un archivo necesario: {name}.")
            if sha256(origen / name) != manifest[code][name]["sha256"]:
                parser.error(f"{code}: la huella de {name} no coincide con la versión auditada.")
    destino.mkdir(parents=True)
    registro = {}
    for code in ("M1", "M2", "M3"):
        origen = getattr(args, code.lower()).resolve()
        out = destino / code
        out.mkdir()
        registro[code] = {}
        for name in PERMITIDOS:
            src, dst = origen / name, out / name
            if name in ("config.json", "tokenizer_config.json", "special_tokens_map.json"):
                obj = sanear(json.loads(src.read_text(encoding="utf-8")))
                dst.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            else:
                shutil.copyfile(src, dst)
            registro[code][name] = {"sha256_origen": sha256(src), "sha256_exportado": sha256(dst), "bytes": dst.stat().st_size}
        metrica = next(x for x in fichas["resultados_prueba"] if x["modelo"] == code)
        base = "M1, adaptación de RoBERTuito con SMPS" if code == "M3" else "pysentimiento/robertuito-sentiment-analysis"
        datos = "SMPS peruano" if code == "M1" else "partición local boliviana con etiquetas humanas"
        aviso = ("El entrenamiento M1 aplica preprocess_tweet, según el cuaderno 07 auditado." if code == "M1" else
                 "Los pesos provienen del entrenamiento histórico sin preprocess_tweet. La carpeta final es una copia consolidada; no acredita un entrenamiento corregido.")
        card = f'''---
language: es
pipeline_tag: text-classification
library_name: transformers
---
# {code} Polaridad textual

Adaptación académica. Base: {base}. Datos de ajuste: {datos}.
Este repositorio contiene pesos y tokenizador; no contiene textos del corpus.

{aviso}

Prueba histórica de 100 textos: exactitud {metrica["exactitud_pct"]} % y F1 macro
{metrica["f1_macro"]:.10f}. Fuente: evaluación oficial conservada, Tabla 4.11
del capítulo IV versión 52. No es una nueva evaluación de esta exportación.
Una persona anotó la referencia; la prueba contiene cinco positivos y corresponde
a un contexto universitario. No acredita diagnóstico ni generalización poblacional.

Inferencia: preprocess_tweet(lang="es"), 128 posiciones, stride 32,
overflow y promedio Softmax; clases según config.json (NEG, NEU, POS).
Huella SHA256 de los pesos: {registro[code]["model.safetensors"]["sha256_exportado"]}.

No se asigna una nueva licencia. La redistribución queda pendiente de comprobar
las condiciones del modelo base y de los datos usados antes de subir este repo.
'''
        (out / "README.md").write_text(card, encoding="utf-8")
    (destino / "manifest_exportacion.json").write_text(json.dumps(registro, indent=2) + "\n", encoding="utf-8")
    print("Exportación local completada: tres carpetas y manifiesto. No se ha subido ningún archivo.")


if __name__ == "__main__":
    main()
