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
    W, H = 470, 330
    x0, x1, y0, y1 = 52, 462, 290, 30
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
    W, H = 250, 398
    x0, x1, y0, y1 = 40, 244, 356, 34
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
    """Flujo de la PoC: cuatro pasos con el mismo estilo (ícono en círculo, nombre y función)."""
    W, H = 1043, 146
    steps = [
        ("load", "k6", "genera 30 req/s"),
        ("cube", "API Node.js", "expone métricas RED"),
        ("radar", "Prometheus", "recolecta y alerta"),
        ("dashboard", "Grafana", "dashboard RED"),
    ]
    cw, r, cy = W / 4, 38, 44
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Flujo de la prueba de concepto: k6, API, Prometheus, Grafana">',
           f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
           f'<path d="M0,0 L10,5 L0,10 z" fill="{ORANGE}"/></marker></defs>']
    for i, (ic, title, desc) in enumerate(steps):
        cx = cw * (i + 0.5)
        out.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="{r}" fill="#FBFAF7" stroke="#CFC8BA" stroke-width="2"/>')
        out.append(icon_at(ic, INK2, f"{cx - 23:.1f}", cy - 23, 46))
        out.append(f'<circle cx="{cx - r + 4:.1f}" cy="{cy - r + 6}" r="13" fill="{ORANGE}"/>')
        out.append(f'<text x="{cx - r + 4:.1f}" y="{cy - r + 11.5}" text-anchor="middle" class="num">{i + 1}</text>')
        out.append(f'<text x="{cx:.1f}" y="{cy + r + 32}" text-anchor="middle" class="box" fill="{INK}">{title}</text>')
        out.append(f'<text x="{cx:.1f}" y="{cy + r + 56}" text-anchor="middle" class="desc" fill="{MUTED}">{desc}</text>')
        if i < 3:
            out.append(f'<line x1="{cx + r + 18:.1f}" x2="{cx + cw - r - 18:.1f}" y1="{cy}" y2="{cy}" '
                       f'stroke="{ORANGE}" stroke-width="3" marker-end="url(#ah)"/>')
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
    return (f'<svg viewBox="0 0 120 150" width="70" role="img" aria-label="Health check: 200 OK">'
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
        # Carga: pulso de actividad (k6)
        "load": f'<path d="M3,26 H13 L18,10 L27,40 L32,24 H45" {s}/>',
        # API: cubo
        "cube": f'<path d="M24,5 L42,15 V34 L24,44 L6,34 V15 Z" {s}/><path d="M6,15 L24,25 L42,15 M24,25 V44" {s}/>',
        # Recolectar: radar
        "radar": f'<circle cx="24" cy="24" r="18" {s}/><circle cx="24" cy="24" r="9" {s}/>'
                 f'<path d="M24,24 L37,11" {s}/><circle cx="24" cy="24" r="3" fill="{color}"/>',
        # Visualizar: dashboard
        "dashboard": f'<rect x="5" y="8" width="38" height="32" rx="4" {s}/><path d="M5,16 H43" {s}/>'
                     f'<path d="M14,33 V27 M22,33 V22 M30,33 V25 M38,33 V20" {s}/>',
        # Servidor (API)
        "server": f'<rect x="6" y="6" width="36" height="15" rx="3" {s}/><rect x="6" y="27" width="36" height="15" rx="3" {s}/>'
                  f'<circle cx="14" cy="13.5" r="2" fill="{color}"/><circle cx="14" cy="34.5" r="2" fill="{color}"/>',
    }[kind]
    return f'<svg viewBox="0 0 48 48" width="{size}" height="{size}" aria-hidden="true">{body}</svg>'


def icon_at(kind, color, x, y, size):
    """Ícono dentro de otro SVG, en la posición (x, y)."""
    return icon(kind, color, size).replace("<svg ", f'<svg x="{x}" y="{y}" ', 1)


def failing_api():
    """Servidor con alerta roja: la API sí está fallando."""
    return (f'<svg viewBox="0 0 64 64" width="66" role="img" aria-label="API con fallos">'
            + icon_at("server", "#B7C0CE", 0, 4, 54)
            + f'<circle cx="46" cy="46" r="15" fill="{CRIT}" stroke="{INK}" stroke-width="3"/>'
            f'<path d="M46,37 V48" stroke="#fff" stroke-width="4" stroke-linecap="round"/>'
            f'<circle cx="46" cy="54" r="2.4" fill="#fff"/></svg>')


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


