#!/usr/bin/env python3
"""Genera grafana/dashboards/api-red.json (dashboard provisionado de la PoC).

Mantener el dashboard como código permite versionarlo y revisarlo como cualquier
otro artefacto (Dashboards as Code). Ejecutar:  python3 scripts/build_dashboard.py
"""
import json
from pathlib import Path

DS = {"type": "prometheus", "uid": "prometheus"}
API = 'job="demo-api", route=~"/api/.*"'
OUT = Path(__file__).resolve().parent.parent / "grafana" / "dashboards" / "api-red.json"

_next_id = 0


def pid():
    global _next_id
    _next_id += 1
    return _next_id


def target(expr, legend="", ref="A", **extra):
    t = {"datasource": DS, "expr": expr, "legendFormat": legend, "refId": ref, "range": True}
    t.update(extra)
    return t


def thresholds(*steps):
    """steps: (color, value) — el primero con value None."""
    return {"mode": "absolute", "steps": [{"color": c, "value": v} for c, v in steps]}


def stat(title, expr, x, w, unit="none", th=None, mappings=None, legend="", text_mode="value",
         decimals=None, description=""):
    defaults = {"unit": unit, "color": {"mode": "thresholds"},
                "thresholds": th or thresholds(("green", None)), "mappings": mappings or []}
    if decimals is not None:
        defaults["decimals"] = decimals
    return {
        "id": pid(), "type": "stat", "title": title, "description": description, "datasource": DS,
        "gridPos": {"h": 4, "w": w, "x": x, "y": 1},
        "targets": [target(expr, legend, instant=False)],
        "fieldConfig": {"defaults": defaults, "overrides": []},
        "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "colorMode": "background", "graphMode": "area", "textMode": text_mode,
                    "justifyMode": "center", "orientation": "auto", "wideLayout": True},
    }


def timeseries(title, targets, grid, unit="short", th=None, show_th=False, stack=False,
               overrides=None, description="", min_=0, max_=None):
    custom = {"drawStyle": "line", "lineWidth": 2, "fillOpacity": 15 if stack else 8,
              "showPoints": "never", "spanNulls": True,
              "stacking": {"mode": "normal" if stack else "none", "group": "A"},
              "thresholdsStyle": {"mode": "line+area" if show_th else "off"}}
    defaults = {"unit": unit, "min": min_, "custom": custom, "color": {"mode": "palette-classic"},
                "thresholds": th or thresholds(("green", None))}
    if max_ is not None:
        defaults["max"] = max_
    return {
        "id": pid(), "type": "timeseries", "title": title, "description": description,
        "datasource": DS, "gridPos": grid, "targets": targets,
        "fieldConfig": {"defaults": defaults, "overrides": overrides or []},
        "options": {"legend": {"displayMode": "table", "placement": "bottom",
                               "calcs": ["lastNotNull", "max"]},
                    "tooltip": {"mode": "multi", "sort": "desc"}},
    }


def color_override(name_regex, color):
    return {"matcher": {"id": "byRegexp", "options": name_regex},
            "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": color}}]}


def row(title, y):
    return {"id": pid(), "type": "row", "title": title, "collapsed": False,
            "gridPos": {"h": 1, "w": 24, "x": 0, "y": y}, "panels": []}


panels = []

# --- Fila 1: resumen ---------------------------------------------------------
panels.append(row("Resumen: ¿está disponible? ¿está sana?", 0))
panels += [
    stat("Target Prometheus (up)", 'up{job="demo-api"}', 0, 4,
         mappings=[{"type": "value", "options": {
             "0": {"text": "CAÍDO", "color": "red", "index": 0},
             "1": {"text": "ARRIBA", "color": "green", "index": 1}}}],
         th=thresholds(("red", None), ("green", 1)),
         description="1 si Prometheus consigue hacer scrape de /metrics."),
    stat("Health check /health",
         'sum(rate(http_requests_total{job="demo-api", route="/health", status_code="200"}[1m])) > bool 0',
         4, 4,
         mappings=[{"type": "value", "options": {
             "0": {"text": "FALLA", "color": "red", "index": 0},
             "1": {"text": "OK", "color": "green", "index": 1}}}],
         th=thresholds(("red", None), ("green", 1)),
         description="El healthcheck de Docker llama a /health cada 10 s. Sigue en OK durante toda la degradación."),
    stat("Escenario inyectado", 'demo_chaos_mode{job="demo-api"} == 1', 8, 4, legend="{{mode}}",
         text_mode="name", th=thresholds(("blue", None)),
         description="Modo de inyección de fallos activo (solo para correlacionar en la demo)."),
    stat("Tráfico", "api:requests:rate1m", 12, 4, unit="reqps", decimals=1,
         th=thresholds(("blue", None))),
    stat("Errores 5xx (1m)", "api:errors_5xx:ratio_rate1m", 16, 4, unit="percentunit", decimals=1,
         th=thresholds(("green", None), ("yellow", 0.01), ("red", 0.05)),
         description="Proporción de respuestas 5xx sobre el total en /api/*. SLO: < 5 %."),
    stat("Latencia p95 (1m)", "api:latency_seconds:p95_rate1m", 20, 4, unit="s", decimals=2,
         th=thresholds(("green", None), ("yellow", 0.3), ("red", 0.5)),
         description="Percentil 95 estimado desde el histograma. SLO: < 500 ms."),
]

