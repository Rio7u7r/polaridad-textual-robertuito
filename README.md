# Polaridad textual con RoBERTuito

[Ver la muestra en Hugging Face](https://huggingface.co/spaces/Rio7u7/polaridad-textual-robertuito) · [Consultar los 15 notebooks](notebooks/)

El repositorio reúne el aplicativo Python y las copias de consulta de los cuadernos 00–14. El [manifiesto](MANIFIESTO_NOTEBOOKS.json) identifica sus versiones y la [evidencia de paridad](evidencia/PARIDAD_Y_TIEMPOS.md) documenta la prueba de los cuatro modelos. En la muestra web, M1 aparece primero por su resultado en la prueba de 100 textos.

Aplicación académica para ingresar un texto en español y visualizar su polaridad
negativa, neutral o positiva. Permite clasificar con un modelo o comparar M0, M1,
M2 y M3. Los ejemplos E1–E6 son inventados; no son publicaciones del corpus.

**Resultado orientativo de polaridad del texto. No es un diagnóstico ni una
evaluación de la persona.**

La aplicación no escribe los textos ingresados ni sus resultados en archivos,
no conserva un historial y desactiva la analítica de Gradio. Los textos se
procesan temporalmente en memoria y permanecen visibles en el navegador hasta
reemplazarlos o cerrar la página. Esto no constituye una garantía sobre los
registros del proveedor que aloje el servicio.

## Modelos y alcance

| Modelo | Procedencia | Exactitud histórica (100 textos) | F1 macro |
| --- | --- | ---: | ---: |
| M0 | RoBERTuito publicado, TASS | 70 % | 0,6008 |
| M1 | Adaptación de M0 con SMPS peruano | 76 % | 0,6646 |
| M2 | Adaptación boliviana desde M0 | 63 % | 0,5186 |
| M3 | Adaptación boliviana desde M1 | 64 % | 0,5268 |

Fuente: evaluación oficial conservada en los cuadernos 08 y 11 y Tabla 4.11
del capítulo IV, versión 52; no es una evaluación nueva de esta interfaz.
M3 es el modelo local seleccionado entre M2 y M3 por F1 macro de validación
(0,8037751). M1 obtuvo mayor exactitud en prueba; ese resultado no modifica la
selección por validación.

**M2 y M3 disponibles conservan pesos históricos cuyo entrenamiento no aplicó
`preprocess_tweet`. Las carpetas `*_final` son copias consolidadas, no
reentrenamientos corregidos.** La inferencia de los cuatro modelos sí aplica
`preprocess_tweet(lang="es")`, ventanas de 128 posiciones, solapamiento de 32
tokens y promedio de Softmax. Las clases se leen del `config.json`.

La referencia humana fue anotada por una persona, el corpus corresponde a un
contexto universitario y la prueba incluye cinco positivos. No se generaliza a
toda la población joven boliviana. La salida es polaridad textual, no un estado
emocional ni una característica de la persona.

## Ejecución

Con Python 3.13, en un entorno virtual:

```text
python -m pip install -r requirements.txt
python app.py
```

Abra la dirección local que corresponda, por defecto `http://127.0.0.1:7860`.
No se abre un enlace público mediante Gradio. La descarga inicial necesita
internet, salvo que configure carpetas locales con todos los archivos.

M0 se obtiene de [su repositorio original](https://huggingface.co/pysentimiento/robertuito-sentiment-analysis)
en una revisión fija. Para M1–M3 configure `HF_MODEL_OWNER`, o cada
`M1_REPO_ID`, `M2_REPO_ID`, `M3_REPO_ID`; además indique `M1_REVISION`,
`M2_REVISION`, `M3_REVISION` con los identificadores completos de los commits.
Guarde el acceso de lectura exclusivamente en el **Secret `HF_TOKEN`**.
La ausencia de estos datos se muestra como aviso; M0 se puede usar por separado.
Alternativamente se aceptan `M0_LOCAL_PATH` a `M3_LOCAL_PATH` para uso local.

Solo se conserva un modelo cargado a la vez. La comparación procesa los cuatro
secuencialmente; cambiar de modelo requiere recargarlo. `DEFAULT_MODEL=M1`
cambia el modelo inicial; por defecto es M3. `TORCH_NUM_THREADS=2` fija los
hilos de CPU usados en las pruebas.

## Estado y publicación

Esta carpeta prepara una aplicación para ejecutar y subir. No acredita que
exista un Space publicado. Consulte `SUBIR_AL_SPACE.md`, `PROTOCOLO.md` y las
evidencias de entrega. La cuenta, las licencias y el alojamiento deben quedar
comprobados antes de publicar los pesos. No se incluyen corpus, credenciales
ni archivos de entrenamiento.
