"""
Genera los sprites faltantes para las especies sin imagen en sprites/
Usa Imagen 4 Fast (Google Gemini API). Redimensiona a 128x128 con NEAREST.

Uso: python gen_sprites.py
"""
import os, io, json, time, sys

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from google import genai
from PIL import Image

API_KEY = open('.env').read().split('=', 1)[1].strip()
client = genai.Client(api_key=API_KEY)
MODEL = 'imagen-4.0-fast-generate-001'
SPRITES_DIR = 'sprites'
TARGET_SIZE = (128, 128)
RATE_LIMIT_WAIT = 50  # seconds to wait on 429

d = json.load(open('aviario_data.json', encoding='utf-8'))
especies = d['especies']

tasks = []
for e in especies:
    sprites = e.get('sprites', {})
    prompts = e.get('prompts_pixelart', {})
    for key, filename in sprites.items():
        out_path = os.path.join(SPRITES_DIR, filename)
        if os.path.exists(out_path):
            continue
        prompt = prompts.get(key)
        if not prompt:
            print(f'  SKIP {filename}: sin prompt')
            continue
        tasks.append((e['nombre_comun'], filename, out_path, prompt))

if not tasks:
    print('No hay sprites faltantes.')
    sys.exit(0)

print(f'{len(tasks)} sprites a generar:\n')
for nombre, fn, _, _ in tasks:
    print(f'  {fn}  ({nombre})')

print()
for i, (nombre, filename, out_path, prompt) in enumerate(tasks, 1):
    print(f'[{i}/{len(tasks)}] {filename} ...', flush=True)
    attempt = 0
    while attempt < 3:
        try:
            response = client.models.generate_images(
                model=MODEL,
                prompt=prompt,
                config={'number_of_images': 1, 'aspect_ratio': '1:1'}
            )
            img_bytes = response.generated_images[0].image.image_bytes
            img = Image.open(io.BytesIO(img_bytes))
            img_resized = img.resize(TARGET_SIZE, Image.NEAREST)
            img_resized.save(out_path)
            print(f'  OK  (orig {img.size[0]}x{img.size[1]} -> 128x128)', flush=True)
            break
        except Exception as ex:
            msg = str(ex)
            if '429' in msg:
                print(f'  Rate limit, esperando {RATE_LIMIT_WAIT}s...', flush=True)
                time.sleep(RATE_LIMIT_WAIT)
                attempt += 1
            else:
                print(f'  ERROR: {msg[:120]}', flush=True)
                break
    if i < len(tasks):
        time.sleep(1.5)

print('\nListo.')
