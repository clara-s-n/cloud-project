// Lógica compartida por los tres escenarios de la PoC.
//
// Cada escenario genera el MISMO patrón de tráfico (tasa constante de peticiones,
// mezcla realista de endpoints) y solo cambia la configuración de fallos que se
// inyecta en la API. Así cualquier diferencia en las métricas se debe al fallo,
// no a un cambio en la carga.
import http from 'k6/http';
import { check } from 'k6';

export const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';
const RATE = Number(__ENV.RATE || 30); // peticiones por segundo
const DURATION = __ENV.DURATION || '3m';

export function buildOptions(thresholds) {
  return {
    scenarios: {
      trafico: {
        // Tasa de llegada constante (modelo "abierto"): si la API se vuelve lenta,
        // k6 sigue enviando peticiones al mismo ritmo en lugar de frenar.
        // Así no se oculta la degradación (evita el "coordinated omission").
        executor: 'constant-arrival-rate',
        rate: RATE,
        timeUnit: '1s',
        duration: DURATION,
        preAllocatedVUs: 50, // suficientes para ~1,5 s × 30 req/s sin tener que crear VUs a mitad de la prueba
        maxVUs: 200,
      },
    },
    thresholds,
    // Las respuestas 404 forman parte del tráfico esperado (ids inexistentes).
    summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  };
}

export function setChaos(mode) {
  const res = http.post(`${BASE_URL}/admin/chaos`, JSON.stringify({ mode }), {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'admin' },
  });
  if (res.status !== 200) {
    throw new Error(`No se pudo configurar el modo "${mode}": ${res.status} ${res.body}`);
  }
  console.log(`Modo de caos configurado: ${res.body}`);
}

// Mezcla de tráfico: 60 % listado, 25 % detalle, 15 % creación de pedidos.
export function traffic() {
  const r = Math.random();

  if (r < 0.6) {
    const res = http.get(`${BASE_URL}/api/products`, { tags: { name: 'GET /api/products' } });
    check(res, { 'listado 200': (x) => x.status === 200 });
  } else if (r < 0.85) {
    // ~8 % de los ids no existen -> 404 esperado (error del cliente, no del servicio).
    const id = Math.floor(Math.random() * 13) + 1;
    const res = http.get(`${BASE_URL}/api/products/${id}`, {
      tags: { name: 'GET /api/products/:id' },
      responseCallback: http.expectedStatuses(200, 404),
    });
    check(res, { 'detalle 200/404': (x) => x.status === 200 || x.status === 404 });
  } else {
    const body = JSON.stringify({
      productId: Math.floor(Math.random() * 12) + 1,
      quantity: Math.floor(Math.random() * 3) + 1,
    });
    const res = http.post(`${BASE_URL}/api/orders`, body, {
      headers: { 'Content-Type': 'application/json' },
      tags: { name: 'POST /api/orders' },
    });
    check(res, { 'pedido 201': (x) => x.status === 201 });
  }
}
