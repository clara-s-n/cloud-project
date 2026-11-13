'use strict';

/**
 * API de demostración instrumentada con prom-client.
 *
 * Expone:
 *   - /api/*        Endpoints de negocio (productos y pedidos).
 *   - /health       Health check "ingenuo": siempre responde 200 mientras el proceso vive.
 *   - /metrics      Métricas en formato de exposición de Prometheus.
 *   - /admin/chaos  Inyección controlada de fallos (latencia y errores) para la PoC.
 *
 * La idea central de la PoC: /health sigue respondiendo 200 (la API "está disponible")
 * mientras las métricas RED (Rate, Errors, Duration) revelan la degradación.
 */

const express = require('express');
const client = require('prom-client');
const chaos = require('./chaos');

const PORT = Number(process.env.PORT || 3000);
const SERVICE_NAME = process.env.SERVICE_NAME || 'demo-api';

// ---------------------------------------------------------------------------
// Métricas
// ---------------------------------------------------------------------------
const register = new client.Registry();
register.setDefaultLabels({ service: SERVICE_NAME });

// Métricas de proceso de Node.js (CPU, memoria, event loop lag, GC...).
client.collectDefaultMetrics({ register });

// Rate + Errors: contador de peticiones etiquetado por método, ruta y código HTTP.
const httpRequestsTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total de peticiones HTTP atendidas',
  labelNames: ['method', 'route', 'status_code'],
  registers: [register],
});

// Duration: histograma de latencia. Los buckets se eligieron alrededor del
// objetivo de la PoC (p95 < 300 ms) para que histogram_quantile sea preciso ahí.
const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duración de las peticiones HTTP en segundos',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1, 1.5, 2.5, 5],
  registers: [register],
});

// Saturación: peticiones en curso.
const httpRequestsInFlight = new client.Gauge({
  name: 'http_requests_in_flight',
  help: 'Peticiones HTTP actualmente en procesamiento',
  registers: [register],
});

// Configuración de caos activa, para poder correlacionar en Grafana
// "qué inyectamos" con "qué observamos".
const chaosConfigGauge = new client.Gauge({
  name: 'demo_chaos_config',
  help: 'Configuración de inyección de fallos activa (solo para la demo)',
  labelNames: ['setting'],
  registers: [register],
});
const chaosModeGauge = new client.Gauge({
  name: 'demo_chaos_mode',
  help: 'Modo de caos activo (1 = activo)',
  labelNames: ['mode'],
  registers: [register],
});

function publishChaosMetrics() {
  const cfg = chaos.getConfig();
  chaosConfigGauge.set({ setting: 'latency_ms' }, cfg.latencyMs);
  chaosConfigGauge.set({ setting: 'latency_ratio' }, cfg.latencyRatio);
  chaosConfigGauge.set({ setting: 'error_ratio' }, cfg.errorRatio);
  for (const mode of chaos.MODES) {
    chaosModeGauge.set({ mode }, mode === cfg.mode ? 1 : 0);
  }
}
publishChaosMetrics();

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------
const app = express();
app.disable('x-powered-by');
app.use(express.json());

// Middleware de instrumentación. Se registra antes que las rutas para medir
// también el tiempo añadido por el resto de middlewares.
app.use((req, res, next) => {
  if (req.path === '/metrics') return next(); // no medimos el scrape propio

  const start = process.hrtime.bigint();
  httpRequestsInFlight.inc();

  res.on('finish', () => {
    httpRequestsInFlight.dec();
    const seconds = Number(process.hrtime.bigint() - start) / 1e9;
    // Usamos la PLANTILLA de la ruta (/api/products/:id), no la URL real,
    // para evitar una explosión de cardinalidad en Prometheus.
    const route = req.route ? req.baseUrl + req.route.path : 'unmatched';
    const labels = { method: req.method, route, status_code: String(res.statusCode) };
    httpRequestsTotal.inc(labels);
    httpRequestDuration.observe(labels, seconds);
  });

  next();
});

// --- Infraestructura -------------------------------------------------------
app.get('/health', (_req, res) => {
  // Health check intencionalmente superficial: comprueba que el proceso responde,
  // no que el servicio funcione bien. Es lo que usan muchos balanceadores.
  res.json({ status: 'ok', uptimeSeconds: Math.round(process.uptime()) });
});

app.get('/metrics', async (_req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

// --- Control de caos (solo demo) -------------------------------------------
app.get('/admin/chaos', (_req, res) => res.json(chaos.getConfig()));

app.post('/admin/chaos', (req, res) => {
  try {
    const cfg = chaos.setConfig(req.body || {});
    publishChaosMetrics();
    console.log(`[chaos] ${JSON.stringify(cfg)}`);
    res.json(cfg);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// --- Negocio -----------------------------------------------------------------
// La inyección de fallos se aplica POR RUTA (y no con router.use) para que
// Express ya haya resuelto req.route cuando se responde con un 500 simulado.
// Si no, esas respuestas quedarían etiquetadas como route="unmatched".
const api = express.Router();

const products = Array.from({ length: 12 }, (_, i) => ({
  id: i + 1,
  name: `Producto ${i + 1}`,
  price: Number((5 + i * 3.5).toFixed(2)),
  stock: 10 + ((i * 7) % 25),
}));
let nextOrderId = 1;

api.get('/products', chaos.middleware, async (_req, res) => {
  await simulateWork(5, 30);
  res.json(products);
});

api.get('/products/:id', chaos.middleware, async (req, res) => {
  await simulateWork(3, 20);
  const product = products.find((p) => p.id === Number(req.params.id));
  if (!product) return res.status(404).json({ error: 'Producto no encontrado' });
  res.json(product);
});

api.post('/orders', chaos.middleware, async (req, res) => {
  await simulateWork(20, 60); // escribir un pedido es más costoso que leer
  const { productId, quantity = 1 } = req.body || {};
  const product = products.find((p) => p.id === Number(productId));
  if (!product) return res.status(400).json({ error: 'productId inválido' });
  if (!Number.isInteger(quantity) || quantity < 1) {
    return res.status(400).json({ error: 'quantity debe ser un entero positivo' });
  }
  res.status(201).json({ id: nextOrderId++, productId: product.id, quantity, total: product.price * quantity });
});

app.use('/api', api);

app.use((_req, res) => res.status(404).json({ error: 'Not found' }));

// eslint-disable-next-line no-unused-vars
app.use((err, _req, res, _next) => {
  console.error(err);
  res.status(500).json({ error: 'Internal Server Error' });
});

function simulateWork(minMs, maxMs) {
  const ms = minMs + Math.random() * (maxMs - minMs);
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ---------------------------------------------------------------------------
const server = app.listen(PORT, () => {
  console.log(`${SERVICE_NAME} escuchando en :${PORT}`);
});

function shutdown(signal) {
  console.log(`${signal} recibido, cerrando...`);
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(1), 5000).unref();
}
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
