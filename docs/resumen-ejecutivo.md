---
title: "Detección de degradaciones en una API mediante monitoreo con Prometheus y Grafana"
subtitle: "Resumen ejecutivo. Proyecto final, Electiva Cloud Computing"
author: "Ana Clara Sena · Francisco Lima · Nicolás Márquez"
date: "Noviembre de 2026"
lang: es
---

**Categoría:** 3.2 Cloud Native Computing Foundation (CNCF). Observabilidad.

# 1. Problema y objetivo

Un health check responde una pregunta binaria: ¿el servicio contesta? Pero en sistemas distribuidos los
fallos más frecuentes son **degradaciones parciales** (una dependencia lenta, un error intermitente), en
las que el servicio sigue "arriba" mientras los usuarios se ven afectados.

**Pregunta de investigación:** ¿cómo detectar que una API presenta problemas de rendimiento o errores
aunque continúe disponible? **Hipótesis:** el tráfico, la tasa de errores y la latencia en percentiles
detectan degradaciones que un health check no ve. La ponemos a prueba con una PoC reproducible.

# 2. Marco teórico

**Señales de servicio.** El libro de SRE de Google propone cuatro *Golden Signals*: latencia, tráfico,
errores y saturación (Beyer et al., 2016). Para servicios orientados a peticiones, Wilkie (2018) las reduce
al **método RED**: *Rate* (peticiones/s), *Errors* (proporción de peticiones fallidas) y *Duration*
(distribución de la latencia). El método USE (Gregg, 2013), es decir utilización, saturación y errores, se
aplica a los recursos (CPU, disco, red) y complementa a RED.

**Percentiles.** La latencia suele ser asimétrica o bimodal: la media mezcla los modos y la mediana ignora
la cola. p95 y p99 describen al peor 5 % y 1 % de las peticiones, donde aparecen las degradaciones parciales.

**Prometheus** es una base de datos de series temporales y sistema de alertas, el segundo proyecto en graduarse
en la CNCF (2018). Usa un **modelo pull**: consulta el endpoint `/metrics` de cada servicio y, si falla,
`up = 0`. Cada serie es un nombre más un conjunto de etiquetas, así que cada combinación de etiquetas es una
serie y hay que controlar la **cardinalidad**. Ofrece *counters*, *gauges*, *histograms* (conteos por bucket,
agregables) y *summaries* (percentiles en el cliente, no agregables), el lenguaje **PromQL** y reglas de
grabación y de alerta. **Grafana** no almacena datos: consulta con PromQL y visualiza. Su datasource y sus
dashboards se cargan desde archivos versionados (*provisioning*).

# 3. Arquitectura de la PoC

```
k6 (30 req/s) ──HTTP──▶ API Node.js/Express + prom-client ◀──scrape 5 s── Prometheus ◀──PromQL── Grafana
                        /api/*  /health  /metrics  /admin/chaos             reglas + alertas      dashboard RED
```

Todo se levanta con `docker compose up` (Node 22, Prometheus 3.5 LTS, Grafana 12.1, k6 1.3).

- **Instrumentación:** `http_requests_total` (counter) y `http_request_duration_seconds` (histograma de 13
  buckets entre 5 ms y 5 s), etiquetados por método, **plantilla de ruta** (`/api/products/:id`, nunca la
  URL real) y código HTTP; además `http_requests_in_flight` y las métricas por defecto de Node.js.
- `/health` responde 200 mientras el proceso vive, como hacen muchos balanceadores. `POST /admin/chaos`
  inyecta fallos sin tocar la carga: 25 % de peticiones con +1,2 s, o 12 % con error 500.
- **Reglas:** errores 5xx > 5 % durante 1 min (`ApiTasaErroresAlta`); p95 > 500 ms durante 1 min
  (`ApiLatenciaP95Alta`); `up == 0` durante 30 s (`ApiCaida`).
