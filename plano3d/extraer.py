"""Paso 2: extraer estanterías, góndolas, equipos y paredes de una región del DXF.
Uso: python3 extraer.py plano.dxf config.json escena.json [catalogo.json]
config.json: {"cliente": "...", "region": [x0, x1, y0, y1], "altura_local": 2.6,
              "alturas": {"Cámara de frío": 1.96}, "vistas": {...opcional}}
Reglas:
- Módulos = textos 'NNxNNN' (fondo x largo en cm). Centro = centro del texto; dirección = rotación.
- Góndola = módulos enfrentados (separación entre 0,30 y 0,75 m) en el mismo eje; el resto, pared.
- Textos 'Cabecero' = remate en el extremo de góndola más cercano.
- Equipos = polilíneas cerradas reconocidas por color y medidas según catalogo.json.
- Módulo de pared dentro de un arcón = estantería por encima del arcón."""
import sys, json, math, re, os
import ezdxf
from ezdxf import bbox

dxf, cfgp, outp = sys.argv[1:4]
catp = sys.argv[4] if len(sys.argv) > 4 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'catalogo.json')
cfg = json.load(open(cfgp)); cat = json.load(open(catp))
doc = ezdxf.readfile(dxf); msp = doc.modelspace()
X0, X1, Y0, Y1 = cfg['region']

def inreg_b(b): return b.has_data and b.extmin.x >= X0 and b.extmax.x <= X1 and b.extmin.y >= Y0 and b.extmax.y <= Y1
def rect(cx, cy, ang, L, D):
    a = math.radians(ang); u = (math.cos(a), math.sin(a)); v = (-u[1], u[0])
    return [(cx+sx*L/2*u[0]+sy*D/2*v[0], cy+sx*L/2*u[1]+sy*D/2*v[1]) for sx, sy in ((-1,-1),(1,-1),(1,1),(-1,1))]
def pip(p, poly):
    x, y = p; ins = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1: ins = not ins
    return ins
def grow(poly, d):
    cx = sum(p[0] for p in poly)/len(poly); cy = sum(p[1] for p in poly)/len(poly); out = []
    for x, y in poly:
        dx, dy = x-cx, y-cy; n = math.hypot(dx, dy) or 1; out.append((x+dx/n*d, y+dy/n*d))
    return out
def rect_from_pts(p):
    cx = sum(q[0] for q in p[:4])/4; cy = sum(q[1] for q in p[:4])/4
    a = math.dist(p[0], p[1]); c = math.dist(p[1], p[2])
    if a >= c: ang = math.degrees(math.atan2(p[1][1]-p[0][1], p[1][0]-p[0][0])); L, D = a, c
    else: ang = math.degrees(math.atan2(p[2][1]-p[1][1], p[2][0]-p[1][0])); L, D = c, a
    return cx, cy, ang % 360, L, D

# ---------- textos
texts = []
for t in msp.query('TEXT MTEXT'):
    s = (t.dxf.text if t.dxftype() == 'TEXT' else t.plain_text()).strip()
    try: b = bbox.extents([t])
    except Exception: continue
    if not inreg_b(b): continue
    texts.append(dict(s=s, cx=b.center.x, cy=b.center.y, rot=(t.dxf.get('rotation', 0) or 0) % 360))
mods = []
for t in texts:
    m = re.fullmatch(r'(\d{2})\s*[xX]\s*(\d{3})', t['s'])
    if m: mods.append(dict(cx=t['cx'], cy=t['cy'], rot=t['rot'], D=int(m.group(1))/100, L=int(m.group(2))/100, label=f"{m.group(1)}x{m.group(2)}"))
cabs = [t for t in texts if t['s'].lower().startswith('cabecero')]

