"""Presentación HTML local: no guarda entradas ni solicita recursos externos."""

from html import escape
import math

CLASES = (("NEG", "Negativa", "neg"), ("NEU", "Neutral", "neu"), ("POS", "Positiva", "pos"))

CSS = """
.gradio-container, .dark .gradio-container {
 max-width:1160px !important; margin:auto; padding:clamp(16px,4vw,48px) !important;
 --body-background-fill:#f5f3fb; --body-text-color:#201a39; --body-text-color-subdued:#5c5672;
 --block-background-fill:#fff; --input-background-fill:#f8f7fc; --border-color-primary:#ddd7ec;
 --button-primary-background-fill:#5836be; --button-primary-background-fill-hover:#4727a5;
 --button-primary-text-color:#fff; --color-accent:#5836be; --color-accent-soft:#eee9ff;
 --block-label-text-color:#453b61; --block-info-text-color:#635b77;
 --checkbox-label-background-fill:#f8f7fc; --checkbox-label-text-color:#382d55;
 --button-secondary-background-fill:#f0ecf8; --button-secondary-text-color:#443663;
 --background-fill-primary:#fff; --background-fill-secondary:#f5f3fb;
 font-family:"Segoe UI",system-ui,sans-serif !important;
}
body, body.dark, gradio-app {background:#f5f3fb !important;color:#201a39;}
.portada {padding:0 0 12px;}
.portada h1 {font-size:clamp(2.1rem,5vw,3.5rem);letter-spacing:-.055em;line-height:1.06;margin:0 0 12px;color:#21193d;}
.portada p {margin:0;color:#5c5672;font-size:1.06rem;}
.mesa .tab-nav {border-bottom:1px solid #ded7ee;}
.mesa .tab-nav button {padding:12px 17px;font-weight:650;color:#51476e;}
.mesa .tab-nav button.selected {color:#5836be;border-color:#5836be;}
.mesa .tabitem {border:0;padding:18px 0 0;background:transparent;}
.mesa .column:has(> .form #texto_clasificar), .mesa .column:has(> #resultado_clasificar) {
 background:white;border:1px solid #e2ddf0;border-radius:22px;padding:clamp(16px,3vw,27px);box-shadow:0 10px 28px #3020570c;
}
.mesa h2 {font-size:1.35rem;letter-spacing:-.035em;margin:0;color:#21193d;}
.mesa .form {border-color:#e5dff0;}
.mesa .block .label, .mesa .block .block-title, .mesa .block .block-label,
.mesa .block label > span:not(.sr-only), .mesa .block legend {color:#453b61 !important;}
#texto_clasificar textarea {border:1px solid #ddd7ec;border-radius:12px;}
#texto_clasificar textarea:focus {outline:2px solid #7653d8;outline-offset:1px;}
#selector_modelo .wrap {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;}
#selector_modelo label {min-width:0;display:flex;justify-content:center;align-items:center;text-align:center;padding:10px 5px;border-radius:10px;background:#f8f7fc;color:#382d55;border:1px solid #ddd7ec;}
#selector_modelo label:has(input:checked) {background:#eee9ff;border-color:#7653d8;color:#3d238f;}
#selector_modelo input[type=radio] {flex-shrink:0;appearance:auto;accent-color:#5836be;}
.mesa button.primary {border-radius:12px;min-height:46px;font-weight:700;}
.aviso {padding:12px 16px;background:#eee9f8;color:#473866;border-radius:12px;line-height:1.5;font-size:.92rem;}
.medidor {width:min(100%,292px);display:block;margin:5px auto 0;}
.medidor-leyenda {display:flex;justify-content:space-between;gap:8px;width:min(100%,292px);margin:0 auto 14px;font-size:.8rem;color:#51476e;}
.medidor-titulo {text-align:center;}
.medidor-titulo h3 {color:#241a43;font-size:1.8rem !important;margin-bottom:2px !important;}
.medidor-titulo p {margin:0;color:#5c5672;}
.resultado-vacio {text-align:center;color:#5c5672;padding:7px 0 15px;}
.resultado-vacio .medidor {opacity:.62;}
.aguja {
 transform-origin:160px 152px;
 transform:rotate(var(--angulo));
 animation:girar-aguja .86s both;
}
@keyframes girar-aguja {
 0% {transform:rotate(-87deg);animation-timing-function:cubic-bezier(.2,.72,.28,1);}
 72% {transform:rotate(calc(var(--angulo) + 5deg));animation-timing-function:ease-in-out;}
 88% {transform:rotate(calc(var(--angulo) - 1.5deg));animation-timing-function:ease-out;}
 100% {transform:rotate(var(--angulo));}
}
.ficha-estudio {border-radius:14px;margin-top:10px;}
@media(prefers-reduced-motion:reduce) {.aguja {animation:none;}}
.resultado {font-size:16px; line-height:1.5; color:var(--body-text-color);}
.resultado h3 {font-size:22px; margin:0 0 10px;}
.resultado h4 {font-size:17px; margin:20px 0 10px;}
.nota {line-height:1.5; margin:10px 0;}
.barras {display:grid; gap:10px; margin:12px 0;}
.barra-fila {display:grid; grid-template-columns:80px minmax(45px,1fr) 72px; gap:10px; align-items:center;}
.barra-pista {height:8px; background:#eeebf4; border-radius:99px; overflow:hidden;}
.barra-relleno {height:100%; min-width:0;}
.neg {background:#cc5266;} .neu {background:#b67b17;} .pos {background:#13816d;}
.porcentaje {font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap;}
.tabla-scroll {overflow-x:auto; margin:14px 0;}
.tabla-resultados {border-collapse:collapse; width:100%; font-size:15px;}
.tabla-resultados th,.tabla-resultados td {border:1px solid #b7bec6; padding:9px 11px; text-align:left;}
.tabla-resultados th {background:#e9eef3; color:#1f2937;}
.tabla-resultados caption {font-weight:600; text-align:left; padding:0 0 8px;}
.tabla-resultados .numero {text-align:right; font-variant-numeric:tabular-nums;}
.grupo-modelo,.grupo-tramo {margin:18px 0; padding:12px; border:1px solid #b7bec6; border-radius:6px;}
.grupo-modelo h4,.grupo-tramo h4 {margin:0 0 8px;}
.mensaje-error {padding:12px; border:1px solid #d9a5a5; border-radius:6px; line-height:1.5;}
@media(max-width:600px) {
 .gradio-container {padding:14px !important;}
 #selector_modelo .wrap {grid-template-columns:repeat(2,minmax(0,1fr));}
 .barra-fila {grid-template-columns:68px minmax(30px,1fr) 64px; gap:6px; font-size:14px;}
 .tabla-resultados th,.tabla-resultados td {padding:7px; font-size:13px;}
 .resultado h3 {font-size:20px;}
}
"""


