#!/usr/bin/env bash
# Consulta la API HTTP de Prometheus y muestra el valor actual de cada señal.
# Uso: ./scripts/snapshot.sh [etiqueta]
set -euo pipefail

PROM="${PROM_URL:-http://localhost:9090}"
LABEL="${1:-ahora}"

# AT permite consultar un instante pasado (timestamp Unix o RFC3339).
AT="${AT:-}"
TIME_ARGS=()
[ -n "$AT" ] && TIME_ARGS=(--data-urlencode "time=$AT")

query() {
  curl -fsG "$PROM/api/v1/query" --data-urlencode "query=$1" "${TIME_ARGS[@]}" |
    python3 -c 'import json,sys; r=json.load(sys.stdin)["data"]["result"]; print(r[0]["value"][1] if r else "nan")'
}

query_all() {
  curl -fsG "$PROM/api/v1/query" --data-urlencode "query=$1" "${TIME_ARGS[@]}" |
    python3 -c 'import json,sys
r = json.load(sys.stdin)["data"]["result"]
print(", ".join("%s(%s)" % (x["metric"]["alertname"], x["metric"]["alertstate"]) for x in r) or "ninguna")'
}

API='job="demo-api", route=~"/api/.*"'
up=$(query 'up{job="demo-api"}')
health=$(query 'sum(rate(http_requests_total{job="demo-api", route="/health", status_code="200"}[1m])) > bool 0')
rps=$(query 'api:requests:rate1m')
err=$(query 'api:errors_5xx:ratio_rate1m')
avg=$(query 'api:latency_seconds:avg_rate1m')
p50=$(query "histogram_quantile(0.5, sum by (le) (rate(http_request_duration_seconds_bucket{$API}[1m])))")
p95=$(query 'api:latency_seconds:p95_rate1m')
p99=$(query "histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket{$API}[1m])))")
alerts=$(query_all 'ALERTS{alertname=~"Api.*"}')

python3 - "$LABEL" "$up" "$health" "$rps" "$err" "$avg" "$p50" "$p95" "$p99" "$alerts" <<'PY'
import sys
label, up, health, rps, err, avg, p50, p95, p99, alerts = sys.argv[1:]
f = lambda v, m=1, d=1: "n/d" if v == "nan" else f"{float(v)*m:.{d}f}"
print(f"Señales RED [{label}] (ventana 1 min)")
print(f"  up={up}  health={'OK' if health == '1' else 'FALLA'}  tráfico={f(rps)} req/s")
print(f"  errores 5xx={f(err,100,2)} %")
print(f"  latencia: media={f(avg,1000,0)} ms  p50={f(p50,1000,0)} ms  p95={f(p95,1000,0)} ms  p99={f(p99,1000,0)} ms")
print(f"  alertas: {alerts}")
PY