# ---------- equipos
equip = []
for e in msp.query('LWPOLYLINE'):
    b = bbox.extents([e])
    if not inreg_b(b): continue
    pts = [tuple(map(float, q)) for q in e.get_points('xy')]
    if len(pts) not in (4, 5): continue
    cx, cy, ang, L, D = rect_from_pts(pts)
    col = e.dxf.color
    for it in cat['equipos']:
        if col in it['color'] and it['L'][0] <= L <= it['L'][1] and it['D'][0] <= D <= it['D'][1]:
            H = cfg.get('alturas', {}).get(it['nombre'], it['alto'])
            n = 1
            if it.get('modulo'): n = max(1, round(L / it['modulo']))
            for k in range(n):   # p. ej. dos panaderías dibujadas en un solo rectángulo
                Lk = L/n; off = -L/2 + Lk*(k+0.5); a = math.radians(ang)
                ck = (cx + off*math.cos(a), cy + off*math.sin(a))
                equip.append(dict(name=it['nombre'], kind=it['tipo'], doors=it.get('puertas', 0), info=it['info'],
                                  cx=ck[0], cy=ck[1], ang=ang, L=Lk, D=D, H=H, poly=rect(ck[0], ck[1], ang, Lk, D)))
            break
# equipos dibujados con líneas sueltas: se reconocen por su rótulo (p. ej. 'PAN') y la medida del catálogo
for it in cat['equipos']:
    if not it.get('texto'): continue
    for t in texts:
        if not re.search(it['texto'], t['s']): continue
        if any(e['name'] == it['nombre'] and pip((t['cx'], t['cy']), e['poly']) for e in equip): continue
        L, D = it['medida']; H = cfg.get('alturas', {}).get(it['nombre'], it['alto'])
        equip.append(dict(name=it['nombre'], kind=it['tipo'], doors=it.get('puertas', 0), info=it['info'],
                          cx=t['cx'], cy=t['cy'], ang=t['rot'], L=L, D=D, H=H, poly=rect(t['cx'], t['cy'], t['rot'], L, D)))
# quitar duplicados (misma polilínea dibujada dos veces)
uniq = []
for e in equip:
    if not any(u['name'] == e['name'] and math.dist((u['cx'], u['cy']), (e['cx'], e['cy'])) < 0.05 for u in uniq): uniq.append(e)
equip = uniq
arcon_polys = [grow(e['poly'], 0.05) for e in equip if e['kind'] == 'arcon']
# los textos de módulo que caen dentro de una panadería o caja no son estanterías
blocked = [grow(e['poly'], 0.02) for e in equip if e['kind'] in ('pan', 'caja', 'frutero', 'vertical', 'mural', 'camara')]
mods = [m for m in mods if not any(pip((m['cx'], m['cy']), p) for p in blocked)]

# ---------- góndolas (módulos enfrentados) vs pared
n = len(mods); parent = list(range(n))
def find(i):
    while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
    return i
partner = [False]*n
def uv(m):
    a = math.radians(m['rot'] % 180); u = (math.cos(a), math.sin(a)); return u, (-u[1], u[0])
for i in range(n):
    for j in range(i+1, n):
        mi, mj = mods[i], mods[j]
        da = abs(((mi['rot'] - mj['rot']) + 90) % 180 - 90)
        if da > 3: continue
        u, v = uv(mi); d = (mj['cx']-mi['cx'], mj['cy']-mi['cy'])
        al = d[0]*u[0]+d[1]*u[1]; pe = d[0]*v[0]+d[1]*v[1]
        half = (mi['L']+mj['L'])/2
        if 0.3 < abs(pe) < 0.75 and abs(al) < half + 0.05:
            partner[i] = partner[j] = True; parent[find(i)] = find(j)
        elif abs(pe) < 0.12 and abs(abs(al) - half) < 0.12:
            parent[find(i)] = find(j)
