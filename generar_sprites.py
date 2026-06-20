#!/usr/bin/env python3
"""
Aviario Bonaerense — Generador de sprites con Gemini API
Uso:
    python generar_sprites.py --list
    python generar_sprites.py -s 001
    python generar_sprites.py -s "Furnarius rufus" -v D
    python generar_sprites.py -s "Tordo" --no-normalize
    python generar_sprites.py -s 005 --normalize-only
"""

import argparse
import json
import os
import sys
import time
from io import BytesIO
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: pip install Pillow")
    sys.exit(1)

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    print("Error: pip install google-genai")
    sys.exit(1)


SPRITES_DIR = Path(__file__).parent / "Sprites"
DATA_JSON = Path(__file__).parent / "aviario_data.json"
DOTENV = Path(__file__).parent / ".env"
# Tamaños lógicos (referencia para HTML)
CANVAS_NORMAL = (128, 128)
CANVAS_VUELO = (192, 128)
# Tamaños de salida real (8× escala, misma proporción)
OUTPUT_NORMAL = (1024, 1024)
OUTPUT_VUELO  = (1536, 1024)
# Margen mínimo como fracción del canvas (el pájaro ocupa como máximo 1-2*MARGIN)
OUTPUT_MARGIN = 0.05
WHITE_THRESHOLD = 240
DEFAULT_MODEL = "gemini-3.1-flash-image"


def load_dotenv() -> None:
    """Load KEY=VALUE pairs from .env into os.environ (no overwrite)."""
    try:
        with open(DOTENV, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k, v)
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_data() -> dict:
    with open(DATA_JSON, encoding="utf-8") as f:
        return json.load(f)


def find_species(data: dict, selector: str) -> dict | None:
    s = selector.strip()
    s_lower = s.lower()
    s_num = s.lstrip("#").zfill(3)

    for sp in data["especies"]:
        if sp["num"].lstrip("#") == s_num:
            return sp
        if sp["nombre_cientifico"].lower() == s_lower:
            return sp
        if str(sp["id"]) == s.lstrip("#"):
            return sp

    for sp in data["especies"]:
        if s_lower in sp["nombre_comun"].lower():
            return sp
        if s_lower in sp["nombre_cientifico"].lower():
            return sp

    return None


def sprite_filename(nombre_cientifico: str, variant: str) -> str:
    parts = nombre_cientifico.split()
    return f"{parts[0]}_{parts[1].lower()}_{variant}.png"


def canvas_size(variant: str) -> tuple[int, int]:
    return CANVAS_VUELO if variant == "V" else CANVAS_NORMAL

def output_size(variant: str) -> tuple[int, int]:
    return OUTPUT_VUELO if variant == "V" else OUTPUT_NORMAL


def aspect_ratio(variant: str, model: str = "") -> str:
    if variant != "V":
        return "1:1"
    # Imagen no soporta 3:2 — usar 16:9 (landscape más cercano)
    if "imagen" in model.lower():
        return "16:9"
    return "3:2"


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

def generate_image(client: genai.Client, prompt: str, variant: str, model: str,
                   base_image: "Image.Image | None" = None) -> Image.Image:
    if "imagen" in model.lower():
        if base_image is not None:
            raise RuntimeError(
                "El modo recolor (--base-image) requiere un modelo gemini, no imagen."
            )
        return _generate_imagen(client, prompt, variant, model)
    else:
        return _generate_gemini(client, prompt, variant, model, base_image)


def _generate_imagen(client: genai.Client, prompt: str, variant: str, model: str) -> Image.Image:
    response = client.models.generate_images(
        model=model,
        prompt=prompt,
        config=genai_types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio=aspect_ratio(variant, model),
        ),
    )
    data = response.generated_images[0].image.image_bytes
    return _bytes_to_canvas(data, variant)


def _image_part(img: "Image.Image"):
    """
    Devuelve un 'content part' para la imagen base, robusto entre versiones de
    google-genai. Intenta Part.from_bytes (estable en versiones recientes) y,
    si la firma difiere o no existe, cae al PIL.Image directo (que las versiones
    nuevas también aceptan en contents).
    """
    buf = BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()

    part_cls = getattr(genai_types, "Part", None)
    if part_cls is not None and hasattr(part_cls, "from_bytes"):
        try:
            return part_cls.from_bytes(data=data, mime_type="image/png")
        except TypeError:
            try:
                return part_cls.from_bytes(data, "image/png")  # firma posicional
            except Exception:
                pass
    return img  # fallback: PIL directo


