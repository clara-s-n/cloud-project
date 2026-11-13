# Guion de la exposición (15 min + 5 min de preguntas)

Reparto pensado para tres integrantes. Con dos, el Integrante 2 toma también el bloque del Integrante 3
salvo la demo, que conviene que haga quien maneja el teclado.

| Tiempo | Diapositiva | Quién | Idea clave |
|---|---|---|---|
| 0:00–0:30 | 1. Portada | Integrante 1 | Presentación y gancho |
| 0:30–1:30 | 2. El problema | Integrante 1 | `/health` en verde ≠ servicio sano |
| 1:30–2:15 | 3. Pregunta | Integrante 1 | Hipótesis, método y alcance |
| 2:15–3:30 | 4. Señales RED | Integrante 1 | Rate, Errors, Duration (+ Golden Signals / USE) |
| 3:30–4:45 | 5. Prometheus | Integrante 2 | Pull, etiquetas, PromQL, tipos de métrica |
| 4:45–5:45 | 6. Arquitectura | Integrante 2 | Misma carga, solo cambia el fallo |
| 5:45–7:00 | 7. Instrumentación | Integrante 2 | Cardinalidad + el bug de `route="unmatched"` |
| 7:00–7:45 | 8. Escenarios | Integrante 2 | 25 % lentas / 12 % con error |
| 7:45–8:30 | 9. Resultados | Integrante 3 | Tabla con los números medidos |
| 8:30–9:00 | 10. La media engaña | Integrante 3 | Mediana ≈ igual, p95 ×27; la media no cruza el umbral |
| 9:00–9:30 | 11. Errores | Integrante 3 | Los errores rápidos bajan la latencia |
| 9:30–13:00 | 12. **Demo en vivo** | Integrante 3 | Grafana + alertas en Prometheus |
| 13:00–14:00 | 13. Ventajas/limitaciones | Integrante 3 | Trade-offs |
| 14:00–15:00 | 14. Conclusiones | Integrante 3 | Respuesta a la pregunta |
| 15:00 | 15. Referencias / preguntas | Todos | |

> El tiempo de la rúbrica para la exposición dice "10 min" en un sitio y 15 en otro. Si el docente exige 10,
> recortar así: quitar las diapositivas 8 y 11 (contarlas de palabra) y dejar la demo en 2 minutos, mostrando
> solo latencia y errores sobre datos ya generados.

## Preparación (30 min antes)

1. Levantar el laboratorio y **pre-generar datos** para no depender del tiempo real:
   ```bash
   docker compose up -d --build
   DURATION=2m ./scripts/demo.sh        # ~7 min: deja los tres escenarios en el historial
   ```
2. Abrir en pestañas:
   - Grafana: <http://localhost:3001/d/api-red> (rango *Last 15 minutes*, refresco 5 s).
   - Prometheus: <http://localhost:9090/alerts>.
   - Una terminal con letra grande en la carpeta del proyecto.
3. Tener el **video de respaldo** (2 min) abierto en otra ventana. Grabarlo antes con OBS durante una
   corrida de `demo.sh`.
4. Comprobar que la API está en modo normal:
   ```bash
   curl localhost:3000/admin/chaos
   ```

## Demo en vivo (3,5 min), paso a paso

**Opción A, en vivo (recomendada si la red y el equipo son fiables).** Lanzar el escenario de latencia
*al empezar la diapositiva 9*, para que al llegar a la demo ya lleve ~1,5 min y la alerta esté disparada:

```bash
docker compose run --rm -e DURATION=4m k6 run /scripts/latencia.js
```

1. **Fila "Resumen"**: "Target: ARRIBA, health check: OK. Si solo miráramos esto, todo está bien."
   Señalar **Latencia p95** en rojo.
2. **Panel "Latencia: media vs percentiles"**: "La mediana (verde) sigue en ~20 ms. La media sube algo.
   p95 y p99 superan el segundo. Si alertáramos por la media no veríamos el problema."
3. **Heatmap**: "Se ven dos franjas: las peticiones rápidas y las que tardan ~1,2 s. Es una distribución
   bimodal que ningún número resume bien."
4. **Prometheus → Alerts**: `ApiLatenciaP95Alta` en *FIRING* (o *PENDING*: explicar el `for: 1m`).
5. Cortar k6 (Ctrl+C) y lanzar errores:
   ```bash
   docker compose run --rm -e DURATION=3m k6 run /scripts/errores.js
   ```
6. **Panel "Tráfico por código de estado"**: aparecen barras rojas (500) con el mismo volumen total.
7. **Panel "Tasa de errores (%)"**: cruza la línea del 5 %. Los 4xx (amarillo) están aparte.
8. **Panel "Tasa de errores 5xx por ruta"**: "Sabemos *dónde*: todas las rutas por igual. Eso apunta a
   una causa común, por ejemplo una dependencia compartida."
