#!/usr/bin/env python3
"""Genera docs/poster/poster.html (póster A3 vertical, 297 × 420 mm) con gráficos SVG vectoriales.

Los datos vienen de la corrida de referencia (docs/resultados/demo-run.log y
docs/resultados/linea-de-tiempo-alertas.txt).
Exportar a PDF vectorial:  ./scripts/export_poster.sh Grupo-Apellido1-Apellido2
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "poster" / "poster.html"
QR = (ROOT / "docs" / "poster" / "qr.svg").read_text(encoding="utf-8")
QR = QR[QR.index("<svg"):].replace('width="29mm" height="29mm"', 'width="100%" height="100%"')

AUTORES = "Ana Clara Sena · Francisco Lima · Nicolás Márquez"

# Paleta de series validada (dataviz validate_palette.js: 3 slots, all-pairs, modo claro).
BLUE, AQUA, ORANGE = "#2a78d6", "#1baf7a", "#eb6834"
INK, INK2, MUTED, GRID = "#141A26", "#3A4354", "#5B6475", "#D9D5CC"
WARN, CRIT, OK = "#C98500", "#D63A39", "#1E7F4F"

SCEN = ["Normal", "Latencia", "Errores"]
LAT = {  # ms, medidos por k6 (cliente)
    "p50": [19, 23, 17],
    "media": [22, 312, 18.5],
    "p95": [52, 1400, 47],
}
ERR = [0, 0, 11.95]  # % de respuestas 5xx, k6


def bar(x, y0, w, h, color):
    """Barra anclada a la base con extremo de datos redondeado (4 px)."""
    if h < 5:
        return f'<rect x="{x:.1f}" y="{y0 - max(h, 1.5):.1f}" width="{w}" height="{max(h, 1.5):.1f}" fill="{color}"/>'
    y, r = y0 - h, 4
    return (f'<path d="M{x:.1f},{y0} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} '
            f'H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} V{y0} Z" fill="{color}"/>')


def latency_chart():
    W, H = 470, 290
    x0, x1, y0, y1 = 52, 462, 248, 34
    vmax = 1600
    sy = lambda v: y0 - v / vmax * (y0 - y1)
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" '
           f'aria-label="Latencia p50, media y p95 por escenario frente al umbral de 500 ms">']
    for v in (0, 500, 1000, 1500):
        y = sy(v)
        out.append(f'<line x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}"/>')
        out.append(f'<text x="{x0 - 8}" y="{y + 5:.1f}" text-anchor="end" class="ax">'
                   f'{"0" if v == 0 else f"{v:,}".replace(",", ".")}</text>')
    out.append(f'<text x="{x0 - 8}" y="16" text-anchor="end" class="ax">ms</text>')
    ty = sy(500)
    out.append(f'<line x1="{x0}" x2="{x1}" y1="{ty:.1f}" y2="{ty:.1f}" stroke="{INK}" stroke-width="2" stroke-dasharray="7 5"/>')
    out.append(f'<text x="{x0 + 4}" y="{ty - 8:.1f}" class="lbl b">umbral de alerta 500 ms</text>')
    gw = (x1 - x0) / 3
    series = [("p50", BLUE), ("media", AQUA), ("p95", ORANGE)]
    bw, gap = 34, 2
    for i, name in enumerate(SCEN):
        c = x0 + gw * (i + 0.5)
        for j, (s, col) in enumerate(series):
            v = LAT[s][i]
            x = c - (3 * bw + 2 * gap) / 2 + j * (bw + gap)
            h = v / vmax * (y0 - y1)
            out.append(bar(x, y0, bw, h, col))
            label = f"{v:g}".replace(".", ",") if v < 1000 else f"{v / 1000:g} s".replace(".", ",")
            weight = " b" if (i == 1 and s != "p50") else ""
            out.append(f'<text x="{x + bw / 2:.1f}" y="{y0 - h - 7:.1f}" text-anchor="middle" class="val{weight}">{label}</text>')
        out.append(f'<text x="{c:.1f}" y="{y0 + 26}" text-anchor="middle" class="cat">{name}</text>')
    out.append(f'<line x1="{x0}" x2="{x1}" y1="{y0}" y2="{y0}" stroke="{INK2}" stroke-width="1.5"/>')
    out.append("</svg>")
    return "".join(out)


def error_chart():
    W, H = 250, 268
    x0, x1, y0, y1 = 40, 244, 226, 34
    vmax = 15
    sy = lambda v: y0 - v / vmax * (y0 - y1)
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Tasa de errores 5xx por escenario frente al umbral del 5 %">']
    for v in (0, 5, 10, 15):
        y = sy(v)
        out.append(f'<line x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}"/>')
        out.append(f'<text x="{x0 - 7}" y="{y + 5:.1f}" text-anchor="end" class="ax">{v}%</text>')
    out.append(f'<text x="{x0 - 7}" y="16" text-anchor="end" class="ax">5xx</text>')
    ty = sy(5)
    out.append(f'<line x1="{x0}" x2="{x1}" y1="{ty:.1f}" y2="{ty:.1f}" stroke="{INK}" stroke-width="2" stroke-dasharray="7 5"/>')
    out.append(f'<text x="{x0 + 4}" y="{ty - 8:.1f}" class="lbl b">umbral 5 %</text>')
    gw = (x1 - x0) / 3
    for i, name in enumerate(SCEN):
        c = x0 + gw * (i + 0.5)
        v = ERR[i]
        h = v / vmax * (y0 - y1)
        if v > 0:
            out.append(bar(c - 22, y0, 44, h, ORANGE))
        out.append(f'<text x="{c:.1f}" y="{y0 - h - 7:.1f}" text-anchor="middle" class="val{" b" if v else ""}">{v:.0f} %</text>')
        out.append(f'<text x="{c:.1f}" y="{y0 + 26}" text-anchor="middle" class="cat sm">{name}</text>')
    out.append(f'<line x1="{x0}" x2="{x1}" y1="{y0}" y2="{y0}" stroke="{INK2}" stroke-width="1.5"/>')
    out.append("</svg>")
    return "".join(out)


def pipeline():
    W, H = 1043, 150
    boxes = [
        ("1", "Generar carga", "k6", ["30 req/s constantes,", "igual en los 3 escenarios"], "#FBFAF7", INK),
        ("2", "Instrumentar", "API Node.js", ["prom-client expone", "Rate, Errors y Duration"], INK, "#F6F4EF"),
        ("3", "Recolectar y alertar", "Prometheus", ["scrape cada 5 s · alertas:", "p95 > 500 ms, 5xx > 5 %"], "#FBFAF7", INK),
        ("4", "Visualizar", "Grafana", ["dashboard RED", "provisionado como código"], "#FBFAF7", INK),
    ]
    bw, gap = 222, 50
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Flujo de la prueba de concepto: k6, API, Prometheus, Grafana">',
           f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
           f'<path d="M0,0 L10,5 L0,10 z" fill="{ORANGE}"/></marker></defs>']
    for i, (n, step, title, desc, bg, fg) in enumerate(boxes):
        x = 3 + i * (bw + gap)
        stroke = ORANGE if i == 2 else ("#CFC8BA" if bg != INK else INK)
        sw = 3 if i == 2 else 2
        out.append(f'<rect x="{x}" y="28" width="{bw}" height="118" rx="12" fill="{bg}" stroke="{stroke}" stroke-width="{sw}"/>')
        out.append(f'<circle cx="{x + 20}" cy="28" r="16" fill="{ORANGE}"/>')
        out.append(f'<text x="{x + 20}" y="34" text-anchor="middle" class="num">{n}</text>')
        out.append(f'<text x="{x + 44}" y="20" class="step">{step}</text>')
        out.append(f'<text x="{x + 18}" y="78" class="box" fill="{fg}">{title}</text>')
        col = "#B7C0CE" if bg == INK else MUTED
        for k, line in enumerate(desc):
            out.append(f'<text x="{x + 18}" y="{106 + k * 20}" class="desc" fill="{col}">{line}</text>')
        if i < 3:
            out.append(f'<line x1="{x + bw + 6}" x2="{x + bw + gap - 7}" y1="87" y2="87" stroke="{ORANGE}" stroke-width="3" marker-end="url(#ah)"/>')
    out.append("</svg>")
    return "".join(out)


def people():
    """Cuatro usuarios, uno resaltado: 1 de cada 4 espera más de 1 s."""
    out = ['<svg viewBox="0 0 250 92" width="150" role="img" aria-label="Uno de cada cuatro usuarios afectado">']
    for i in range(4):
        x = 32 + i * 62
        col = ORANGE if i == 3 else "#9AA3B2"
        out.append(f'<circle cx="{x}" cy="22" r="15" fill="{col}"/>')
        out.append(f'<path d="M{x - 25},90 Q{x - 25},44 {x},44 Q{x + 25},44 {x + 25},90 Z" fill="{col}"/>')
    out.append("</svg>")
    return "".join(out)


def shield():
    """Escudo verde con tilde: el health check dice que todo está bien."""
    return (f'<svg viewBox="0 0 120 150" width="92" role="img" aria-label="Health check: 200 OK">'
            f'<path d="M60,6 L110,24 V68 C110,104 88,128 60,144 C32,128 10,104 10,68 V24 Z" fill="{OK}" stroke="#7FD3A6" stroke-width="3"/>'
            f'<path d="M36,74 L54,92 L86,56" stroke="#fff" stroke-width="11" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            f'</svg>')


def icon(kind, color, size=40):
    """Íconos de línea simples (viewBox 48 × 48)."""
    s = f'stroke="{color}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    body = {
        # Rate: velocímetro
        "rate": f'<path d="M8,34 A16,16 0 1 1 40,34" {s}/><path d="M24,34 L33,20" {s}/>'
                f'<circle cx="24" cy="34" r="3" fill="{color}"/>',
        # Errors: triángulo de alerta
        "errors": f'<path d="M24,7 L43,40 H5 Z" {s}/><path d="M24,19 V29" {s}/>'
                  f'<circle cx="24" cy="34.5" r="2.2" fill="{color}"/>',
        # Duration: cronómetro
        "duration": f'<circle cx="24" cy="27" r="16" {s}/><path d="M24,27 V18" {s}/><path d="M24,27 L30,31" {s}/>'
                    f'<path d="M19,5 H29 M24,5 V11" {s}/>',
        # Escudo con tilde
        "shield": f'<path d="M24,5 L40,11 V24 C40,34 33,41 24,44 C15,41 8,34 8,24 V11 Z" {s}/>'
                  f'<path d="M17,24 L22,29 L31,19" {s}/>',
        # Campana de alerta
        "bell": f'<path d="M12,34 V22 A12,12 0 0 1 36,22 V34 L40,38 H8 Z" {s}/><path d="M20,42 A4,4 0 0 0 28,42" {s}/>',
        # Lupa
        "search": f'<circle cx="21" cy="21" r="12" {s}/><path d="M30,30 L41,41" {s}/>',
    }[kind]
    return f'<svg viewBox="0 0 48 48" width="{size}" height="{size}" aria-hidden="true">{body}</svg>'


def red_signals():
    items = [("rate", BLUE, "Rate", "tráfico (req/s)"),
             ("errors", CRIT, "Errors", "% de errores 5xx"),
             ("duration", ORANGE, "Duration", "latencia p95")]
    return '<div class="red">' + "".join(
        f'<div>{icon(k, c, 38)}<span><b style="color:{c}">{t}</b><br>{d}</span></div>'
        for k, c, t, d in items) + "</div>"


def scenarios():
    """Los tres escenarios como flechas encadenadas, misma carga en todos."""
    W, H, w, tip = 1043, 46, 270, 18
    items = [(OK, "1 · Normal", "sin fallos"),
             ("#F2B544", "2 · Latencia", "25 % tarda +1,2 s"),
             (CRIT, "3 · Errores", "12 % responde 500")]
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Tres escenarios: normal, latencia y errores">']
    for i, (col, t, d) in enumerate(items):
        x = i * (w + 6)
        notch = f"L{x + tip},{H / 2}" if i else ""
        out.append(f'<path d="M{x},0 H{x + w} L{x + w + tip},{H / 2} L{x + w},{H} H{x} {notch} Z" fill="{col}"/>')
        tx = x + (tip + 14 if i else 16)
        fill = INK if i == 1 else "#fff"
        out.append(f'<text x="{tx}" y="{H / 2 + 6}" class="scn" fill="{fill}"><tspan font-weight="800">{t}:</tspan> {d}</text>')
    out.append(f'<text x="{W - 4}" y="{H / 2 + 6}" text-anchor="end" class="scn2">'
               f'<tspan font-weight="700" fill="{INK}">Igual carga:</tspan> 2 min 30 s c/u</text>')
    out.append("</svg>")
    return "".join(out)


def mark(ok, text=None):
    if ok:
        return (f'<span class="mk"><svg viewBox="0 0 24 24" width="20" height="20"><circle cx="12" cy="12" r="11" fill="{OK}"/>'
                f'<path d="M6.5 12.5 L10.5 16 L17.5 8.5" stroke="#fff" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
                f'{text or "detecta"}</span>')
    return f'<span class="mk no">— {text or "igual"}</span>'


MATRIX = [
    ("Disponibilidad", "up · /health", mark(False), mark(False)),
    ("Rate", "req/s", mark(False), mark(False)),
    ("Errors", "% 5xx", mark(False), mark(True, "12 %")),
    ("Duration", "p95", mark(True, "1,4 s"), mark(False)),
    ("Alerta", "sostenida 1 min", mark(True, "75 s"), mark(True, "85 s")),
]
matrix = "".join(
    f'<tr><td><b>{a}</b> <span class="sub">{b}</span></td><td>{c}</td><td>{d}</td></tr>'
    for a, b, c, d in MATRIX)

HTML = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Póster · Disponible no significa sano</title>
<style>
@page {{ size: 297mm 420mm; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 297mm; height: 420mm; }}
body {{ font-family: 'Open Sans', 'Helvetica Neue', Arial, sans-serif; color: {INK}; background: #F6F4EF;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.page {{ width: 1123px; height: 1587px; display: flex; flex-direction: column; overflow: hidden; }}
svg text {{ font-family: 'Open Sans', Arial, sans-serif; }}
.ax {{ font-size: 14px; fill: {MUTED}; }}
.cat {{ font-size: 16px; font-weight: 700; fill: {INK}; }}
.cat.sm {{ font-size: 14px; }}
.val {{ font-size: 14px; fill: {INK2}; }}
.lbl {{ font-size: 14px; fill: {INK}; }}
.b {{ font-weight: 700; fill: {INK}; }}
.num {{ font-size: 17px; font-weight: 800; fill: #fff; }}
.step {{ font-size: 15px; font-weight: 700; fill: {ORANGE}; letter-spacing: .5px; text-transform: uppercase; }}
.box {{ font-size: 25px; font-weight: 800; }}
.desc {{ font-size: 15px; }}
.scn {{ font-size: 15px; }}
.scn2 {{ font-size: 15px; fill: {MUTED}; }}

header {{ background: {INK}; color: #F6F4EF; padding: 20px 40px 14px; }}
.eyebrow {{ font-size: 15px; font-weight: 700; letter-spacing: 2.5px; text-transform: uppercase; color: #F09A63; }}
.hd {{ display: flex; align-items: center; gap: 24px; }}
.hl {{ flex: 1; }}
h1 {{ font-size: 64px; line-height: .98; font-weight: 800; letter-spacing: -2.2px; margin: 6px 0 8px; }}
.badge {{ display: flex; flex-direction: column; align-items: center; gap: 4px; }}
.badge span {{ font-size: 22px; font-weight: 800; color: #7FD3A6; line-height: 1.1; text-align: center; }}
.badge small {{ display: block; font-size: 15px; font-weight: 600; color: #B7C0CE; }}
h1 .ne {{ color: #F09A63; }}
.subtitle {{ font-size: 20px; line-height: 1.25; color: #D5DBE5; }}
.authors {{ margin-top: 6px; font-size: 18px; color: #B7C0CE; display: flex; justify-content: space-between; }}
.authors b {{ color: #F6F4EF; }}

main {{ flex: 1; padding: 8px 40px 8px; display: flex; flex-direction: column; gap: 6px; }}
h2 {{ font-size: 25px; font-weight: 800; letter-spacing: -.3px; display: flex; align-items: center; gap: 10px; margin-bottom: 7px; }}
h2 .n {{ width: 32px; height: 32px; border-radius: 50%; background: {ORANGE}; color: #fff; font-size: 17px;
  display: inline-flex; align-items: center; justify-content: center; }}
h3 {{ font-size: 14px; font-weight: 700; color: {MUTED}; text-transform: uppercase; letter-spacing: 1.3px; margin-bottom: 4px; }}
p {{ font-size: 17px; line-height: 1.4; }}
.card {{ background: #FBFAF7; border: 2px solid #E2DDD2; border-radius: 14px; padding: 14px 18px; }}

.obj {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; }}
.q {{ font-size: 20px; line-height: 1.28; font-weight: 700; }}
.hyp {{ margin-top: 6px; font-size: 15.5px; }}
.red {{ display: flex; gap: 14px; margin-top: 8px; }}
.red > div {{ display: flex; align-items: center; gap: 7px; font-size: 14px; line-height: 1.2; color: {MUTED}; }}
.red b {{ font-size: 15.5px; }}
.versus {{ display: grid; grid-template-columns: 1fr 1fr; padding: 0; overflow: hidden; }}
.versus > div {{ padding: 14px 16px; display: flex; flex-direction: column; gap: 6px; }}
.mon {{ background: #E6F1EA; }}
.usr {{ background: #FBE6DA; }}
.pillok {{ align-self: flex-start; background: {OK}; color: #fff; font-weight: 800; font-size: 20px; padding: 4px 14px; border-radius: 999px; }}
.small {{ font-size: 15px; line-height: 1.35; color: {MUTED}; }}

.scen {{ margin-top: 8px; }}

.res {{ display: grid; grid-template-columns: 1.5fr 0.95fr 1.3fr; gap: 12px; }}
.legend {{ display: flex; gap: 14px; font-size: 14px; color: {INK2}; margin: 2px 0 0; }}
.legend i {{ display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 5px; vertical-align: -1px; }}
table.m {{ width: 100%; border-collapse: collapse; font-size: 15px; }}
table.m th {{ text-align: left; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: {MUTED}; padding: 0 4px 6px; }}
table.m td {{ padding: 4px 4px; border-top: 1.5px solid #E2DDD2; vertical-align: middle; line-height: 1.2; }}
table.m tr:last-child td {{ border-top: 2px solid {INK2}; }}
table.m .sub {{ font-size: 13px; color: {MUTED}; }}
.mk {{ display: inline-flex; align-items: center; gap: 6px; font-weight: 700; color: {OK}; white-space: nowrap; }}
.mk.no {{ color: #8A93A3; font-weight: 600; }}

.find {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
.find .card {{ padding: 10px 14px; display: flex; flex-direction: column; gap: 4px; }}
.find .k {{ font-size: 34px; font-weight: 800; letter-spacing: -1.5px; line-height: 1.05; color: {ORANGE}; }}
.find .card.dark {{ background: {INK}; border-color: {INK}; color: #F6F4EF; }}
.find .card.dark .small {{ color: #C8CFDA; }}
.find .card.dark .k {{ color: #F09A63; }}
.find .t {{ font-size: 15.5px; font-weight: 800; line-height: 1.25; }}

.concl {{ display: grid; grid-template-columns: 1.15fr 1fr; gap: 16px; }}
.cl {{ display: flex; flex-direction: column; gap: 3px; }}
.cl > div {{ display: flex; align-items: center; gap: 10px; font-size: 15.5px; line-height: 1.35; }}
.cl svg {{ flex: none; }}
.tradeoff {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 10px 14px; font-size: 14px; line-height: 1.38; }}
.tradeoff b {{ display: block; font-size: 15px; margin-bottom: 3px; }}

footer {{ background: #ECE8DF; padding: 10px 40px; display: flex; gap: 22px; align-items: center; }}
.refs {{ flex: 1; font-size: 12.5px; line-height: 1.45; color: {INK2}; }}
.qr {{ width: 84px; height: 84px; background: #fff; padding: 7px; border-radius: 8px; flex: none; }}
.qrtxt {{ font-size: 13.5px; color: {INK2}; width: 175px; line-height: 1.35; }}
</style></head>
<body><div class="page">

<header>
  <div class="hd"><div class="hl">
  <p class="eyebrow">Proyecto final · Electiva Cloud Computing · CNCF — Observabilidad</p>
  <h1>Disponible<br><span class="ne">no significa sano</span></h1>
  <p class="subtitle">Detección de degradaciones en una API mediante monitoreo con Prometheus y Grafana</p>
  </div>
  <div class="badge">{shield()}<span><small>/health</small>200 OK</span></div></div>
  <div class="authors"><b>{AUTORES}</b><span>Noviembre 2026</span></div>
</header>

<main>
<section>
  <h2><span class="n">1</span>Objetivo e hipótesis</h2>
  <div class="obj">
    <div class="card">
      <p class="q">¿Cómo detectamos que una API tiene problemas de rendimiento o errores <u>aunque siga disponible</u>?</p>
      <p class="hyp"><b>Hipótesis:</b> las señales <b>RED</b> revelan lo que un health check no ve.</p>
      {red_signals()}
    </div>
    <div class="card versus">
      <div class="mon"><h3>El monitor ve</h3><span class="pillok">200 OK · ARRIBA</span>
        <p class="small">El health check solo pregunta “¿responde?”.</p></div>
      <div class="usr"><h3>El usuario vive</h3>{people()}
        <p class="small"><b style="color:{INK}">1 de cada 4</b> espera más de 1 s.</p></div>
    </div>
  </div>
</section>

<section>
  <h2><span class="n">2</span>Metodología: laboratorio reproducible con Docker Compose</h2>
  {pipeline()}
  <div class="scen">{scenarios()}</div>
</section>

<section>
  <h2><span class="n">3</span>Resultados</h2>
  <div class="res">
    <div class="card">
      <h3>Latencia (ms)</h3>
      <div class="legend"><span><i style="background:{BLUE}"></i>mediana p50</span><span><i style="background:{AQUA}"></i>media</span><span><i style="background:{ORANGE}"></i>p95</span></div>
      {latency_chart()}
    </div>
    <div class="card">
      <h3>Errores 5xx</h3>
      <div class="legend"><span><i style="background:{ORANGE}"></i>% de peticiones</span></div>
      {error_chart()}
    </div>
    <div class="card">
      <h3>¿Qué señal detectó cada fallo?</h3>
      <table class="m"><tr><th style="width:40%">Señal</th><th>Latencia</th><th>Errores</th></tr>{matrix}</table>
      <p class="small" style="margin-top:8px;"><b style="color:{INK}">Disponibilidad nunca cambió.</b> Cada fallo lo detectó una señal distinta.</p>
    </div>
  </div>
</section>

<section>
  <h2><span class="n">4</span>Hallazgos</h2>
  <div class="find">
    <div class="card"><p class="k">×27</p><p class="t">El p95 se disparó; la mediana, no</p><p class="small">p95: 52 ms → 1,4 s. Mediana: 19 → 23 ms.</p></div>
    <div class="card dark"><p class="k">312 ms</p><p class="t">La media no llegó al umbral de 500 ms</p><p class="small">Una alerta por promedio nunca habría sonado.</p></div>
    <div class="card"><p class="k">−16 %</p><p class="t">Con errores, la latencia “mejoró”</p><p class="small">Los 500 responden enseguida: fallar rápido parece ir rápido.</p></div>
    <div class="card"><p class="k">12 % vs 0 %</p><p class="t">Un bug ocultaba los errores</p><p class="small">Etiqueta <i>route</i> mal asignada: k6 veía 12 %, Prometheus 0 %.</p></div>
  </div>
</section>

<section>
  <h2><span class="n">5</span>Conclusiones</h2>
  <div class="concl">
    <div class="cl">
      <div>{icon("shield", OK, 34)}<span><b>Hipótesis confirmada:</b> ambas degradaciones se detectaron en menos de 90 s con la API “disponible”.</span></div>
      <div>{icon("bell", ORANGE, 34)}<span><b>Alertar por percentiles y tasa de errores</b>, nunca por promedio ni por estado binario.</span></div>
      <div>{icon("search", BLUE, 34)}<span><b>Validar la instrumentación:</b> etiquetas correctas, cardinalidad acotada, buckets cerca del umbral.</span></div>
    </div>
    <div class="card tradeoff">
      <div><b style="color:{OK}">A favor</b>Estándar abierto (CNCF), PromQL potente, detección de caídas incluida (pull), todo como código.</div>
      <div><b style="color:{CRIT}">Limitaciones</b>Percentiles aproximados, un solo nodo, cardinalidad delicada. Dicen <i>qué</i> y <i>dónde</i>, no <i>por qué</i>.</div>
    </div>
  </div>
</section>
</main>

<footer>
  <div class="refs"><b>Referencias.</b> Beyer et al. (2016) <i>Site Reliability Engineering</i>, cap. 6, O’Reilly ·
  Wilkie (2018) <i>The RED Method</i>, Grafana Labs · Gregg (2013) <i>The USE Method</i> ·
  Prometheus Authors, <i>Documentation</i> · CNCF (2018) <i>Prometheus graduation</i> ·
  Tene (2015) <i>How NOT to Measure Latency</i>.<br>
  <b>Herramientas.</b> Node.js · Express · prom-client · Prometheus 3.5 · Grafana 12.1 · k6 1.3 · Docker Compose.</div>
  <div class="qrtxt"><b>Código, datos y demo</b><br>Escanea para ver el repositorio y reproducir el laboratorio.</div>
  <div class="qr">{QR}</div>
</footer>

</div></body></html>
"""

OUT.write_text(HTML, encoding="utf-8")
print(f"Póster escrito en {OUT}")
