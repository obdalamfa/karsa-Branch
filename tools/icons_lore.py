"""icons_lore.py — Ikon item LORE 64px prosedural (keluarga: lore).

Mengikuti pola tools/make_item_icons.py:
- Supersample 4x lalu LANCZOS ke 64px (tepi mulus).
- Outline gelap (~x0.55), highlight lembut kiri-atas.
- Palet MUTED ala Disco Elysium x Project Zomboid (earthy, low-sat).
- PNG RGBA 64x64, background TRANSPARAN, ke assets/textures/<id>.png.

Item:
- fragmen_prasasti_1/2/3 : tiga pecahan prasasti batu (bentuk beda, bisa disatukan)
- buku_paman_arsa        : buku tua sampul coklat-merah
- peta_mimpi_maya        : gulungan peta krem dgn sentuhan ungu mistis
- surat_paman_arsa_2     : surat terlipat dgn segel lilin merah

Pakai: python tools/icons_lore.py
"""
import math
import random
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
    a = c[3] if len(c) == 4 else 255
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (a,)


def _highlight(img, cx, cy, r, alpha=70):
    """Sapuan highlight lembut kiri-atas (sama pola make_item_icons)."""
    hl = Image.new('RGBA', img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse([cx - r, cy - r, cx + int(r * 0.6), cy + int(r * 0.5)],
               fill=(255, 255, 255, alpha))
    hl = hl.filter(ImageFilter.GaussianBlur(4 * SS))
    img.alpha_composite(hl)


def _engrave(d, pts, col, w=2 * SS):
    """Guratan aksara/ukiran samar: garis gelap tipis."""
    d.line(pts, fill=col, width=w, joint='curve')


# ── Pecahan prasasti batu ──────────────────────────────────────────────
def _stone_shard(poly, glyph_lines, seed):
    """Lempeng batu abu bentuk pecah + guratan aksara samar."""
    img = _new()
    d = ImageDraw.Draw(img)
    base = (150, 148, 142)
    dark = _shade(base, 0.55)
    # Badan batu dgn outline gelap
    d.polygon(poly, fill=base, outline=dark)
    # Tebalkan outline biar terbaca
    d.line(poly + [poly[0]], fill=dark, width=3 * SS, joint='curve')

    # Bevel terang di sisi kiri-atas (kesan batu pahat)
    rnd = random.Random(seed)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        # sisi yang menghadap kiri-atas -> highlight tipis
        if (x1 + x2) * 0.5 < S * 0.55 and (y1 + y2) * 0.5 < S * 0.6:
            d.line([(x1, y1), (x2, y2)], fill=_shade(base, 1.18), width=2 * SS)

    # Bercak gelap (lumut/usia)
    for _ in range(6):
        bx = rnd.uniform(S * 0.25, S * 0.75)
        by = rnd.uniform(S * 0.25, S * 0.75)
        br = rnd.uniform(3 * SS, 6 * SS)
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=_shade(base, 0.86))

    # Guratan aksara kuno samar (garis ukiran gelap)
    glyph_col = _shade(base, 0.45)
    for ln in glyph_lines:
        _engrave(d, ln, glyph_col, w=2 * SS)
    # highlight aksara (ukiran tampak cekung: garis terang tepat di bawahnya)
    for ln in glyph_lines:
        sh = [(x + 1 * SS, y + 1 * SS) for (x, y) in ln]
        _engrave(d, sh, _shade(base, 1.1), w=1 * SS)

    # Mask poligon supaya bercak/garis tidak bocor keluar batu
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    clean = _new()
    clean.paste(img, (0, 0), mask)

    _highlight(clean, S * 0.40, S * 0.38, 13 * SS, alpha=55)
    return clean


