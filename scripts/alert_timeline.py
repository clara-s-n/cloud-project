#!/usr/bin/env python3
"""Reconstruye, desde Prometheus, cuándo cambió el escenario y cuándo pasó cada
alerta a PENDING y a FIRING. Sirve para medir el tiempo de detección.

Uso: python3 scripts/alert_timeline.py [minutos_hacia_atrás]   (por defecto 30)
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

PROM = "http://localhost:9090"
minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 30
end = time.time()
start = end - minutes * 60


def query_range(q, step=5):
    url = f"{PROM}/api/v1/query_range?" + urllib.parse.urlencode(
        {"query": q, "start": start, "end": end, "step": step})
    with urllib.request.urlopen(url) as r:
        return json.load(r)["data"]["result"]


def fmt(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%H:%M:%S")


events = []

for s in query_range('demo_chaos_mode{job="demo-api"} == 1'):
    prev = None
    for ts, _ in s["values"]:
        if prev is None or ts - prev > 10:
            events.append((ts, f"escenario -> {s['metric']['mode']}"))
        prev = ts

for s in query_range('ALERTS{alertname=~"Api.*"}'):
    m = s["metric"]
    prev = None
    for ts, _ in s["values"]:
        if prev is None or ts - prev > 10:
            events.append((ts, f"alerta {m['alertname']} -> {m['alertstate'].upper()}"))
        prev = ts
    events.append((prev, f"alerta {m['alertname']} ({m['alertstate']}) visto por última vez"))

for ts, text in sorted(events):
    print(f"{fmt(ts)} UTC  {text}")
