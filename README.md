# Detección de degradaciones en una API con Prometheus y Grafana

Proyecto final, Electiva Cloud Computing. Categoría **3.2: CNCF / Observabilidad**.

> **Pregunta de investigación:** ¿cómo detectamos que una API tiene problemas de rendimiento o errores
> **aunque siga disponible**?

Una API puede responder `200 OK` en `/health` y aparecer como "arriba" en cualquier monitor de disponibilidad
mientras una cuarta parte de sus usuarios espera más de un segundo o una de cada ocho peticiones falla.
En este laboratorio esas degradaciones se provocan de forma controlada y se detectan con las **señales RED**
(*Rate, Errors, Duration*), que expone la API, recoge Prometheus y muestra Grafana.

## Arquitectura

```
          ┌────────────┐  HTTP (30 req/s)   ┌───────────────────────────┐
          │    k6      │ ─────────────────▶ │  API Node.js / Express    │
          │ (carga)    │  POST /admin/chaos │  prom-client → /metrics   │
          └────────────┘ ─────────────────▶ │  /health (siempre 200)    │
                                            └─────────────┬─────────────┘
                                                          │ scrape cada 5 s (pull)
                                            ┌─────────────▼─────────────┐
                                            │  Prometheus (TSDB)        │
                                            │  recording + alert rules  │
                                            └─────────────┬─────────────┘
                                                          │ PromQL
                                            ┌─────────────▼─────────────┐
                                            │  Grafana (dashboard RED)  │
                                            └───────────────────────────┘
```

| Componente | Versión | Puerto |
|---|---|---|
| API (Node 22 + Express 4 + prom-client 15) | build local | `3000` |
| Prometheus | `v3.5.0` (LTS) | `9090` |
| Grafana | `12.1.0` | `3001` (anónimo lectura · `admin`/`admin`) |
| k6 | `1.3.0` | (se ejecuta bajo demanda) |

## Requisitos

- Docker y Docker Compose v2.
- `curl` y `python3` (solo para `scripts/snapshot.sh`).
- No hace falta tener Node ni k6 instalados: todo corre en contenedores.

## Puesta en marcha

```bash
docker compose up -d --build
```

- Grafana: <http://localhost:3001>. El dashboard **"API demo — Señales RED"** es la página de inicio.
- Prometheus: <http://localhost:9090/alerts> (alertas) y <http://localhost:9090/query>.
- Métricas crudas de la API: <http://localhost:3000/metrics>.

## Escenarios de la PoC

Los tres escenarios usan **el mismo tráfico**: tasa constante de 30 req/s y la misma mezcla de endpoints
(60 % listado, 25 % detalle, 15 % pedidos). Lo único que cambia es el fallo inyectado, así que cualquier
diferencia en las métricas se debe al fallo y no a la carga.

| Escenario | Script | Fallo inyectado | Qué debería verse |
|---|---|---|---|
| 1. Normal | `k6/normal.js` | ninguno | Línea base: p95 ≈ 50 ms, 0 % de errores |
| 2. Latencia | `k6/latencia.js` | 25 % de las peticiones +1,2 s (±25 %) | p95/p99 > 1 s, mientras la mediana sigue en ~20 ms; alerta `ApiLatenciaP95Alta` |
| 3. Errores | `k6/errores.js` | 12 % de las peticiones → `500` | Errores 5xx ≈ 12 %, latencia normal; alerta `ApiTasaErroresAlta` |

En los tres casos `up = 1` y `/health = 200`.

### Ejecutar todo de una vez

```bash
./scripts/demo.sh                 # 3 min por escenario
DURATION=2m ./scripts/demo.sh     # más corto, para la exposición
./scripts/demo.sh latencia        # solo un escenario
```

Al terminar cada escenario, `scripts/snapshot.sh` consulta la API HTTP de Prometheus e imprime las señales.

### Ejecutar un escenario a mano

```bash
docker compose run --rm k6 run /scripts/normal.js
docker compose run --rm -e DURATION=2m -e RATE=50 k6 run /scripts/latencia.js
```