def shard1():
    # Pecahan #1: sobekan di sisi kanan (zig-zag)
    poly = [
        (S * 0.20, S * 0.18), (S * 0.62, S * 0.16),
        (S * 0.72, S * 0.30), (S * 0.60, S * 0.42),
        (S * 0.74, S * 0.56), (S * 0.62, S * 0.72),
        (S * 0.70, S * 0.84), (S * 0.24, S * 0.86),
        (S * 0.16, S * 0.50),
    ]
    glyphs = [
        [(S * 0.30, S * 0.30), (S * 0.30, S * 0.46)],
        [(S * 0.30, S * 0.30), (S * 0.42, S * 0.30)],
        [(S * 0.30, S * 0.38), (S * 0.40, S * 0.38)],
        [(S * 0.30, S * 0.58), (S * 0.46, S * 0.58), (S * 0.46, S * 0.70)],
        [(S * 0.30, S * 0.70), (S * 0.40, S * 0.70)],
    ]
    return _stone_shard(poly, glyphs, seed=1)


def shard2():
    # Pecahan #2: bentuk lebih lebar bawah, sobekan kiri
    poly = [
        (S * 0.32, S * 0.16), (S * 0.80, S * 0.20),
        (S * 0.84, S * 0.54), (S * 0.78, S * 0.82),
        (S * 0.34, S * 0.84), (S * 0.26, S * 0.66),
        (S * 0.36, S * 0.52), (S * 0.24, S * 0.40),
        (S * 0.34, S * 0.30),
    ]
    glyphs = [
        [(S * 0.44, S * 0.30), (S * 0.44, S * 0.48)],
        [(S * 0.44, S * 0.30), (S * 0.58, S * 0.34)],
        [(S * 0.62, S * 0.30), (S * 0.62, S * 0.50)],
        [(S * 0.44, S * 0.62), (S * 0.66, S * 0.62)],
        [(S * 0.54, S * 0.62), (S * 0.54, S * 0.74)],
    ]
    return _stone_shard(poly, glyphs, seed=2)


def shard3():
    # Pecahan #3: bentuk segitiga-bawah, puncak retak
    poly = [
        (S * 0.24, S * 0.24), (S * 0.46, S * 0.14),
        (S * 0.66, S * 0.22), (S * 0.82, S * 0.40),
        (S * 0.66, S * 0.52), (S * 0.78, S * 0.70),
        (S * 0.54, S * 0.86), (S * 0.30, S * 0.74),
        (S * 0.18, S * 0.46),
    ]
    glyphs = [
        [(S * 0.38, S * 0.34), (S * 0.52, S * 0.30), (S * 0.52, S * 0.46)],
        [(S * 0.38, S * 0.34), (S * 0.38, S * 0.50)],
        [(S * 0.60, S * 0.34), (S * 0.60, S * 0.48)],
        [(S * 0.36, S * 0.60), (S * 0.58, S * 0.58)],
        [(S * 0.46, S * 0.60), (S * 0.46, S * 0.72)],
    ]
    return _stone_shard(poly, glyphs, seed=3)


