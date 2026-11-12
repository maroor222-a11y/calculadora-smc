"""Paso 5: montar la página 3D (un solo HTML con la escena y el suelo dentro).
Uso: python3 montar_html.py escena.json suelo.jpg salida.html"""
import sys, json, base64, os, html
here = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(here, 'plantilla.html'), encoding='utf-8').read()
s = json.load(open(sys.argv[1])); f = base64.b64encode(open(sys.argv[2], 'rb').read()).decode()
t = t.replace('/*TITULO*/', html.escape(s.get('cliente') or 'Tienda'))
t = t.replace('/*SCENE*/null', json.dumps(s, ensure_ascii=False)).replace('"/*FLOOR*/"', '"data:image/jpeg;base64,' + f + '"')
open(sys.argv[3], 'w', encoding='utf-8').write(t)
print('HTML', sys.argv[3], round(os.path.getsize(sys.argv[3])/1024), 'KB')
