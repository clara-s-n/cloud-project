# Estado del proyecto (al 14/11/2026)

Resumen de la sesión de trabajo con Claude Code en la que se armó este repositorio. Sirve para que
cualquier integrante (o Claude en otro dispositivo) retome el trabajo sin haber visto esa conversación.

## Contexto

- **Materia:** Electiva Cloud Computing, proyecto final grupal.
- **Equipo:** Ana Sena · Francisco Lima · Nicolás Márquez.
- **Tema aprobado:** categoría 3.2 (CNCF / Observabilidad). *Detección de degradaciones en una API mediante
  monitoreo con Prometheus y Grafana.*
- **Pregunta de investigación:** ¿cómo detectamos que una API tiene problemas de rendimiento o errores aunque
  siga disponible?
- **Hipótesis:** las señales RED (Rate, Errors, Duration en percentiles) detectan degradaciones que un health
  check no ve.
- **Entregables de la consigna:** presentación oral de 15 min + 5 de preguntas, resumen ejecutivo de 2–3
  páginas, PoC funcional (se recomienda un video de respaldo de 2 min) y póster A3 vertical en PDF vectorial
  con nombre `Grupo-Apellido1-Apellido2.pdf`, impreso a color para pegarlo en la última clase.

## Qué está hecho

| Entregable | Dónde | Estado |
|---|---|---|
| PoC: API + Prometheus + Grafana + k6 | `api/`, `prometheus/`, `grafana/`, `k6/`, `docker-compose.yml` | Funciona y está probada de punta a punta |
| Scripts de demo | `scripts/demo.sh`, `snapshot.sh`, `alert_timeline.py` | Listos |
| Resultados de referencia | `docs/resultados/` | Corrida limpia del 12/11 (log y línea de tiempo de alertas) |
| Resumen ejecutivo | `docs/resumen-ejecutivo.md` y `.docx` | Completo, con los nombres |
| Guion de la exposición + 12 preguntas probables | `docs/guion-presentacion.md` | Completo, con reparto: Nicolás (1–4), Ana Clara (5–8), Francisco (9–14 y demo) |
| Guía para grabar el video de respaldo | `docs/grabar-demo.md` | Lista |
| Presentación (15 diapositivas) | Artifact de claude.ai en esta cuenta: https://claude.ai/artifact/UMiuKZcVpJCGZEWnriCcWQ · fuente en `docs/presentacion/` | Completa, con los nombres en la portada y en las notas de orador (versión 11 del artifact, 14/11). Se descarga como .pptx o PDF |
| Póster A3 | `docs/poster/Grupo-Sena-Lima-Marquez.pdf` (generado por `scripts/build_poster.py`) | Regenerado el 14/11 con los nombres reales |

## Cómo funciona la PoC (en 30 segundos)

```
k6 (30 req/s) → API Node.js/Express + prom-client → Prometheus (scrape 5 s, alertas) → Grafana (dashboard RED)
```

- `/health` siempre responde 200: representa el monitoreo de disponibilidad "ingenuo".
- `POST /admin/chaos` inyecta fallos sin cambiar la carga: `normal`, `latency` (25 % de las peticiones +1,2 s)
  o `errors` (12 % de respuestas 500).
- Alertas: `ApiLatenciaP95Alta` (p95 > 500 ms durante 1 min), `ApiTasaErroresAlta` (5xx > 5 % durante 1 min),
  `ApiCaida` (`up == 0`).
- Arranque: `docker compose up -d --build`. Grafana en http://localhost:3001 (sin login), Prometheus en
  http://localhost:9090/alerts. Demo completa: `./scripts/demo.sh` (o `DURATION=2m ./scripts/demo.sh`).

## Resultados de referencia (2 min 30 s por escenario, 30 req/s)

| | Normal | Latencia | Errores |
|---|---|---|---|
| `up` / `/health` | 1 / 200 | 1 / 200 | 1 / 200 |
| Errores 5xx | 0 % | 0 % | 11,95 % |
| p50 / media / p95 | 19 / 22 / 52 ms | 23 / 312 / 1 400 ms | 17 / 18,5 / 47 ms |
| Alerta | ninguna | p95: PENDING a los 15 s, FIRING a los 75 s | errores: PENDING a los 25 s, FIRING a los 85 s |

**Hallazgos que se usan en la presentación, el resumen y el póster:**
1. La disponibilidad no detectó nada; cada fallo lo detectó una señal RED distinta.
2. **La media engaña:** con latencia, la media (312 ms) no llegó al umbral de 500 ms, mientras el p95 se
   multiplicó por 27. Una alerta por promedio nunca habría sonado.
3. **Fallar rápido parece ir rápido:** con errores, la latencia media bajó un 16 %.
4. **Bug real encontrado:** los 500 inyectados quedaban etiquetados como `route="unmatched"` y Prometheus
   marcaba 0 % de errores mientras k6 medía 12 %. Se corrigió aplicando la inyección por ruta. Sirve como
   ejemplo de que la instrumentación también hay que validarla.