groups = {}
for i in range(n): groups.setdefault(find(i), []).append(i)
islands = []; walls = []
for g in groups.values():
    if any(partner[i] for i in g):
        ms = [mods[i] for i in g]; u, v = uv(ms[0]); ang = math.degrees(math.atan2(u[1], u[0]))
        ox, oy = ms[0]['cx'], ms[0]['cy']
        pes = [(m['cx']-ox)*v[0]+(m['cy']-oy)*v[1] for m in ms]
        lo_side = [p for p in pes if p <= (min(pes)+max(pes))/2]; hi_side = [p for p in pes if p > (min(pes)+max(pes))/2]
        sp = ((sum(lo_side)/len(lo_side)) + (sum(hi_side)/len(hi_side) if hi_side else sum(lo_side)/len(lo_side)+0.48))/2
        segs = []
        for m in ms:
            a = (m['cx']-ox)*u[0]+(m['cy']-oy)*u[1]
            seg = (round(a-m['L']/2, 3), round(a+m['L']/2, 3), m['label'])
            if not any(abs(s[0]-seg[0]) < 0.1 and abs(s[1]-seg[1]) < 0.1 for s in segs): segs.append(seg)
        segs.sort()
        org = (ox + sp*v[0], oy + sp*v[1])
        D = max(m['D'] for m in ms)
        islands.append(dict(org=org, ang=ang, segs=segs, D=D, H=cat['gondola']['alto']))
    else:
        for i in g:
            m = mods[i]
            over = any(pip((m['cx'], m['cy']), p) for p in arcon_polys)
            walls.append(dict(cx=m['cx'], cy=m['cy'], ang=m['rot'], L=m['L'], D=m['D'], H=cat['estanteria_pared']['alto'],
                              label=m['label'], over=over, poly=rect(m['cx'], m['cy'], m['rot'], m['L'], m['D'])))
cab_out = []
for c in cabs:
    best = None
    for isl in islands:
        a = math.radians(isl['ang']); u = (math.cos(a), math.sin(a))
        for end, sg in ((isl['segs'][0][0], -1), (isl['segs'][-1][1], 1)):
            p = (isl['org'][0]+u[0]*end, isl['org'][1]+u[1]*end)
            d = math.dist(p, (c['cx'], c['cy']))
            if best is None or d < best[0]: best = (d, isl, end, sg)
    if best and best[0] < 1.2:
        _, isl, end, sg = best; a = math.radians(isl['ang']); u = (math.cos(a), math.sin(a))
        mid = end + sg*cat['gondola']['cabecero_fondo']/2
        cab_out.append(dict(c=(isl['org'][0]+u[0]*mid, isl['org'][1]+u[1]*mid), ang=isl['ang']-90,
                            L=cat['gondola']['cabecero_fondo'], W=2*isl['D']+0.1, H=isl['H']))

# ---------- área del local, paredes y vistas
pts = [p for w in walls for p in w['poly']] + [p for e in equip for p in e['poly']]
for isl in islands:
    a = math.radians(isl['ang']); u = (math.cos(a), math.sin(a))
    for s in (isl['segs'][0][0], isl['segs'][-1][1]): pts.append((isl['org'][0]+u[0]*s, isl['org'][1]+u[1]*s))
if not pts: sys.exit('No se ha encontrado ningún mueble en la región. Revisa "region" en el config.')
AX0 = min(p[0] for p in pts)-0.8; AX1 = max(p[0] for p in pts)+0.8; AY0 = min(p[1] for p in pts)-0.8; AY1 = max(p[1] for p in pts)+0.8
AX0, AX1, AY0, AY1 = cfg.get('area', [AX0, AX1, AY0, AY1])
foot = [grow(e['poly'], 0.06) for e in equip] + [grow(w['poly'], 0.06) for w in walls]
for isl in islands:
    a = math.radians(isl['ang']); u = (math.cos(a), math.sin(a)); v = (-u[1], u[0]); h = isl['D']+0.15
    lo, hi = isl['segs'][0][0]-0.4, isl['segs'][-1][1]+0.4; o = isl['org']
    foot.append([(o[0]+u[0]*s+v[0]*t, o[1]+u[1]*s+v[1]*t) for s, t in ((lo,-h),(hi,-h),(hi,h),(lo,h))])
