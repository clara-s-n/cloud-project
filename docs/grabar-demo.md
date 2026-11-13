# Cómo grabar el video de respaldo de la demo (2 min)

Guía para quien grabe el video. Está pensada para seguirla sin haber participado en el desarrollo.
Hay que reservar unos **45 minutos**: 10 de preparación, unos 25 de carga generando datos y 10 para grabar.

## 1. Requisitos

| Necesitas | Cómo comprobarlo |
|---|---|
| Docker Desktop (Windows/Mac) o Docker Engine (Linux), **en marcha** | `docker compose version` |
| Una terminal **bash**: en Linux/Mac, la normal; en Windows, **WSL** (recomendado) o Git Bash | `bash --version` |
| `git`, `curl` y `python3` | `git --version`, `curl --version`, `python3 --version` |
| Programa para grabar pantalla: [OBS Studio](https://obsproject.com/) (gratis) o el grabador del sistema (Win+Alt+R en Windows, Cmd+Shift+5 en Mac) | — |
| Puertos libres: **3000, 3001 y 9090** | Si algo falla al arrancar, ver "Problemas frecuentes" |

No hace falta instalar Node.js ni k6: todo corre dentro de contenedores.

## 2. Preparar el laboratorio

```bash
git clone https://github.com/clara-s-n/cloud-project.git
cd cloud-project
docker compose up -d --build
```

La primera vez tarda unos minutos porque descarga las imágenes. Comprueba que todo está arriba:

```bash
docker compose ps
curl localhost:3000/health
```

`docker compose ps` debe listar `demo-api` (healthy), `prometheus` y `grafana`, y `curl` debe devolver `{"status":"ok",...}`.

## 3. Generar los datos que se van a mostrar

Lo más seguro es **no grabar mientras se espera**: primero se generan los tres escenarios y después se graba
el dashboard con todo el historial a la vista.

```bash
DURATION=3m ./scripts/demo.sh
```

Tarda unos 10 minutos. Mientras corre **no uses el equipo para tareas pesadas**: si la máquina se satura,
la latencia medida empeora y los datos no reflejan lo que queremos mostrar.

Al terminar cada escenario aparece un resumen. Es normal que k6 diga `código 99` en *latencia* y *errores*:
significa que se superó el umbral, que es justo lo que buscamos.

## 4. Preparar la pantalla

1. Abre <http://localhost:3001>. Se abre directamente el dashboard **"API demo — Señales RED"** (sin login).
2. Arriba a la derecha, pon el rango en **Last 15 minutes** para que se vean los tres escenarios.
   Si tardaste más en grabar, usa *Last 30 minutes*.
3. Pulsa `F11` (pantalla completa del navegador) y ajusta el zoom (Ctrl + / Ctrl −) para que la fila de
   arriba y los dos primeros paneles quepan sin hacer scroll.
4. Abre otra pestaña en <http://localhost:9090/alerts> (alertas de Prometheus).
5. Cierra notificaciones (Slack, WhatsApp, correo) y oculta los marcadores del navegador.

**OBS, configuración mínima:** Fuentes → `+` → *Captura de pantalla*; Ajustes → Salida → formato **mp4**;
Ajustes → Vídeo → 1920×1080, 30 FPS. Si van a narrar sobre el video, graben también el micrófono; si no,
se graba sin audio y se narra en vivo.

## 5. Guion del video (≈2 min)

| Tiempo | Qué mostrar | Qué decir (si se narra) |
|---|---|---|
| 0:00–0:15 | Fila de arriba del dashboard: **Target ARRIBA** y **Health check OK** | "Durante toda la prueba la API estuvo disponible y el health check respondió 200." |
| 0:15–0:30 | Panel **Escenario inyectado** y la línea de tiempo: tres tramos (normal, latency, errors) | "Corrimos tres escenarios con la misma carga: normal, latencia y errores." |
| 0:30–1:00 | Panel **Latencia: media vs percentiles**. Pasa el ratón por el tramo de latencia para que salga el tooltip | "En el tramo de latencia la mediana casi no se mueve, pero p95 y p99 pasan del segundo." |
| 1:00–1:15 | **Heatmap** de latencia en el mismo tramo | "Se ven dos franjas: las peticiones normales y las lentas. Una media no lo mostraría." |
| 1:15–1:40 | Paneles **Tráfico por código de estado** y **Tasa de errores (%)** en el tramo de errores | "El volumen es el mismo, pero aparecen 500 y la tasa supera el 5 %. La latencia sigue normal." |
| 1:40–1:50 | Panel **Tasa de errores 5xx por ruta** | "Además vemos que afecta a todas las rutas por igual." |
| 1:50–2:00 | Pestaña **Prometheus → Alerts** (o el panel *Estado de las alertas*) | "Las alertas de latencia p95 y de tasa de errores se dispararon; la de caída, nunca." |

Consejos: mueve el ratón despacio y deja quieto el cursor 2–3 segundos sobre cada panel. Si te equivocas,
sigue grabando y luego recorta: es más rápido que empezar de nuevo.

## 6. Versión "en vivo" (opcional)

Si prefieren un video que muestre la degradación ocurriendo, graba mientras corre solo un escenario. La
alerta tarda ~20 s en pasar a *PENDING* y ~80 s en pasar a *FIRING*:

```bash
./scripts/demo.sh latencia
```

## 7. Al terminar

- Revisa el video completo y comprueba que se lee el texto de los paneles.
- Nómbralo `demo-respaldo.mp4` y súbelo a la carpeta compartida del equipo. **No lo subas al repositorio.**
- Apaga el laboratorio:

```bash
docker compose down
```

Con `docker compose down -v` también se borran los datos de Prometheus y Grafana.

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| `port is already allocated` al arrancar | Otro programa usa el puerto 3000, 3001 o 9090. Ciérralo, o cambia el puerto de la izquierda en `docker-compose.yml` (p. ej. `"3002:3000"`). |
| `permission denied: ./scripts/demo.sh` | `chmod +x scripts/*.sh` |
| En Windows, `bash\r: No such file or directory` | Git convirtió los saltos de línea. Clona dentro de WSL, o ejecuta `git config --global core.autocrlf input` y vuelve a clonar. |
| El dashboard aparece vacío ("No data") | Espera 30 s y recarga. Comprueba el rango de tiempo y que <http://localhost:9090/targets> muestre `demo-api` en *UP*. |
| No aparece el dashboard | `docker compose restart grafana` y recarga la página. |
| La latencia "normal" sale alta (p95 > 300 ms) | El equipo está saturado. Cierra programas y repite el paso 3. |
| Quiero empezar de cero | `docker compose down -v && docker compose up -d --build` |