def medidor_html(clase: str | None = None) -> str:
    """La aguja representa una clase discreta, con sectores de igual tamaño."""
    cx, cy, radio = 160, 152, 111

    def punto(angulo, distancia):
        radianes = math.radians(angulo)
        return cx + distancia * math.cos(radianes), cy - distancia * math.sin(radianes)

    segmentos = []
    aguja = ""
    sectores = (("negativa", "#ce4c63", 180, 122, "q6-6 12 0"),
                ("neutral", "#b77a16", 118, 62, "h12"),
                ("positiva", "#16816c", 58, 0, "q6 6 12 0"))
    for nombre, color, inicio, fin, boca in sectores:
        x1, y1 = punto(inicio, radio)
        x2, y2 = punto(fin, radio)
        x, y = punto((inicio + fin) / 2, radio)
        segmentos.append(
            f'<path d="M{x1:.2f} {y1:.2f} A{radio} {radio} 0 0 1 {x2:.2f} {y2:.2f}" fill="none" stroke="{color}" stroke-width="38" />'
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="13" fill="none" stroke="#fff" stroke-width="1.4"/>'
            f'<circle cx="{x-4:.2f}" cy="{y-3:.2f}" r="1.25" fill="#fff"/>'
            f'<circle cx="{x+4:.2f}" cy="{y-3:.2f}" r="1.25" fill="#fff"/>'
            f'<path d="M{x-6:.2f} {y+5:.2f}{boca}" fill="none" stroke="#fff" stroke-linecap="round" stroke-width="1.5"/>'
        )
        if clase == nombre:
            angulo = 90 - (inicio + fin) / 2
            aguja = (
                f'<g class="aguja" style="--angulo:{angulo:g}deg">'
                f'<path d="M{cx-4} {cy} Q{cx-2} {cy-58} {cx} {cy-91} '
                f'Q{cx+2} {cy-58} {cx+4} {cy}Z" fill="#241a43"/></g>'
                f'<circle cx="{cx}" cy="{cy}" r="9" fill="#241a43"/>'
                f'<circle cx="{cx}" cy="{cy}" r="3" fill="#fff"/>'
            )
    return (
        '<svg class="medidor" viewBox="0 0 320 170" aria-hidden="true">'
        + "".join(segmentos) + aguja + '</svg>'
        '<div class="medidor-leyenda"><span>Negativa</span><span>Neutral</span><span>Positiva</span></div>'
    )


RESULTADO_VACIO = (
    '<div class="resultado-vacio">' + medidor_html() +
    '<p>Elige un modelo y clasifica un texto para ver el resultado.</p></div>'
)


def _numero(valor) -> float:
    numero = float(valor)
    if not math.isfinite(numero) or not 0 <= numero <= 100.0001:
        raise ValueError("Porcentaje fuera de rango.")
    return min(100.0, numero)


