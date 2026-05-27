"""
gen_textures.py — Generate textures procedural HD untuk tembok/lantai/jalan.

Output: 128x128 PNG di assets/ — siap dipakai sebagai pengganti tekstur 64x64
yang flat. Style: Stardew Valley / Animal Crossing cozy — patternful tapi
nilai brightness tinggi, saturasi sedang.

Run:
    python tools/gen_textures.py
"""
import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / 'assets'
random.seed(42)


def _noise(w, h, scale=0.5):
    """Grain noise overlay (Gaussian-ish)."""
    px = []
    for _ in range(w * h):
        n = sum(random.uniform(-1, 1) for _ in range(4)) / 4
        px.append(int(128 + n * 127 * scale))
    img = Image.new('L', (w, h))
    img.putdata(px)
    return img


def _tint(rgb, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in rgb)


def gen_house_wall():
    """Plaster cream dengan bayangan papan kayu vertikal halus."""
    w, h = 128, 128
    base = Image.new('RGBA', (w, h), (245, 230, 200, 255))
    d = ImageDraw.Draw(base)
    # Papan vertikal: garis gelap tipis tiap 16px
    for x in range(0, w, 16):
        d.line([(x, 0), (x, h)], fill=(195, 170, 130, 200), width=1)
        d.line([(x+1, 0), (x+1, h)], fill=(225, 205, 170, 180), width=1)
    # Highlight horizontal tipis (kayu nodes)
    for _ in range(8):
        y = random.randint(0, h-1)
        d.line([(0, y), (w, y)], fill=(255, 245, 220, 80), width=1)
    # Grain noise
    noise_l = _noise(w, h, scale=0.18)
    noise_rgba = Image.merge('RGBA', (noise_l, noise_l, noise_l, Image.new('L', (w,h), 255)))
    base = Image.blend(base, noise_rgba, 0.06)
    base.save(OUT / 'house_wall.png')


