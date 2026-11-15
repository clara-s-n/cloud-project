# Guion de la exposición (15 min + 5 min de preguntas)

La exposición se divide en tres bloques parejos, uno por integrante, y termina con la demo:

| Bloque | Quién | Diapositivas | Duración |
|---|---|---|---|
| Introducción y marco teórico | Nicolás | 1–4 | 3:30 |
| La PoC | Ana Clara | 5–8 | 3:30 |
| Resultados y análisis | Francisco | 9–13 | 3:40 |
| **Demo** | Francisco al teclado | 14 | 3:00 |
| Preguntas | Todos | 15 | 0:20 |

Total: 14:00, con **1 minuto de margen** sobre los 15. Si falta alguien y quedan dos, Ana Clara toma también
el bloque de Francisco salvo la demo, que conviene que haga quien maneja el teclado.

| Tiempo | Diapositiva | Quién | Idea clave |
|---|---|---|---|
| 0:00–0:30 | 1. Portada | Nicolás | Presentación y gancho |
| 0:30–1:30 | 2. El problema | Nicolás | `/health` en verde ≠ servicio sano |
| 1:30–2:15 | 3. Pregunta | Nicolás | Hipótesis, método y alcance |
| 2:15–3:30 | 4. Señales RED | Nicolás | Rate, Errors, Duration (+ Golden Signals / USE) |
| 3:30–4:30 | 5. Prometheus | Ana Clara | Pull, etiquetas, PromQL, tipos de métrica |
| 4:30–5:20 | 6. Arquitectura | Ana Clara | Misma carga, solo cambia el fallo |
| 5:20–6:20 | 7. Instrumentación | Ana Clara | Cardinalidad + el bug de `route="unmatched"` |
| 6:20–7:00 | 8. Escenarios | Ana Clara | 25 % lentas / 12 % con error |
| 7:00–7:45 | 9. Resultados | Francisco | Tabla con los números medidos |
| 7:45–8:20 | 10. La media engaña | Francisco | Mediana ≈ igual, p95 ×27; la media no cruza el umbral |
| 8:20–8:50 | 11. Errores | Francisco | Los errores rápidos bajan la latencia |
| 8:50–9:50 | 12. Ventajas/limitaciones | Francisco | Trade-offs |
| 9:50–10:40 | 13. Conclusiones | Francisco | Respuesta a la pregunta; transición: "ahora lo vemos funcionando" |
| 10:40–13:40 | 14. **Demo en vivo** | Francisco | Grafana + alertas en Prometheus |
| 13:40–14:00 | 15. Referencias / preguntas | Todos | |

> El tiempo de la rúbrica para la exposición dice "10 min" en un sitio y 15 en otro. Si el docente exige 10,
> recortar así: quitar las diapositivas 8 y 11 (contarlas de palabra), acortar cada bloque a unos 2:30 y
> dejar la demo en 2 minutos al final, con la opción B (solo latencia y errores sobre datos ya generados).

## Preparación (30 min antes)

1. Levantar el laboratorio y **pre-generar datos** con el equipo libre (si la máquina está cargada, las
   latencias salen falsas):
   ```bash
   docker compose up -d --build
   DURATION=3m ./scripts/demo.sh        # ~10 min: deja los tres escenarios en el historial
   ```
2. Abrir en pestañas:
   - Grafana: <http://localhost:3001/d/api-red> (rango *Last 15 minutes*).
   - Prometheus: <http://localhost:9090/alerts>.
   - Una terminal con letra grande en la carpeta del proyecto.
3. Tener el **video de respaldo** (`demo-respaldo.mp4`, 2 min 15 s, sin audio y con subtítulos) abierto en
   otra ventana. Si hay que usarlo, narrarlo en vivo.
4. Comprobar que la API está en modo normal:
   ```bash
   curl localhost:3000/admin/chaos
   ```

## Demo en vivo (3 min), paso a paso

La demo va al final, después de Conclusiones: sirve para mostrar funcionando lo que se acaba de contar.

**Opción A, en vivo (recomendada si la red y el equipo son fiables).** Lanzar el escenario de latencia
*al empezar la diapositiva 11* (~8:20), para que al llegar a la demo ya lleve más de 2 min y la alerta esté
disparada:

```bash
docker compose run --rm -e DURATION=4m k6 run /scripts/latencia.js
```

1. **Fila "Resumen"** (0:00–0:20): "Target: ARRIBA, health check: OK. Si solo miráramos esto, todo está
   bien." Señalar **Latencia p95** en rojo.
2. **Panel "Latencia: media vs percentiles"** (0:20–0:50): "La mediana (verde) sigue en ~20 ms. La media sube
   algo. p95 y p99 superan el segundo. Si alertáramos por la media no veríamos el problema."
3. **Heatmap** (0:50–1:05): "Se ven dos franjas: las peticiones rápidas y las que tardan ~1,2 s. Es una
   distribución bimodal que ningún número resume bien."
4. **Prometheus → Alerts** (1:05–1:20): `ApiLatenciaP95Alta` en *FIRING*.
5. Cortar k6 (Ctrl+C) y lanzar errores (1:20):
   ```bash
   docker compose run --rm -e DURATION=3m k6 run /scripts/errores.js
   ```
6. **Panel "Tráfico por código de estado"** (1:30–1:50): aparecen barras rojas (500) con el mismo volumen
   total.
7. **Panel "Tasa de errores (%)"** (1:50–2:10): cruza la línea del 5 %. Los 4xx (amarillo) están aparte.
8. **Panel "Tasa de errores 5xx por ruta"** (2:10–2:30): "Sabemos *dónde*: todas las rutas por igual. Eso
   apunta a una causa común, por ejemplo una dependencia compartida."
9. **Prometheus → Alerts** (2:30–2:50): `ApiTasaErroresAlta` estará en *PENDING* (pasa a *FIRING* ~85 s
   después de lanzar el escenario). Aprovechar para explicar el `for: 1m`.
10. Cerrar (2:50–3:00): "En ningún momento la API dejó de estar disponible, y aun así RED detectó las dos
    degradaciones." Pasar a la diapositiva de preguntas.

**Opción B, sobre historial.** Si no hay tiempo de esperar o algo falla, poner el rango en *Last 15
minutes* sobre los datos de la preparación y recorrer los mismos paneles señalando cada tramo (el panel
"Escenario inyectado" y el de alertas muestran qué pasó en cada momento). Si tampoco funciona Grafana,
pasar al video de respaldo.

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
