import json
import subprocess
from pathlib import Path

VARIANT_LABEL = {'D':'adulto','R':'reproductivo','M':'macho','F':'hembra','J':'juvenil','V':'vuelo'}

data = json.load(open('aviario_data.json', encoding='utf-8'))
sprites_dir = Path('Sprites')

# SP: relative paths to PNG files — keeps HTML small, browser loads images normally
sp = {}
for p in sorted(sprites_dir.glob('*.png')):
    if '(' in p.name:
        continue
    sp[p.stem] = f'Sprites/{p.name}'
print(f'Sprites cargados: {len(sp)}')

sp_js = 'const SP={' + ',\n'.join(f"'{k}': '{v}'" for k, v in sp.items()) + '}'

def jstr(v):
    if isinstance(v, str):
        escaped = v.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return '[' + ','.join(jstr(x) for x in v) + ']'
    if isinstance(v, dict):
        return '{' + ','.join(f'{k}:{jstr(w)}' for k, w in v.items()) + '}'

birds_js_parts = []
for bird in data['especies']:
    parts = bird['nombre_cientifico'].split()

    sprites = {}
    for code in ['D', 'R', 'M', 'F', 'J', 'V']:
        key = f'{parts[0]}_{parts[1].lower()}_{code}'
        if key in sp:
            sprites[VARIANT_LABEL[code]] = key

    desc = {}
    for k, v in bird.get('descripcion', {}).items():
        label = VARIANT_LABEL.get(k, k)
        desc[label] = v

    b = {
        'id': bird['id'],
        'num': bird['num'],
        'nombre_comun': bird['nombre_comun'],
        'nombre_cientifico': bird['nombre_cientifico'],
        'familia': bird['familia'],
        'orden': bird['orden'],
        'descripcion': desc,
        'habitat': bird['habitat'],
        'residencia': bird['residencia'],
        'tamanio': bird['tamanio_categoria'],
        'largo_cm': bird['largo_cm'],
        'envergadura_cm': bird.get('envergadura_cm'),
        'estado': bird['estado_conservacion'],
        'provincias': bird['provincias'],
        'curiosidades': bird.get('curiosidades', ''),
        'sprites': sprites,
        'audio_ebird_code': bird.get('audio_ebird_code', ''),
    }
    birds_js_parts.append('{' + ','.join(f'{k}:{jstr(v)}' for k, v in b.items()) + '}')

birds_js = 'const birds=[\n' + ',\n'.join(birds_js_parts) + '\n];'

hc = "const HC={humedal:'hab-humedal','ribereño':'hab-ribere',costa:'hab-costa',pastizal:'hab-pastizal','agrícola':'hab-agricola',urbano:'hab-urbano',monte:'hab-monte',bosque:'hab-bosque','aéreo':'hab-aereo',laguna:'hab-laguna'};"
tc = "const TC={chico:'tam-chico',mediano:'tam-mediano',grande:'tam-grande'};"
rc = "const RC={permanente:'res-permanente',estival:'res-estival'};"
wide = "const WIDE=['vuelo','Vuelo'];"

# ---------------------------------------------------------------------------
# Read HTML and locate section boundaries
# ---------------------------------------------------------------------------
RUNTIME_MARKER = 'let sel=null'  # First line of JS runtime (state vars)

with open('index.html', encoding='utf-8') as f:
    lines = f.readlines()

# Find header end dynamically: the <script> tag that opens the data section
header_end = None
for i, line in enumerate(lines):
    if line.strip() == '<script>':
        header_end = i
        break
if header_end is None:
    raise RuntimeError("No se encontro el tag <script> en el HTML.")
print(f'Header: {header_end} lineas de markup estatico')

# Find runtime JS start — it comes right after the data constants
runtime_start = None
for i, line in enumerate(lines):
    if line.strip().startswith(RUNTIME_MARKER):
        runtime_start = i
        break

if runtime_start is not None:
    print(f'Runtime JS encontrado en linea {runtime_start + 1}')
    runtime_js = ''.join(lines[runtime_start:])
else:
    # Runtime JS was lost in a previous bad rebuild — restore from git
    print('Runtime JS no encontrado en el HTML actual, restaurando desde git...')
    result = subprocess.run(
        ['git', 'show', 'HEAD:aviario_bonaerense.html'],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode != 0:
        raise RuntimeError('No se pudo leer el HTML original desde git: ' + result.stderr)
    orig_lines = result.stdout.splitlines(keepends=True)
    orig_start = None
    for i, line in enumerate(orig_lines):
        if line.strip().startswith(RUNTIME_MARKER):
            orig_start = i
            break
    if orig_start is None:
        raise RuntimeError(f"Marcador '{RUNTIME_MARKER}' no encontrado en el HTML de git.")
    print(f'Restaurado desde git (linea original {orig_start + 1})')
    runtime_js = ''.join(orig_lines[orig_start:])

new_html = (
    ''.join(lines[:header_end]) +
    '<script>\n' +
    sp_js + '\n' +
    hc + '\n' + tc + '\n' + rc + '\n' + wide + '\n' +
    birds_js + '\n' +
    runtime_js
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f'HTML regenerado: {len(sp)} sprites, {len(data["especies"])} especies')
