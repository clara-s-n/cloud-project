// Escenario 1 — Funcionamiento normal (línea base).
// Establece cómo se ven las métricas cuando todo va bien.
import { buildOptions, setChaos, traffic } from './lib/common.js';

export const options = buildOptions({
  http_req_failed: ['rate<0.01'],
  http_req_duration: ['p(95)<300'],
});

export function setup() {
  setChaos('normal');
}

export default traffic;
