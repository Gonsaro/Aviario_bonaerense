"""Calcula el índice de frecuencia en el AMBA (campo amba_indice de aviario_data.json).

Cuenta los registros GBIF de cada especie dentro de un rectángulo que cubre CABA,
el conurbano y el Gran La Plata, y los expresa como % de los registros del Benteveo
en la misma zona (así se compensa el esfuerzo de observación). La app usa el índice
para el "modo ciudad": oculta las especies por debajo de AMBA_MIN (en index.html).

Uso:
  python calcular_amba.py            # solo especies sin amba_indice
  python calcular_amba.py --todas    # recalcula todas
  python calcular_amba.py -s "Genus species"
"""
import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BBOX = 'decimalLatitude=-35.05,-34.35&decimalLongitude=-59.0,-57.85'
BENTEVEO = 'taxonKey=2482755'
# Nombres que GBIF no resuelve con scientificName: se consulta por otro nombre o taxonKey
GBIF_ALIAS = {
    'Daptrius chimango': 'verbatimScientificName=Daptrius%20chimango',  # eBird lo publica así y GBIF no lo resuelve
    'Aramides cajaneus': 'scientificName=Aramides%20cajanea',
    'Charadrius collaris': 'verbatimScientificName=Anarhynchus%20collaris',  # eBird usa el género nuevo
}


def count(q):
    u = f'https://api.gbif.org/v1/occurrence/search?country=AR&limit=0&{BBOX}&{q}'
    for i in range(8):
        try:
            req = urllib.request.Request(u, headers={'User-Agent': 'aviario'})
            return json.load(urllib.request.urlopen(req, timeout=60))['count']
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(2 * (i + 1))
    raise RuntimeError('GBIF devolvió 429 de forma persistente')


def query(sci):
    return GBIF_ALIAS.get(sci, 'scientificName=' + urllib.parse.quote(sci))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--todas', action='store_true')
    ap.add_argument('-s', '--especie')
    a = ap.parse_args()

    p = 'aviario_data.json'
    raw = open(p, encoding='utf-8').read()
    d = json.loads(raw)
    if a.especie:
        objetivo = [s for s in d['especies'] if s['nombre_cientifico'] == a.especie]
    elif a.todas:
        objetivo = d['especies']
    else:
        objetivo = [s for s in d['especies'] if s.get('amba_indice') is None]
    if not objetivo:
        print('Nada para calcular.')
        return

    bt = count(BENTEVEO)
    with ThreadPoolExecutor(3) as ex:
        counts = list(ex.map(lambda s: count(query(s['nombre_cientifico'])), objetivo))
    for s, c in zip(objetivo, counts):
        s['amba_indice'] = round(c / bt * 100, 2)
        print(f"{s['amba_indice']:7.2f}%  {c:6d}  {s['nombre_comun']}")

    open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))


if __name__ == '__main__':
    main()
