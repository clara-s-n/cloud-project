// Escenario 3 — Degradación por errores.
// El 12 % de las peticiones responde 500. La API sigue "arriba" (up = 1,
// /health = 200) y la latencia es normal: solo la tasa de errores lo revela.
import { buildOptions, setChaos, traffic } from './lib/common.js';

// Mismos umbrales que la línea base: se espera que el de errores FALLE.
export const options = buildOptions({
  http_req_failed: ['rate<0.01'],
  http_req_duration: ['p(95)<300'],
});

export function setup() {
  setChaos('errors');
}

export default traffic;

export function teardown() {
  if (__ENV.KEEP_CHAOS !== '1') setChaos('normal');
}
