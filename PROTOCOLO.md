# Protocolo y verificación

La referencia es el cuaderno original **08_evaluacion_modelo.ipynb**, celda de índice 5, SHA-256 `52e7c6343b65b5b9c2e16a8037e13dad27ad18994023300c5e4febdae747d053`. El archivo `notebooks/08_resultados_finales.ipynb` del proyecto es una plantilla. El cuaderno 14 conserva el mismo método de inferencia y el 11 consolida resultados históricos. Ninguno se modificó.

`predecir` prepara el texto con `preprocess_tweet(lang="es")`. El tokenizador usa `max_length=128`, `truncation=True`, `stride=32`, `return_overflowing_tokens=True` y `padding=True`. Se aplica Softmax por tramo y se calcula su media aritmética, asignando las clases a partir de `id2label`. Los cuatro archivos auditados tienen 0=NEG, 1=NEU y 2=POS. `checkpoint_manifest.json` identifica pesos, configuración y tokenizador; las copias saneadas para subida conservan un manifiesto separado.

La prueba `verificar_paridad.py` implementa por separado el cálculo de la celda de referencia. Su adaptación expone probabilidades y tramos que la función original calculaba, pero no devolvía. Ambos lados usan el mismo modelo, tokenizador y tipo numérico en CPU. El umbral es diferencia absoluta máxima menor que 0,001 en escala 0–1, equivalente a 0,1 puntos porcentuales. Se exige también coincidencia de etiqueta y tramos. Para E6 se verifica el desborde y la media por clase. No es una nueva evaluación del corpus.

```text
python -m unittest discover -s tests -v
python verificar_paridad.py --config-local RUTA_CONFIG_PRIVADA --cuaderno-08 RUTA_08_ORIGINAL --salida RUTA_NUEVA
```

El archivo privado de configuración admite `M0_LOCAL_PATH` a `M3_LOCAL_PATH`, `HF_HUB_OFFLINE` y `TORCH_NUM_THREADS`; no contiene tokens. Las salidas registran el ID de ejemplo, huellas, versiones, probabilidades y tiempos, sin copiar los textos. Una llamada fría incluye carga e inferencia; los tiempos calientes excluyen carga. No se vació la caché de disco. No se extrapolan los tiempos ni la memoria a Spaces.

Las dependencias principales fijan la compilación CPU de PyTorch para Windows o Linux x86-64 con Python 3.13. El archivo de versiones transitivas para Windows documenta el entorno local. Se resolvieron metadatos y ruedas de Linux desde Windows, sin iniciar una instancia Linux ni comprobar el arranque de un Space. Las dependencias de este aplicativo se registran aparte del entorno de entrenamiento con CUDA de la Tabla 4.1.