# --- Fila 2: Rate y Errors ---------------------------------------------------
panels.append(row("RED: Rate y Errors", 5))
panels.append(timeseries(
    "Tráfico por código de estado (req/s)",
    [target(f'sum by (status_code) (rate(http_requests_total{{{API}}}[$__rate_interval]))',
            "{{status_code}}")],
    {"h": 8, "w": 12, "x": 0, "y": 6}, unit="reqps", stack=True,
    overrides=[color_override("2..", "green"), color_override("4..", "yellow"),
               color_override("5..", "red")],
    description="Tráfico total apilado. Si las barras rojas crecen, hay errores aunque el volumen sea normal."))
panels.append(timeseries(
    "Tasa de errores (%)",
    [target("api:errors_5xx:ratio_rate1m", "5xx (errores del servidor)"),
     target(f'(sum(rate(http_requests_total{{{API}, status_code=~"4.."}}[1m])) or vector(0)) '
            f'/ sum(rate(http_requests_total{{{API}}}[1m]))', "4xx (errores del cliente)", "B")],
    {"h": 8, "w": 12, "x": 12, "y": 6}, unit="percentunit",
    th=thresholds(("transparent", None), ("red", 0.05)), show_th=True,
    overrides=[color_override("5xx.*", "red"), color_override("4xx.*", "yellow")],
    description="Línea roja = umbral de alerta (5 %). Los 4xx se muestran aparte: suelen ser culpa del cliente y no cuentan para el SLO."))

# --- Fila 3: Duration --------------------------------------------------------
panels.append(row("RED: Duration (latencia)", 14))
q = lambda p: (f'histogram_quantile({p}, sum by (le) '
               f'(rate(http_request_duration_seconds_bucket{{{API}}}[$__rate_interval])))')
panels.append(timeseries(
    "Latencia: media vs percentiles",
    [target(f'sum(rate(http_request_duration_seconds_sum{{{API}}}[$__rate_interval])) / '
            f'sum(rate(http_request_duration_seconds_count{{{API}}}[$__rate_interval]))', "media", "A"),
     target(q(0.50), "p50", "B"), target(q(0.95), "p95", "C"), target(q(0.99), "p99", "D")],
    {"h": 9, "w": 12, "x": 0, "y": 15}, unit="s",
    th=thresholds(("transparent", None), ("red", 0.5)), show_th=True,
    overrides=[color_override("media", "blue"), color_override("p50", "green"),
               color_override("p95", "orange"), color_override("p99", "red")],
    description="Con latencia parcial (25 % de peticiones lentas) la media y la mediana casi no se mueven; p95/p99 sí."))
panels.append({
    "id": pid(), "type": "heatmap", "title": "Distribución de latencia (buckets del histograma)",
    "description": "Cada columna es un intervalo de tiempo; cada fila un bucket. Permite ver distribuciones bimodales.",
    "datasource": DS, "gridPos": {"h": 9, "w": 12, "x": 12, "y": 15},
    "targets": [target(f'sum by (le) (increase(http_request_duration_seconds_bucket{{{API}}}[$__rate_interval]))',
                       "{{le}}", format="heatmap")],
    "fieldConfig": {"defaults": {}, "overrides": []},
    "options": {"calculate": False, "yAxis": {"unit": "s", "axisPlacement": "left"},
                "cellGap": 1, "color": {"mode": "scheme", "scheme": "Oranges", "scale": "exponential",
                                        "exponent": 0.5, "steps": 64},
                "rowsFrame": {"layout": "auto"}, "tooltip": {"mode": "single", "yHistogram": True},
                "legend": {"show": True}, "exemplars": {"color": "rgba(255,0,255,0.7)"}},
})

