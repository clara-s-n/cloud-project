#!/usr/bin/env bash
# Ejecuta los tres escenarios de la PoC uno detrás de otro y, al final de cada
# uno, imprime una "foto" de las señales RED tomada desde Prometheus.
#
# Uso:  ./scripts/demo.sh            (3 min por escenario)
#       DURATION=2m ./scripts/demo.sh
#       ./scripts/demo.sh latencia   (solo un escenario: normal | latencia | errores)
set -uo pipefail
cd "$(dirname "$0")/.."

DURATION="${DURATION:-3m}"
RATE="${RATE:-30}"
SCENARIOS=("${@:-normal latencia errores}")
read -r -a SCENARIOS <<< "${SCENARIOS[*]}"

echo "==> Levantando el laboratorio (API, Prometheus, Grafana)..."
docker compose up -d --build api prometheus grafana >/dev/null

echo "==> Esperando a que la API responda..."
for _ in $(seq 1 30); do
  curl -fs http://localhost:3000/health >/dev/null && break
  sleep 1
done

cat <<EOF

  Grafana     http://localhost:3001   (dashboard "API demo — Señales RED")
  Prometheus  http://localhost:9090/alerts
  API         http://localhost:3000/health

EOF

for scenario in "${SCENARIOS[@]}"; do
  echo "================================================================"
  echo "==> Escenario: ${scenario}  (${DURATION} a ${RATE} req/s)"
  echo "================================================================"
  # k6 devuelve código != 0 si fallan los umbrales; en los escenarios de
  # degradación eso es lo esperado, así que no abortamos.
  docker compose run --rm -e DURATION="$DURATION" -e RATE="$RATE" -e KEEP_CHAOS=1 \
    k6 run --quiet "/scripts/${scenario}.js"
  code=$?
  # Foto tomada 3 s antes del final de k6, para que la ventana de 1 min no
  # incluya la pausa entre escenarios.
  end_ts=$(( $(date +%s) - 3 ))
  echo "--- k6 terminó con código ${code} (≠0 = algún umbral superado)"
  echo
  AT="$end_ts" ./scripts/snapshot.sh "$scenario"
  echo
done

echo "==> Restaurando modo normal"
curl -fs -X POST -H 'Content-Type: application/json' -d '{"mode":"normal"}' \
  http://localhost:3000/admin/chaos && echo
