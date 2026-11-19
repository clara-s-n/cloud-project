#!/usr/bin/env python3
"""Genera docs/poster/poster.html: póster A3 vertical (297 × 420 mm), estilo infografía.

Diseño sencillo: título grande, objetivo en una línea, tres filas de tres tarjetas
(¿Cuál es el problema? · ¿Cómo lo probamos? · ¿Qué encontramos?) con ilustraciones
SVG vectoriales y poco texto, y una banda final con las conclusiones.

Los datos vienen de la corrida de referencia (docs/resultados/demo-run.log y
docs/resultados/linea-de-tiempo-alertas.txt).
Exportar a PDF vectorial:  ./scripts/export_poster.sh Grupo-Sena-Lima-Marquez
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "poster" / "poster.html"
QR = (ROOT / "docs" / "poster" / "qr.svg").read_text(encoding="utf-8")
QR = QR[QR.index("<svg"):].replace('width="29mm" height="29mm"', 'width="100%" height="100%"')

AUTORES = "Ana Clara Sena · Francisco Lima · Nicolás Márquez"

# Paleta
INK = "#17192B"          # trazos y títulos
LAV, LAV_SH, LAV_TX = "#D6D4F0", "#C4C1EA", "#3B3E7A"      # tarjeta lavanda
CRM, CRM_SH, CRM_TX = "#FDF8E2", "#F3EAC2", "#3A3F5C"      # tarjeta crema
PCH, PCH_SH, PCH_TX = "#FDDDA0", "#F7CC7E", "#A8380F"      # tarjeta durazno
BAND = "#5F63D2"         # banda de conclusiones
ACC = "#F28C28"          # acento naranja (íconos de la banda)
GREEN, RED, BLUE = "#2E9A5E", "#D9443F", "#5F63D2"

S = f'stroke="{INK}" stroke-width="3.2" fill="none" stroke-linecap="round" stroke-linejoin="round"'


def svg(body, label, vb="0 0 200 140", w=180):
    return f'<svg viewBox="{vb}" width="{w}" role="img" aria-label="{label}">{body}</svg>'


def person(x, y, fill, scale=1.0):
    """Persona simple: cabeza y torso, con contorno."""
    r = 13 * scale
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" {S.replace("fill=\"none\" ", "")}/>'
            f'<path d="M{x - 22 * scale},{y + 58 * scale} Q{x - 22 * scale},{y + 20 * scale} {x},{y + 20 * scale} '
            f'Q{x + 22 * scale},{y + 20 * scale} {x + 22 * scale},{y + 58 * scale} Z" fill="{fill}" '
            f'{S.replace("fill=\"none\" ", "")}/>')


# --- Ilustraciones -----------------------------------------------------------

def ill_health_ok():
    """Monitor con tilde verde: el health check dice que todo está bien."""
    return svg(
        f'<rect x="30" y="34" width="140" height="86" rx="8" fill="#B9B6E8" opacity=".55"/>'
        f'<rect x="38" y="18" width="124" height="84" rx="8" fill="#FFFFFF" {S.replace("fill=\"none\" ", "")}/>'
        f'<path d="M86,102 L80,122 H120 L114,102" {S}/><path d="M72,122 H128" {S}/>'
        f'<circle cx="100" cy="52" r="20" fill="{GREEN}"/>'
        f'<path d="M90,52 L97,59 L111,45" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<text x="100" y="92" text-anchor="middle" class="svgt" fill="{INK}">200 OK</text>',
        "Monitor con un health check en verde: 200 OK")


def ill_waiting():
    """Cuatro usuarios; uno, resaltado, espera con un reloj encima."""
    body = ""
    for i in range(4):
        x = 34 + i * 44
        col = "#F4F0DA" if i < 3 else ACC
        body += person(x, 62, col, 0.85)
    # reloj sobre el usuario que espera
    body += (f'<circle cx="166" cy="22" r="16" fill="#FFFFFF" {S.replace("fill=\"none\" ", "")}/>'
             f'<path d="M166,22 V13 M166,22 L172,26" {S}/>'
             f'<path d="M150,4 Q140,0 132,8" {S}/><path d="M124,16 Q120,26 126,34" {S}/>')
    return svg(body, "Cuatro usuarios, uno de ellos esperando")


def ill_error():
    """Ventana de navegador con error 500."""
    return svg(
        f'<rect x="28" y="30" width="150" height="96" rx="10" fill="{PCH_SH}"/>'
        f'<rect x="22" y="20" width="150" height="96" rx="10" fill="#FFF7E6" {S.replace("fill=\"none\" ", "")}/>'
        f'<path d="M22,40 H172" {S}/><circle cx="36" cy="30" r="3.5" fill="{INK}"/><circle cx="48" cy="30" r="3.5" fill="{INK}"/>'
        f'<path d="M97,52 L120,92 H74 Z" fill="{RED}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
        f'<path d="M97,64 V78" stroke="#fff" stroke-width="5" stroke-linecap="round"/><circle cx="97" cy="85" r="3" fill="#fff"/>'
        f'<text x="140" y="80" text-anchor="middle" class="svgt" fill="{PCH_TX}">500</text>',
        "Ventana con un error 500")


def ill_traffic():
    """k6: flechas de peticiones hacia la API."""
    body = (f'<rect x="120" y="34" width="62" height="74" rx="10" fill="#B9B6E8" opacity=".55"/>'
            f'<rect x="114" y="26" width="62" height="74" rx="10" fill="#FFFFFF" {S.replace("fill=\"none\" ", "")}/>'
            f'<text x="145" y="70" text-anchor="middle" class="svgt" fill="{INK}">API</text>')
    for k, y in enumerate((36, 63, 90)):
        body += f'<path d="M{18 + k * 6},{y} H96" {S}/><path d="M86,{y - 8} L97,{y} L86,{y + 8}" {S}/>'
    body += f'<text x="58" y="124" text-anchor="middle" class="svgs" fill="{LAV_TX}">30 peticiones/s</text>'
    return svg(body, "Tráfico constante de 30 peticiones por segundo hacia la API")


def ill_chaos():
    """La API con un rayo (errores) y un reloj de arena (lentitud)."""
    return svg(
        f'<rect x="58" y="30" width="88" height="88" rx="12" fill="{CRM_SH}"/>'
        f'<rect x="52" y="22" width="88" height="88" rx="12" fill="#FFFFFF" {S.replace("fill=\"none\" ", "")}/>'
        f'<text x="96" y="74" text-anchor="middle" class="svgt" fill="{INK}">API</text>'
        # rayo
        f'<path d="M168,8 L150,44 H166 L148,82" stroke="{RED}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        # reloj de arena
        f'<path d="M18,34 H44 M18,94 H44 M22,34 Q22,56 31,64 Q22,72 22,94 M40,34 Q40,56 31,64 Q40,72 40,94" {S}/>'
        f'<path d="M25,88 Q31,76 37,88 Z" fill="{ACC}"/>',
        "La API con fallos inyectados: lentitud y errores")


def ill_dashboard():
    """Dashboard con tres señales: Rate, Errors, Duration."""
    return svg(
        f'<rect x="26" y="26" width="160" height="100" rx="10" fill="{PCH_SH}"/>'
        f'<rect x="18" y="16" width="160" height="100" rx="10" fill="#FFF7E6" {S.replace("fill=\"none\" ", "")}/>'
        f'<path d="M34,96 L58,74 L78,84 L104,50 L124,62 L160,30" stroke="{ACC}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M150,28 L161,29 L160,40" {S}/>'
        f'<path d="M34,104 H162" {S}/>'
        f'<text x="98" y="136" text-anchor="middle" class="svgs" fill="{PCH_TX}">Rate · Errors · Duration</text>',
        "Dashboard con las señales RED", vb="0 0 200 142")


def ill_shield():
    """Escudo verde: /health respondió 200 OK siempre."""
    return svg(
        f'<path d="M106,14 L150,30 V66 C150,98 130,118 106,130 C82,118 62,98 62,66 V30 Z" fill="#B9B6E8" opacity=".55"/>'
        f'<path d="M100,8 L144,24 V60 C144,92 124,112 100,124 C76,112 56,92 56,60 V24 Z" fill="{GREEN}" stroke="{INK}" stroke-width="3.2" stroke-linejoin="round"/>'
        f'<path d="M80,64 L95,79 L121,51" stroke="#fff" stroke-width="8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
        "Escudo verde: el health check siempre respondió 200 OK")


def ill_latency():
    """Mini gráfico del escenario de latencia: la media no cruza el umbral de 500 ms; el p95, sí."""
    base, top, vmax = 84, 6, 1450
    h = lambda v: (base - top) * v / vmax
    bars = [("media", 312, "#9C98DE", "312 ms"), ("p95", 1400, ACC, "1,4 s")]
    body = ""
    for i, (name, v, col, lab) in enumerate(bars):
        x = 80 + i * 74
        hh = h(v)
        body += f'<rect x="{x}" y="{base - hh:.1f}" width="44" height="{hh:.1f}" rx="4" fill="{col}" stroke="{INK}" stroke-width="2.4"/>'
        body += f'<text x="{x + 22}" y="{base + 17}" text-anchor="middle" class="svgs" fill="{CRM_TX}">{name}</text>'
        body += f'<text x="{x + 22}" y="{base + 34}" text-anchor="middle" class="svgv" fill="{INK}">{lab}</text>'
    ty = base - h(500)
    body += f'<path d="M6,{ty:.1f} H196" stroke="{RED}" stroke-width="2.6" stroke-dasharray="7 5"/>'
    body += f'<text x="6" y="{ty - 7:.1f}" class="svgs" fill="{RED}">umbral</text>'
    body += f'<text x="6" y="{ty + 17:.1f}" class="svgs" fill="{RED}">500 ms</text>'
    body += f'<path d="M66,{base} H196" {S}/>'
    return svg(body, "Escenario de latencia: media 312 ms, por debajo del umbral de 500 ms; p95 1,4 s, por encima", vb="0 0 202 122", w=230)


def ill_errors():
    """12 de cada 100: cuadrícula de 10 × 10 con 12 celdas rojas y una campana."""
    body = ""
    red = {3, 17, 25, 38, 41, 56, 62, 70, 77, 84, 93, 99}
    for k in range(100):
        r, c = divmod(k, 10)
        col = RED if k in red else "#FFF7E6"
        body += f'<rect x="{4 + c * 10}" y="{4 + r * 10}" width="8.4" height="8.4" rx="1.6" fill="{col}" stroke="{INK}" stroke-width="1.1"/>'
    body += (f'<path d="M122,64 V46 A16,16 0 0 1 154,46 V64 L160,70 H116 Z" fill="{ACC}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
             f'<path d="M132,76 A6,6 0 0 0 144,76" {S}/>'
             f'<path d="M116,32 L110,26 M160,32 L166,26" {S}/>')
    return svg(body, "12 de cada 100 respuestas fueron errores; la alerta sonó", vb="0 0 172 106")


# --- Íconos de la banda (blancos) ----------------------------------------------

def band_icon(kind):
    s = 'stroke="#FFFFFF" stroke-width="3.4" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    body = {
        "neq": f'<rect x="4" y="4" width="40" height="40" rx="8" fill="{ACC}"/>'
               f'<path d="M13,19 H35 M13,29 H35 M30,11 L18,37" {s}/>',
        "pct": f'<rect x="4" y="4" width="40" height="40" rx="8" fill="{ACC}"/>'
               f'<path d="M14,35 L34,13" {s}/><circle cx="16" cy="16" r="4" {s}/><circle cx="32" cy="32" r="4" {s}/>',
        "check": f'<rect x="4" y="4" width="40" height="40" rx="8" fill="{ACC}"/>'
                 f'<circle cx="21" cy="21" r="9" {s}/><path d="M28,28 L36,36" {s}/><path d="M17,21 L20,24 L25,18" {s}/>',
    }[kind]
    return f'<svg viewBox="0 0 48 48" width="46" height="46" aria-hidden="true">{body}</svg>'


def card(tone, ill, text):
    return f'<div class="card {tone}"><div class="ill">{ill}</div><p>{text}</p></div>'


CLOUD = (f'<svg class="cloud" viewBox="0 0 420 220" aria-hidden="true">'
         f'<ellipse cx="210" cy="130" rx="190" ry="70" fill="#CFD2F7" opacity=".55"/>'
         f'<ellipse cx="150" cy="96" rx="90" ry="66" fill="#C6C9F5" opacity=".5"/>'
         f'<ellipse cx="262" cy="80" rx="104" ry="72" fill="#D3D6F8" opacity=".55"/>'
         f'<ellipse cx="330" cy="128" rx="74" ry="52" fill="#C9CCF6" opacity=".45"/></svg>')

HTML = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Póster · Disponible no significa sano</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Inter:wght@700;800&display=swap">
<style>
@page {{ size: 297mm 420mm; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 297mm; height: 420mm; }}
body {{ font-family: 'Nunito', 'Open Sans', Arial, sans-serif; color: {INK}; background: #FFFFFF;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.page {{ width: 1123px; height: 1587px; position: relative; overflow: hidden; display: flex; flex-direction: column; }}
.svgt {{ font-family: 'Inter', Arial, sans-serif; font-size: 19px; font-weight: 800; }}
.svgv {{ font-family: 'Nunito', Arial, sans-serif; font-size: 15px; font-weight: 800; }}
.svgs {{ font-family: 'Nunito', Arial, sans-serif; font-size: 15px; font-weight: 700; }}

.top {{ position: relative; padding: 46px 64px 0; }}
.cloud {{ position: absolute; right: 30px; top: 22px; width: 400px; }}
h1, h2, h3 {{ font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif; position: relative; }}
h1 {{ font-size: 70px; line-height: 1; font-weight: 800; letter-spacing: -2.5px; }}
.sub {{ font-family: 'Inter', Arial, sans-serif; font-size: 36px; font-weight: 700; letter-spacing: -.8px; margin-top: 10px; position: relative; }}
.intro {{ margin-top: 20px; border-left: 4px solid {INK}; padding: 2px 0 2px 18px; font-size: 20px; line-height: 1.45; max-width: 960px; position: relative; }}

main {{ padding: 0 64px 30px; display: flex; flex-direction: column; }}
h2 {{ font-size: 36px; font-weight: 800; letter-spacing: -1px; margin: 18px 0 12px; }}
.row {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; padding-right: 10px; }}
.card {{ position: relative; border: 2.6px solid {INK}; border-radius: 18px; padding: 12px 16px 14px;
  display: flex; flex-direction: column; align-items: center; gap: 6px; }}
.card::before {{ content: ""; position: absolute; left: 9px; top: 9px; right: -11px; bottom: -11px;
  border-radius: 18px; z-index: -1; }}
.card .ill {{ height: 124px; display: flex; align-items: center; justify-content: center; }}
.card p {{ font-size: 18.5px; line-height: 1.38; text-align: center; font-weight: 600; }}
.card p b {{ font-weight: 800; }}
.card .big {{ font-family: 'Inter', Arial, sans-serif; font-size: 28px; font-weight: 800; letter-spacing: -1px; display: block; line-height: 1.1; }}
.lav {{ background: {LAV}; color: {LAV_TX}; }} .lav::before {{ background: {LAV_SH}; }}
.crm {{ background: {CRM}; color: {CRM_TX}; }} .crm::before {{ background: {CRM_SH}; }}
.pch {{ background: {PCH}; color: {PCH_TX}; }} .pch::before {{ background: {PCH_SH}; }}
.row {{ isolation: isolate; }}

.band {{ margin-top: auto; position: relative; top: 0; background: {BAND}; color: #FFFFFF; border: 2.6px solid {INK}; border-bottom: none;
  border-radius: 34px 34px 0 0; margin-left: -3px; margin-right: 18px; padding: 30px 64px 26px; }}
.band h3 {{ font-size: 34px; font-weight: 800; letter-spacing: -.6px; margin-bottom: 18px; }}
.concl {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 28px; }}
.concl .t {{ display: flex; align-items: center; gap: 12px; font-family: 'Inter', Arial, sans-serif; font-size: 24px; font-weight: 800; letter-spacing: -.4px; line-height: 1.1; }}
.concl p {{ font-size: 18.5px; line-height: 1.4; margin-top: 8px; color: #EEF0FF; }}
.foot {{ display: flex; align-items: center; gap: 22px; margin-top: 24px; padding-top: 18px; border-top: 2px solid rgba(255,255,255,.35); }}
.foot .who {{ flex: 1; }}
.foot .auth {{ font-family: 'Inter', Arial, sans-serif; font-size: 22px; font-weight: 800; }}
.foot .meta {{ font-size: 15px; line-height: 1.45; color: #E3E5FF; margin-top: 4px; }}
.qrtxt {{ font-size: 15px; line-height: 1.35; color: #E3E5FF; width: 150px; text-align: right; }}
.qr {{ width: 92px; height: 92px; background: #FFFFFF; padding: 7px; border-radius: 10px; flex: none; }}
</style></head>
<body><div class="page">

<div class="top">
  {CLOUD}
  <h1>Disponible no significa sano</h1>
  <p class="sub">Cómo detectar una API que falla sin caerse</p>
  <p class="intro"><b>Objetivo:</b> descubrir cómo detectar que una API tiene problemas aunque siga respondiendo.
  <b>Hipótesis:</b> medir tráfico, errores y latencia (las señales <b>RED</b>) lo revela.</p>
</div>

<main>
  <h2>¿Cuál es el problema?</h2>
  <div class="row">
    {card("lav", ill_health_ok(), "El chequeo de salud de la API responde <b>“200 OK”</b>: todo parece estar bien.")}
    {card("crm", ill_waiting(), "Pero <b>1 de cada 4 usuarios</b> espera más de un segundo por una respuesta…")}
    {card("pch", ill_error(), "¡…y a otros les llega un <b>error</b>, aunque el monitor siga en verde!")}
  </div>

  <h2>¿Cómo lo probamos?</h2>
  <div class="row">
    {card("lav", ill_traffic(), "<b>k6</b> envía el mismo tráfico constante a una API hecha en Node.js.")}
    {card("crm", ill_chaos(), "Le provocamos fallos a propósito: <b>lentitud</b> en un escenario y <b>errores</b> en otro.")}
    {card("pch", ill_dashboard(), "<b>Prometheus</b> mide las señales y avisa; <b>Grafana</b> las muestra en un panel.")}
  </div>

  <h2>¿Qué encontramos?</h2>
  <div class="row">
    {card("lav", ill_shield(), "<span class='big'>200 OK siempre</span>El chequeo de salud no vio ninguno de los fallos.")}
    {card("crm", ill_latency(), "<span class='big'>p95: 1,4 s</span>La alerta de lentitud sonó a los 75 s. El promedio no habría avisado.")}
    {card("pch", ill_errors(), "<span class='big'>12 % de errores</span>La alerta de errores sonó a los 85 s.")}
  </div>
</main>

<div class="band">
  <h3>Lo que aprendimos</h3>
  <div class="concl">
    <div><p class="t">{band_icon("neq")}Disponible ≠ sano</p><p>Hay que medir tráfico, errores y latencia, no solo si la API responde.</p></div>
    <div><p class="t">{band_icon("pct")}Mirar percentiles</p><p>Alertar por el p95 y el % de errores, no por el promedio.</p></div>
    <div><p class="t">{band_icon("check")}Validar las métricas</p><p>Un error en una etiqueta llegó a ocultar todos los errores.</p></div>
  </div>
  <div class="foot">
    <div class="who"><p class="auth">{AUTORES}</p>
      <p class="meta">Electiva Cloud Computing · CNCF / Observabilidad · Node.js · Prometheus · Grafana · k6 · Docker<br>
      Ref.: Beyer et al. (2016) <i>Site Reliability Engineering</i> · Wilkie (2018) <i>The RED Method</i></p></div>
    <p class="qrtxt"><b>Probalo vos:</b> código, datos y demo en el repositorio</p>
    <div class="qr">{QR}</div>
  </div>
</div>

</div></body></html>
"""

OUT.write_text(HTML, encoding="utf-8")
print(f"Póster escrito en {OUT}")
