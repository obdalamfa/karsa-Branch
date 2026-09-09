"""make_item_icons.py — Ikon item inventory 64px prosedural (ROADMAP M3).

Tanpa Blender: gambar emblem PIL per item (palet muted Disco/Zomboid) ke
assets/textures/<item>.png. Grid inventory (_item_icon_tex) otomatis memuat
`<item>.png` / `crop_<base>.png`, jadi cukup taruh file di sini.

Render 4x lalu di-LANCZOS-kan ke 64px untuk tepi mulus.
Pakai: python tools/make_item_icons.py
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / 'assets' / 'textures'
OUT.mkdir(parents=True, exist_ok=True)
SS = 4                 # supersample
S = 64 * SS

def _new():
    return Image.new('RGBA', (S, S), (0, 0, 0, 0))

def _save(img, name):
    img = img.resize((64, 64), Image.LANCZOS)
    img.save(OUT / f'{name}.png')
    return name

def _shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)

def _outline_ellipse(d, box, col, ow=3 * SS):
    d.ellipse(box, fill=col, outline=_shade(col, 0.55), width=ow)

def _leaf(d, cx, top, col=(95, 165, 80)):
    """Daun kecil di atas (penanda hasil tani)."""
    w = 14 * SS
    d.polygon([(cx, top - 12 * SS), (cx - w, top), (cx, top + 4 * SS)], fill=col)
    d.polygon([(cx, top - 12 * SS), (cx + w, top), (cx, top + 4 * SS)], fill=_shade(col, 0.82))

def _highlight(img, cx, cy, r):
    hl = Image.new('RGBA', img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse([cx - r, cy - r, cx + int(r * 0.6), cy + int(r * 0.5)], fill=(255, 255, 255, 70))
    hl = hl.filter(ImageFilter.GaussianBlur(4 * SS))
    img.alpha_composite(hl)

# ── Item bulat (crop) dengan daun ──
def crop_icon(col, leaf=True):
    img = _new(); d = ImageDraw.Draw(img)
    m = 12 * SS
    _outline_ellipse(d, [m, m + 6 * SS, S - m, S - m], col)
    _highlight(img, S * 0.40, S * 0.40, 14 * SS)
    if leaf:
        _leaf(d, S // 2, m + 6 * SS)
    return img

# ── Mineral/bahan: bongkah segi banyak ──
def chunk_icon(col):
    img = _new(); d = ImageDraw.Draw(img)
    pts = [(S*0.5, S*0.12), (S*0.86, S*0.36), (S*0.74, S*0.84),
           (S*0.30, S*0.86), (S*0.12, S*0.42)]
    d.polygon(pts, fill=col, outline=_shade(col, 0.5))
    # faset terang
    d.polygon([(S*0.5, S*0.12), (S*0.86, S*0.36), (S*0.5, S*0.5)], fill=_shade(col, 1.18))
    d.polygon([(S*0.5, S*0.5), (S*0.30, S*0.86), (S*0.12, S*0.42)], fill=_shade(col, 0.82))
    return img

# ── Kayu: dua gelondong ──
def log_icon(col=(150, 110, 70)):
    img = _new(); d = ImageDraw.Draw(img)
    for ox in (-10 * SS, 10 * SS):
        d.rounded_rectangle([S*0.22 + ox, S*0.30, S*0.58 + ox, S*0.74],
                            radius=8 * SS, fill=col, outline=_shade(col, 0.55), width=2 * SS)
        cx = (S*0.22 + S*0.58) / 2 + ox
        d.ellipse([cx - 7*SS, S*0.30 + 2*SS, cx + 7*SS, S*0.30 + 16*SS],
                  fill=_shade(col, 1.2), outline=_shade(col, 0.6))
    return img

# ── Produk khusus ──
def milk_icon():       # tetes susu
    img = _new(); d = ImageDraw.Draw(img); col = (240, 240, 232)
    d.ellipse([S*0.30, S*0.40, S*0.70, S*0.82], fill=col, outline=_shade(col, 0.7), width=2*SS)
    d.polygon([(S*0.5, S*0.16), (S*0.34, S*0.52), (S*0.66, S*0.52)], fill=col)
    _highlight(img, S*0.44, S*0.55, 9*SS)
    return img

def egg_icon():
    img = _new(); d = ImageDraw.Draw(img); col = (243, 228, 188)
    d.ellipse([S*0.30, S*0.20, S*0.70, S*0.84], fill=col, outline=_shade(col, 0.7), width=2*SS)
    _highlight(img, S*0.44, S*0.42, 11*SS)
    return img

def wool_icon():
    img = _new(); d = ImageDraw.Draw(img); col = (224, 220, 214)
    for (ox, oy, r) in [(-12,-2,16), (12,-2,16), (0,-12,15), (0,8,18)]:
        d.ellipse([S*0.5+ox*SS-r*SS, S*0.5+oy*SS-r*SS, S*0.5+ox*SS+r*SS, S*0.5+oy*SS+r*SS],
                  fill=col, outline=_shade(col, 0.78), width=2*SS)
    _highlight(img, S*0.42, S*0.40, 12*SS)
    return img

def mushroom_icon():   # jamur: tudung + batang
    img = _new(); d = ImageDraw.Draw(img); cap = (188, 96, 84); stem = (228, 216, 196)
    d.rounded_rectangle([S*0.42, S*0.50, S*0.58, S*0.80], radius=4*SS, fill=stem, outline=_shade(stem,0.7), width=2*SS)
    d.pieslice([S*0.22, S*0.26, S*0.78, S*0.70], 180, 360, fill=cap, outline=_shade(cap,0.6), width=2*SS)
    for sx in (0.36, 0.5, 0.64):
        d.ellipse([S*sx-4*SS, S*0.40-4*SS, S*sx+4*SS, S*0.40+4*SS], fill=(235,225,210))
    return img

# Palet item (muted)
CROP_COL = {
    'lobak':    (220, 96, 116),
    'wortel':   (232, 138, 52),
    'stroberi': (208, 58, 62),
    'jagung':   (234, 198, 72),
    'tomat':    (210, 72, 56),
    'labu':     (210, 120, 46),
    'bayam':    (86, 152, 74),
    'jamur':    None,   # khusus
}
MAT_COL = {
    'batu':    (150, 150, 156),
    'tembaga': (190, 116, 70),
    'besi':    (172, 178, 188),
    'emas':    (226, 186, 72),
    'kristal': (128, 200, 214),
    'perak':   (200, 205, 212),
}

def main():
    made = []
    for k, c in CROP_COL.items():
        if k == 'jamur':
            made.append(_save(mushroom_icon(), 'jamur'))
        else:
            made.append(_save(crop_icon(c), k))
    made.append(_save(milk_icon(), 'susu'))
    made.append(_save(egg_icon(), 'telur'))
    made.append(_save(wool_icon(), 'wol'))
    made.append(_save(log_icon(), 'kayu'))
    for k, c in MAT_COL.items():
        made.append(_save(chunk_icon(c), k))
    print(f"[make_item_icons] {len(made)} ikon -> {OUT}")
    print("  " + ", ".join(made))

if __name__ == '__main__':
    main()