- **Carga:** k6 con **tasa de llegada constante** (modelo abierto), que no frena si la API se vuelve lenta y
  evita la *coordinated omission* (Tene, 2015). La mezcla es idéntica en los tres escenarios: 60 % listado,
  25 % detalle (con algunos 404) y 15 % pedidos.

# 4. Resultados

Corrida de 2 min 30 s por escenario, a 30 req/s (≈4 500 peticiones por escenario). Valores de k6 (medición
del lado del cliente sobre todo el escenario) y de Prometheus (ventana de 1 min al final del escenario).

| Métrica | Normal | Latencia | Errores |
|---|---|---|---|
| `up` / `/health` | 1 / 200 | 1 / 200 | 1 / 200 |
| Tráfico (Prometheus) | 30,0 req/s | 29,9 req/s | 30,0 req/s |
| Errores 5xx (k6 · Prometheus) | 0 % · 0 % | 0 % · 0 % | **11,95 % · 11,0 %** |
| Latencia media (k6) | 22 ms | 312 ms | 18,5 ms |
| Mediana p50 (k6 · Prometheus) | 19 · 19 ms | 23 · 23 ms | 17 · 17 ms |
| p95 (k6 · Prometheus) | 52 · 51 ms | **1 400 · 1 390 ms** | 47 · 48 ms |
| p99 (k6 · Prometheus) | 61 · 91 ms | **1 490 · 1 492 ms** | 59 · 85 ms |
| Alerta disparada | ninguna | `ApiLatenciaP95Alta` | `ApiTasaErroresAlta` |
| Tiempo hasta *PENDING* / *FIRING* | — | 15 s / 75 s | 25 s / 85 s |

*Evidencia completa en `docs/resultados/demo-run.log` y `docs/resultados/linea-de-tiempo-alertas.txt`.*

**Hallazgos.**

1. **La disponibilidad no detectó nada.** En los tres escenarios `up = 1` y `/health` respondió 200 en todo
   momento. Solo las señales RED mostraron la degradación.
2. **Cada señal detecta un tipo de fallo distinto.** En el escenario de latencia la tasa de errores fue 0 %;
   en el de errores la latencia se mantuvo normal. Ninguna señal sola basta.
3. **El promedio y la mediana ocultan las degradaciones parciales.** Con el 25 % de las peticiones lentas, la mediana pasó de 19 a 23 ms, casi sin cambios, mientras el p95 se multiplicó por 27 (52 ms → 1,4 s). La media subió a 312 ms, pero quedó **por debajo** del umbral de 500 ms: una alerta por promedio no se habría disparado nunca, aunque uno de cada cuatro usuarios esperaba más de un segundo. El heatmap muestra una distribución bimodal que ningún estadístico resume por sí solo.
4. **Los errores rápidos "mejoran" la latencia.** En el escenario de errores la latencia media *bajó* de 22 a 18,5 ms, porque los 500 inyectados responden sin hacer el trabajo de la petición. Un servicio que falla rápido puede parecer más rápido; por eso la latencia debe leerse junto a la tasa de errores (o filtrarse a respuestas exitosas).
5. **Precisión de los percentiles.** Donde los buckets son densos (alrededor de 1–1,5 s) Prometheus coincidió
   con k6 con un error < 1 %. En el escenario normal, el p99 real (61 ms, k6) cae en el bucket 50–100 ms y la
   interpolación lineal lo estimó en 91 ms (+49 %). Es la limitación conocida de los histogramas: la precisión
   depende de dónde se ponen los buckets, por eso se diseñan alrededor del umbral que se vigila.
6. **La propia instrumentación puede fallar en silencio.** En la primera corrida el middleware de caos
   respondía 500 antes de que Express resolviera la ruta, y esas respuestas quedaban etiquetadas como
   `route="unmatched"`. El filtro `route=~"/api/.*"` las excluía: k6 midió un 11,9 % de errores y Prometheus,
   0 %. La alerta no se habría disparado nunca. Lo corregimos aplicando la inyección por ruta. La lección
   es contrastar las métricas con una fuente independiente, en este caso el generador de carga.

