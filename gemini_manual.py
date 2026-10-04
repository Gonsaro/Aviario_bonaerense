"""Sprites a mano en Gemini web (sin créditos de API).

Uso:
  python gemini_manual.py lista
      Especies sin ningún sprite (ocultas en la app), con sus variantes.
  python gemini_manual.py prompt <especie> [-v D] [--ref]
      Muestra el prompt y lo copia al portapapeles. Si la variante es un recolor,
      dice qué sprite adjuntar. --ref arma la versión para adjuntar una foto o
      lámina de referencia (pose, silueta y colores).
  python gemini_manual.py importar <imagen descargada> <especie> [-v D] [--espejar] [--con-marca]
      Recorta al ave, centra y guarda en Sprites/Genus_species_V.png
      (1024x1024, vuelo 1536x1024). Borra la marca de agua de Gemini (esquina
      inferior derecha) salvo con --con-marca. Si ya existía, la copia va a Sprites/backup/.

<especie> acepta id, nombre común o científico (igual que generar_sprites.py).
"""
import argparse
import base64
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent
SPRITES = ROOT / 'Sprites'
VARIANTES = ['D', 'R', 'M', 'F', 'O', 'J', 'V', 'A']
REF_PREFIX = ('Use the attached image only as a reference for the pose, silhouette, proportions and colors of the bird; '
              'redraw it as a new sprite following this description: ')
MARCA = 0.08  # lado del cuadrado de la esquina inferior derecha que se blanquea


def cargar():
    return json.load(open(ROOT / 'aviario_data.json', encoding='utf-8'))['especies']


def norm(t):
    return unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()


def buscar(especies, sel):
    s = norm(sel.strip().lstrip('#'))
    for e in especies:
        if s.isdigit() and int(s) == e['id']:
            return e
    for e in especies:
        if s in (norm(e['nombre_comun']), norm(e['nombre_cientifico'])):
            return e
    parciales = [e for e in especies if s in norm(e['nombre_comun']) or s in norm(e['nombre_cientifico'])]
    if len(parciales) == 1:
        return parciales[0]
    if parciales:
        sys.exit('Ambiguo: ' + ', '.join(e['nombre_comun'] for e in parciales))
    sys.exit(f"No encontré '{sel}'")


def archivo(e, v):
    g, s = e['nombre_cientifico'].split()[:2]
    return SPRITES / f'{g}_{s.lower()}_{v}.png'


def slug(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')


def copiar(texto):
    b64 = base64.b64encode(texto.encode('utf-8')).decode()
    cmd = f"Set-Clipboard -Value ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{b64}')))"
    try:
        subprocess.run(['powershell', '-NoProfile', '-Command', cmd], check=True)
        return True
    except Exception:
        return False


def cmd_lista(a):
    pend = [e for e in cargar() if not any(archivo(e, v).exists() for v in VARIANTES)]
    print(f'{len(pend)} especies sin sprite (ocultas en la app):')
    for e in sorted(pend, key=lambda e: e['id']):
        print(f"  {e['id']:>4}  {e['nombre_comun']:<30} {', '.join(e.get('prompts_pixelart', {}))}")


def cmd_prompt(a):
    e = buscar(cargar(), a.especie)
    prompts = e.get('prompts_pixelart', {})
    v = a.v or next((x for x in ('D', 'M') if x in prompts), next(iter(prompts), None))
    if v not in prompts:
        sys.exit(f"{e['nombre_comun']} no tiene prompt {v}. Tiene: {', '.join(prompts)}")
    p = prompts[v]
    print(f"\n{e['nombre_comun']} ({e['nombre_cientifico']}) — variante {v} -> {archivo(e, v).name}")
    if p.startswith('recolor this exact sprite'):
        base = (e.get('recolor_base') or {}).get(v)
        if not base:
            base = next((archivo(e, x).name for x in ('D', 'M') if x != v and archivo(e, x).exists()), None)
        print(f"RECOLOR: adjuntá en Gemini Sprites/{base or '<sprite base: falta generarlo primero>'}")
    elif a.ref:
        p = REF_PREFIX + p
        print('REFERENCIA: adjuntá la foto o lámina junto con el prompt.')
    print(f"Lámina UNL: https://www.fcv.unl.edu.ar/aves/categorias/{e['familia'].lower()}/{slug(e['nombre_comun'])}/")
    print(f"Fotos AR:   https://www.inaturalist.org/observations?place_id=7190&photos&taxon_name={e['nombre_cientifico'].replace(' ', '%20')}")
    print('\n' + p + '\n')
    print('(copiado al portapapeles)' if copiar(p) else '(no se pudo copiar al portapapeles)')


def cmd_importar(a):
    import generar_sprites as g
    e = buscar(cargar(), a.especie)
    v = a.v
    img = Image.open(a.imagen)
    img.load()
    if not a.con_marca:
        img = img.convert('RGBA')
        w, h = img.size
        lado = round(min(w, h) * MARCA)
        img.paste((255, 255, 255, 255), (w - lado, h - lado, w, h))
    if a.espejar:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    buf = BytesIO()
    img.save(buf, 'PNG')
    out = g._bytes_to_canvas(buf.getvalue(), v)
    dest = archivo(e, v)
    if dest.exists():
        (SPRITES / 'backup').mkdir(exist_ok=True)
        n = 1
        while (SPRITES / 'backup' / f'{dest.stem}_{n}.png').exists():
            n += 1
        shutil.copy(dest, SPRITES / 'backup' / f'{dest.stem}_{n}.png')
        print(f'Backup del anterior: Sprites/backup/{dest.stem}_{n}.png')
    out.save(dest, 'PNG')
    print(f'Guardado {dest.relative_to(ROOT)} ({out.width}x{out.height}). '
          'Después: python build_html.py y bumpear la caché en sw.js')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('lista').set_defaults(f=cmd_lista)
    sp = sub.add_parser('prompt')
    sp.add_argument('especie')
    sp.add_argument('-v', choices=VARIANTES)
    sp.add_argument('--ref', action='store_true', help='versión para adjuntar foto o lámina de referencia')
    sp.set_defaults(f=cmd_prompt)
    si = sub.add_parser('importar')
    si.add_argument('imagen')
    si.add_argument('especie')
    si.add_argument('-v', choices=VARIANTES, default='D')
    si.add_argument('--espejar', action='store_true', help='espejar si el ave mira a la derecha')
    si.add_argument('--con-marca', action='store_true', help='no borrar la esquina de la marca de agua')
    si.set_defaults(f=cmd_importar)
    a = p.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