def clip(a, b):  # Liang-Barsky contra el área
    x0, y0 = a; dx, dy = b[0]-x0, b[1]-y0; t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0-AX0), (dx, AX1-x0), (-dy, y0-AY0), (dy, AY1-y0)):
        if p == 0:
            if q < 0: return None
        else:
            r = q/p
            if p < 0: t0 = max(t0, r)
            else: t1 = min(t1, r)
    if t0 > t1: return None
    return (x0+t0*dx, y0+t0*dy), (x0+t1*dx, y0+t1*dy)
segs = []
for e in msp:
    if e.dxftype() not in ('LINE', 'LWPOLYLINE') or e.dxf.color not in (256, 7): continue
    try: b = bbox.extents([e])
    except Exception: continue
    if not inreg_b(b): continue
    if e.dxftype() == 'LINE': P = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    else:
        P = [tuple(map(float, q)) for q in e.get_points('xy')]
        if e.closed: P.append(P[0])
    for a, bb in zip(P, P[1:]):
        r = clip(a, bb)
        if not r or math.dist(*r) < 0.6: continue
        a2, b2 = r; mid = ((a2[0]+b2[0])/2, (a2[1]+b2[1])/2)
        if any(pip(mid, f) for f in foot): continue
        segs.append([a2, b2])

ox, oy = AX0, AY0
T = lambda p: [round(p[0]-ox, 3), round(p[1]-oy, 3)]
allc = [(w['cx'], w['cy']) for w in walls] + [(e['cx'], e['cy']) for e in equip] + [isl['org'] for isl in islands]
CX = sum(p[0] for p in allc)/len(allc); CY = sum(p[1] for p in allc)/len(allc)
FW, FH = AX1-AX0, AY1-AY0; S = max(FW, FH)
cxl, cyl = CX-ox, CY-oy
def W3(x, y, h=0): return [round(x, 2), round(h, 2), round(-y, 2)]
views = dict(
    gen=dict(pos=W3(cxl-0.54*S, cyl-0.57*S, 0.56*S), tgt=W3(cxl, cyl)),
    top=dict(pos=W3(FW/2, FH/2, 0.95*S), tgt=W3(FW/2, FH/2+0.05)),
)
# vista a la altura de los ojos: desde la esquina del local más alejada de los equipos verticales, mirando al centro
cands = [(AX0+1.4, AY0+1.0), (AX1-1.4, AY0+1.0), (AX0+1.4, AY1-1.0), (AX1-1.4, AY1-1.0)]
def free(p): return not any(pip(p, f) for f in foot)
cands = [c for c in cands if free(c)] or cands
eye = min(cands, key=lambda c: abs(math.dist(c, (CX, CY)) - 0.45*S))
views['eye'] = dict(pos=W3(eye[0]-ox, eye[1]-oy, 1.6), tgt=W3(cxl, cyl, 1.2))
# primeros planos por grupo de muebles
grp_def = [('fruteros', 'Fruteros y panaderías', ('frutero', 'pan')),
           ('arcones', 'Arcones con estantería encima', ('arcon',)), ('caja', 'Mostrador de caja', ('caja',))]