# --- Fila 4: diagnóstico -----------------------------------------------------
panels.append(row("Diagnóstico: ¿dónde está el problema?", 24))
panels.append(timeseries(
    "Tasa de errores 5xx por ruta",
    [target(f'(sum by (route) (rate(http_requests_total{{{API}, status_code=~"5.."}}[1m])) '
            f'or 0 * sum by (route) (rate(http_requests_total{{{API}}}[1m]))) / '
            f'sum by (route) (rate(http_requests_total{{{API}}}[1m]))', "{{route}}")],
    {"h": 8, "w": 8, "x": 0, "y": 25}, unit="percentunit"))
panels.append(timeseries(
    "Latencia p95 por ruta",
    [target(f'histogram_quantile(0.95, sum by (le, route) '
            f'(rate(http_request_duration_seconds_bucket{{{API}}}[$__rate_interval])))', "{{route}}")],
    {"h": 8, "w": 8, "x": 8, "y": 25}, unit="s"))
panels.append(timeseries(
    "Saturación: peticiones en curso y event loop lag",
    [target('http_requests_in_flight{job="demo-api"}', "peticiones en curso", "A"),
     target('nodejs_eventloop_lag_p99_seconds{job="demo-api"} * 1000', "event loop lag p99 (ms)", "B")],
    {"h": 8, "w": 8, "x": 16, "y": 25}, unit="short",
    description="Con latencia por espera (I/O) las peticiones en curso suben pero el event loop no se bloquea."))

panels.append(row("Alertas y recursos", 33))
panels.append({
    "id": pid(), "type": "state-timeline", "title": "Estado de las alertas de Prometheus",
    "datasource": DS, "gridPos": {"h": 7, "w": 12, "x": 0, "y": 34},
    "targets": [target('max by (alertname) (ALERTS{alertname=~"Api.*", alertstate="firing"} * 2 '
                       'or ALERTS{alertname=~"Api.*", alertstate="pending"})', "{{alertname}}")],
    "fieldConfig": {"defaults": {
        "color": {"mode": "thresholds"},
        "thresholds": thresholds(("yellow", None), ("red", 2)),
        "mappings": [{"type": "value", "options": {
            "1": {"text": "PENDING", "color": "yellow", "index": 0},
            "2": {"text": "FIRING", "color": "red", "index": 1}}}],
        "custom": {"fillOpacity": 80, "lineWidth": 0}}, "overrides": []},
    "options": {"showValue": "auto", "mergeValues": True, "rowHeight": 0.8, "alignValue": "center",
                "legend": {"showLegend": False}, "tooltip": {"mode": "single"}},
})
panels.append(timeseries(
    "Recursos del proceso",
    [target('rate(process_cpu_seconds_total{job="demo-api"}[$__rate_interval])', "CPU (núcleos)", "A"),
     target('process_resident_memory_bytes{job="demo-api"} / 1024 / 1024', "memoria RSS (MiB)", "B")],
    {"h": 7, "w": 12, "x": 12, "y": 34}, unit="short"))

dashboard = {
    "uid": "api-red",
    "title": "API demo — Señales RED (Prometheus)",
    "description": "PoC: detección de degradaciones en una API con Prometheus y Grafana",
    "tags": ["poc", "red", "prometheus"],
    "timezone": "browser",
    "schemaVersion": 39,
    "version": 1,
    "editable": True,
    "graphTooltip": 1,
    "refresh": "5s",
    "time": {"from": "now-15m", "to": "now"},
    "timepicker": {"refresh_intervals": ["5s", "10s", "30s", "1m"]},
    "templating": {"list": []},
    "annotations": {"list": [{
        "builtIn": 1, "datasource": {"type": "grafana", "uid": "-- Grafana --"}, "enable": True,
        "hide": True, "iconColor": "rgba(0, 211, 255, 1)", "name": "Annotations & Alerts",
        "type": "dashboard"}]},
    "panels": panels,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Dashboard escrito en {OUT}")
