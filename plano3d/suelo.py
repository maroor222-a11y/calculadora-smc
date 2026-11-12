"""Paso 4: textura del suelo (el plano en gris claro, sin textos ni cotas).
Uso: python3 suelo.py plano.dxf escena.json suelo.jpg"""
import sys, json, ezdxf
from ezdxf import bbox
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy
from PIL import Image
doc = ezdxf.readfile(sys.argv[1]); msp = doc.modelspace(); s = json.load(open(sys.argv[2]))
X0, X1, Y0, Y1 = s['area']
def keep(e):
    if e.dxftype() in ('TEXT', 'MTEXT', 'DIMENSION', 'INSERT', 'HATCH', 'IMAGE'): return False
    try: b = bbox.extents([e])
    except Exception: return False
    return b.has_data and b.extmax.x >= X0-1 and b.extmin.x <= X1+1 and b.extmax.y >= Y0-1 and b.extmin.y <= Y1+1 and (b.extmax.x-b.extmin.x) < 200
ks = set(e for e in msp if keep(e))
W, H = X1-X0, Y1-Y0; k = 100/max(W, H)*0.9
fig = plt.figure(figsize=(W*k*0.22, H*k*0.22)); ax = fig.add_axes([0, 0, 1, 1])
Frontend(RenderContext(doc), MatplotlibBackend(ax), config=Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK)).draw_layout(msp, finalize=False, filter_func=lambda e: e in ks)
ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1); ax.axis('off')
tmp = sys.argv[3] + '.png'; fig.savefig(tmp, dpi=110, facecolor='white')
im = Image.open(tmp).convert('L'); im = im.point(lambda v: 150+int(v*0.4)); im.save(sys.argv[3], quality=80)
print('suelo', im.size)
