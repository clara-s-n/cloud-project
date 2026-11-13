#!/usr/bin/env bash
# Genera el póster (HTML) y lo exporta a PDF vectorial A3 y a una vista previa PNG
# usando Chrome headless en un contenedor (no requiere instalar nada más que Docker).
#
# Uso: ./scripts/export_poster.sh [Grupo-Apellido1-Apellido2]
set -euo pipefail
cd "$(dirname "$0")/.."

NAME="${1:-Grupo-Apellido1-Apellido2}"
python3 scripts/build_poster.py

docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD/docs/poster":/work \
  --entrypoint chromium-browser zenika/alpine-chrome:124 \
  --headless --no-sandbox --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="/work/${NAME}.pdf" file:///work/poster.html 2>/dev/null

docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD/docs/poster":/work \
  --entrypoint chromium-browser zenika/alpine-chrome:124 \
  --headless --no-sandbox --disable-gpu --hide-scrollbars --window-size=1123,1587 \
  --force-device-scale-factor=1 --screenshot=/work/preview.png file:///work/poster.html 2>/dev/null

echo "PDF:      docs/poster/${NAME}.pdf"
echo "Preview:  docs/poster/preview.png"
