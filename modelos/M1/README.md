---
language: es
pipeline_tag: text-classification
library_name: transformers
---
# M1 Polaridad textual

Adaptación académica. Base: pysentimiento/robertuito-sentiment-analysis. Datos de ajuste: SMPS peruano.
Este repositorio contiene pesos y tokenizador; no contiene textos del corpus.

El entrenamiento M1 aplica preprocess_tweet, según el cuaderno 07 auditado.

Prueba histórica de 100 textos: exactitud 76 % y F1 macro
0.6645584046. Fuente: evaluación oficial conservada, Tabla 4.11
del capítulo IV versión 52. No es una nueva evaluación de esta exportación.
Una persona anotó la referencia; la prueba contiene cinco positivos y corresponde
a un contexto universitario. No acredita diagnóstico ni generalización poblacional.

Inferencia: preprocess_tweet(lang="es"), 128 posiciones, stride 32,
overflow y promedio Softmax; clases según config.json (NEG, NEU, POS).
Huella SHA256 de los pesos: db0876a7c0fc24624253860d53d64c7ff73a68aaeb34e67722549aa2043544e2.

No se asigna una nueva licencia. La redistribución queda pendiente de comprobar
las condiciones del modelo base y de los datos usados antes de subir este repo.
