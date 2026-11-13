'use strict';

/**
 * Inyección de fallos controlada para los escenarios de la PoC.
 *
 *   normal  -> sin fallos.
 *   latency -> el 25 % de las peticiones tarda ~1,2 s extra. La media sube poco,
 *              pero los percentiles altos (p95/p99) se disparan.
 *   errors  -> el 12 % de las peticiones responde 500. La API sigue "arriba".
 *
 * También se puede enviar una configuración personalizada:
 *   { "latencyMs": 800, "latencyRatio": 0.5, "errorRatio": 0.02 }
 */

const PRESETS = {
  normal: { latencyMs: 0, latencyRatio: 0, errorRatio: 0 },
  latency: { latencyMs: 1200, latencyRatio: 0.25, errorRatio: 0 },
  errors: { latencyMs: 0, latencyRatio: 0, errorRatio: 0.12 },
};
const MODES = [...Object.keys(PRESETS), 'custom'];

let config = { mode: 'normal', ...PRESETS.normal };

function getConfig() {
  return { ...config };
}

function setConfig(body) {
  if (body.mode && body.mode !== 'custom') {
    if (!PRESETS[body.mode]) {
      throw new Error(`Modo desconocido "${body.mode}". Válidos: ${MODES.join(', ')}`);
    }
    config = { mode: body.mode, ...PRESETS[body.mode] };
    return getConfig();
  }

  const next = {
    mode: 'custom',
    latencyMs: num(body.latencyMs, config.latencyMs, 0, 30000, 'latencyMs'),
    latencyRatio: num(body.latencyRatio, config.latencyRatio, 0, 1, 'latencyRatio'),
    errorRatio: num(body.errorRatio, config.errorRatio, 0, 1, 'errorRatio'),
  };
  config = next;
  return getConfig();
}

function num(value, fallback, min, max, name) {
  if (value === undefined) return fallback;
  const n = Number(value);
  if (!Number.isFinite(n) || n < min || n > max) {
    throw new Error(`${name} debe estar entre ${min} y ${max}`);
  }
  return n;
}

async function middleware(_req, res, next) {
  const { latencyMs, latencyRatio, errorRatio } = config;

  if (latencyMs > 0 && Math.random() < latencyRatio) {
    // ±25 % de variación para que no sea un valor constante artificial.
    const jitter = 0.75 + Math.random() * 0.5;
    await new Promise((resolve) => setTimeout(resolve, latencyMs * jitter));
  }

  if (errorRatio > 0 && Math.random() < errorRatio) {
    return res.status(500).json({ error: 'Fallo simulado (chaos)' });
  }

  next();
}

module.exports = { MODES, PRESETS, getConfig, setConfig, middleware };