k6 termina con código `99` cuando se supera un umbral (`p(95)<300ms`, `errores<1%`). En los escenarios
de degradación es lo esperado.

### Inyectar fallos sin k6

```bash
curl -X POST localhost:3000/admin/chaos -H 'Content-Type: application/json' -d '{"mode":"latency"}'
curl -X POST localhost:3000/admin/chaos -H 'Content-Type: application/json' \
     -d '{"latencyMs":800,"latencyRatio":0.5,"errorRatio":0.03}'      # configuración libre
curl -X POST localhost:3000/admin/chaos -H 'Content-Type: application/json' -d '{"mode":"normal"}'
```

## Métricas y reglas

**Instrumentación** ([`api/src/server.js`](api/src/server.js)):

| Métrica | Tipo | Señal |
|---|---|---|
| `http_requests_total{method,route,status_code}` | Counter | Rate y Errors |
| `http_request_duration_seconds{method,route,status_code}` | Histogram (13 buckets, 5 ms–5 s) | Duration |
| `http_requests_in_flight` | Gauge | Saturación |
| `nodejs_*`, `process_*` | métricas por defecto | Recursos / event loop |
| `demo_chaos_mode`, `demo_chaos_config` | Gauge | Solo para correlacionar la demo |

La etiqueta `route` lleva la **plantilla** de la ruta (`/api/products/:id`) y no la URL real. Con la URL
cada id crearía una serie temporal nueva y la cardinalidad crecería sin límite.

**Reglas** ([`prometheus/rules/api-rules.yml`](prometheus/rules/api-rules.yml)):

| Regla | Expresión (resumen) | Umbral |
|---|---|---|
| `api:errors_5xx:ratio_rate1m` | 5xx / total, ventana 1 min | — |
| `api:latency_seconds:p95_rate1m` | `histogram_quantile(0.95, …)` | — |
| `ApiCaida` | `up == 0` durante 30 s | crítica |
| `ApiTasaErroresAlta` | errores > 5 % durante 1 min | warning |
| `ApiLatenciaP95Alta` | p95 > 500 ms durante 1 min | warning |
| `ApiSinTrafico` | < 1 req/s con la API arriba, durante 2 min | info |

El dashboard se genera con código ([`scripts/build_dashboard.py`](scripts/build_dashboard.py)) y Grafana
lo carga por *provisioning*:

```bash
python3 scripts/build_dashboard.py && docker compose restart grafana
```

## Estructura

```
api/                 API Node.js instrumentada + Dockerfile
k6/                  Escenarios de carga (normal, latencia, errores)
prometheus/          prometheus.yml + reglas de grabación y alertas
grafana/             Provisioning (datasource, dashboards) + dashboard JSON
scripts/             demo.sh, snapshot.sh, build_dashboard.py
docs/                Resumen ejecutivo, guion de la exposición y preguntas
```

## Documentación

- **[Estado del proyecto y pendientes](docs/ESTADO-DEL-PROYECTO.md)** (empezar por acá)
- [Resumen ejecutivo](docs/resumen-ejecutivo.md)
- [Guion de la exposición y preguntas probables](docs/guion-presentacion.md)
- [Cómo grabar el video de respaldo de la demo](docs/grabar-demo.md)
- [Póster A3 (PDF vectorial)](docs/poster/Grupo-Sena-Lima-Marquez.pdf). Para regenerarlo, editar `scripts/build_poster.py` y ejecutar `./scripts/export_poster.sh Grupo-Sena-Lima-Marquez`.
- [Estado del proyecto y pendientes](docs/ESTADO-DEL-PROYECTO.md)

## Fuera de alcance

Kubernetes, alta disponibilidad de Prometheus, Alertmanager (las alertas se ven en la UI de Prometheus
y en Grafana), almacenamiento a largo plazo (Thanos, Mimir), trazas y logs. El endpoint `/admin/chaos`
no tiene autenticación y existe solo para el laboratorio.

## Limpieza

```bash
docker compose down -v
```