def numero_es(valor, decimales=2) -> str:
    return f"{float(valor):.{decimales}f}".replace(".", ",")


def barras(porcentajes: dict, titulo: str) -> str:
    filas = []
    for clave, nombre, color in CLASES:
        valor = _numero(porcentajes[clave])
        etiqueta = f"{nombre}: {numero_es(valor)} %"
        filas.append(
            f'<div class="barra-fila"><span>{nombre}</span>'
            f'<div class="barra-pista" role="meter" aria-label="{escape(etiqueta)}" '
            f'aria-valuenow="{valor:.6f}" aria-valuemin="0" aria-valuemax="100">'
            f'<div class="barra-relleno {color}" style="width:{valor:.6f}%"></div></div>'
            f'<span class="porcentaje">{numero_es(valor)} %</span></div>'
        )
    return f'<div class="barras" role="group" aria-label="{escape(titulo)}">{"".join(filas)}</div>'


def resultado_html(resultado: dict) -> str:
    modelo = escape(str(resultado["modelo"]))
    etiqueta = escape(str(resultado["etiqueta"]).capitalize())
    n_tramos = int(resultado["n_tramos"])
    partes = ['<section class="resultado" aria-label="Resultado de clasificación" aria-live="polite">',
              medidor_html(str(resultado["etiqueta"]).lower()),
              f'<div class="medidor-titulo"><h3>{etiqueta}</h3>',
              f'<p>{modelo} · {n_tramos} {"tramo" if n_tramos == 1 else "tramos"}</p></div>',
              barras(resultado["porcentajes"], "Porcentajes de polaridad del texto"),
              '<p class="nota">La aguja indica la clase predicha. Las barras muestran las tres probabilidades del modelo.</p>']
    if n_tramos > 1:
        partes.append('<h4>Polaridad por tramo y promedio (P-2)</h4><p>Se aplica el mismo peso a cada tramo, incluidos los tramos solapados.</p>')
        for indice, tramo in enumerate(resultado["porcentajes_por_tramo"], 1):
            partes.append(f'<div class="grupo-tramo"><h4>Tramo {indice}</h4>{barras(tramo, f"Tramo {indice}")}</div>')
        partes.append('<div class="grupo-tramo"><h4>Promedio de tramos</h4>' + barras(resultado["porcentajes"], "Promedio de tramos") + '</div>')
    partes.append('</section>')
    return "".join(partes)


def comparacion_html(resultados: list[dict], errores: dict[str, str]) -> str:
    por_modelo = {r["modelo"]: r for r in resultados}
    filas, grupos = [], []
    for codigo in ("M0", "M1", "M2"):
        resultado = por_modelo.get(codigo)
        if resultado is None:
            mensaje = escape(errores.get(codigo, "No evaluado."))
            filas.append(f'<tr><th scope="row">{codigo}</th><td colspan="5">{mensaje}</td></tr>')
            continue
        porcentajes = resultado["porcentajes"]
        columnas = ''.join(f'<td class="numero">{numero_es(_numero(porcentajes[clave]))} %</td>' for clave, _, _ in CLASES)
        filas.append(f'<tr><th scope="row">{codigo}</th><td>{escape(str(resultado["etiqueta"]).capitalize())}</td>{columnas}<td class="numero">{int(resultado["n_tramos"])}</td></tr>')
        grupos.append(f'<div class="grupo-modelo"><h4>{codigo}</h4>{barras(porcentajes, f"Porcentajes de {codigo}")}</div>')
    tabla = '<div class="tabla-scroll"><table class="tabla-resultados"><caption>Comparación del mismo texto (P-1)</caption><thead><tr><th>Modelo</th><th>Etiqueta</th><th>NEG</th><th>NEU</th><th>POS</th><th>Tramos</th></tr></thead><tbody>' + ''.join(filas) + '</tbody></table></div>'
    return '<section class="resultado">' + tabla + ''.join(grupos) + '</section>'


def error_html(mensaje: str) -> str:
    return f'<div class="mensaje-error" role="alert">{escape(mensaje)}</div>'


def tabla_prueba_html(filas: list[dict]) -> str:
    if not filas:
        return '<p>La ficha de evaluación interna está disponible para la corrida de tres épocas.</p>'
    cuerpo = []
    for fila in filas:
        cuerpo.append('<tr><th scope="row">' + escape(str(fila["modelo"])) + '</th><td class="numero">' + numero_es(fila["exactitud_pct"], 2) + ' %</td><td class="numero">' + numero_es(fila["f1_macro"], 4) + '</td></tr>')
    return '<div class="tabla-scroll"><table class="tabla-resultados"><caption>Evaluación interna de 454 publicaciones</caption><thead><tr><th>Modelo</th><th>Exactitud</th><th>F1 macro</th></tr></thead><tbody>' + ''.join(cuerpo) + '</tbody></table></div>'
