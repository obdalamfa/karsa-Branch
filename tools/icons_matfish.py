"""icons_matfish.py — Ikon item keluarga 'matfish' 64px prosedural.

Mengikuti pola make_item_icons.py: supersample 4x lalu LANCZOS ke 64px,
outline gelap (~x0.55), highlight lembut kiri-atas, palet MUTED ala
Disco Elysium x Project Zomboid (rendah saturasi, earthy). Background
TRANSPARAN. Output ke assets/textures/<id>.png.

Item:
  - mithril          : bongkah bijih mithril (kristal berfaset biru-putih pucat)
  - mutiara          : mutiara krem-putih dgn sheen + potongan cangkang
  - ikan_laut        : ikan laut biasa, abu-biru, tampak samping
  - ikan_legendaris  : ikan emas berkilau, sirip megah, kesan langka

Pakai: python tools/icons_matfish.py
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
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def _highlight(img, cx, cy, r, alpha=70):
    """Highlight lembut kiri-atas (blur)."""
    hl = Image.new('RGBA', img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse([cx - r, cy - r, cx + int(r * 0.6), cy + int(r * 0.5)],
               fill=(255, 255, 255, alpha))
    hl = hl.filter(ImageFilter.GaussianBlur(4 * SS))
    img.alpha_composite(hl)


def _glow(img, cx, cy, r, col, alpha=110):
    """Sinar/aura lembut berwarna (untuk kesan langka)."""
    g = Image.new('RGBA', img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (alpha,))
    g = g.filter(ImageFilter.GaussianBlur(7 * SS))
    img.alpha_composite(g)


def _sparkle(d, cx, cy, r, col=(255, 255, 255, 230)):
    """Kilau bintang 4-arah kecil."""
    d.polygon([(cx, cy - r), (cx + r * 0.22, cy), (cx, cy + r),
               (cx - r * 0.22, cy)], fill=col)
    d.polygon([(cx - r, cy), (cx, cy + r * 0.22), (cx + r, cy),
               (cx, cy - r * 0.22)], fill=col)


# ── mithril: bongkah bijih kristal berfaset biru-putih pucat ──
def mithril_icon():
    img = _new(); d = ImageDraw.Draw(img)
    crystal = (150, 195, 210)
    rock = (78, 86, 92)          # batu gelap di dasar
    # batu dasar gelap
    d.polygon([(S * 0.18, S * 0.74), (S * 0.40, S * 0.62), (S * 0.82, S * 0.70),
               (S * 0.86, S * 0.88), (S * 0.16, S * 0.90)],
              fill=rock, outline=_shade(rock, 0.6))
    d.polygon([(S * 0.40, S * 0.62), (S * 0.82, S * 0.70), (S * 0.60, S * 0.78)],
              fill=_shade(rock, 1.25))
    # kristal utama (prisma berfaset) muncul dari batu
    main = [(S * 0.50, S * 0.10), (S * 0.70, S * 0.40), (S * 0.58, S * 0.72),
            (S * 0.40, S * 0.72), (S * 0.30, S * 0.40)]
    d.polygon(main, fill=crystal, outline=_shade(crystal, 0.5))
    # faset terang (sisi kiri-atas kena cahaya)
    d.polygon([(S * 0.50, S * 0.10), (S * 0.30, S * 0.40), (S * 0.50, S * 0.46)],
              fill=_shade(crystal, 1.20))
    d.polygon([(S * 0.50, S * 0.10), (S * 0.50, S * 0.46), (S * 0.70, S * 0.40)],
              fill=_shade(crystal, 1.06))
    # faset gelap (sisi kanan-bawah)
    d.polygon([(S * 0.50, S * 0.46), (S * 0.70, S * 0.40), (S * 0.58, S * 0.72),
               (S * 0.50, S * 0.72)], fill=_shade(crystal, 0.78))
    d.polygon([(S * 0.50, S * 0.46), (S * 0.30, S * 0.40), (S * 0.40, S * 0.72),
               (S * 0.50, S * 0.72)], fill=_shade(crystal, 0.90))
    # kristal kecil pendamping kanan
    sub = [(S * 0.70, S * 0.34), (S * 0.82, S * 0.52), (S * 0.72, S * 0.66),
           (S * 0.64, S * 0.50)]
    d.polygon(sub, fill=_shade(crystal, 0.94), outline=_shade(crystal, 0.5))
    d.polygon([(S * 0.70, S * 0.34), (S * 0.64, S * 0.50), (S * 0.73, S * 0.50)],
              fill=_shade(crystal, 1.16))
    # highlight terang + sedikit glow dingin
    _glow(img, S * 0.50, S * 0.40, 18 * SS, crystal, alpha=55)
    _highlight(img, S * 0.44, S * 0.34, 13 * SS, alpha=120)
    d2 = ImageDraw.Draw(img)
    _sparkle(d2, S * 0.40, S * 0.26, 6 * SS, col=(245, 252, 255, 220))
    return img


# ── mutiara: bola krem-putih dgn sheen lembut + potongan cangkang ──
def mutiara_icon():
    img = _new(); d = ImageDraw.Draw(img)
    pearl = (232, 228, 220)
    shell = (150, 150, 156)       # cangkang abu
    # potongan cangkang di bawah (kipas)
    d.pieslice([S * 0.10, S * 0.40, S * 0.90, S * 1.02], 180, 360,
               fill=shell, outline=_shade(shell, 0.6), width=2 * SS)
    # rusuk cangkang
    cx, cyb = S * 0.50, S * 0.92
    for ang in (205, 230, 255, 285, 310, 335):
        rad = math.radians(ang)
        d.line([(cx, cyb), (cx + math.cos(rad) * S * 0.40,
                            cyb + math.sin(rad) * S * 0.40)],
               fill=_shade(shell, 0.62), width=2 * SS)
    d.pieslice([S * 0.10, S * 0.40, S * 0.90, S * 1.02], 180, 360,
               fill=None, outline=_shade(shell, 0.55), width=3 * SS)
    # mutiara (bola)
    pcx, pcy, pr = S * 0.50, S * 0.46, S * 0.26
    d.ellipse([pcx - pr, pcy - pr, pcx + pr, pcy + pr],
              fill=pearl, outline=_shade(pearl, 0.7), width=2 * SS)
    # gradasi bawah (sedikit bayangan untuk volume)
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.ellipse([pcx - pr * 0.7, pcy + pr * 0.05, pcx + pr * 0.8, pcy + pr * 0.9],
               fill=_shade(pearl, 0.78) + (160,))
    sh = sh.filter(ImageFilter.GaussianBlur(5 * SS))
    img.alpha_composite(sh)
    # sheen / kilau lembut
    _highlight(img, pcx - pr * 0.25, pcy - pr * 0.35, 13 * SS, alpha=150)
    d2 = ImageDraw.Draw(img)
    d2.ellipse([pcx - pr * 0.30, pcy - pr * 0.50, pcx + pr * 0.02, pcy - pr * 0.18],
               fill=(255, 255, 255, 190))
    _sparkle(d2, pcx - pr * 0.18, pcy - pr * 0.36, 5 * SS)
    return img


# ── ikan_laut: siluet ikan tampak samping, abu-biru ──
def ikan_laut_icon():
    img = _new(); d = ImageDraw.Draw(img)
    body = (120, 150, 170)
    cx, cy = S * 0.46, S * 0.52
    bw, bh = S * 0.30, S * 0.19      # setengah lebar/tinggi badan
    # ekor (kiri) — pangkal menempel ke badan
    d.polygon([(cx - bw * 0.7, cy), (cx - bw - S * 0.18, cy - S * 0.16),
               (cx - bw - S * 0.12, cy), (cx - bw - S * 0.18, cy + S * 0.16)],
              fill=_shade(body, 0.88), outline=_shade(body, 0.55))
    # sirip atas
    d.polygon([(cx - S * 0.04, cy - bh * 0.9), (cx + S * 0.12, cy - bh * 1.7),
               (cx + S * 0.16, cy - bh * 0.7)],
              fill=_shade(body, 0.92), outline=_shade(body, 0.55))
    # sirip bawah
    d.polygon([(cx - S * 0.02, cy + bh * 0.85), (cx + S * 0.06, cy + bh * 1.5),
               (cx + S * 0.14, cy + bh * 0.7)],
              fill=_shade(body, 0.82), outline=_shade(body, 0.55))
    # badan (oval)
    d.ellipse([cx - bw, cy - bh, cx + bw, cy + bh],
              fill=body, outline=_shade(body, 0.5), width=2 * SS)
    # gradasi punggung gelap / perut terang
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.ellipse([cx - bw, cy - bh, cx + bw, cy + bh * 0.1],
               fill=_shade(body, 0.78) + (120,))
    sh = sh.filter(ImageFilter.GaussianBlur(5 * SS))
    img.alpha_composite(sh)
    lo = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lo)
    ld.ellipse([cx - bw, cy + bh * 0.1, cx + bw, cy + bh],
               fill=_shade(body, 1.18) + (110,))
    lo = lo.filter(ImageFilter.GaussianBlur(5 * SS))
    img.alpha_composite(lo)
    d2 = ImageDraw.Draw(img)
    # garis insang
    d2.arc([cx + bw * 0.30, cy - bh * 0.75, cx + bw * 0.95, cy + bh * 0.75],
           300, 60, fill=_shade(body, 0.55), width=2 * SS)
    # mata (di dalam badan)
    ex, ey = cx + bw * 0.55, cy - bh * 0.18
    d2.ellipse([ex - 5 * SS, ey - 5 * SS, ex + 5 * SS, ey + 5 * SS],
               fill=(235, 235, 230), outline=_shade(body, 0.4), width=SS)
    d2.ellipse([ex - 2.5 * SS, ey - 2.5 * SS, ex + 2.5 * SS, ey + 2.5 * SS],
               fill=(40, 45, 50))
    # sisik (beberapa busur kecil)
    for sx in (cx - bw * 0.3, cx + bw * 0.05, cx - bw * 0.55):
        for sy in (cy - bh * 0.2, cy + bh * 0.3):
            d2.arc([sx - 6 * SS, sy - 6 * SS, sx + 6 * SS, sy + 6 * SS],
                   200, 340, fill=_shade(body, 0.7), width=SS)
    _highlight(img, cx - bw * 0.2, cy - bh * 0.4, 11 * SS, alpha=70)
    return img


# ── ikan_legendaris: ikan emas berkilau, sirip megah ──
def ikan_legendaris_icon():
    img = _new(); d = ImageDraw.Draw(img)
    gold = (220, 185, 90)
    accent = (200, 120, 60)         # aksen sirip lebih hangat/gelap
    cx, cy = S * 0.46, S * 0.52
    bw, bh = S * 0.30, S * 0.20
    # aura langka (glow emas) di belakang
    _glow(img, cx, cy, 28 * SS, gold, alpha=52)
    d = ImageDraw.Draw(img)
    # ekor megah (kipas besar bercabang) — pangkal menempel ke badan
    d.polygon([(cx - bw * 0.7, cy), (cx - bw - S * 0.22, cy - S * 0.22),
               (cx - bw - S * 0.12, cy - S * 0.04),
               (cx - bw - S * 0.24, cy + S * 0.04),
               (cx - bw - S * 0.12, cy + S * 0.10),
               (cx - bw - S * 0.20, cy + S * 0.24)],
              fill=_shade(gold, 0.92), outline=_shade(accent, 0.7))
    # sirip atas megah (bergerigi rapi, makin pendek ke belakang)
    d.polygon([(cx - S * 0.08, cy - bh * 0.9), (cx - S * 0.02, cy - bh * 2.05),
               (cx + S * 0.03, cy - bh * 1.15), (cx + S * 0.08, cy - bh * 1.85),
               (cx + S * 0.12, cy - bh * 1.05), (cx + S * 0.16, cy - bh * 1.55),
               (cx + S * 0.18, cy - bh * 0.75)],
              fill=_shade(gold, 0.96), outline=_shade(accent, 0.7))
    # sirip bawah
    d.polygon([(cx - S * 0.04, cy + bh * 0.85), (cx + S * 0.04, cy + bh * 1.8),
               (cx + S * 0.12, cy + bh * 0.95), (cx + S * 0.18, cy + bh * 1.5),
               (cx + S * 0.20, cy + bh * 0.7)],
              fill=_shade(gold, 0.82), outline=_shade(accent, 0.7))
    # sirip dada
    d.polygon([(cx + bw * 0.2, cy + bh * 0.2), (cx + bw * 0.5, cy + bh * 1.2),
               (cx + bw * 0.75, cy + bh * 0.5)],
              fill=_shade(gold, 0.86), outline=_shade(accent, 0.7))
    # badan
    d.ellipse([cx - bw, cy - bh, cx + bw, cy + bh],
              fill=gold, outline=_shade(accent, 0.65), width=2 * SS)
    # gradasi volume
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.ellipse([cx - bw, cy - bh, cx + bw, cy - bh * 0.1],
               fill=_shade(accent, 0.85) + (110,))
    sh = sh.filter(ImageFilter.GaussianBlur(5 * SS))
    img.alpha_composite(sh)
    lo = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lo)
    ld.ellipse([cx - bw, cy + bh * 0.15, cx + bw, cy + bh],
               fill=_shade(gold, 1.20) + (120,))
    lo = lo.filter(ImageFilter.GaussianBlur(5 * SS))
    img.alpha_composite(lo)
    d2 = ImageDraw.Draw(img)
    # sisik berkilau (busur emas terang)
    for sx in (cx - bw * 0.4, cx, cx + bw * 0.35):
        for sy in (cy - bh * 0.3, cy + bh * 0.25):
            d2.arc([sx - 7 * SS, sy - 7 * SS, sx + 7 * SS, sy + 7 * SS],
                   200, 340, fill=_shade(gold, 1.25), width=SS)
    # garis insang
    d2.arc([cx + bw * 0.25, cy - bh * 0.7, cx + bw * 0.95, cy + bh * 0.7],
           300, 60, fill=_shade(accent, 0.7), width=2 * SS)
    # mata berkilau (di dalam badan, tidak menyentuh tepi)
    ex, ey = cx + bw * 0.52, cy - bh * 0.18
    d2.ellipse([ex - 5.5 * SS, ey - 5.5 * SS, ex + 5.5 * SS, ey + 5.5 * SS],
               fill=(245, 240, 225), outline=_shade(accent, 0.4), width=SS)
    d2.ellipse([ex - 3 * SS, ey - 3 * SS, ex + 3 * SS, ey + 3 * SS],
               fill=(60, 45, 30))
    d2.ellipse([ex - 1 * SS, ey - 2.5 * SS, ex + 1.5 * SS, ey], fill=(255, 255, 255))
    _highlight(img, cx - bw * 0.2, cy - bh * 0.35, 12 * SS, alpha=120)
    # kilau langka di badan & sirip
    _sparkle(d2, cx + bw * 0.05, cy - bh * 0.25, 7 * SS)
    _sparkle(d2, cx + bw * 0.55, cy + bh * 0.4, 5 * SS)
    _sparkle(d2, cx - bw * 0.5, cy - bh * 0.1, 4 * SS, col=(255, 250, 220, 200))
    return img


def main():
    made = []
    made.append(_save(mithril_icon(), 'mithril'))
    made.append(_save(mutiara_icon(), 'mutiara'))
    made.append(_save(ikan_laut_icon(), 'ikan_laut'))
    made.append(_save(ikan_legendaris_icon(), 'ikan_legendaris'))
    print(f"[icons_matfish] {len(made)} ikon -> {OUT}")
    print("  " + ", ".join(made))


if __name__ == '__main__':
    main()