def _generate_gemini(client: genai.Client, prompt: str, variant: str, model: str,
                     base_image: "Image.Image | None" = None) -> Image.Image:
    # Si hay imagen base -> image-to-image (recolor): se manda imagen + prompt.
    # Si no -> text-to-image como siempre.
    if base_image is not None:
        contents = [_image_part(base_image), prompt]
    else:
        contents = prompt
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=genai_types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )
    for part in response.candidates[0].content.parts:
        if getattr(part, "inline_data", None) is not None:
            data = part.inline_data.data
            # SDK puede devolver bytes o base64 según versión
            if isinstance(data, str):
                import base64
                data = base64.b64decode(data)
            return _bytes_to_canvas(data, variant)
    raise RuntimeError("La API no devolvió imagen")


def _bytes_to_canvas(data: bytes, variant: str) -> Image.Image:
    """
    Decode image bytes and fit into the standard output canvas with white background.
    Output is always OUTPUT_NORMAL (1024x1024) or OUTPUT_VUELO (1536x1024).
    A minimum margin (OUTPUT_MARGIN) is enforced on each side so the bird
    never bleeds to the canvas edge.
    """
    img = Image.open(BytesIO(data))

    # Flatten transparency onto white
    if img.mode in ("RGBA", "LA", "P"):
        if img.mode == "P":
            img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")

    ow, oh = output_size(variant)
    margin_px_w = round(ow * OUTPUT_MARGIN)
    margin_px_h = round(oh * OUTPUT_MARGIN)
    max_w = ow - 2 * margin_px_w
    max_h = oh - 2 * margin_px_h

    scale = min(max_w / img.width, max_h / img.height)
    nw, nh = round(img.width * scale), round(img.height * scale)
    img = img.resize((nw, nh), Image.NEAREST)

    canvas = Image.new("RGB", (ow, oh), (255, 255, 255))
    ox = (ow - nw) // 2
    oy = (oh - nh) // 2
    canvas.paste(img, (ox, oy))
    return canvas


# ---------------------------------------------------------------------------
# Bounding-box normalization
# ---------------------------------------------------------------------------

def content_bbox(img: Image.Image) -> tuple[int, int, int, int] | None:
    """Return (left, top, right, bottom) of non-white pixels, or None."""
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


