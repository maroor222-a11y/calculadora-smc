"""Paso 6: capturas de la página 3D con Chrome sin pantalla.
Uso: python3 capturas.py pagina.html escena.json carpeta_salida [--ui]
Saca general.png y planta.png (con paredes y rótulos, recortadas) y un primer plano por grupo de equipos
(sin paredes ni rótulos). --ui deja visibles cabecera y leyenda (para revisar)."""
import asyncio, sys, json, os, shutil
from playwright.async_api import async_playwright
from PIL import Image, ImageChops
ROOT = '/tmp/three/node_modules/three/'
html, scenep, out = sys.argv[1:4]; ui = '--ui' in sys.argv
s = json.load(open(scenep)); os.makedirs(out, exist_ok=True)
V = [('general', s['views']['gen'], True, True), ('planta', s['views']['top'], True, True), ('ojos', s['views']['eye'], False, False)]
V += [(c['key'], c, False, False) for c in s['views'].get('close', [])]
def chrome():
    for p in ('/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser', shutil.which('google-chrome') or ''):
        if p and os.path.exists(p): return p
    return None
async def main():
    async with async_playwright() as p:
        kw = dict(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        if chrome(): kw['executable_path'] = chrome()
        b = await p.chromium.launch(**kw)
        pg = await b.new_page(viewport={'width': 1600, 'height': 1000}, device_scale_factor=1.5)
        async def route(r): await r.fulfill(path=ROOT + r.request.url.split('three@0.160.0/')[1], content_type='application/javascript')
        await pg.route('**/three@0.160.0/**', route)
        await pg.goto('file://' + os.path.abspath(html)); await pg.wait_for_function('window.__ready===true', timeout=90000)
        if not ui: await pg.add_style_tag(content='header,#legend,#help,#tip{display:none!important}')
        for name, v, w, l in V:
            await pg.evaluate(f"window.__walls({str(w).lower()}); window.__labels({str(l).lower()}); window.__cam({json.dumps(v['pos'])},{json.dumps(v['tgt'])})")
            await pg.wait_for_timeout(2500)
            await pg.screenshot(path=f'{out}/{name}.png')
        await b.close()
asyncio.run(main())
for n in ('general', 'planta'):   # recortar al contenido
    im = Image.open(f'{out}/{n}.png').convert('RGB'); bg = Image.new('RGB', im.size, im.getpixel((5, 5)))
    bb = ImageChops.difference(im, bg).convert('L').point(lambda v: 255 if v > 12 else 0).getbbox()
    if bb:
        m = 60; im.crop((max(0, bb[0]-m), max(0, bb[1]-m), min(im.width, bb[2]+m), min(im.height, bb[3]+m))).save(f'{out}/{n}.png')
print('Capturas:', [n for n, *_ in V])
