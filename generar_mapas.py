#!/usr/bin/env python3
"""
generar_mapas.py  — Mapas de distribución por especie (GBIF + Argentina)
Uso:
  python generar_mapas.py -s "Phoenicopterus chilensis"
  python generar_mapas.py --all
  python generar_mapas.py --all --overwrite
"""

import argparse, json, sys, time
from pathlib import Path

import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Rutas ──────────────────────────────────────────────────────────────────
MAPS_DIR    = Path('Maps')
GEO_CACHE   = Path('argentina_provincias.geojson')
GEO_SRC     = Path('limites_provinciales.js')   # fuente oficial IGN
GBIF_SEARCH = 'https://api.gbif.org/v1/occurrence/search'

# ── Límites del mapa ────────────────────────────────────────────────────────
LON_MIN, LON_MAX = -73.5, -53.0
LAT_MIN, LAT_MAX = -55.5, -21.5

# ── Estilo ──────────────────────────────────────────────────────────────────
C_WATER  = '#b8d4e8'
C_LAND   = '#deded4'
C_BORDER = '#888880'
C_DOT    = '#E85D04'
MAP_W, MAP_H, DPI = 3.5, 5.5, 220


def _rdp(points, eps):
    """Ramer-Douglas-Peucker sobre una polilínea abierta."""
    if len(points) < 3:
        return points
    x1, y1 = points[0]
    x2, y2 = points[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = (dx*dx + dy*dy) ** 0.5 or 1e-10
    dists = [abs(dy*(x-x1) - dx*(y-y1)) / norm for x, y in points]
    idx = max(range(len(dists)), key=lambda i: dists[i])
    if dists[idx] > eps:
        left  = _rdp(points[:idx+1], eps)
        right = _rdp(points[idx:],   eps)
        return left[:-1] + right
    return [points[0], points[-1]]


def _rdp_ring(ring, eps):
    """RDP para rings cerradas (primer punto == último punto)."""
    if len(ring) < 4:
        return ring
    # Abre la ring, aplica RDP, cierra de nuevo
    open_ring = ring[:-1]
    simplified = _rdp(open_ring, eps)
    return simplified + [simplified[0]]


def _simplify_geojson(raw, eps=0.01):
    """Simplifica todas las geometrías del FeatureCollection."""
    features = []
    for feat in raw.get('features', []):
        geom = feat['geometry']
        t = geom['type']
        if t == 'Polygon':
            new_geom = {'type': 'Polygon',
                        'coordinates': [_rdp_ring(r, eps) for r in geom['coordinates']]}
        elif t == 'MultiPolygon':
            new_polys = [[_rdp_ring(r, eps) for r in poly]
                         for poly in geom['coordinates']]
            new_geom = {'type': 'MultiPolygon', 'coordinates': new_polys}
        else:
            continue
        features.append({
            'type': 'Feature',
            'properties': {'nam': feat['properties'].get('nam', '')},
            'geometry': new_geom,
        })
    return {'type': 'FeatureCollection', 'features': features}


def load_geojson():
    if GEO_CACHE.exists():
        return json.loads(GEO_CACHE.read_text(encoding='utf-8'))
    print('Procesando límites provinciales (primera vez, puede tardar) ...')
    raw_text = GEO_SRC.read_text(encoding='utf-8', errors='replace').strip()
    raw_text = raw_text[raw_text.index('=') + 1:].strip().rstrip(';')
    raw = json.loads(raw_text)
    simplified = _simplify_geojson(raw, eps=0.01)
    total = sum(
        len(ring)
        for f in simplified['features']
        for poly in (f['geometry']['coordinates']
                     if f['geometry']['type'] == 'MultiPolygon'
                     else [f['geometry']['coordinates']])
        for ring in poly
    )
    print(f'  {len(simplified["features"])} provincias, {total:,} coords tras simplificar')
    GEO_CACHE.write_text(json.dumps(simplified), encoding='utf-8')
    return simplified


def fetch_occurrences(scientific_name, max_occ=500):
    pts, offset = [], 0
    while len(pts) < max_occ:
        r = requests.get(GBIF_SEARCH, params={
            'scientificName': scientific_name,
            'country': 'AR',
            'hasCoordinate': 'true',
            'limit': 300,
            'offset': offset,
        }, timeout=30)
        r.raise_for_status()
        body = r.json()
        for occ in body.get('results', []):
            lat = occ.get('decimalLatitude')
            lon = occ.get('decimalLongitude')
            if lat is not None and lon is not None:
                pts.append((float(lon), float(lat)))
        if body.get('endOfRecords') or not body.get('results'):
            break
        offset += 300
        time.sleep(0.2)
    return pts


def draw_provinces(ax, geojson):
    for feat in geojson.get('features', []):
        geom = feat.get('geometry', {})
        t = geom.get('type', '')
        if t == 'Polygon':
            rings_list = [geom['coordinates']]   # wrap to unify loop
        elif t == 'MultiPolygon':
            rings_list = geom['coordinates']
        else:
            continue
        for poly in rings_list:
            for ring in poly:
                if len(ring) < 3:
                    continue
                xs = [c[0] for c in ring]
                ys = [c[1] for c in ring]
                ax.fill(xs, ys, color=C_LAND, zorder=1)
                ax.plot(xs, ys, color=C_BORDER, linewidth=0.5, zorder=2)


def generate(sp, overwrite=False):
    sci  = sp['nombre_cientifico']
    stem = sci.replace(' ', '_')
    out  = MAPS_DIR / f'{stem}_map.png'

    if out.exists() and not overwrite:
        print(f'  Ya existe: {out.name}  (--overwrite para regenerar)')
        return

    print(f'  Consultando GBIF: {sci} ...')
    pts = fetch_occurrences(sci)
    print(f'  {len(pts)} registros con coordenadas')

    geo = load_geojson()

    fig, ax = plt.subplots(figsize=(MAP_W, MAP_H), dpi=DPI)
    fig.patch.set_facecolor('white')
    ax.set_facecolor(C_WATER)

    draw_provinces(ax, geo)

    if pts:
        lons, lats = zip(*pts)
        ax.scatter(lons, lats, s=5, c=C_DOT, alpha=0.55, linewidths=0, zorder=3)

    ax.set_xlim(LON_MIN, LON_MAX)
    ax.set_ylim(LAT_MIN, LAT_MAX)
    ax.set_aspect('equal')
    ax.axis('off')

    MAPS_DIR.mkdir(exist_ok=True)
    plt.savefig(out, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'  Guardado: {out}')


def main():
    ap = argparse.ArgumentParser(description='Genera mapas de distribución GBIF')
    ap.add_argument('-s', '--species', help='Nombre científico o común (parcial)')
    ap.add_argument('--all', action='store_true', help='Todas las especies')
    ap.add_argument('--overwrite', action='store_true')
    args = ap.parse_args()

    data = json.loads(Path('aviario_data.json').read_text(encoding='utf-8'))

    if args.all:
        targets = data['especies']
    elif args.species:
        q = args.species.lower()
        targets = [e for e in data['especies'] if
                   q in e['nombre_cientifico'].lower() or
                   q in e['nombre_comun'].lower()]
        if not targets:
            sys.exit(f'Especie no encontrada: {args.species}')
    else:
        ap.print_help()
        sys.exit(0)

    for sp in targets:
        print(f'\n#{sp["id"]:02d}  {sp["nombre_comun"]} ({sp["nombre_cientifico"]})')
        generate(sp, overwrite=args.overwrite)


if __name__ == '__main__':
    main()