# ── Buku tua paman Arsa ─────────────────────────────────────────────────
def buku():
    img = _new()
    d = ImageDraw.Draw(img)
    cover = (140, 80, 60)          # coklat-merah
    cover_d = _shade(cover, 0.55)
    pages = (224, 210, 178)        # krem halaman
    pages_d = _shade(pages, 0.72)

    # Sudut buku sedikit miring (tampak 3/4)
    # Tumpukan halaman (sisi kanan & bawah)
    page_box = [S * 0.30, S * 0.22, S * 0.74, S * 0.80]
    # garis halaman di sisi kanan
    for i in range(5):
        ox = i * 1.4 * SS
        d.line([(page_box[2] + ox, page_box[1] + 4 * SS),
                (page_box[2] + ox, page_box[3] - 2 * SS)],
               fill=_shade(pages, 0.9 - i * 0.05), width=1 * SS)
    d.rectangle([page_box[2], page_box[1] + 3 * SS,
                 page_box[2] + 7 * SS, page_box[3] - 2 * SS],
                fill=pages, outline=pages_d, width=1 * SS)

    # Sampul depan
    d.rounded_rectangle(page_box, radius=4 * SS, fill=cover,
                        outline=cover_d, width=3 * SS)
    # Punggung buku (spine) gelap di kiri
    d.rectangle([page_box[0], page_box[1], page_box[0] + 7 * SS, page_box[3]],
                fill=_shade(cover, 0.8))
    d.line([(page_box[0] + 7 * SS, page_box[1]),
            (page_box[0] + 7 * SS, page_box[3])],
           fill=cover_d, width=2 * SS)

    # Bingkai hiasan di sampul
    inset = [page_box[0] + 12 * SS, page_box[1] + 8 * SS,
             page_box[2] - 6 * SS, page_box[3] - 8 * SS]
    d.rectangle(inset, outline=_shade(cover, 1.25), width=2 * SS)

    # Tali pembatas merah keluar dari bawah
    band = (170, 60, 56)
    d.rectangle([S * 0.52, page_box[3] - 2 * SS, S * 0.58, S * 0.90],
                fill=band, outline=_shade(band, 0.6), width=1 * SS)
    d.polygon([(S * 0.52, S * 0.90), (S * 0.58, S * 0.90),
               (S * 0.55, S * 0.95)], fill=_shade(band, 0.85))

    _highlight(img, S * 0.42, S * 0.34, 14 * SS, alpha=55)
    return img


# ── Peta mimpi Maya ─────────────────────────────────────────────────────
def peta():
    img = _new()
    d = ImageDraw.Draw(img)
    paper = (220, 205, 170)        # krem
    paper_d = _shade(paper, 0.66)
    roll = (198, 180, 142)         # gulungan tepi

    # Lembar peta terbuka lebar (area tengah dominan biar terbaca)
    sheet = [S * 0.18, S * 0.22, S * 0.82, S * 0.78]
    d.rounded_rectangle(sheet, radius=3 * SS, fill=paper,
                        outline=paper_d, width=2 * SS)

    # Sentuhan ungu mistis (aura mimpi) DI BAWAH garis peta
    aura = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ad = ImageDraw.Draw(aura)
    ad.ellipse([S * 0.30, S * 0.28, S * 0.70, S * 0.68],
               fill=(124, 86, 158, 120))
    ad.ellipse([S * 0.40, S * 0.36, S * 0.62, S * 0.60],
               fill=(156, 116, 188, 95))
    aura = aura.filter(ImageFilter.GaussianBlur(7 * SS))
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle(sheet, radius=3 * SS, fill=255)
    img.alpha_composite(Image.composite(
        aura, Image.new('RGBA', img.size, (0, 0, 0, 0)), mask))
    d = ImageDraw.Draw(img)

    # Garis peta (sungai / pesisir) lebih tegas
    line_col = _shade(paper, 0.5)
    d.line([(S * 0.28, S * 0.36), (S * 0.42, S * 0.44),
            (S * 0.38, S * 0.58), (S * 0.56, S * 0.64),
            (S * 0.66, S * 0.56)],
           fill=line_col, width=3 * SS, joint='curve')
    # kontur bukit (lengkung kecil)
    d.arc([S * 0.46, S * 0.30, S * 0.66, S * 0.46], 200, 340,
          fill=line_col, width=2 * SS)
    # garis putus-putus rute
    dash = _shade(paper, 0.46)
    for t in range(0, 6):
        x = S * 0.30 + t * S * 0.07
        y = S * 0.50 + (2 if t % 2 else -2) * SS
        d.line([(x, y), (x + S * 0.035, y)], fill=dash, width=2 * SS)

    # tanda 'X' tujuan ungu tegas
    xc = (96, 60, 132, 255)
    d.line([(S * 0.58, S * 0.44), (S * 0.66, S * 0.54)], fill=xc, width=3 * SS)
    d.line([(S * 0.66, S * 0.44), (S * 0.58, S * 0.54)], fill=xc, width=3 * SS)

    # Gulungan di kiri & kanan (di atas lembar) — lebih ramping
    for sx in (sheet[0], sheet[2]):
        d.rounded_rectangle([sx - 6 * SS, sheet[1] - 4 * SS,
                             sx + 6 * SS, sheet[3] + 4 * SS],
                            radius=6 * SS, fill=roll,
                            outline=_shade(roll, 0.6), width=2 * SS)
        d.ellipse([sx - 6 * SS, sheet[1] - 8 * SS, sx + 6 * SS, sheet[1] + 4 * SS],
                  fill=_shade(roll, 1.12), outline=_shade(roll, 0.6))

    _highlight(img, S * 0.36, S * 0.32, 12 * SS, alpha=45)
    return img