# 5. Análisis crítico: ventajas y limitaciones

| Aspecto | Ventaja | Limitación |
|---|---|---|
| Modelo pull | `up` gratis; el servicio no depende del monitor | Poco natural para *jobs* efímeros o serverless (requiere Pushgateway u OTel) |
| Histogramas | Agregables entre rutas e instancias | Percentiles aproximados por interpolación lineal dentro del bucket; hay que diseñar los buckets |
| Escalabilidad | Ligero: un servicio genera unos cientos de series | Un solo nodo, retención local; HA y largo plazo requieren Thanos/Mimir |
| Etiquetas | Diagnóstico por ruta, código, instancia | Un error de cardinalidad (ids, URLs) degrada a Prometheus |
| Alcance | Responde *qué* pasa y *dónde* | No responde *por qué*: hacen falta trazas (OpenTelemetry) y logs |
| Operación | Todo como código; resolución configurable | Curva de PromQL; los picos más cortos que el *scrape* se suavizan |

**Frente a alternativas:** un APM comercial (Datadog, New Relic) trae trazas y retención listas, pero cobra
por host o por serie y ata al proveedor. Los Prometheus gestionados (AWS, Google, Grafana Cloud) conservan
PromQL. Como la instrumentación usa un formato abierto (OpenMetrics), cambiar de *backend* no obliga a
modificar el código.

# 6. Conclusiones

- La hipótesis se confirma: con las tres señales RED y alertas con ventana temporal, ambas degradaciones se
  detectaron en menos de 90 s (*FIRING* a los 75 y 85 s, con `for: 1m`), mientras los indicadores de disponibilidad seguían en verde.
- **Hay que alertar por percentiles y por proporción de errores**, no por promedio ni por estado binario.
- La calidad del monitoreo depende de la instrumentación: etiquetas correctas, cardinalidad acotada y buckets
  pensados para el umbral que se quiere vigilar.
- Siguientes pasos naturales: alertas por consumo del presupuesto de error (*burn rate*, Google SRE
  Workbook), Alertmanager para notificaciones, *native histograms* de Prometheus 3 y trazas con
  OpenTelemetry enlazadas mediante *exemplars*.

# Referencias

- Beyer, B., Jones, C., Petoff, J. y Murphy, N. R. (2016). *Site Reliability Engineering: How Google Runs
  Production Systems*, cap. 6 "Monitoring Distributed Systems". O'Reilly. <https://sre.google/sre-book/monitoring-distributed-systems/>
- Beyer, B., Murphy, N. R., Rensin, D., Kawahara, K. y Thorne, S. (2018). *The Site Reliability Workbook*,
  cap. 5 "Alerting on SLOs". O'Reilly. <https://sre.google/workbook/alerting-on-slos/>
- Wilkie, T. (2018). *The RED Method: How to Instrument Your Services*. Grafana Labs.
  <https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/>
- Gregg, B. (2013). *The USE Method*. <https://www.brendangregg.com/usemethod.html>
- Prometheus Authors. *Documentation: Data model; Metric types; Histograms and summaries; Alerting rules*.
  <https://prometheus.io/docs/>
- Cloud Native Computing Foundation (2018). *Cloud Native Computing Foundation Announces Prometheus Graduation*.
  <https://www.cncf.io/announcements/2018/08/09/prometheus-graduates/>
- Grafana Labs. *Grafana documentation: Provisioning*; *k6 documentation: Open and closed models,
  constant-arrival-rate*. <https://grafana.com/docs/>
- Tene, G. (2015). *How NOT to Measure Latency*. Strange Loop.
- prom-client (siimon/prom-client). *Prometheus client for Node.js*. <https://github.com/siimon/prom-client>
