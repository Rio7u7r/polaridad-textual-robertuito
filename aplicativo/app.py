"""Interfaz Gradio de polaridad textual. Ejecutar: python app.py."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

# Se define antes de importar Gradio. No desactiva políticas del proveedor.
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import gradio as gr
from starlette.middleware import Middleware

from ejemplos import EJEMPLOS, texto_ejemplo
from nucleo import MODELOS, ErrorModelo, corrida_actual, estado_modelos, predecir, validar_texto
from ui_render import CSS, RESULTADO_VACIO, comparacion_html, error_html, resultado_html, tabla_prueba_html


OPCIONES_MODELO = [
    ("M0 · RoBERTuito base", "M0"),
    ("M1 · Corpus peruano", "M1"),
    ("M2 · Corpus peruano + boliviano", "M2"),
]
OPCIONES_MODELO = [opcion for opcion in OPCIONES_MODELO if opcion[1] in MODELOS]
DEFAULT_MODEL = "M2"
COMPARATIVA = len(MODELOS) > 1
AVISO = "Resultado orientativo de polaridad del texto. No es un diagnóstico ni una evaluación de la persona."
OBJETIVO = (
    "Desarrollar un modelo computacional basado en Procesamiento del Lenguaje Natural "
    "y aprendizaje automático que permita detectar y clasificar la polaridad de los "
    "estados emocionales presentes en publicaciones digitales de jóvenes bolivianos"
)


def leer_ficha() -> dict:
    ruta = Path(__file__).with_name("ficha_modelos.json")
    if not ruta.is_file():
        return {}
    try:
        ficha = json.loads(ruta.read_text(encoding="utf-8"))
        if ficha["corrida"] != corrida_actual():
            return {}
        ficha["resultados_prueba"] = [fila for fila in ficha["resultados_prueba"] if fila["modelo"] in MODELOS]
        if not COMPARATIVA:
            ficha["seleccion"] = "Esta edición clasifica con M2."
        return ficha
    except (OSError, ValueError):
        return {}


def preparar_clasificacion(texto: str, modelo: str):
    try:
        validar_texto(texto)
        if modelo not in MODELOS:
            raise ValueError("Selecciona un modelo disponible.")
    except (ValueError, ErrorModelo) as exc:
        return str(exc), ""
    return f"Cargando modelo {modelo} y clasificando… La primera carga puede tardar más.", ""


def clasificar(texto: str, modelo: str):
    try:
        resultado = predecir(texto, modelo)
        return "Clasificación terminada.", resultado_html(resultado)
    except (ValueError, ErrorModelo) as exc:
        return "No se pudo clasificar el texto.", error_html(str(exc))
    except Exception:
        # Evita exponer entrada, rutas, token o detalle interno en la interfaz.
        return "No se pudo clasificar el texto.", error_html("Ocurrió un error interno. Intenta otra vez o consulta al responsable de la aplicación.")


def preparar_comparacion(texto: str):
    try:
        validar_texto(texto)
    except (ValueError, ErrorModelo) as exc:
        return str(exc), ""
    return "Cargando modelos y comparando… Se procesan M0, M1 y M2 uno por uno.", ""


def comparar(texto: str):
    try:
        validar_texto(texto)
    except (ValueError, ErrorModelo) as exc:
        return "No se pudo comparar el texto.", error_html(str(exc))
    resultados, errores = [], {}
    for modelo in MODELOS:
        try:
            resultados.append(predecir(texto, modelo))
        except (ValueError, ErrorModelo) as exc:
            errores[modelo] = str(exc)
        except Exception:
            errores[modelo] = "No se pudo evaluar este modelo. Consulta al responsable de la aplicación."
    mensaje = ("Comparación terminada: tres modelos evaluados." if len(resultados) == len(MODELOS) else
               f"Comparación incompleta: {len(resultados)} de {len(MODELOS)} modelos evaluados. Revisa los avisos de la tabla.")
    return mensaje, comparacion_html(resultados, errores)


def disponibilidad_texto() -> str:
    estados = estado_modelos()
    pendientes = [e["codigo"] for e in estados if not e["disponible"]]
    if pendientes:
        return "**Modelos sin configurar:** " + ", ".join(pendientes) + ". Revisa la corrida elegida y sus carpetas de pesos."
    return "Modelos listos para usar."


def construir_app() -> gr.Blocks:
    ficha = leer_ficha()
    # Fuentes del sistema explícitas: no Google Fonts ni recursos CDN propios.
    tema = gr.themes.Base(font=["Segoe UI", "Arial", "sans-serif"], font_mono=["Courier New", "monospace"])
    with gr.Blocks(title="Polaridad textual · RoBERTuito", theme=tema, css=CSS, analytics_enabled=False) as demo:
        gr.HTML('<header class="portada"><h1>Polaridad textual</h1><p>Explora cómo RoBERTuito clasifica un texto en español.</p></header>')
        disponibilidad = disponibilidad_texto()
        if disponibilidad.startswith("**"):
            gr.Markdown(disponibilidad)
        with gr.Tabs(elem_classes="mesa"):
            with gr.Tab("Clasificar"):
                with gr.Row():
                    with gr.Column(scale=1, min_width=280):
                        gr.Markdown("## Tu texto")
                        texto = gr.Textbox(label="Texto en español", placeholder="Escribe un texto o elige un ejemplo sintético…", lines=6, max_lines=12, max_length=2000, info="Máximo 2.000 caracteres. Evita información personal.", elem_id="texto_clasificar")
                        modelo = gr.Radio(choices=OPCIONES_MODELO, value=DEFAULT_MODEL, label="Modelo", elem_id="selector_modelo", visible=COMPARATIVA)
                        ejemplo = gr.Dropdown(choices=list(EJEMPLOS), label="Ejemplos sintéticos E1–E6", value=None)
                        boton = gr.Button("Clasificar texto", variant="primary", elem_id="boton_clasificar")
                        borrar = gr.Button("Borrar texto y resultado")
                    with gr.Column(scale=1, min_width=280):
                        gr.Markdown("## Resultado del análisis")
                        resultado = gr.HTML(RESULTADO_VACIO, elem_id="resultado_clasificar")
                        estado = gr.Markdown("", elem_id="estado_clasificar")
                ejemplo.change(texto_ejemplo, ejemplo, texto, queue=False, api_name=False)
                borrar.click(lambda: ("", None, "Texto y resultado borrados.", RESULTADO_VACIO), outputs=[texto, ejemplo, estado, resultado], queue=False, api_name=False)
                boton.click(preparar_clasificacion, [texto, modelo], [estado, resultado], queue=False, api_name=False).then(clasificar, [texto, modelo], [estado, resultado], queue=False, show_progress="full", api_name=False)
            with gr.Tab("Comparar", visible=COMPARATIVA):
                texto_c = gr.Textbox(label="El mismo texto para los tres modelos", lines=5, max_lines=12, max_length=2000, info="Máximo 2.000 caracteres.", elem_id="texto_comparar")
                ejemplo_c = gr.Dropdown(choices=list(EJEMPLOS), label="Ejemplos sintéticos E1–E6", value=None)
                boton_c = gr.Button("Comparar M0, M1 y M2", variant="primary", elem_id="boton_comparar")
                borrar_c = gr.Button("Borrar texto y resultado")
                estado_c = gr.Markdown("La comparación carga los modelos de forma secuencial y puede tardar más.", elem_id="estado_comparar")
                resultado_c = gr.HTML(elem_id="resultado_comparar")
                ejemplo_c.change(texto_ejemplo, ejemplo_c, texto_c, queue=False, api_name=False)
                borrar_c.click(lambda: ("", None, "Texto y resultado borrados.", ""), outputs=[texto_c, ejemplo_c, estado_c, resultado_c], queue=False, api_name=False)
                boton_c.click(preparar_comparacion, texto_c, [estado_c, resultado_c], queue=False, api_name=False).then(comparar, texto_c, [estado_c, resultado_c], queue=False, show_progress="full", api_name=False)
        gr.HTML(f'<div class="aviso">{AVISO}</div>')
        with gr.Accordion("Ficha del estudio", open=False, elem_classes="ficha-estudio"):
            gr.Markdown("## Propósito académico\n" + ficha.get("objetivo", OBJETIVO))
            gr.Markdown("Procedencia del objetivo: " + ficha.get("objetivo_fuente", "marco introductorio de trabajo, sección 1.4.1.") + "\n\nLa salida de este aplicativo es **polaridad del texto**. No identifica estados emocionales específicos ni evalúa a una persona.")
            gr.Markdown("## Objetivo específico del aplicativo\nImplementar un prototipo de aplicación que permita ingresar un texto y visualizar la polaridad emocional predicha por el modelo seleccionado.\n\n**Clasificar** muestra la etiqueta, sus tres probabilidades y los resultados por tramo." + (" **Comparar** contrasta M0, M1 y M2 sobre el mismo texto." if COMPARATIVA else " Esta edición utiliza M2."))
            gr.Markdown("## Relación con los objetivos de la tesis\nLa recolección, preparación, anotación, entrenamiento, evaluación y visualización del corpus se documentan en los cuadernos de la tesis. Aquí puedes consultar la evaluación interna y clasificar textos con los pesos de la corrida publicada.")
            gr.Markdown("## Qué significan las clases\n**NEG:** polaridad negativa. **NEU:** polaridad neutral. **POS:** polaridad positiva. El resultado corresponde al mayor porcentaje del modelo y puede ser incorrecto, especialmente con ironía, ambigüedad o contextos distintos a los estudiados.")
            gr.Markdown("## Modelos\n" + ("**M0:** modelo publicado RoBERTuito. **M1:** ajuste con SMPS peruano. " if COMPARATIVA else "") + "**M2:** ajuste con el corpus boliviano a partir de M1.")
            gr.Markdown(ficha.get("aviso_checkpoint", "La condición de entrenamiento y la procedencia de los checkpoints deben consultarse en la ficha de esta instalación; el nombre «final» no demuestra por sí mismo un entrenamiento corregido."))
            gr.HTML(tabla_prueba_html(ficha.get("resultados_prueba", [])))
            gr.Markdown(ficha.get("resultados_fuente", "Las métricas registradas corresponden al análisis de las 454 publicaciones de evaluación interna."))
            gr.Markdown(ficha.get("seleccion", "La aplicación abre con M2 y permite seleccionar otro modelo."))
            gr.Markdown("## Límites\nLa referencia de evaluación fue anotada por una persona y corresponde a un corpus de contexto universitario. Los resultados no representan a toda la población joven boliviana. Este aplicativo no ofrece un diagnóstico, orientación clínica ni una evaluación individual.")
            gr.Markdown("## Funcionamiento y privacidad\nEl texto se preprocesa en español y se divide en ventanas de hasta 128 posiciones, con 32 tokens de solapamiento. Se promedian las probabilidades de los tramos. La aplicación carga los pesos locales y utiliza CPU. No registra el contenido de entrada, no tiene historial ni botones para guardar ejemplos, y tiene desactivada la analítica de Gradio. Los resultados permanecen en la página hasta sustituirlos, recargarla o cerrarla.")
            gr.Markdown(ficha.get("estado_publicacion", "Demostración de la corrida de tres épocas."))
    return demo


class RecursosLocales:
    """Retira recursos externos de la plantilla HTML incluida en Gradio 5.49."""

    externos = re.compile(
        rb'<script\b[^>]*\bsrc="https://cdnjs\.cloudflare\.com/[^"]+"[^>]*>\s*</script>'
        rb'|<link\b[^>]*\bhref="https://fonts\.(?:googleapis|gstatic)\.com[^"]*"[^>]*>',
        re.IGNORECASE,
    )

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "GET":
            return await self.app(scope, receive, send)
        inicio, partes = None, []

        async def enviar(mensaje):
            nonlocal inicio
            if mensaje["type"] == "http.response.start":
                cabeceras = dict(mensaje["headers"])
                if cabeceras.get(b"content-type", b"").startswith(b"text/html") and b"content-encoding" not in cabeceras:
                    inicio = mensaje
                    return
            if mensaje["type"] == "http.response.body" and inicio is not None:
                partes.append(mensaje.get("body", b""))
                if mensaje.get("more_body", False):
                    return
                cuerpo = self.externos.sub(b"", b"".join(partes))
                inicio["headers"] = [(k, v) for k, v in inicio["headers"] if k not in (b"content-length", b"etag")]
                inicio["headers"].append((b"content-length", str(len(cuerpo)).encode("ascii")))
                await send(inicio)
                await send({"type": "http.response.body", "body": cuerpo})
                return
            await send(mensaje)

        return await self.app(scope, receive, enviar)


def iniciar(compartir=False):
    construir_app().launch(
        server_name="0.0.0.0" if os.getenv("SPACE_ID") else "127.0.0.1",
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
        share=compartir,
        inbrowser=os.getenv("TESIS_ABRIR_NAVEGADOR") == "1",
        show_error=False,
        show_api=False,
        quiet=not compartir,
        ssr_mode=False,
        app_kwargs={"middleware": [Middleware(RecursosLocales)]},
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--compartir", action="store_true", help="Genera un enlace público temporal de Gradio.")
    iniciar(compartir=parser.parse_args().compartir)
