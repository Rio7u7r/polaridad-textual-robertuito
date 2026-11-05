# Aplicación y cuadernos de tesis

El código de Gradio está en la raíz y los quince cuadernos de trabajo están en notebooks/, en orden del 00 al 14. Se conservó el contenido de las celdas y se retiraron las salidas guardadas, los adjuntos y los metadatos de ejecución para compartir copias de consulta. Los originales se identifican por SHA-256 en MANIFIESTO_NOTEBOOKS.json.

La evidencia de paridad se guarda en evidencia/. Esta prueba se realizó localmente con los cuatro modelos. Los cuadernos no se ejecutaron al preparar el ZIP. La reproducción del pipeline requiere configurar los datos y accesos autorizados para cada etapa. Los pesos, el corpus y las credenciales se gestionan por separado.

Para Hugging Face, consulta SUBIR_AL_SPACE.md. Si el mismo repositorio va a alojar los cuadernos, conserva notebooks/ junto a app.py y mantén la estructura del ZIP. Gradio utiliza app.py como punto de entrada. El archivo .gitignore incluye una excepción para versionar estas copias. Comprueba la visibilidad del destino antes de compartir los cuadernos.