5. Los percentiles de Prometheus son aproximados: el p99 normal real era de 61 ms y Prometheus lo estimó en
   91 ms, por la interpolación dentro del bucket.

## Pendientes y preguntas abiertas

1. ~~El póster PDF todavía muestra los nombres de ejemplo.~~ **Resuelto el 14/11:** los nombres están en
   `AUTORES` (`scripts/build_poster.py`) y el PDF y la vista previa se regeneraron con
   `./scripts/export_poster.sh Grupo-Sena-Lima-Marquez` (1 página A3, vectorial).
2. ~~Falta definir el reparto de la exposición.~~ **Resuelto el 14/11:** Nicolás (diapositivas 1–4),
   Ana Clara (5–8) y Francisco (9–14, incluida la demo). Está en `docs/guion-presentacion.md` y en las notas
   de orador del repo y del artifact.
3. **El video de respaldo no está grabado.** Se va a grabar en este dispositivo; seguir
   `docs/grabar-demo.md`. Antes de grabar, generar datos con `DURATION=3m ./scripts/demo.sh` y no usar el
   equipo para nada pesado mientras corre, porque eso altera las latencias.
   El 14/11 ya se generaron datos en el equipo de Francisco: corrida limpia de 3 min por escenario, de
   20:33 a 20:41 (UTC−3), sin `dropped_iterations` y con las dos alertas en *FIRING*. Quedaron en el volumen
   `poc-observabilidad_prometheus-data` y sirven hasta el 16/11 (retención de 2 días). Para usarlos:
   `docker compose up -d` y abrir el dashboard con `/?orgId=1&from=1794699060000&to=1794699840000`. Pasado
   ese plazo hay que volver a correr la demo. Ver también la nota sobre WSL y Chrome más abajo.
   El 14/11 (después del reinicio) se comprobó que los datos siguen en el volumen: tráfico de 20:33 a 20:41
   y las alertas `ApiLatenciaP95Alta` y `ApiTasaErroresAlta` en *FIRING*.
4. **Duración de la exposición:** la rúbrica dice "10 min" en un lugar y 15 en otro. El guion está armado
   para 15 e indica qué recortar si son 10. Conviene confirmarlo con el docente.
5. **Largo del resumen ejecutivo:** son unas 1 600 palabras con 3 tablas; se estimó en ~3 páginas, pero
   no se verificó en Word. Si pasa de 3, bajar la letra a 11 pt o los márgenes a 2 cm.
6. **Presentación privada:** el artifact solo lo ve el dueño de la cuenta; para que lo vean los demás hay
   que compartirlo desde su menú *Share*.
7. **Impresión:** A3 vertical a color. Antes de mandarlo a la imprenta, imprimir una prueba en A4: el
   texto más chico (referencias, ejes de los gráficos) mide unos 9–10 pt.
8. **Rama `docs/team-names` sin fusionar.** Los cambios del 14/11 (póster, nombres, reparto, README y
   este documento) están en esa rama, que ya está en GitHub. Falta fusionarla en `main`; no hay pull
   request abierto.

## Notas para retomar el trabajo

- **WSL con `networkingMode=mirrored` (equipo de Francisco):** Chrome en Windows no abre
  `localhost:3001` ni `127.0.0.1:3001`, aunque `curl.exe` y PowerShell de Windows sí llegan. No es un
  problema del laboratorio. Hay dos salidas: (a) volver a la red NAT quitando esa línea de
  `C:\Users\<usuario>\.wslconfig` y ejecutando `wsl --shutdown`; (b) un puente TCP temporal en Windows
  (PowerShell, escuchando solo en `127.0.0.1`) de 13001→3001 y 19090→9090, y abrir
  `http://127.0.0.1:13001` y `http://127.0.0.1:19090/alerts`. La opción (b) se verificó el 14/11 cargando
  el dashboard en Chrome.
  **Actualización 14/11:** en `.wslconfig` la línea `networkingMode=mirrored` está comentada y WSL corre en
  modo `nat` (`wslinfo --networking-mode`). Así no hace falta el puente: desde Windows, `curl.exe` llega a
  `localhost:3001` y `localhost:9090`, y Chrome abre el dashboard directamente (confirmado por Francisco).

- En Windows, usar WSL (o clonar con `core.autocrlf input`): los scripts son bash.
- Todo corre en contenedores; no hace falta instalar Node ni k6.
- El dashboard de Grafana se genera con `scripts/build_dashboard.py`: no editarlo a mano en Grafana.
- El póster también es código (`scripts/build_poster.py`): conviene editar ahí, no en `poster.html`.
- Si la máquina está cargada durante una corrida aparecen `dropped_iterations` en k6 y colas de latencia
  falsas. Hay que repetir la corrida con el equipo libre.
