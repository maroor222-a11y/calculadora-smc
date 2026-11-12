#!/usr/bin/env bash
# Prepara el entorno para plano3d: Python, three.js local y LibreDWG (dwg2dxf).
set -e
pip install --break-system-packages -q ezdxf matplotlib reportlab playwright pillow 2>/dev/null || pip install -q ezdxf matplotlib reportlab playwright pillow
if [ ! -d /tmp/three/node_modules/three ]; then
  mkdir -p /tmp/three && (cd /tmp/three && npm i three@0.160.0 --silent)
fi
if ! command -v dwg2dxf >/dev/null && [ ! -x /tmp/libredwg-0.13.3/programs/dwg2dxf ]; then
  (cd /tmp && curl -sSL -o lr.tar.xz https://github.com/LibreDWG/libredwg/releases/download/0.13.3/libredwg-0.13.3.tar.xz \
    && tar xf lr.tar.xz && cd libredwg-0.13.3 && ./configure --disable-bindings --disable-docs -q >/dev/null && make -j8 >/dev/null)
fi
echo "OK. dwg2dxf: $(command -v dwg2dxf || echo /tmp/libredwg-0.13.3/programs/dwg2dxf)"
