"""Paso 7: PDF A4 apaisado con las vistas 3D para el cliente.
Uso: python3 pdf_vistas.py escena.json carpeta_capturas salida.pdf [vista1 vista2 ...]
Por defecto: general, planta, ojos y los primeros planos que existan."""
import sys, json, os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
def font(name, files):
    for f in files:
        if os.path.exists(f): pdfmetrics.registerFont(TTFont(name, f)); return name
    return 'Helvetica-Bold' if 'B' in name else 'Helvetica'
FB = font('PB', ['/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'])
FR = font('PR', ['/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'])
NAVY = HexColor('#0F204B'); GREEN = HexColor('#80BF68'); GREY = HexColor('#5d6577'); LINE = HexColor('#dfe3ea')
s = json.load(open(sys.argv[1])); d = sys.argv[2]; out = sys.argv[3]
cap = {'general': ('Vista general', 'Distribución completa del local con estanterías, góndolas y equipos.'),
       'planta': ('Vista en planta', 'Distribución vista desde arriba.'),
       'ojos': ('A la altura de los ojos', 'Recorrido por la tienda a la altura de un cliente.')}
for c in s['views'].get('close', []): cap[c['key']] = (c['title'], c.get('caption', ''))
cap.update({k: tuple(v) for k, v in s.get('captions', {}).items()})
order = sys.argv[4:] or ['general', 'planta', 'ojos'] + [c['key'] for c in s['views'].get('close', [])]
order = [o for o in order if os.path.exists(f'{d}/{o}.png')]
W, H = landscape(A4); c = canvas.Canvas(out, pagesize=(W, H)); cli = s.get('cliente') or 'Tienda'
c.setTitle(f'{cli} · Propuesta 3D · SMC')
def logo(x, y, k=1.0):
    for col, dy in ((NAVY, 2*14.5*k), (GREEN, 14.5*k), (NAVY, 0)):
        c.setFillColor(col); p = c.beginPath(); p.moveTo(x, y+dy+10*k); p.lineTo(x+30*k, y+dy+10*k); p.lineTo(x+30*k, y+dy); p.lineTo(x+6*k, y+dy); p.close(); c.drawPath(p, fill=1, stroke=0)
    c.setFillColor(NAVY); c.setFont(FB, 37*k); c.drawString(x+33*k, y+3*k, 'SMC')
for k, name in enumerate(order, 1):
    title, text = cap.get(name, (name, ''))
    logo(W-150, H-62, 0.95)
    c.setFillColor(NAVY); c.setFont(FB, 20); c.drawString(36, H-48, cli)
    c.setFillColor(GREY); c.setFont(FR, 11); c.drawString(36, H-66, 'Propuesta de equipamiento · vista 3D')
    c.setStrokeColor(LINE); c.setLineWidth(0.8); c.line(36, H-80, W-36, H-80)
    ir = ImageReader(f'{d}/{name}.png'); iw, ih = ir.getSize()
    bx, by, bw, bh = 36, 62, W-72, H-80-62-38; sc = min(bw/iw, bh/ih)
    c.drawImage(ir, bx+(bw-iw*sc)/2, by+(bh-ih*sc)/2, iw*sc, ih*sc)
    c.setFillColor(NAVY); c.setFont(FB, 13); c.drawString(36, H-104, f'{k}. {title}')
    c.setFillColor(GREY); c.setFont(FR, 10.5); c.drawString(36, 40, text)
    c.setFont(FR, 8); c.setFillColor(HexColor('#8a91a0'))
    c.drawString(36, 22, 'Imagen orientativa. Medidas según plano y fichas de los fabricantes. Suministros Materiales Canarias SL · smccanarias.com')
    c.drawRightString(W-36, 22, f'{k} / {len(order)}'); c.showPage()
c.save(); print('PDF', out, len(order), 'páginas')