def gen_wall_stone():
    """Batu blok abu-abu dengan garis mortar."""
    w, h = 128, 128
    base = Image.new('RGBA', (w, h), (170, 162, 152, 255))
    d = ImageDraw.Draw(base)
    # Pola batu blok 32×16: alternating rows offset
    block_w, block_h = 32, 16
    for row, y in enumerate(range(0, h, block_h)):
        offset = (block_w // 2) if row % 2 == 1 else 0
        for x in range(-block_w, w + block_w, block_w):
            xpos = x + offset
            # Inner block fill (variasi)
            col = (
                random.randint(150, 185),
                random.randint(145, 175),
                random.randint(135, 165),
            )
            d.rectangle([xpos+1, y+1, xpos+block_w-2, y+block_h-2],
                        fill=(*col, 255))
        # Mortar lines (gelap)
        d.line([(0, y), (w, y)], fill=(95, 85, 75, 255), width=1)
    # Vertical mortar
    for row, y in enumerate(range(0, h, block_h)):
        offset = (block_w // 2) if row % 2 == 1 else 0
        for x in range(-block_w, w + block_w, block_w):
            xpos = x + offset
            d.line([(xpos, y), (xpos, y+block_h)], fill=(95, 85, 75, 255), width=1)
    # Noise overlay
    _nl = _noise(w, h, scale=0.25)
    _nrgba = Image.merge('RGBA', (_nl, _nl, _nl, Image.new('L', (w,h), 255)))
    base = Image.blend(base, _nrgba, 0.10)
    base.save(OUT / 'wall_stone.png')


def gen_path_stone():
    """Cobblestone jalan: batu bulat-bulat coklat keabu-abuan."""
    w, h = 128, 128
    base = Image.new('RGBA', (w, h), (105, 95, 82, 255))
    d = ImageDraw.Draw(base)
    # Random cobblestones
    for _ in range(45):
        cx = random.randint(0, w)
        cy = random.randint(0, h)
        r  = random.randint(8, 14)
        col_base = random.randint(130, 180)
        col = (
            col_base + random.randint(-15, 10),
            col_base + random.randint(-10, 10) - 8,
            col_base + random.randint(-10, 10) - 20,
        )
        d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(*col, 255),
                  outline=(70, 60, 50, 255), width=1)
        # Highlight kecil di atas
        d.ellipse([cx-r//2, cy-r, cx+r//3, cy-r//3],
                  fill=(_tint(col, 1.25) + (180,)))
    _nl = _noise(w, h, scale=0.3)
    _nrgba = Image.merge('RGBA', (_nl, _nl, _nl, Image.new('L', (w,h), 255)))
    base = Image.blend(base, _nrgba, 0.08)
    base.save(OUT / 'path_stone.png')


def gen_floor_wood():
    """Lantai kayu planks horizontal — kayu hangat dengan grain."""
    w, h = 128, 128
    base = Image.new('RGBA', (w, h), (165, 115, 70, 255))
    d = ImageDraw.Draw(base)
    plank_h = 16
    for row, y in enumerate(range(0, h, plank_h)):
        # Variasi warna per plank
        hue_shift = random.randint(-15, 10)
        plank_col = (
            165 + hue_shift,
            115 + hue_shift // 2,
            70  + hue_shift // 3,
        )
        d.rectangle([0, y+1, w, y+plank_h-1], fill=(*plank_col, 255))
        # Grain horizontal halus
        for _ in range(3):
            gy = random.randint(y+2, y+plank_h-3)
            d.line([(0, gy), (w, gy)],
                   fill=(_tint(plank_col, 0.85) + (120,)), width=1)
        # Separator gelap
        d.line([(0, y), (w, y)], fill=(70, 45, 25, 255), width=1)
    _nl = _noise(w, h, scale=0.2)
    _nrgba = Image.merge('RGBA', (_nl, _nl, _nl, Image.new('L', (w,h), 255)))
    base = Image.blend(base, _nrgba, 0.06)
    base.save(OUT / 'floor_wood.png')


def gen_wood_plank():
    """Versi sederhana — papan kayu vertical untuk dock, gate."""
    w, h = 128, 128
    base = Image.new('RGBA', (w, h), (140, 95, 55, 255))
    d = ImageDraw.Draw(base)
    plank_w = 18
    for col, x in enumerate(range(0, w, plank_w)):
        hue = random.randint(-15, 5)
        c = (140+hue, 95+hue//2, 55+hue//3)
        d.rectangle([x+1, 0, x+plank_w-1, h], fill=(*c, 255))
        # Nodes (simpul)
        for _ in range(2):
            ny = random.randint(8, h-8)
            d.ellipse([x+4, ny-3, x+plank_w-5, ny+3],
                      fill=(_tint(c, 0.6) + (255,)))
    # Separators
    for x in range(0, w, plank_w):
        d.line([(x, 0), (x, h)], fill=(55, 32, 18, 255), width=1)
    _nl = _noise(w, h, scale=0.2)
    _nrgba = Image.merge('RGBA', (_nl, _nl, _nl, Image.new('L', (w,h), 255)))
    base = Image.blend(base, _nrgba, 0.07)
    base.save(OUT / 'wood_plank.png')


def gen_wall_cave():
    """Batu gua gelap dengan retakan."""
    w, h = 128, 128
    base = Image.new('RGBA', (w, h), (62, 55, 65, 255))
    d = ImageDraw.Draw(base)
    # Random rock chunks
    for _ in range(30):
        cx = random.randint(0, w)
        cy = random.randint(0, h)
        r  = random.randint(10, 22)
        col = (
            random.randint(55, 90),
            random.randint(50, 85),
            random.randint(60, 95),
        )
        d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(*col, 255))
    # Retakan (cracks)
    for _ in range(6):
        x, y = random.randint(0, w), random.randint(0, h)
        for _ in range(random.randint(8, 16)):
            nx = x + random.randint(-4, 4)
            ny = y + random.randint(-4, 4)
            d.line([(x, y), (nx, ny)], fill=(30, 25, 35, 255), width=1)
            x, y = nx, ny
    _nl = _noise(w, h, scale=0.3)
    _nrgba = Image.merge('RGBA', (_nl, _nl, _nl, Image.new('L', (w,h), 255)))
    base = Image.blend(base, _nrgba, 0.10)
    base.save(OUT / 'wall_cave.png')


def gen_cave_floor():
    """Lantai gua: kerikil pasir gelap."""
    w, h = 128, 128
    base = Image.new('RGBA', (w, h), (85, 75, 65, 255))
    d = ImageDraw.Draw(base)
    for _ in range(150):
        x = random.randint(0, w-1)
        y = random.randint(0, h-1)
        r = random.randint(1, 3)
        col = random.randint(60, 115)
        d.ellipse([x-r, y-r, x+r, y+r], fill=(col, col-5, col-12, 255))
    _nl = _noise(w, h, scale=0.3)
    _nrgba = Image.merge('RGBA', (_nl, _nl, _nl, Image.new('L', (w,h), 255)))
    base = Image.blend(base, _nrgba, 0.12)
    base.save(OUT / 'cave_floor.png')


def gen_brick_red():
    """Bata merah warm — buat alternatif house_wall."""
    w, h = 128, 128
    base = Image.new('RGBA', (w, h), (195, 110, 78, 255))
    d = ImageDraw.Draw(base)
    block_w, block_h = 24, 12
    for row, y in enumerate(range(0, h, block_h)):
        offset = (block_w // 2) if row % 2 == 1 else 0
        for x in range(-block_w, w + block_w, block_w):
            xpos = x + offset
            col = (
                195 + random.randint(-20, 15),
                110 + random.randint(-15, 15),
                78  + random.randint(-12, 10),
            )
            d.rectangle([xpos+1, y+1, xpos+block_w-2, y+block_h-2],
                        fill=(*col, 255))
        d.line([(0, y), (w, y)], fill=(150, 130, 110, 255), width=1)
        for x in range(-block_w, w + block_w, block_w):
            xpos = x + offset
            d.line([(xpos, y), (xpos, y+block_h)],
                   fill=(150, 130, 110, 255), width=1)
    _nl = _noise(w, h, scale=0.22)
    _nrgba = Image.merge('RGBA', (_nl, _nl, _nl, Image.new('L', (w,h), 255)))
    base = Image.blend(base, _nrgba, 0.08)
    base.save(OUT / 'brick_red.png')


def gen_dirt_path():
    """Jalan tanah coklat — alternatif road tile."""
    w, h = 128, 128
    base = Image.new('RGBA', (w, h), (155, 125, 85, 255))
    d = ImageDraw.Draw(base)
    # Pebbles + dirt clumps
    for _ in range(80):
        x = random.randint(0, w-1)
        y = random.randint(0, h-1)
        r = random.randint(1, 4)
        col = (
            155 + random.randint(-25, 20),
            125 + random.randint(-20, 15),
            85  + random.randint(-15, 10),
        )
        d.ellipse([x-r, y-r, x+r, y+r], fill=(*col, 255))
    _nl = _noise(w, h, scale=0.25)
    _nrgba = Image.merge('RGBA', (_nl, _nl, _nl, Image.new('L', (w,h), 255)))
    base = Image.blend(base, _nrgba, 0.10)
    base.save(OUT / 'dirt_path.png')


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    gen_house_wall()
    gen_wall_stone()
    gen_path_stone()
    gen_floor_wood()
    gen_wood_plank()
    gen_wall_cave()
    gen_cave_floor()
    gen_brick_red()
    gen_dirt_path()
    print(f"[gen_textures] Generated 9 PNG to {OUT}")
    for f in sorted(OUT.glob('*.png')):
        if f.stat().st_mtime > __import__('time').time() - 60:
            print(f"  {f.name}: {f.stat().st_size}B  ({Image.open(f).size})")
