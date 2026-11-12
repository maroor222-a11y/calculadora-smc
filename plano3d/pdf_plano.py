"""PDF 2D del plano con el logo SMC (A4), como los planos que se mandan al cliente.
Uso: python3 pdf_plano.py plano.dxf x0 x1 y0 y1 salida.pdf [--sin-medidas] [--negro] [--apaisado] [--quitar "texto"]...
--sin-medidas: quita los rótulos de módulo (40x120...) · --negro: todo el trazo en negro."""
import sys, re, ezdxf
from ezdxf import bbox
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from matplotlib import font_manager as fm
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, LineweightPolicy, ColorPolicy
a = sys.argv; src = a[1]; X0, X1, Y0, Y1 = map(float, a[2:6]); out = a[6]
sin = '--sin-medidas' in a; negro = '--negro' in a; apa = '--apaisado' in a
quitar = [a[i+1] for i, x in enumerate(a) if x == '--quitar' and i+1 < len(a)]
doc = ezdxf.readfile(src); msp = doc.modelspace()
def keep(e):
    if e.dxftype() == 'TEXT':
        t = e.dxf.text.strip()
        if sin and re.fullmatch(r'\d{2}\s*[xX]\s*\d{3}', t): return False
        if t in quitar: return False
    try: b = bbox.extents([e])
    except Exception: return False
    return b.has_data and b.extmin.x >= X0 and b.extmax.x <= X1 and b.extmin.y >= Y0 and b.extmax.y <= Y1
ents = [e for e in msp if keep(e)]; ks = set(ents); b = bbox.extents(ents)
px0, px1, py0, py1 = b.extmin.x, b.extmax.x, b.extmin.y, b.extmax.y
W, H = (297, 210) if apa else (210, 297)
fig = plt.figure(figsize=(W/25.4, H/25.4)); page = fig.add_axes([0, 0, 1, 1]); page.set_xlim(0, W); page.set_ylim(0, H); page.axis('off')
page.add_patch(Rectangle((12, 12), W-24, H-24, fill=False, lw=0.6, ec='#c8c8c8'))
navy, green = '#0F204B', '#80BF68'; lx, ly = W-60, H-35
for col, dy in ((navy, 10.4), (green, 5.2), (navy, 0)):
    page.add_patch(Polygon([(lx, ly+dy+3.6), (lx+11, ly+dy+3.6), (lx+11, ly+dy), (lx+2.2, ly+dy)], closed=True, fc=col, ec='none'))
try: fp = fm.FontProperties(fname='/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf')
except Exception: fp = fm.FontProperties(weight='bold')
page.text(lx+11.6, ly+7.0, 'SMC', fontproperties=fp, fontsize=31, color=navy, va='center', ha='left')
mx0, mx1, my0, my1 = (22, W-22, 20, H-38) if apa else (30, W-30, 25, H-47)
pw, ph = px1-px0, py1-py0; sc = min((mx1-mx0)/pw, (my1-my0)/ph); cw, ch = pw*sc, ph*sc
ox, oy = (W-cw)/2, my0 + ((my1-my0)-ch)/2
ax = fig.add_axes([ox/W, oy/H, cw/W, ch/H])
kw = dict(background_policy=BackgroundPolicy.WHITE, lineweight_policy=LineweightPolicy.ABSOLUTE, min_lineweight=0.12)
if negro: kw['color_policy'] = ColorPolicy.BLACK
Frontend(RenderContext(doc), MatplotlibBackend(ax), config=Configuration(**kw)).draw_layout(msp, finalize=False, filter_func=lambda e: e in ks)
ax.set_xlim(px0, px1); ax.set_ylim(py0, py1); ax.set_aspect('equal'); ax.axis('off')
fig.savefig(out); print('PDF', out)
