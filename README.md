# Tesis RoBERTuito M0–M2

Versión del marco aplicativo v56 y de la corrida `corrida_03_epocas`. Reúne
los cuadernos 00–09 con el arranque directo en Colab, el iniciador de la
secuencia, el código de entrenamiento y evaluación y el aplicativo Gradio.
Los tres pesos se vinculan con sus manifiestos `ejecucion.json` y se
descargan con Git LFS.

## Abrir en Colab

Abre los cuadernos desde la [copia de trabajo en Drive](https://drive.google.com/drive/folders/1qcBf7NCd7_gRp8sAeVP5l-mbFRWz0ahD).
`INICIAR_EN_COLAB.ipynb` ejecuta la secuencia completa y guarda una
corrida con fecha. Cada cuaderno numerado también puede abrirse por separado.
Los corpus, las etiquetas por publicación y las predicciones individuales
se consultan desde la copia de trabajo autorizada.

## Ejecutar Gradio

En un entorno con Python y Git LFS, instala las dependencias con
`python -m pip install -r requirements.txt` y ejecuta `python aplicativo/app.py`.
M2 es el modelo inicial. La pestaña Comparar permite contrastar M0, M1 y M2.
La variable `TESIS_VARIANTE=m2` activa la edición de un solo modelo.

## Trazabilidad

| Objetivo | Evidencia |
| --- | --- |
| OE1 y OE2, preparar textos | Cuadernos 00–05. El 04 guarda 2.647 publicaciones preprocesadas tras excluir 22 filas vacías. El 05 separa sugerencias y etiquetas humanas. |
| OE3, ajustar modelos | Cuadernos 06–08 y `entrenamiento.py`. M0 es la referencia publicada. M1 se ajustó con 9.336 registros peruanos y M2 se ajustó a partir de M1 con 1.809 publicaciones bolivianas. Ambos ajustes completaron tres épocas. |
| OE4, evaluar | Cuaderno 09 y `evaluar.py`. Los gráficos en `evaluacion/corrida_03_epocas/figuras` corresponden a la evaluación interna de 454 publicaciones y al seguimiento de los dos ajustes. |
| OE5, demostrar la aplicación | `aplicativo/app.py` y `nucleo.py`. El aplicativo muestra la polaridad de un texto y sus probabilidades. Emplea tramos de 128 tokens con solapamiento de 32 y promedia las probabilidades. |

El alcance académico se documentó en el marco introductorio de trabajo,
§§ 1.4–1.5, y el marco aplicativo v56, con los criterios de trazabilidad de
M p. 25 y T pp. 17–18. La evaluación interna describe la partición usada.
La hipótesis en prueba independiente corresponde a su propia evaluación.
