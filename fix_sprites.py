"""
Operaciones de imagen para Aviario Bonaerense:
  --mirror FILE [FILE...]   Espeja horizontalmente los archivos dados
  --symbols                 Agrega simbolo de sexo a todos los sprites _M y _F
  --normalize SPECIES       Normaliza escala entre variantes de una especie
"""
import sys
import argparse
from pathlib import Path
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: pip install Pillow")
    sys.exit(1)

SPRITES_DIR = Path(__file__).parent / "Sprites"

MALE_SYMBOL   = "♂"
FEMALE_SYMBOL = "♀"
SYMBOL_COLOR  = (30, 30, 30)     # gris muy oscuro — neutral para ambos sexos

# Fuentes Windows que soportan ♂ y ♀
FONT_CANDIDATES = [
    "C:/Windows/Fonts/seguisym.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
]

WHITE_THRESHOLD = 240


def get_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def mirror(path: Path) -> None:
    img = Image.open(path)
    img = img.transpose(Image.FLIP_LEFT_RIGHT)
    img.save(path)
    print(f"  Espejado: {path.name}")


def add_symbol(path: Path, symbol: str) -> None:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    font_size = max(50, h // 9)
    font = get_font(font_size)
    draw = ImageDraw.Draw(img)

    # Calcular tamanio real del glifo con su offset
    bbox = draw.textbbox((0, 0), symbol, font=font)
    # bbox = (left_offset, top_offset, right_edge, bottom_edge)
    # Para posicionar correctamente usamos los extremos del bbox, no el tamanio
    margin = max(40, h // 20)
    # Colocar de modo que bbox[2] quede a 'margin' del borde derecho
    # y bbox[3] quede a 'margin' del borde inferior
    x = w - margin - bbox[2]
    y = h - margin - bbox[3]
    x = max(0, x)
    y = max(0, y)

    # Texto oscuro con contorno blanco — legible sobre el sprite en cualquier zona
    draw.text((x, y), symbol, font=font,
              fill=SYMBOL_COLOR, stroke_width=2, stroke_fill=(255, 255, 255))

    img.save(path)
    print(f"  Simbolo de sexo agregado: {path.name}")


def erase_symbol_area(path: Path) -> None:
    """Borra la esquina inferior-derecha con blanco para eliminar el simbolo anterior."""
    img = Image.open(path).convert("RGB")
    w, h = img.size
    erase_w = w // 4
    erase_h = h // 5
    draw = ImageDraw.Draw(img)
    draw.rectangle([w - erase_w, h - erase_h, w, h], fill=(255, 255, 255))
    img.save(path)


def normalize_species(genus: str, species: str) -> None:
    """Normaliza altura de pajaro entre variantes de la misma especie (mismo tamaño de canvas)."""
    pattern = f"{genus}_{species}_*.png"
    paths = [p for p in SPRITES_DIR.glob(pattern) if "(" not in p.name]
    if len(paths) < 2:
        print(f"  Solo {len(paths)} sprite(s) para {genus} {species}, nada que normalizar.")
        return

    # Calcular bounding box del pajaro en cada imagen
    def content_bbox(img):
        px = img.convert("RGB").load()
        w, h = img.size
        x0, y0, x1, y1 = w, h, -1, -1
        for y in range(h):
            for x in range(w):
                r, g, b = px[x, y]
                if r < WHITE_THRESHOLD or g < WHITE_THRESHOLD or b < WHITE_THRESHOLD:
                    if x < x0: x0 = x
                    if y < y0: y0 = y
                    if x > x1: x1 = x
                    if y > y1: y1 = y
        return (x0, y0, x1 + 1, y1 + 1) if x1 >= 0 else None

    by_size: dict = {}
    for p in paths:
        img = Image.open(p).convert("RGB")
        bb = content_bbox(img)
        by_size.setdefault(img.size, []).append((p, img, bb))

    for canvas_sz, entries in by_size.items():
        entries = [(p, img, bb) for p, img, bb in entries if bb is not None]
        if len(entries) < 2:
            continue
        max_h = max(bb[3] - bb[1] for _, _, bb in entries)
        for path, img, (bx0, by0, bx1, by1) in entries:
            bb_h = by1 - by0
            bb_w = bx1 - bx0
            if bb_h >= max_h:
                continue
            scale = max_h / bb_h
            new_w = round(bb_w * scale)
            new_h = max_h
            if new_w > canvas_sz[0]:
                scale = canvas_sz[0] / bb_w
                new_w = canvas_sz[0]
                new_h = round(bb_h * scale)
            content = img.crop((bx0, by0, bx1, by1)).resize((new_w, new_h), Image.LANCZOS)
            canvas = Image.new("RGB", canvas_sz, (255, 255, 255))
            cx = (canvas_sz[0] - new_w) // 2
            cy = max(0, (canvas_sz[1] - new_h) // 2)
            canvas.paste(content, (cx, cy))
            canvas.save(path)
            print(f"  Normalizado: {path.name}  (x{scale:.2f})")


def main():
    p = argparse.ArgumentParser(description="Operaciones de imagen para Aviario")
    p.add_argument("--mirror", nargs="+", metavar="FILE", help="Espeja horizontalmente")
    p.add_argument("--symbols", action="store_true", help="Agrega simbolos de sexo a _M y _F sprites")
    p.add_argument("--normalize", nargs=2, metavar=("GENUS", "SPECIES"),
                   help="Normaliza escala entre variantes de una especie")
    args = p.parse_args()

    if not any([args.mirror, args.symbols, args.normalize]):
        p.print_help()
        return

    if args.mirror:
        for fname in args.mirror:
            path = SPRITES_DIR / fname if not Path(fname).is_absolute() else Path(fname)
            if path.exists():
                mirror(path)
            else:
                print(f"  No encontrado: {path}")

    if args.symbols:
        all_mf = (
            [p for p in sorted(SPRITES_DIR.glob("*_M.png")) if "(" not in p.name] +
            [p for p in sorted(SPRITES_DIR.glob("*_F.png")) if "(" not in p.name]
        )
        # Borrar simbolo anterior antes de redibujar
        for path in all_mf:
            erase_symbol_area(path)
        for path in sorted(SPRITES_DIR.glob("*_M.png")):
            if "(" not in path.name:
                add_symbol(path, MALE_SYMBOL)
        for path in sorted(SPRITES_DIR.glob("*_F.png")):
            if "(" not in path.name:
                add_symbol(path, FEMALE_SYMBOL)

    if args.normalize:
        normalize_species(args.normalize[0], args.normalize[1].lower())


if __name__ == "__main__":
    main()