# ── Surat paman Arsa #2 ─────────────────────────────────────────────────
def surat():
    img = _new()
    d = ImageDraw.Draw(img)
    paper = (224, 212, 184)        # krem
    paper_d = _shade(paper, 0.66)
    fold = _shade(paper, 0.84)

    # Kertas terlipat (amplop) sedikit miring
    env = [S * 0.20, S * 0.26, S * 0.80, S * 0.74]
    d.rounded_rectangle(env, radius=3 * SS, fill=paper,
                        outline=paper_d, width=2 * SS)

    # Lipatan tutup amplop (segitiga atas)
    flap = [(env[0], env[1]), (env[2], env[1]),
            ((env[0] + env[2]) / 2, env[1] + (env[3] - env[1]) * 0.5)]
    d.polygon(flap, fill=fold, outline=paper_d)
    d.line([flap[0], flap[2]], fill=paper_d, width=2 * SS)
    d.line([flap[1], flap[2]], fill=paper_d, width=2 * SS)

    # Garis lipatan horizontal samar (kesan surat dilipat)
    d.line([(env[0] + 4 * SS, env[1] + (env[3] - env[1]) * 0.72),
            (env[2] - 4 * SS, env[1] + (env[3] - env[1]) * 0.72)],
           fill=fold, width=1 * SS)

    # Segel lilin merah
    seal_c = (185, 52, 42)
    seal_d = _shade(seal_c, 0.6)
    scx, scy = (env[0] + env[2]) / 2, flap[2][1]
    sr = 9 * SS
    d.ellipse([scx - sr, scy - sr, scx + sr, scy + sr],
              fill=seal_c, outline=seal_d, width=2 * SS)
    # tepi lilin bergerigi
    for k in range(12):
        a = k / 12 * 2 * math.pi
        rr = sr + 2.4 * SS
        d.ellipse([scx + math.cos(a) * sr - 1.5 * SS,
                   scy + math.sin(a) * sr - 1.5 * SS,
                   scx + math.cos(a) * sr + 1.5 * SS,
                   scy + math.sin(a) * sr + 1.5 * SS],
                  fill=_shade(seal_c, 0.92))
    # cap di tengah segel
    d.ellipse([scx - 4 * SS, scy - 4 * SS, scx + 4 * SS, scy + 4 * SS],
              outline=_shade(seal_c, 1.3), width=2 * SS)
    _highlight(img, scx - 3 * SS, scy - 3 * SS, 4 * SS, alpha=90)

    _highlight(img, S * 0.36, S * 0.34, 13 * SS, alpha=50)
    return img


def main():
    made = []
    made.append(_save(shard1(), 'fragmen_prasasti_1'))
    made.append(_save(shard2(), 'fragmen_prasasti_2'))
    made.append(_save(shard3(), 'fragmen_prasasti_3'))
    made.append(_save(buku(), 'buku_paman_arsa'))
    made.append(_save(peta(), 'peta_mimpi_maya'))
    made.append(_save(surat(), 'surat_paman_arsa_2'))
    print(f"[icons_lore] {len(made)} ikon -> {OUT}")
    print("  " + ", ".join(made))


if __name__ == '__main__':
    main()