9. Cerrar: "En ningún momento la API dejó de estar disponible."

**Opción B, sobre historial.** Si no hay tiempo de esperar, poner el rango en *Last 15 minutes* sobre
los datos de la preparación y recorrer los mismos paneles señalando cada tramo (el panel
"Escenario inyectado" y el de alertas muestran qué pasó en cada momento).

## Preguntas probables y respuestas

**¿Por qué Prometheus y no un APM comercial (Datadog, New Relic)?**
Prometheus es abierto, graduado en la CNCF y el estándar en Kubernetes; su formato (OpenMetrics) lo
aceptan casi todos los proveedores, incluidos los comerciales. Un APM da más cosas listas (trazas,
perfiles, retención), pero cuesta por host o por serie y genera dependencia del proveedor. Para el objetivo
del trabajo, entender las señales, la herramienta abierta es más didáctica.

**¿Por qué histograma y no summary?**
El summary calcula los percentiles en el cliente y no se pueden agregar: no se puede promediar el p95 de
dos instancias. El histograma guarda conteos por bucket, que sí se suman, y el percentil se calcula después
en PromQL. El costo es la precisión: el resultado es una interpolación dentro del bucket.

**¿Qué tan preciso es el p95 que muestra Prometheus?**
Depende de los buckets. `histogram_quantile` asume distribución uniforme dentro del bucket. Pusimos
buckets densos alrededor de 300–500 ms (nuestro umbral) para que la decisión de alertar sea precisa. En la
corrida, k6 (medición exacta del lado del cliente) y Prometheus dieron p95 muy parecidos (ver resumen
ejecutivo). Prometheus 3 tiene *native histograms*, con buckets exponenciales automáticos, que reducen
este problema.

**¿Por qué pull y no push?**
Pull da detección de caídas gratis (`up`), evita que un servicio sature al monitor y permite consultar
`/metrics` a mano para depurar. Para trabajos cortos (batch, serverless) existe Pushgateway, o se usa
OpenTelemetry con *remote write*.

**¿Por qué la ventana `for: 1m`? ¿No es tarde?**
Es un compromiso entre rapidez y falsos positivos: un pico de 5 s no debería despertar a nadie. En
producción se usan alertas por *burn rate* del presupuesto de error (Google SRE Workbook), con dos
ventanas (p. ej. 5 min y 1 h), que son rápidas para incidentes graves y tolerantes con los leves.

**¿Qué es la cardinalidad y por qué importa?**
Cada combinación distinta de valores de etiquetas es una serie temporal que Prometheus guarda en memoria.
Si pusiéramos la URL completa (`/api/products/1`, `/2`, …) o un id de usuario, las series crecerían sin
límite y Prometheus se degradaría. Por eso etiquetamos con la plantilla de la ruta.

**¿Los 404 cuentan como errores?**
No para el SLO: son errores del cliente (pidió algo que no existe). Se muestran aparte. Si los 404
subieran de golpe podría indicar un despliegue roto (un enlace mal generado), así que se observan,
pero no se alerta por ellos.

**¿Por qué la latencia media bajó en el escenario de errores?**
Porque los 500 inyectados responden enseguida, sin hacer el trabajo de la petición. Es un patrón real:
un servicio que falla rápido puede *parecer* más rápido. Mirar la latencia de las respuestas exitosas por
separado lo evita.

**¿Cómo escalaría esto en Kubernetes?**
Con el Prometheus Operator (o kube-prometheus-stack): los servicios se descubren con `ServiceMonitor` en
vez de `static_configs`, las reglas son recursos `PrometheusRule` y Alertmanager envía las notificaciones.
Para alta disponibilidad y retención larga se añaden Thanos o Mimir. La instrumentación de la API no cambia.

**¿Qué faltaría para encontrar la causa raíz?**
Las métricas dicen *qué* y *dónde* (qué ruta). Para el *por qué* hacen falta trazas distribuidas
(OpenTelemetry → Jaeger/Tempo) y logs correlacionados. Prometheus admite *exemplars*: enlaces desde un
punto del histograma a una traza concreta.

**¿Por qué k6 con tasa constante y no con usuarios virtuales?**
Con un modelo cerrado (N usuarios en bucle), si la API se vuelve lenta los usuarios envían menos
peticiones y la carga baja sola, lo que suaviza la degradación medida (*coordinated omission*). Con tasa
de llegada constante, la carga es la misma en los tres escenarios.

**¿Y la seguridad de `/admin/chaos` y `/metrics`?**
En el laboratorio no tienen autenticación. En producción `/admin/chaos` no existiría (o estaría detrás de
un *feature flag*), y `/metrics` se expondría solo en la red interna o en otro puerto.