close = []
# pasillo de frío vertical: cámara al principio de la fila de armarios, mirando a lo largo de ella
ver = [e for e in equip if e['kind'] == 'vertical']
if ver:
    a = math.radians(ver[0]['ang']); u = (math.cos(a), math.sin(a)); v = (-u[1], u[0])
    gx = sum(e['cx'] for e in ver)/len(ver); gy = sum(e['cy'] for e in ver)/len(ver)
    if (CX-gx)*v[0] + (CY-gy)*v[1] < 0: v = (-v[0], -v[1])
    al = [(e['cx']-gx)*u[0] + (e['cy']-gy)*u[1] for e in ver]
    lo = min(al) - max(e['L'] for e in ver)/2; hi = max(al) + max(e['L'] for e in ver)/2
    off = ver[0]['D']/2 + 0.75
    p0 = (gx + u[0]*(lo-0.6) + v[0]*off, gy + u[1]*(lo-0.6) + v[1]*off)
    p1 = (gx + u[0]*hi + v[0]*(off-0.35), gy + u[1]*hi + v[1]*(off-0.35))
    # empezar por el extremo que esté libre
    if not free(p0): p0, p1 = (gx + u[0]*(hi+0.6) + v[0]*off, gy + u[1]*(hi+0.6) + v[1]*off), (gx + u[0]*lo + v[0]*(off-0.35), gy + u[1]*lo + v[1]*(off-0.35))
    close.append(dict(key='neveras', title='Pasillo de frío vertical', pos=W3(p0[0]-ox, p0[1]-oy, 1.6), tgt=W3(p1[0]-ox, p1[1]-oy, 1.2)))
for key, title, kinds in grp_def:
    es = [e for e in equip if e['kind'] in kinds]
    if not es: continue
    gx = sum(e['cx'] for e in es)/len(es); gy = sum(e['cy'] for e in es)/len(es)
    dx, dy = CX-gx, CY-gy; dn = math.hypot(dx, dy) or 1
    span = max(math.dist((a['cx'], a['cy']), (b['cx'], b['cy'])) for a in es for b in es) + max(e['L'] for e in es)
    dist = max(3.8, 1.1*span)
    px, py = gx + dx/dn*dist, gy + dy/dn*dist
    close.append(dict(key=key, title=title, pos=W3(px-ox, py-oy, 2.8), tgt=W3(gx-ox, gy-oy, 0.8)))
views['close'] = close
views.update({k: v for k, v in cfg.get('vistas', {}).items()})

scene = dict(
    cliente=cfg.get('cliente', ''), origin=[ox, oy], area=[AX0, AX1, AY0, AY1], size=[round(FW, 3), round(FH, 3)],
    center=T((CX, CY)), room_h=cfg.get('altura_local', 2.6), canto=cfg.get('color_canto', cat['color_canto']),
    shelf=cat['estanteria_pared'], gondola=cat['gondola'],
    equip=[dict(name=e['name'], kind=e['kind'], doors=e['doors'], info=e['info'], c=T((e['cx'], e['cy'])), ang=round(e['ang'], 3), L=round(e['L'], 3), D=round(e['D'], 3), H=e['H']) for e in equip],
    walls=[dict(c=T((w['cx'], w['cy'])), ang=round(w['ang'], 3), L=w['L'], D=w['D'], H=w['H'], label=w['label'], over=w['over']) for w in walls],
    islands=[dict(o=T(i['org']), ang=round(i['ang'], 3), segs=i['segs'], D=i['D'], H=i['H']) for i in islands],
    cabs=[dict(c=T(c['c']), ang=round(c['ang'], 3), L=c['L'], W=round(c['W'], 3), H=c['H']) for c in cab_out],
    segs=[[T(a), T(b)] for a, b in segs], views=views)
json.dump(scene, open(outp, 'w'), ensure_ascii=False)
from collections import Counter
print('Estantería de pared:', len(walls), 'módulos (', sum(w['over'] for w in walls), 'sobre arcón )')
print('Góndolas:', len(islands), '·', sum(len(i['segs']) for i in islands), 'tramos · cabeceros:', len(cab_out))
print('Equipos:', dict(Counter(e['name'] for e in equip)))
print('Paredes:', len(segs), 'segmentos · área', [round(v, 2) for v in (AX0, AX1, AY0, AY1)])
otros = sorted(set(t['s'] for t in texts if not re.fullmatch(r'(\d{2})\s*[xX]\s*(\d{3})', t['s']) and not t['s'].lower().startswith('cabecero')))
print('Otros textos en la región (revisar si falta algún mueble):', otros)
