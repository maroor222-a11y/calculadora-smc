# plano3d · Vistas 3D de planos de estanterías SMC

Convierte el DWG de una tienda en:

- una **página 3D interactiva** (un solo HTML con three.js),
- un **PDF de vistas** en A4 apaisado para el cliente,
- y, si hace falta, el **PDF 2D del plano** con el logo SMC (con o sin medidas, en color o en negro).

Lo usa la habilidad `plano-3d-smc` de Claude.

## Pasos

```bash
P=/ruta/a/calculadora-smc/plano3d
bash $P/setup.sh                                   # dependencias + LibreDWG (dwg2dxf)
/tmp/libredwg-0.13.3/programs/dwg2dxf -y -o plano.dxf plano.dwg

python3 $P/vista_general.py plano.dxf todo.png     # ver distribuciones y elegir región
# crear config.json (ver ejemplos/alba.json): cliente, region [x0, x1, y0, y1], altura_local, alturas

python3 $P/extraer.py plano.dxf config.json escena.json
python3 $P/control2d.py plano.dxf escena.json control.png   # revisar
python3 $P/suelo.py plano.dxf escena.json suelo.jpg
python3 $P/montar_html.py escena.json suelo.jpg tienda_3d.html
python3 $P/capturas.py tienda_3d.html escena.json capturas
python3 $P/pdf_vistas.py escena.json capturas tienda_vistas.pdf

# plano 2D con logo
python3 $P/pdf_plano.py plano.dxf x0 x1 y0 y1 plano.pdf [--sin-medidas] [--negro] [--apaisado]
```

## Cómo reconoce los muebles

| En el DWG | Se dibuja como |
|---|---|
| Texto `40x120`, `40x100`, `30x120`… | Módulo de estantería (fondo × largo en cm) |
| Módulos enfrentados en el mismo eje | Góndola de pasillo (1,60 m) |
| Módulo suelto | Estantería de pared (2,00 m) |
| Módulo de pared encima de un arcón | Estantería con baldas solo por encima del arcón |
| Texto `Cabecero` | Remate de góndola |
| Texto `PAN` | Panadería 1,00 × 0,40, 2,00 m de alto |
| Polilínea cerrada de color y medida del catálogo | Equipo (RVC, mural, SMR, cámara, frutero, caja) |

Las medidas, colores y alturas están en `catalogo.json`. Para añadir un mueble nuevo, se añade una línea al catálogo y su dibujo en `plantilla.html`.

## Ajustes por tienda (config.json)

- `region`: recuadro del DWG donde está la distribución buena (los DWG suelen traer varias).
- `altura_local`: altura del techo (por defecto 2,60).
- `alturas`: alturas concretas por equipo, p. ej. `{"Cámara de frío": 1.96}`.
- `color_canto`: color del canto de las baldas (por defecto verde `#1f8a3b`).
- `vistas`: para cambiar a mano una vista (`gen`, `top`, `eye`), con `pos` y `tgt` en coordenadas 3D.
- `area`: recuadro del local si el automático corta algo.
