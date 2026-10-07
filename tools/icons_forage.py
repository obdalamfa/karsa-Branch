"""icons_forage.py — Ikon item keluarga FORAGE 64px prosedural (ROADMAP M3).

Meniru pola tools/make_item_icons.py: supersample 4x lalu LANCZOS ke 64px,
outline gelap (~x0.55), highlight lembut kiri-atas, daun penanda. Palet MUTED
ala Disco Elysium x Project Zomboid (earthy, rendah saturasi). Background
TRANSPARAN. Output ke assets/textures/<id>.png.

Ikon:
  mandrake          akar mandrake bercabang seperti kaki + daun di atas
  running_mushroom  jamur tudung merah berbintik + 2 kaki kecil
  firefly           kunang-kunang badan gelap + ekor bercahaya + sayap
  wild_herb         seikat sprig daun hijau muted bertangkai
  wild_berry        gerombolan beri merah-ungu + daun kecil

Pakai: python tools/icons_forage.py
"""
import math
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
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (c[3],) if len(c) == 4 \
        else tuple(max(0, min(255, int(v * f))) for v in c)


def _highlight(img, cx, cy, r, alpha=70):
    hl = Image.new('RGBA', img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse([cx - r, cy - r, cx + int(r * 0.6), cy + int(r * 0.5)], fill=(255, 255, 255, alpha))
    hl = hl.filter(ImageFilter.GaussianBlur(4 * SS))
    img.alpha_composite(hl)


def _glow(img, cx, cy, r, col, alpha=150):
    """Cahaya lembut radial (untuk firefly)."""
    gl = Image.new('RGBA', img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(gl)
    gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (alpha,))
    gl = gl.filter(ImageFilter.GaussianBlur(6 * SS))
    img.alpha_composite(gl)


def _leaf(d, cx, cy, ln, col=(95, 150, 80), ang=0.0):
    """Daun lancip menyilang, dirotasi (ang radian, 0 = mengarah atas)."""
    w = ln * 0.42
    # titik dalam koordinat lokal (atas = -y)
    pts = [(0, -ln), (-w, -ln * 0.35), (0, ln * 0.12), (w, -ln * 0.35)]
    ca, sa = math.cos(ang), math.sin(ang)
    rot = [(cx + px * ca - py * sa, cy + px * sa + py * ca) for px, py in pts]
    d.polygon(rot, fill=col, outline=_shade(col, 0.55))
    # tulang daun
    tip = (cx + (0) * ca - (-ln) * sa, cy + (0) * sa + (-ln) * ca)
    base = (cx + (0) * ca - (ln * 0.12) * sa, cy + (0) * sa + (ln * 0.12) * ca)
    d.line([base, tip], fill=_shade(col, 0.62), width=max(1, int(SS * 0.8)))


# ── mandrake: akar umbi bercabang seperti kaki + daun ──
def mandrake_icon():
    img = _new()
    d = ImageDraw.Draw(img)
    body = (150, 110, 75)
    dark = _shade(body, 0.55)
    cx = S * 0.5

    # daun-daun di atas umbi (jambul)
    for ang in (-0.55, -0.18, 0.18, 0.55):
        _leaf(d, cx + ang * 16 * SS, S * 0.30, 17 * SS, col=(96, 150, 78), ang=ang)

    # tubuh umbi: badan bulat lonjong
    d.ellipse([cx - 17 * SS, S * 0.34, cx + 17 * SS, S * 0.66],
              fill=body, outline=dark, width=2 * SS)

    # dua "kaki" bercabang ke bawah
    for sgn in (-1, 1):
        bx = cx + sgn * 8 * SS
        leg = [(bx - 6 * SS, S * 0.58), (bx + 6 * SS, S * 0.58),
               (cx + sgn * 16 * SS, S * 0.86), (cx + sgn * 9 * SS, S * 0.88)]
        d.polygon(leg, fill=body, outline=dark)
        # ujung kaki membulat
        ex, ey = cx + sgn * 12.5 * SS, S * 0.86
        d.ellipse([ex - 5 * SS, ey - 5 * SS, ex + 5 * SS, ey + 5 * SS],
                  fill=body, outline=dark, width=int(SS * 1.5))

    # dua "lengan" pendek ke samping
    for sgn in (-1, 1):
        ax, ay = cx + sgn * 16 * SS, S * 0.45
        d.ellipse([ax - 6 * SS, ay - 4 * SS, ax + 6 * SS, ay + 6 * SS],
                  fill=body, outline=dark, width=int(SS * 1.2))

    # garis wajah samar (kesan mistis)
    d.ellipse([cx - 5 * SS, S * 0.43, cx - 1 * SS, S * 0.47], fill=dark)
    d.ellipse([cx + 1 * SS, S * 0.43, cx + 5 * SS, S * 0.47], fill=dark)
    d.arc([cx - 5 * SS, S * 0.48, cx + 5 * SS, S * 0.56], 20, 160, fill=dark, width=int(SS))

    _highlight(img, cx - 8 * SS, S * 0.42, 11 * SS, alpha=55)
    return img


# ── running_mushroom: jamur tudung merah berbintik + kaki kecil ──
def running_mushroom_icon():
    img = _new()
    d = ImageDraw.Draw(img)
    cap = (190, 90, 80)
    stem = (224, 210, 188)
    capdk = _shade(cap, 0.6)
    cx = S * 0.5

    # batang krem
    d.rounded_rectangle([cx - 7 * SS, S * 0.48, cx + 7 * SS, S * 0.74],
                        radius=4 * SS, fill=stem, outline=_shade(stem, 0.72), width=2 * SS)

    # dua kaki kecil lucu di bawah batang
    for sgn in (-1, 1):
        fx = cx + sgn * 4 * SS
        d.line([(fx, S * 0.74), (cx + sgn * 12 * SS, S * 0.86)],
               fill=_shade(stem, 0.78), width=3 * SS)
        # telapak kaki
        ex, ey = cx + sgn * 13 * SS, S * 0.87
        d.ellipse([ex - 4.5 * SS, ey - 3 * SS, ex + 4.5 * SS, ey + 3 * SS],
                  fill=stem, outline=_shade(stem, 0.7), width=int(SS))

    # tudung jamur (kubah)
    d.pieslice([cx - 22 * SS, S * 0.18, cx + 22 * SS, S * 0.62], 180, 360,
               fill=cap, outline=capdk, width=2 * SS)
    # alas tudung
    d.ellipse([cx - 22 * SS, S * 0.36, cx + 22 * SS, S * 0.50], fill=cap, outline=capdk, width=2 * SS)

    # bintik-bintik di tudung
    for (sx, sy, r) in [(-11, 0.30, 4), (3, 0.27, 5), (12, 0.33, 3.5), (-4, 0.36, 3)]:
        bx = cx + sx * SS
        by = S * sy
        d.ellipse([bx - r * SS, by - r * SS, bx + r * SS, by + r * SS],
                  fill=(232, 222, 206))

    _highlight(img, cx - 9 * SS, S * 0.28, 12 * SS, alpha=60)
    return img


# ── firefly: kunang-kunang badan gelap + ekor bercahaya + sayap ──
def firefly_icon():
    img = _new()
    cx = S * 0.5
    cy = S * 0.52

    # glow di belakang (ekor), digambar dulu agar di bawah
    _glow(img, cx, cy + 8 * SS, 16 * SS, (190, 210, 110), alpha=120)
    _glow(img, cx, cy + 8 * SS, 9 * SS, (220, 235, 150), alpha=170)

    d = ImageDraw.Draw(img)
    body = (58, 54, 48)
    bdk = _shade(body, 0.6)

    # sayap transparan sepasang
    wing = Image.new('RGBA', img.size, (0, 0, 0, 0))
    wd = ImageDraw.Draw(wing)
    for sgn in (-1, 1):
        wd.ellipse([cx + sgn * 2 * SS - (sgn < 0) * 18 * SS,
                    cy - 16 * SS,
                    cx + sgn * 2 * SS + (sgn > 0) * 18 * SS,
                    cy + 4 * SS],
                   fill=(210, 225, 230, 90), outline=(160, 175, 185, 120))
    wing = wing.filter(ImageFilter.GaussianBlur(SS))
    img.alpha_composite(wing)
    d = ImageDraw.Draw(img)

    # kepala
    d.ellipse([cx - 7 * SS, cy - 18 * SS, cx + 7 * SS, cy - 4 * SS],
              fill=body, outline=bdk, width=2 * SS)
    # toraks/badan gelap
    d.ellipse([cx - 8 * SS, cy - 8 * SS, cx + 8 * SS, cy + 8 * SS],
              fill=body, outline=bdk, width=2 * SS)
    # ekor bercahaya (segmen menyala)
    d.ellipse([cx - 9 * SS, cy + 4 * SS, cx + 9 * SS, cy + 20 * SS],
              fill=(214, 232, 140), outline=_shade((150, 170, 90), 1.0), width=2 * SS)
    d.ellipse([cx - 5 * SS, cy + 8 * SS, cx + 5 * SS, cy + 17 * SS],
              fill=(240, 248, 200))

    # antena
    for sgn in (-1, 1):
        d.line([(cx + sgn * 2 * SS, cy - 16 * SS), (cx + sgn * 9 * SS, cy - 24 * SS)],
               fill=bdk, width=int(SS * 1.2))
    return img


# ── wild_herb: seikat sprig daun hijau muted bertangkai ──
def wild_herb_icon():
    img = _new()
    d = ImageDraw.Draw(img)
    stem = (108, 122, 72)
    cx = S * 0.5
    base_y = S * 0.82

    # 3 tangkai terpisah & lebih melebar supaya "seikat" terbaca, bukan blob
    sprigs = [(-0.62, 0.24), (0.02, 0.16), (0.60, 0.26)]
    for tilt, topf in sprigs:
        tx = cx + tilt * 24 * SS
        ty = S * topf
        # tangkai jelas
        d.line([(cx, base_y), (tx, ty)], fill=_shade(stem, 0.85), width=int(SS * 2.4))
        ang_dir = math.atan2(ty - base_y, tx - cx)   # arah tangkai
        # sepasang daun berseling di 3 titik, ditata renggang
        n = 3
        for i in range(1, n + 1):
            f = i / (n + 0.4)
            px = cx + (tx - cx) * f
            py = base_y + (ty - base_y) * f
            ll = (9 + (1 - f) * 2) * SS
            col = (92 + int(f * 22), 152, 82)
            # daun keluar tegak-lurus tangkai, dua sisi
            _leaf(d, px, py, ll, col=col, ang=ang_dir + 0.95)
            _leaf(d, px, py, ll, col=_shade(col, 0.88), ang=ang_dir - 0.95)
        # daun ujung mengarah sesuai tangkai
        _leaf(d, tx, ty, 11 * SS, col=(112, 166, 90), ang=ang_dir + math.pi / 2)

    # ikatan tali di pangkal (lebih tebal & terbaca)
    d.rounded_rectangle([cx - 7 * SS, base_y - 2 * SS, cx + 7 * SS, base_y + 7 * SS],
                        radius=2 * SS, fill=(150, 120, 80), outline=(110, 86, 56), width=int(SS))
    d.line([(cx - 7 * SS, base_y + 2 * SS), (cx + 7 * SS, base_y + 2 * SS)],
           fill=(120, 94, 62), width=int(SS * 1.4))

    _highlight(img, cx - 6 * SS, S * 0.36, 12 * SS, alpha=45)
    return img


# ── wild_berry: gerombolan beri merah-ungu + daun ──
def wild_berry_icon():
    img = _new()
    d = ImageDraw.Draw(img)
    berry = (140, 60, 90)
    bdk = _shade(berry, 0.58)
    cx = S * 0.5

    # daun kecil di belakang gerombolan (digambar dulu)
    _leaf(d, cx - 4 * SS, S * 0.28, 16 * SS, col=(92, 146, 76), ang=-0.5)
    _leaf(d, cx + 8 * SS, S * 0.26, 14 * SS, col=(102, 156, 82), ang=0.4)

    # gerombolan beri (cluster), beberapa bulatan
    berries = [(-9, 0.50, 9), (8, 0.48, 9), (-2, 0.40, 8),
               (-13, 0.62, 8), (1, 0.62, 9.5), (13, 0.62, 8),
               (-6, 0.74, 8), (7, 0.74, 8)]
    for (ox, oyf, r) in berries:
        bx = cx + ox * SS
        by = S * oyf
        # tonal sedikit beragam supaya bervolume
        c = _shade(berry, 1.0 + (ox % 3 - 1) * 0.06)
        d.ellipse([bx - r * SS, by - r * SS, bx + r * SS, by + r * SS],
                  fill=c, outline=bdk, width=int(SS * 1.3))
        # kilau kecil tiap beri
        d.ellipse([bx - r * SS * 0.55, by - r * SS * 0.6,
                   bx - r * SS * 0.05, by - r * SS * 0.1],
                  fill=(235, 200, 215, 120))

    _highlight(img, cx - 8 * SS, S * 0.46, 12 * SS, alpha=40)
    return img


def main():
    made = []
    made.append(_save(mandrake_icon(), 'mandrake'))
    made.append(_save(running_mushroom_icon(), 'running_mushroom'))
    made.append(_save(firefly_icon(), 'firefly'))
    made.append(_save(wild_herb_icon(), 'wild_herb'))
    made.append(_save(wild_berry_icon(), 'wild_berry'))
    print(f"[icons_forage] {len(made)} ikon -> {OUT}")
    print("  " + ", ".join(made))


if __name__ == '__main__':
    main()