def normalize_scale(paths: list[Path]) -> None:
    """
    Scale sprites so the bird fills the same height within each size group.
    Groups images by pixel dimensions (skips mixing landscape/portrait).
    The tallest bounding box becomes the reference; shorter sprites are
    enlarged proportionally and re-centered on a fresh white canvas.
    """
    by_size: dict[tuple, list] = {}
    for p in paths:
        img = Image.open(p).convert("RGB")
        by_size.setdefault(img.size, []).append((p, img, content_bbox(img)))

    for canvas_sz, entries in by_size.items():
        entries = [(p, img, bb) for p, img, bb in entries if bb is not None]
        if len(entries) < 2:
            continue

        max_h = max(bb[3] - bb[1] for _, _, bb in entries)

        for path, img, (bx0, by0, bx1, by1) in entries:
            bb_w, bb_h = bx1 - bx0, by1 - by0
            if bb_h >= max_h:
                continue

            scale = max_h / bb_h
            new_w = round(bb_w * scale)
            new_h = max_h

            if new_w > canvas_sz[0]:
                scale = canvas_sz[0] / bb_w
                new_w = canvas_sz[0]
                new_h = round(bb_h * scale)

            content = img.crop((bx0, by0, bx1, by1)).resize((new_w, new_h), Image.NEAREST)
            canvas = Image.new("RGB", canvas_sz, (255, 255, 255))
            cx = (canvas_sz[0] - new_w) // 2
            cy = max(0, (canvas_sz[1] - new_h) // 2)
            canvas.paste(content, (cx, cy))
            canvas.save(path)
            print(f"  Normalizado: {path.name}  (x{scale:.2f})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Genera sprites de aves para Aviario Bonaerense usando Gemini API"
    )
    p.add_argument("--species", "-s",
                   help="Especie: número (001 / #001), id, nombre científico o común")
    p.add_argument("--variant", "-v", choices=["D", "R", "M", "F", "J", "V"],
                   help="Variante a generar (omitir = todas)")
    p.add_argument("--no-normalize", action="store_true",
                   help="No normalizar escala entre variantes")
    p.add_argument("--normalize-only", action="store_true",
                   help="Solo normalizar sprites existentes, sin llamar a la API")
    p.add_argument("--model", default=DEFAULT_MODEL,
                   help=f"Modelo Gemini (default: {DEFAULT_MODEL})")
    p.add_argument("--base-image",
                   help="Ruta a un sprite base para modo recolor (image-to-image). "
                        "El prompt debe describir solo los cambios de color. Solo gemini.")
    p.add_argument("--api-key", help="Gemini API key (o GEMINI_API_KEY env var)")
    p.add_argument("--output-dir", default=str(SPRITES_DIR),
                   help=f"Directorio de salida (default: {SPRITES_DIR})")
    p.add_argument("--dry-run", action="store_true",
                   help="Muestra lo que se generaría sin llamar a la API")
    p.add_argument("--overwrite", action="store_true",
                   help="Sobreescribir sprites existentes (por defecto los saltea)")
    p.add_argument("--retry", type=int, default=3,
                   help="Reintentos por imagen (default: 3)")
    p.add_argument("--list", "-l", action="store_true",
                   help="Lista especies disponibles")
    return p


def main() -> None:
    load_dotenv()
    args = build_parser().parse_args()
    data = load_data()

    if args.list:
        print(f"\nEspecies cargadas ({len(data['especies'])}):")
        for sp in data["especies"]:
            variants = sorted(sp.get("prompts_pixelart", {}).keys())
            v_str = f"  [{', '.join(variants)}]" if variants else "  [sin prompts]"
            print(f"  {sp['num']}  {sp['nombre_comun']:<28}  {sp['nombre_cientifico']}{v_str}")
        return

    if not args.species:
        build_parser().error("Se requiere --species (o --list para ver opciones)")

    sp = find_species(data, args.species)
    if sp is None:
        print(f"Error: especie '{args.species}' no encontrada. Usa --list.")
        sys.exit(1)

    prompts: dict[str, str] = sp.get("prompts_pixelart", {})
    if not prompts:
        print(f"Error: '{sp['nombre_comun']}' no tiene prompts_pixelart.")
        sys.exit(1)

    if args.variant:
        if args.variant not in prompts:
            print(f"Error: variante '{args.variant}' no existe para {sp['nombre_comun']}.")
            print(f"  Disponibles: {', '.join(sorted(prompts))}")
            sys.exit(1)
        variants = [args.variant]
    else:
        variants = sorted(prompts)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    print(f"\n{sp['num']}  {sp['nombre_comun']} ({sp['nombre_cientifico']})")
    print(f"Variantes: {', '.join(variants)}")

    # --normalize-only: skip API, just normalize what's on disk
    if args.normalize_only:
        existing = [output_dir / sprite_filename(sp["nombre_cientifico"], v) for v in variants]
        existing = [p for p in existing if p.exists()]
        if len(existing) < 2:
            print("Se necesitan al menos 2 sprites existentes para normalizar.")
        else:
            print(f"\nNormalizando {len(existing)} sprite(s)...")
            normalize_scale(existing)
        return

    if args.dry_run:
        print("\n[Dry run]")
        for v in variants:
            fname = sprite_filename(sp["nombre_cientifico"], v)
            cw, ch = canvas_size(v)
            print(f"  {fname}  {cw}×{ch}")
            print(f"  {prompts[v][:90]}{'…' if len(prompts[v]) > 90 else ''}")
        return

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: define GEMINI_API_KEY o usa --api-key.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    generated: list[Path] = []

    base_image = None
    if args.base_image:
        base_path = Path(args.base_image)
        if not base_path.exists():
            print(f"Error: no se encontró la imagen base '{base_path}'.")
            sys.exit(1)
        base_image = Image.open(base_path).convert("RGB")
        print(f"Modo recolor: usando base {base_path.name}")

    for v in variants:
        prompt = prompts[v]
        fname = sprite_filename(sp["nombre_cientifico"], v)
        out_path = output_dir / fname
        cw, ch = canvas_size(v)

        print(f"\n-> {fname}  ({cw}x{ch})")

        if out_path.exists() and not args.overwrite:
            print(f"  Ya existe, salteando (usa --overwrite para regenerar)")
            generated.append(out_path)
            continue

        print(f"  {prompt[:100]}{'…' if len(prompt) > 100 else ''}")

        img = None
        for attempt in range(args.retry):
            try:
                img = generate_image(client, prompt, v, args.model, base_image)
                break
            except Exception as exc:
                print(f"  Intento {attempt + 1}/{args.retry} fallido: {exc}")
                if attempt < args.retry - 1:
                    time.sleep(2 ** attempt)

        if img is None:
            print(f"  ERROR: no se pudo generar {fname}")
            continue

        img.save(out_path, "PNG")
        generated.append(out_path)
        print(f"  Guardado: {out_path}")

    if not args.no_normalize and len(generated) >= 2:
        non_flight = [p for p in generated if not p.stem.endswith("_V")]
        if len(non_flight) >= 2:
            print(f"\nNormalizando escala entre {len(non_flight)} variante(s)...")
            normalize_scale(non_flight)

    print(f"\nListo. {len(generated)} sprite(s) generado(s).")


if __name__ == "__main__":
    main()
