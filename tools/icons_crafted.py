"""icons_crafted.py — Ikon item "crafted" 64px prosedural (keluarga crafted).

Meniru pola tools/make_item_icons.py: render supersample 4x lalu LANCZOS ke 64px,
outline gelap ~x0.55, highlight lembut kiri-atas. Palet MUTED Disco/Zomboid
(earthy, rendah saturasi). Output PNG RGBA 64x64 transparan ke assets/textures/.

Ikon: jala, obor, perahu, peti_kayu, pagar_kayu.
Pakai: python tools/icons_crafted.py
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / 'assets' / 'textures'
OUT.mkdir(parents=True, exist_ok=True)
SS = 4                 # supersample
S = 64 * SS

# Palet kayu muted
WOOD       = (150, 110, 70)
WOOD_LIGHT = (175, 132, 88)
WOOD_DARK  = (96, 70, 46)
ROPE       = (198, 172, 122)   # tali manila


def _new():
    return Image.new('RGBA', (S, S), (0, 0, 0, 0))


def _save(img, name):
    img = img.resize((64, 64), Image.LANCZOS)
    img.save(OUT / f'{name}.png')
    return name


def _shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def _highlight(img, cx, cy, r, a=70):
    hl = Image.new('RGBA', img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse([cx - r, cy - r, cx + int(r * 0.6), cy + int(r * 0.5)],
               fill=(255, 255, 255, a))
    hl = hl.filter(ImageFilter.GaussianBlur(4 * SS))
    img.alpha_composite(hl)


def _grain(d, x0, y0, x1, y1, col, n=3):
    """Garis serat kayu halus arah panjang papan (horizontal)."""
    gc = _shade(col, 0.78)
    span = y1 - y0
    for i in range(1, n + 1):
        yy = y0 + span * i / (n + 1)
        d.line([(x0 + 3 * SS, yy), (x1 - 3 * SS, yy)], fill=gc, width=1 * SS)


# ── jala: jaring belah-ketupat dalam lingkaran, tali manila, simpul ──
def jala_icon():
    img = _new(); d = ImageDraw.Draw(img)
    cx, cy = S * 0.5, S * 0.52
    R = S * 0.40
    box = [cx - R, cy - R, cx + R, cy + R]
    # cincin tepi tali (tebal, sedikit lebih gelap di luar)
    d.ellipse(box, outline=_shade(ROPE, 0.62), width=5 * SS)
    d.ellipse([box[0] + 2 * SS, box[1] + 2 * SS, box[2] - 2 * SS, box[3] - 2 * SS],
              outline=ROPE, width=3 * SS)

    # Mask lingkaran dalam untuk jaring (digambar di layer lalu di-clip)
    net = Image.new('RGBA', img.size, (0, 0, 0, 0))
    nd = ImageDraw.Draw(net)
    step = int(S * 0.13)
    lo, hi = int(cx - R), int(cx + R)
    span = int(2 * R)
    nc = _shade(ROPE, 0.92)
    # diagonal "/" -> garis dgn intersep konstan (x - y = k)
    for k in range(-span, span + step, step):
        nd.line([(lo + k, lo), (hi + k, hi)], fill=nc, width=2 * SS)
    # diagonal "\" -> garis dgn intersep konstan (x + y = k)
    for k in range(0, 2 * hi + step, step):
        nd.line([(k - (hi - lo), hi), (k, lo)], fill=nc, width=2 * SS)
    # clip ke lingkaran dalam
    mask = Image.new('L', img.size, 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([box[0] + 4 * SS, box[1] + 4 * SS, box[2] - 4 * SS, box[3] - 4 * SS], fill=255)
    img.paste(net, (0, 0), Image.composite(net.split()[3], Image.new('L', img.size, 0), mask))

    # simpul kecil di beberapa perpotongan
    kc = _shade(ROPE, 1.12)
    for gx in (-1, 0, 1):
        for gy in (-1, 0, 1):
            px = cx + gx * step
            py = cy + gy * step
            if (px - cx) ** 2 + (py - cy) ** 2 < (R - 6 * SS) ** 2:
                d.ellipse([px - 3 * SS, py - 3 * SS, px + 3 * SS, py + 3 * SS],
                          fill=kc, outline=_shade(ROPE, 0.6))
    _highlight(img, cx - R * 0.4, cy - R * 0.4, 14 * SS, a=55)
    return img


# ── obor: batang kayu vertikal + api oranye muted dgn inti kuning ──
def obor_icon():
    img = _new(); d = ImageDraw.Draw(img)
    cx = S * 0.5
    # glow lembut di belakang api
    glow = Image.new('RGBA', img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - 18 * SS, S * 0.10, cx + 18 * SS, S * 0.46], fill=(210, 120, 50, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(8 * SS))
    img.alpha_composite(glow)

    # batang kayu
    d.rounded_rectangle([cx - 6 * SS, S * 0.40, cx + 6 * SS, S * 0.90],
                        radius=4 * SS, fill=WOOD, outline=WOOD_DARK, width=2 * SS)
    _grain(d, cx - 6 * SS, S * 0.40, cx + 6 * SS, S * 0.90, WOOD, n=2)
    # bungkus kepala obor (lebih gelap, tempat kain/ter)
    d.rounded_rectangle([cx - 10 * SS, S * 0.34, cx + 10 * SS, S * 0.48],
                        radius=5 * SS, fill=WOOD_DARK, outline=_shade(WOOD_DARK, 0.7), width=2 * SS)

    # api: lapisan luar oranye muted -> inti kuning
    flame_o = [(cx, S * 0.08), (cx + 14 * SS, S * 0.30), (cx + 8 * SS, S * 0.40),
               (cx, S * 0.36), (cx - 8 * SS, S * 0.40), (cx - 14 * SS, S * 0.30)]
    d.polygon(flame_o, fill=(210, 120, 50), outline=_shade((210, 120, 50), 0.7))
    flame_m = [(cx, S * 0.15), (cx + 9 * SS, S * 0.31), (cx, S * 0.38),
               (cx - 9 * SS, S * 0.31)]
    d.polygon(flame_m, fill=(226, 158, 64))
    flame_i = [(cx, S * 0.22), (cx + 5 * SS, S * 0.32), (cx, S * 0.37),
               (cx - 5 * SS, S * 0.32)]
    d.polygon(flame_i, fill=(238, 206, 110))
    return img


# ── perahu: lambung kayu melengkung tampak samping + 1 dayung ──
def perahu_icon():
    img = _new(); d = ImageDraw.Draw(img)
    # dayung (di belakang lambung, miring)
    d.line([(S * 0.66, S * 0.22), (S * 0.40, S * 0.60)], fill=WOOD_DARK, width=4 * SS)
    d.ellipse([S * 0.62, S * 0.16, S * 0.78, S * 0.30], fill=WOOD, outline=WOOD_DARK, width=2 * SS)

    # lambung: bentuk bulan sabit (sisi atas terbuka)
    hull = [
        (S * 0.12, S * 0.52),
        (S * 0.22, S * 0.78),
        (S * 0.78, S * 0.78),
        (S * 0.90, S * 0.52),
        (S * 0.74, S * 0.56),
        (S * 0.50, S * 0.58),
        (S * 0.26, S * 0.56),
    ]
    d.polygon(hull, fill=WOOD, outline=WOOD_DARK)
    # interior lebih gelap (cekungan dalam perahu)
    inner = [
        (S * 0.24, S * 0.555),
        (S * 0.50, S * 0.575),
        (S * 0.74, S * 0.555),
        (S * 0.66, S * 0.66),
        (S * 0.34, S * 0.66),
    ]
    d.polygon(inner, fill=WOOD_DARK)
    # papan/bangku menyilang
    for fx in (0.40, 0.58):
        d.line([(S * fx, S * 0.575), (S * fx, S * 0.66)], fill=_shade(WOOD_DARK, 0.8), width=2 * SS)
    # garis serat di lambung bawah
    d.line([(S * 0.20, S * 0.70), (S * 0.80, S * 0.70)], fill=_shade(WOOD, 0.8), width=1 * SS)
    # outline tebal lambung bawah
    d.line([(S * 0.12, S * 0.52), (S * 0.22, S * 0.78)], fill=WOOD_DARK, width=3 * SS)
    d.line([(S * 0.90, S * 0.52), (S * 0.78, S * 0.78)], fill=WOOD_DARK, width=3 * SS)
    _highlight(img, S * 0.34, S * 0.64, 12 * SS, a=50)
    return img


# ── peti_kayu: kotak papan kayu + siku logam gelap di sudut ──
def peti_kayu_icon():
    img = _new(); d = ImageDraw.Draw(img)
    plank = (160, 120, 75)
    x0, y0, x1, y1 = S * 0.18, S * 0.26, S * 0.82, S * 0.78
    metal = (66, 62, 58)
    # badan peti
    d.rounded_rectangle([x0, y0, x1, y1], radius=4 * SS,
                        fill=plank, outline=_shade(plank, 0.5), width=2 * SS)
    # papan horizontal (3 papan)
    span = y1 - y0
    for i in range(1, 3):
        yy = y0 + span * i / 3
        d.line([(x0 + 2 * SS, yy), (x1 - 2 * SS, yy)], fill=_shade(plank, 0.6), width=2 * SS)
    for i in range(1, 3):
        yy = y0 + span * i / 3 + 1 * SS
        d.line([(x0 + 2 * SS, yy), (x1 - 2 * SS, yy)], fill=_shade(plank, 1.12), width=1 * SS)
    # bingkai/siku logam vertikal di kiri & kanan
    bw = 6 * SS
    d.rectangle([x0, y0, x0 + bw, y1], fill=metal, outline=_shade(metal, 0.7))
    d.rectangle([x1 - bw, y0, x1, y1], fill=metal, outline=_shade(metal, 0.7))
    # palang logam tengah (gembok)
    d.rectangle([S * 0.46, y0, S * 0.54, y1], fill=_shade(metal, 1.1), outline=_shade(metal, 0.7))
    d.ellipse([S * 0.47, S * 0.46, S * 0.53, S * 0.54], fill=_shade(metal, 1.3))
    # paku/baut di siku
    for sx in (x0 + bw / 2, x1 - bw / 2):
        for sy in (y0 + 5 * SS, y1 - 5 * SS):
            d.ellipse([sx - 2 * SS, sy - 2 * SS, sx + 2 * SS, sy + 2 * SS],
                      fill=_shade(metal, 1.5))
    _highlight(img, S * 0.32, S * 0.36, 13 * SS, a=45)
    return img


# ── pagar_kayu: 2-3 tiang vertikal + 2 palang horizontal, kayu lapuk ──
def pagar_kayu_icon():
    img = _new(); d = ImageDraw.Draw(img)
    wood = (148, 112, 72)
    dark = _shade(wood, 0.55)
    posts_x = [S * 0.26, S * 0.50, S * 0.74]
    pw = 7 * SS
    py0, py1 = S * 0.20, S * 0.86
    # palang horizontal (di belakang tiang) - 2 buah
    for ry in (S * 0.40, S * 0.66):
        d.rounded_rectangle([S * 0.16, ry - 4 * SS, S * 0.84, ry + 4 * SS],
                            radius=3 * SS, fill=_shade(wood, 0.92), outline=dark, width=2 * SS)
        d.line([(S * 0.18, ry), (S * 0.82, ry)], fill=_shade(wood, 0.78), width=1 * SS)
    # tiang vertikal dgn ujung lancip (pagar pancang)
    for px in posts_x:
        d.polygon([
            (px - pw, py0 + 6 * SS),
            (px, py0),
            (px + pw, py0 + 6 * SS),
            (px + pw, py1),
            (px - pw, py1),
        ], fill=wood, outline=dark)
        # serat vertikal
        d.line([(px - 2 * SS, py0 + 8 * SS), (px - 2 * SS, py1 - 3 * SS)],
               fill=_shade(wood, 0.74), width=1 * SS)
        d.line([(px + 2 * SS, py0 + 8 * SS), (px + 2 * SS, py1 - 3 * SS)],
               fill=_shade(wood, 1.1), width=1 * SS)
    _highlight(img, S * 0.30, S * 0.30, 12 * SS, a=45)
    return img


def main():
    made = []
    made.append(_save(jala_icon(), 'jala'))
    made.append(_save(obor_icon(), 'obor'))
    made.append(_save(perahu_icon(), 'perahu'))
    made.append(_save(peti_kayu_icon(), 'peti_kayu'))
    made.append(_save(pagar_kayu_icon(), 'pagar_kayu'))
    print(f"[icons_crafted] {len(made)} ikon -> {OUT}")
    print("  " + ", ".join(made))


if __name__ == '__main__':
    main()
