"""Paso 1: ver qué distribuciones hay en el DXF y elegir la región.
Uso: python3 vista_general.py plano.dxf salida.png [x0 x1 y0 y1]
Sin región: dibuja todo (ignorando puntos sueltos muy lejanos) con cuadrícula de coordenadas
y lista las zonas con más entidades. Con región: dibuja solo esa zona."""
import sys, collections, statistics
import ezdxf
from ezdxf import bbox
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy

doc = ezdxf.readfile(sys.argv[1]); msp = doc.modelspace()
cs = []
for e in msp:
    try: b = bbox.extents([e])
    except Exception: continue
    if b.has_data: cs.append((b.center.x, b.center.y))
if len(sys.argv) >= 7:
    x0, x1, y0, y1 = map(float, sys.argv[3:7])
else:
    mx = statistics.median(c[0] for c in cs); my = statistics.median(c[1] for c in cs)
    near = [c for c in cs if abs(c[0]-mx) < 300 and abs(c[1]-my) < 300]
    x0 = min(c[0] for c in near) - 2; x1 = max(c[0] for c in near) + 2
    y0 = min(c[1] for c in near) - 2; y1 = max(c[1] for c in near) + 2
    g = collections.Counter((int(c[0]//10)*10, int(c[1]//10)*10) for c in near)
    print('Zonas con más entidades (x, y de la celda de 10 u):')
    for k, v in g.most_common(15): print(' ', k, v)
w = 16; h = max(4, w*(y1-y0)/(x1-x0))
fig = plt.figure(figsize=(w, h)); ax = fig.add_axes([0.03, 0.03, 0.95, 0.95])
Frontend(RenderContext(doc), MatplotlibBackend(ax), config=Configuration(background_policy=BackgroundPolicy.WHITE)).draw_layout(msp, finalize=False)
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal')
ax.grid(True, lw=0.3, alpha=0.5)
fig.savefig(sys.argv[2], dpi=100, facecolor='white')
print('Región dibujada:', round(x0, 1), round(x1, 1), round(y0, 1), round(y1, 1))
