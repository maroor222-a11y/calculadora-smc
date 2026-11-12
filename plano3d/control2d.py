"""Paso 3: dibujo de control 2D de lo extraído sobre el plano (para revisar antes del 3D).
Uso: python3 control2d.py plano.dxf escena.json control.png"""
import sys, json, math, ezdxf
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy
doc = ezdxf.readfile(sys.argv[1]); msp = doc.modelspace(); s = json.load(open(sys.argv[2]))
ox, oy = s['origin']; X0, X1, Y0, Y1 = s['area']
def R(c, ang, L, D):
    a = math.radians(ang); u = (math.cos(a), math.sin(a)); v = (-u[1], u[0]); cx, cy = c[0]+ox, c[1]+oy
    return [(cx+sx*L/2*u[0]+sy*D/2*v[0], cy+sx*L/2*u[1]+sy*D/2*v[1]) for sx, sy in ((-1,-1),(1,-1),(1,1),(-1,1))]
fig = plt.figure(figsize=(14, 14*(Y1-Y0)/(X1-X0))); ax = fig.add_axes([0, 0, 1, 1])
Frontend(RenderContext(doc), MatplotlibBackend(ax), config=Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK)).draw_layout(msp, finalize=False)
for w in s['walls']: ax.add_patch(Polygon(R(w['c'], w['ang'], w['L'], w['D']), fc='magenta' if w['over'] else 'orange', alpha=.45))
for i in s['islands']:
    a = math.radians(i['ang']); u = (math.cos(a), math.sin(a)); v = (-u[1], u[0])
    for s0, s1, _ in i['segs']:
        for sd in (-1, 1):
            m = (s0+s1)/2; off = sd*(i['D']/2+0.03)
            c = (i['o'][0]+u[0]*m+v[0]*off, i['o'][1]+u[1]*m+v[1]*off)
            ax.add_patch(Polygon(R(c, i['ang'], s1-s0, i['D']), fc='green', alpha=.45))
for c in s['cabs']: ax.add_patch(Polygon(R(c['c'], c['ang'], c['W'], c['L']), fc='purple', alpha=.5))
for e in s['equip']:
    ax.add_patch(Polygon(R(e['c'], e['ang'], e['L'], e['D']), fc='tab:blue', alpha=.4))
    ax.text(e['c'][0]+ox, e['c'][1]+oy, e['name'], fontsize=7, ha='center', color='navy')
for a, b in s['segs']: ax.plot([a[0]+ox, b[0]+ox], [a[1]+oy, b[1]+oy], color='red', lw=1)
ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1); ax.set_aspect('equal'); ax.axis('off')
fig.savefig(sys.argv[3], dpi=90, facecolor='white')
print('naranja = pared · magenta = pared sobre arcón · verde = góndola · morado = cabecero · azul = equipos · rojo = paredes del local')
