// Escenario 2 — Degradación por latencia.
// El 25 % de las peticiones tarda ~1,2 s extra. Todas responden 200:
// un monitoreo de disponibilidad no detecta nada, pero la experiencia empeora.
import { buildOptions, setChaos, traffic } from './lib/common.js';

// Mismos umbrales que la línea base: se espera que el de latencia FALLE.
export const options = buildOptions({
  http_req_failed: ['rate<0.01'],
  http_req_duration: ['p(95)<300'],
});

export function setup() {
  setChaos('latency');
}

export default traffic;

export function teardown() {
  if (__ENV.KEEP_CHAOS !== '1') setChaos('normal');
}
