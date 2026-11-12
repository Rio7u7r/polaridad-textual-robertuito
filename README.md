# Tesis RoBERTuito M0–M2

Versión del marco aplicativo v56 y de la corrida `corrida_03_epocas`. Reúne
los cuadernos 00–10 con el arranque directo en Colab, el iniciador de la
secuencia, el código de entrenamiento y evaluación y el aplicativo Gradio.
Los tres pesos se vinculan con sus manifiestos `ejecucion.json` y se
descargan con Git LFS.

## Abrir en Colab

Abre los cuadernos desde la [copia de trabajo en Drive](https://drive.google.com/drive/folders/1qcBf7NCd7_gRp8sAeVP5l-mbFRWz0ahD).
`INICIAR_EN_COLAB.ipynb` ejecuta la secuencia completa y guarda una
corrida con fecha. Cada cuaderno numerado también puede abrirse por separado.
Los corpus, las etiquetas por publicación y las predicciones individuales
se consultan desde la copia de trabajo autorizada.

La secuencia 00–09 permite usar **Ejecutar todo** en modo de revisión. El 05
reutiliza las propuestas guardadas. El 06–08 verifica los pesos y muestra
el historial de pérdida. El 06–09 reconstruye las métricas y las figuras a
partir de las 454 predicciones de evaluación guardadas por modelo.
`GENERAR_PROPUESTAS`, `ENTRENAR_MODELO`, `PREGUNTAR_CARGA` y
`RECALCULAR_EVALUACION` tienen el valor predeterminado `False`.
Un nuevo ajuste de M1 o M2 requiere activar `ENTRENAR_MODELO` y disponer de GPU CUDA.

Los cuadernos públicos 00–05 presentan su código. Sus salidas por publicación
se conservan en Drive. Las salidas de 06–09 incluyen los registros de ajuste
y las evaluaciones agregadas.

Abre [10_PROBAR_APLICATIVO.ipynb](10_PROBAR_APLICATIVO.ipynb) en Colab para
escribir un texto y probar M2 o comparar los tres modelos con los pesos
de la corrida seleccionada en Drive. También puedes abrir Gradio dentro del cuaderno.

Para preparar una copia local desde GitHub, descarga los pesos con `git lfs pull`.
Copia desde Drive las carpetas `data`, `TABLAS` e `insumos`, y los tres JSON
de `evaluacion/corrida_03_epocas`, conservando sus rutas relativas.
`insumos` incluye `propuestas_reproducidas.xlsx` y su manifiesto JSON.
Instala PyTorch 2.10.0 para el equipo y las dependencias de
`requirements-anaconda.txt` en un entorno de Anaconda con Python 3.12.
Registra el kernel con `python -m ipykernel install --user --name tesis-robertuito --display-name "Tesis RoBERTuito"`
y abre Jupyter desde la carpeta que contiene `corrida.json`.
`python ejecutar_cuadernos.py` ejecuta la revisión con los resultados guardados.
`python ejecutar_cuadernos.py --entrenar` habilita explícitamente el recorrido de ajuste.

## Ejecutar Gradio

En un entorno con Python y Git LFS, instala las dependencias con
`python -m pip install -r requirements.txt` y ejecuta `python aplicativo/app.py`.
M2 es el modelo inicial. La pestaña Comparar permite contrastar M0, M1 y M2.
La variable `TESIS_VARIANTE=m2` activa la edición de un solo modelo.
`python aplicativo/app.py --compartir` genera un enlace público temporal de
Gradio mientras el proceso permanezca activo.

## Trazabilidad

| Objetivo | Evidencia |
| --- | --- |
| OE1 y OE2, preparar textos | Cuadernos 00–05. El 04 guarda 2.647 publicaciones preprocesadas tras excluir 22 filas vacías. El 05 separa sugerencias y etiquetas humanas. |
| OE3, ajustar modelos | Cuadernos 06–08 y `entrenamiento.py`. M0 es la referencia publicada. M1 se ajustó con 9.336 registros peruanos y M2 se ajustó a partir de M1 con 1.809 publicaciones bolivianas. Ambos ajustes completaron tres épocas. |
| OE4, evaluar | Cuaderno 09 y `evaluar.py`. Los gráficos en `evaluacion/corrida_03_epocas/figuras` corresponden a la evaluación interna de 454 publicaciones y al seguimiento de los dos ajustes. |
| OE5, demostrar la aplicación | `aplicativo/app.py` y `nucleo.py`. El aplicativo muestra la polaridad de un texto y sus probabilidades. Emplea tramos de 128 tokens con solapamiento de 32 y promedia las probabilidades. |
| OE5, probar desde Colab | `10_PROBAR_APLICATIVO.ipynb`, celdas 1–3. Usa los pesos de la corrida seleccionada en Drive, pasa el texto ingresado a `nucleo.predecir` y presenta una tabla de probabilidades. La celda 3 abre el mismo `aplicativo/app.py`. |
| Revisar la secuencia | `gestion_modelos.py`, 05 y 06–09. Se verifican los archivos guardados y se regeneran las tablas y figuras. El ajuste y las nuevas predicciones requieren habilitación explícita. |

`VERIFICACION_REVISION.json` documenta la prueba de 00–09 en kernels Jupyter,
con las funciones de entrenamiento, predicción y entrada interactiva bloqueadas.
La prueba completó la revisión y recuperó 363, 346 y 401 aciertos para M0, M1 y M2,
respectivamente, sobre 454 publicaciones. Los registros conservados pertenecen a
la corrida original.

El alcance académico se documentó en el marco introductorio de trabajo,
§§ 1.4–1.5, y el marco aplicativo v56, con los criterios de trazabilidad de
M p. 25 y T pp. 17–18. La evaluación interna describe la partición usada.
La hipótesis en prueba independiente corresponde a su propia evaluación.