def scorecard():
    """¿Qué detectó cada fallo? Filas = señal, columnas = escenario; resaltadas las detecciones."""
    cols = [("Normal", OK), ("Latencia", "#E0A12E"), ("Errores", CRIT)]
    rows = [
        ("shield", "/health", ["200 OK", "200 OK", "200 OK"], [None, None, None]),
        ("duration", "Latencia p95", ["52 ms", "1,4 s", "47 ms"], [None, 1, None]),
        ("errors", "Errores 5xx", ["0 %", "0 %", "12 %"], [None, None, 2]),
        ("bell", "Alerta a los", ["—", "75 s", "85 s"], [None, 1, 2]),
    ]
    tint = {1: "#FCEFD6", 2: "#FBE1DF"}
    head = "".join(f'<th style="border-bottom:4px solid {c}">{t}</th>' for t, c in cols)
    body = []
    for ic, name, vals, hits in rows:
        cells = []
        for v, h in zip(vals, hits):
            if h:
                cells.append(f'<td class="hit" style="background:{tint[h]}">{v}</td>')
            elif name == "/health":
                cells.append(f'<td class="okc">{v}</td>')
            else:
                cells.append(f'<td>{v}</td>')
        body.append(f'<tr><th class="rh">{icon(ic, INK2, 28)}<span>{name}</span></th>{"".join(cells)}</tr>')
    return f'<table class="sc"><tr><th></th>{head}</tr>{"".join(body)}</table>'

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
.ax {{ font-size: 16px; fill: {MUTED}; }}
.cat {{ font-size: 18px; font-weight: 700; fill: {INK}; }}
.cat.sm {{ font-size: 14px; }}
.val {{ font-size: 16px; fill: {INK2}; }}
.lbl {{ font-size: 16px; fill: {INK}; }}
.b {{ font-weight: 700; fill: {INK}; }}
.num {{ font-size: 17px; font-weight: 800; fill: #fff; }}
.step {{ font-size: 15px; font-weight: 700; fill: {ORANGE}; letter-spacing: .5px; text-transform: uppercase; }}
.box {{ font-size: 24px; font-weight: 800; }}
.desc {{ font-size: 16px; }}
.scn {{ font-size: 15px; }}
.scn2 {{ font-size: 15px; fill: {MUTED}; }}

header {{ background: {INK}; color: #F6F4EF; padding: 20px 40px 14px; }}
.eyebrow {{ font-size: 15px; font-weight: 700; letter-spacing: 2.5px; text-transform: uppercase; color: #F09A63; }}
.hd {{ display: flex; align-items: center; gap: 24px; }}
.hl {{ flex: 1; }}
h1 {{ font-size: 64px; line-height: .98; font-weight: 800; letter-spacing: -2.2px; margin: 6px 0 8px; }}
.badge {{ display: flex; flex-direction: column; align-items: center; gap: 4px; }}
.badges {{ display: flex; align-items: center; gap: 10px; }}
.neq {{ font-size: 44px; font-weight: 800; color: #F09A63; }}
.badge.bad span {{ color: #FF8A86; }}
.badge span {{ font-size: 22px; font-weight: 800; color: #7FD3A6; line-height: 1.1; text-align: center; }}
.badge small {{ display: block; font-size: 15px; font-weight: 600; color: #B7C0CE; }}
h1 .ne {{ color: #F09A63; }}
.subtitle {{ font-size: 19px; line-height: 1.25; color: #D5DBE5; }}

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
.small {{ font-size: 15.5px; line-height: 1.35; color: {MUTED}; }}

.scen {{ margin-top: 8px; }}

.res {{ display: grid; grid-template-columns: 1.15fr 1fr; gap: 14px; }}
.res > .card {{ display: flex; flex-direction: column; justify-content: space-between; }}
table.sc {{ width: 100%; border-collapse: separate; border-spacing: 0 6px; }}
table.sc th {{ font-size: 17px; font-weight: 800; text-align: center; padding: 4px 4px 6px; }}
table.sc th.rh {{ text-align: left; font-size: 17px; white-space: nowrap; }}
table.sc th.rh svg {{ vertical-align: middle; margin-right: 6px; }}
table.sc td {{ text-align: center; font-size: 19px; font-weight: 600; color: {INK2}; padding: 11px 4px; border-radius: 8px; }}
table.sc td.okc {{ color: {OK}; font-weight: 700; }}
table.sc td.hit {{ font-size: 28px; font-weight: 800; color: {INK}; }}
.cap {{ display: flex; align-items: center; gap: 8px; font-size: 16.5px; margin-top: 4px; }}
.def {{ font-size: 15px; color: {INK2}; margin-top: 4px; }}
.legend {{ display: flex; gap: 14px; font-size: 15.5px; color: {INK2}; margin: 2px 0 0; }}
.legend i {{ display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 5px; vertical-align: -1px; }}

.find {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
.find .card {{ padding: 8px 16px; display: flex; align-items: center; gap: 14px; }}
.find .card svg {{ flex: none; }}
.find .small {{ margin-top: 3px; }}
.find .k {{ font-size: 36px; font-weight: 800; letter-spacing: -1.5px; line-height: 1.05; color: {ORANGE}; }}
.find .card.dark {{ background: {INK}; border-color: {INK}; color: #F6F4EF; }}
.find .card.dark .small {{ color: #C8CFDA; }}
.find .card.dark .k {{ color: #F09A63; }}
.find .t {{ font-size: 17px; font-weight: 800; line-height: 1.25; }}

.concl {{ display: grid; grid-template-columns: 1.35fr 1fr; gap: 16px; align-items: center; }}
.closing {{ background: {INK}; color: #F6F4EF; border-radius: 14px; padding: 12px 18px; font-size: 18px; line-height: 1.4; }}
.closing b {{ color: #F09A63; }}
.cl {{ display: flex; flex-direction: column; gap: 8px; }}
.cl > div {{ display: flex; align-items: center; gap: 10px; font-size: 16.5px; line-height: 1.3; }}
.cl svg {{ flex: none; }}

footer {{ background: #ECE8DF; padding: 10px 40px; display: flex; gap: 22px; align-items: center; }}
.refs {{ flex: 1; font-size: 14px; line-height: 1.45; color: {INK2}; }}
.auth {{ font-size: 20px; font-weight: 800; color: {INK}; margin-bottom: 4px; }}
.qr {{ width: 84px; height: 84px; background: #fff; padding: 7px; border-radius: 8px; flex: none; }}
.qrtxt {{ font-size: 14.5px; color: {INK2}; width: 175px; line-height: 1.35; }}
</style></head>
<body><div class="page">

<header>
  <div class="hd"><div class="hl">
  <h1>Disponible<br><span class="ne">no significa sano</span></h1>
  <p class="subtitle">Detección de degradaciones en una API mediante monitoreo con Prometheus y Grafana</p>
  </div>
  <div class="badges">
    <div class="badge">{shield()}<span><small>/health</small>200 OK</span></div>
    <div class="neq">≠</div>
    <div class="badge bad">{failing_api()}<span><small>la API</small>falla</span></div>
  </div></div>
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
  <h2><span class="n">3</span>Resultados: ¿qué detectó cada fallo?</h2>
  <div class="res">
    <div class="card">
      {scorecard()}
      <p class="cap">{icon("shield", OK, 26)}<span>En los tres escenarios, <b>/health respondió 200 OK</b>: no vio ningún fallo.</span></p>
    </div>
    <div class="card">
      <h3>Latencia por escenario (ms)</h3>
      <div class="legend"><span><i style="background:{BLUE}"></i>mediana</span><span><i style="background:{AQUA}"></i>media</span><span><i style="background:{ORANGE}"></i>p95</span></div>
      <p class="def"><b>p95:</b> el 95 % de las solicitudes tardó ese tiempo o menos.</p>
      {latency_chart()}
    </div>
  </div>
</section>

<section>
  <h2><span class="n">4</span>Hallazgos</h2>
  <div class="find">
    <div class="card">{icon("duration", ORANGE, 46)}<div><p class="k">47 ms</p><p class="t">Con un 12 % de errores, el p95 siguió bajo</p><p class="small">Los 500 responden rápido: medir solo latencia no alcanza.</p></div></div>
    <div class="card">{icon("search", BLUE, 46)}<div><p class="k">12 % vs 0 %</p><p class="t">Un bug de instrumentación ocultaba los errores</p><p class="small"><b>k6</b> (cliente) registró 12 % de 5xx; <b>Prometheus</b> mostraba 0 % por una etiqueta mal asignada.</p></div></div>
  </div>
</section>

<section>
  <h2><span class="n">5</span>Conclusiones</h2>
  <div class="concl">
    <p class="closing">En nuestro laboratorio, <b>/health respondió 200 OK en los tres escenarios</b>. La alerta de latencia detectó la lentitud en <b>75 s</b> y la de errores detectó las respuestas 5xx en <b>85 s</b>.</p>
    <div class="cl">
      <div>{icon("bell", ORANGE, 40)}<span><b>Alertar por p95 y % de errores</b>, no por promedio ni por un chequeo binario</span></div>
      <div>{icon("search", BLUE, 40)}<span><b>Validar la instrumentación</b> contra una fuente independiente</span></div>
    </div>
  </div>
</section>
</main>

<footer>
  <div class="refs"><p class="auth">{AUTORES}</p><b>Referencias.</b> Beyer et al. (2016) <i>Site Reliability Engineering</i>, cap. 6, O’Reilly ·
  Wilkie (2018) <i>The RED Method</i>, Grafana Labs · Prometheus Authors, <i>Documentation</i>.</div>
  <div class="qrtxt"><b>Código, datos y demo</b><br>Escanea para ver el repositorio y reproducir el laboratorio.</div>
  <div class="qr">{QR}</div>
</footer>

</div></body></html>
"""

OUT.write_text(HTML, encoding="utf-8")
print(f"Póster escrito en {OUT}")
