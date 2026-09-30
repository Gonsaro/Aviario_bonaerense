"""Edita un sprite existente con Gemini (image-to-image) sin cambiar su pose.

Uso: python editar_sprite.py <archivo en Sprites/> "<cambios concretos>"
Guarda el original en Sprites/backup/<nombre>_<n>.png antes de pisarlo.
"""
import os
import shutil
import sys
from pathlib import Path

from PIL import Image

import generar_sprites as g


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    path = Path('Sprites') / sys.argv[1]
    cambios = sys.argv[2]
    if not path.exists():
        print(f'No existe {path}')
        sys.exit(1)

    backup_dir = Path('Sprites/backup')
    backup_dir.mkdir(exist_ok=True)
    n = 1
    while (backup_dir / f'{path.stem}_{n}.png').exists():
        n += 1
    shutil.copy(path, backup_dir / f'{path.stem}_{n}.png')

    g.load_dotenv()
    from google import genai
    client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
    variant = path.stem.rsplit('_', 1)[-1]
    prompt = ('edit this exact sprite, keep the same pose, outline, size and composition unchanged, '
              f'only change: {cambios}, keep white background, no shadow, no text')
    img = g.generate_image(client, prompt, variant, g.DEFAULT_MODEL, Image.open(path).convert('RGB'))
    img.save(path, 'PNG')
    print(f'Editado: {path} (backup: {backup_dir / f"{path.stem}_{n}.png"})')


if __name__ == '__main__':
    main()
