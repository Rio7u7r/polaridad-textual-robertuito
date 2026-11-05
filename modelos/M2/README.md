---
language: es
pipeline_tag: text-classification
library_name: transformers
---
# M2 Polaridad textual

Adaptación académica. Base: pysentimiento/robertuito-sentiment-analysis. Datos de ajuste: partición local boliviana con etiquetas humanas.
Este repositorio contiene pesos y tokenizador; no contiene textos del corpus.

Los pesos provienen del entrenamiento histórico sin preprocess_tweet. La carpeta final es una copia consolidada; no acredita un entrenamiento corregido.

Prueba histórica de 100 textos: exactitud 63 % y F1 macro
0.5185897436. Fuente: evaluación oficial conservada, Tabla 4.11
del capítulo IV versión 52. No es una nueva evaluación de esta exportación.
Una persona anotó la referencia; la prueba contiene cinco positivos y corresponde
a un contexto universitario. No acredita diagnóstico ni generalización poblacional.

Inferencia: preprocess_tweet(lang="es"), 128 posiciones, stride 32,
overflow y promedio Softmax; clases según config.json (NEG, NEU, POS).
Huella SHA256 de los pesos: 250cc56b1577383bf769ae3b4e2e882cfb1aeaea71f5101917075ac0731db40b.

No se asigna una nueva licencia. La redistribución queda pendiente de comprobar
las condiciones del modelo base y de los datos usados antes de subir este repo.
