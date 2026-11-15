# Guion de la exposición (15 min + 5 min de preguntas)

La exposición se divide en tres bloques parejos, uno por integrante, y termina con la demo:

| Bloque | Quién | Diapositivas | Duración |
|---|---|---|---|
| Introducción y marco teórico | Nicolás | 1–4 | 3:30 |
| La PoC | Ana Clara | 5–8 | 3:30 |
| Resultados y análisis | Francisco | 9–13 | 3:40 |
| **Demo** (video narrado) | Francisco | 14 | 3:00 |
| Preguntas | Todos | 15 | 0:20 |

Total: 14:00, con **1 minuto de margen** sobre los 15. Si falta alguien y quedan dos, Ana Clara toma también
el bloque de Francisco y también narra el video de la demo.

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
| 10:40–13:40 | 14. **Demo (video)** | Francisco | Video narrado: Grafana + alertas en Prometheus |
| 13:40–14:00 | 15. Referencias / preguntas | Todos | |

> El tiempo de la rúbrica para la exposición dice "10 min" en un sitio y 15 en otro. Si el docente exige 10,
> recortar así: quitar las diapositivas 8 y 11 (contarlas de palabra), acortar cada bloque a unos 2:30 y
> dejar la demo en 2 minutos al final: pasar el video desde 0:28 y cortarlo en 1:50 (latencia, heatmap y
> errores), contando las alertas de palabra.

## Preparación (antes de empezar)

1. Copiar `demo-respaldo.mp4` (la versión **sin música**) al equipo que se conecta al proyector y abrirlo en
   el reproductor, en pausa en el primer cuadro. Tener una copia en un pendrive o en la carpeta compartida.
2. Probar que se ve a pantalla completa y que los subtítulos se leen desde el fondo del aula.
3. Opcional: tener el laboratorio levantado por si en las preguntas piden ver algo en vivo. Si se hace,
   generar antes los datos con el equipo libre:
   ```bash
   docker compose up -d --build
   DURATION=3m ./scripts/demo.sh        # ~10 min: deja los tres escenarios en el historial
   ```

## Demo (3 min): video narrado

La demo va al final, después de Conclusiones, y se hace con el video `demo-respaldo.mp4` (2 min 15 s, datos
reales de la PoC, sin audio y con subtítulos). Francisco lo narra en vivo; los subtítulos dicen lo
esencial, así que la narración agrega contexto en vez de leerlos. Sobran unos 45 s para pausar: usarlos en
el panel de latencia y en las alertas.

| Video (aprox.) | Qué se ve | Qué decir |
|---|---|---|
| 0:00–0:04 | Portada "Disponible no significa sano" | "Esto es lo que midió la PoC, con la misma carga en los tres escenarios." |
| 0:04–0:16 | Fila de arriba: **Target ARRIBA**, **Health check OK** | "Si solo miráramos esto, todo está bien: la API nunca dejó de estar disponible." |
| 0:16–0:28 | Panel **Escenario inyectado** | "Corrimos normal, latencia y errores, uno detrás del otro." |
| 0:28–0:58 | **Latencia: media vs percentiles**, con el tooltip | **Pausar.** "La mediana casi no se mueve; p95 y p99 pasan del segundo. La media queda por debajo de 500 ms: una alerta por promedio no habría sonado." |
| 0:58–1:12 | **Heatmap** | "Dos franjas: las peticiones normales y las lentas. Ningún número solo lo resume." |
| 1:12–1:38 | **Tráfico por código** y **Tasa de errores (%)** | "El volumen es el mismo, pero aparecen 500 y la tasa supera el 5 %. La latencia sigue normal: fallar rápido parece ir rápido." |
| 1:38–1:50 | **Tasa de errores 5xx por ruta** | "Sabemos *dónde*: todas las rutas por igual, lo que apunta a una causa común." |
| 1:50–2:10 | Historial de alertas en Prometheus (PENDING = 1, FIRING = 2) | **Pausar.** "Cada alerta pasa primero a PENDING y, si la condición dura un minuto (`for: 1m`), a FIRING. La de caída nunca se disparó." |
| 2:10–2:15 | Cierre | "En ningún momento la API dejó de estar disponible, y aun así RED detectó las dos degradaciones." Pasar a la diapositiva de preguntas. |

Si el reproductor falla, volver a las diapositivas 9 a 11 (resultados) y contar los mismos puntos de
palabra; no improvisar una demo en vivo.

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
