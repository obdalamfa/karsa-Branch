"""
generate_relic_textures.py — Generator tekstur artefak arkeologis untuk makhluk halus.
Gaya @archaeologyart: arca batu candi, terakota retak, perunggu verdigris.

Output → assets/textures/relic_andesite.png, relic_terracotta.png, relic_bronze.png
Jalankan: python tools/generate_relic_textures.py
"""
import math, random
from pathlib import Path
from PIL import Image

SIZE = 256
OUT = Path(__file__).resolve().parent.parent / 'assets' / 'textures'


def _clamp(v):
    return max(0, min(255, int(v)))


def _noise(seed):
    """Smooth-ish value noise lewat beberapa frekuensi sin (deterministik)."""
    rnd = random.Random(seed)
    a = [rnd.uniform(0, math.tau) for _ in range(6)]

    def f(x, y):
        n = (math.sin(x * 0.08 + a[0]) * math.cos(y * 0.07 + a[1]) * 0.5 +
             math.sin(x * 0.21 + a[2]) * math.cos(y * 0.19 + a[3]) * 0.3 +
             math.sin(x * 0.5 + a[4]) * math.cos(y * 0.47 + a[5]) * 0.2)
        return (n + 1.0) * 0.5  # 0..1
    return f


def _draw_cracks(px, w, h, n_cracks, crack_col, seed, branch=True):
    """Gambar retakan sebagai random-walk garis gelap tipis."""
    rnd = random.Random(seed)
    for _ in range(n_cracks):
        x = rnd.uniform(0, w); y = rnd.uniform(0, h)
        ang = rnd.uniform(0, math.tau)
        steps = rnd.randint(30, 90)
        for _ in range(steps):
            ang += rnd.uniform(-0.5, 0.5)
            x += math.cos(ang); y += math.sin(ang)
            ix, iy = int(x) % w, int(y) % h
            px[ix, iy] = crack_col
            # sedikit lebar
            if rnd.random() < 0.5:
                px[(ix+1) % w, iy] = crack_col
        if branch and rnd.random() < 0.6:
            # cabang
            bx, by = x, y; bang = ang + rnd.uniform(0.6, 1.4)
            for _ in range(rnd.randint(10, 40)):
                bang += rnd.uniform(-0.4, 0.4)
                bx += math.cos(bang); by += math.sin(bang)
                px[int(bx) % w, int(by) % h] = crack_col


def _patches(px, w, h, base_noise, patch_col, threshold, blend, seed):
    """Tempel bercak (lumut/oksidasi) di area noise tinggi."""
    nf = _noise(seed)
    for y in range(h):
        for x in range(w):
            if nf(x, y) > threshold:
                r, g, b = px[x, y]
                pr, pg, pb = patch_col
                px[x, y] = (_clamp(r*(1-blend)+pr*blend),
                            _clamp(g*(1-blend)+pg*blend),
                            _clamp(b*(1-blend)+pb*blend))


def make_andesite():
    """Batu candi andesit abu gelap + lumut hijau + retak — untuk arca/Kuntilanak."""
    img = Image.new('RGB', (SIZE, SIZE)); px = img.load()
    nf = _noise(11); nf2 = _noise(23)
    for y in range(SIZE):
        for x in range(SIZE):
            n = nf(x, y); speck = nf2(x*1.7, y*1.7)
            base = 78 + n*42 + speck*18
            px[x, y] = (_clamp(base*0.96), _clamp(base*1.0), _clamp(base*1.05))
    _patches(px, SIZE, SIZE, nf, (62, 92, 58), 0.62, 0.55, 31)   # lumut hijau
    _patches(px, SIZE, SIZE, nf2, (40, 44, 48), 0.70, 0.4, 37)   # noda gelap
    _draw_cracks(px, SIZE, SIZE, 7, (34, 36, 40), 41)
    img.save(OUT / 'relic_andesite.png')


def make_terracotta():
    """Tanah liat oranye-coklat pudar + retak laba-laba — untuk Pocong/Wewe Gombel."""
    img = Image.new('RGB', (SIZE, SIZE)); px = img.load()
    nf = _noise(51); nf2 = _noise(63)
    for y in range(SIZE):
        for x in range(SIZE):
            n = nf(x, y); speck = nf2(x*2.1, y*2.1)
            r = 138 + n*48 + speck*20
            g = 92 + n*30 + speck*12
            b = 62 + n*20 + speck*8
            px[x, y] = (_clamp(r), _clamp(g), _clamp(b))
    _patches(px, SIZE, SIZE, nf2, (88, 58, 40), 0.66, 0.45, 71)  # noda gelap
    _patches(px, SIZE, SIZE, nf, (96, 110, 78), 0.78, 0.3, 73)   # sedikit lumut
    _draw_cracks(px, SIZE, SIZE, 12, (70, 44, 30), 81)            # retak banyak
    img.save(OUT / 'relic_terracotta.png')


def make_bronze():
    """Perunggu teroksidasi verdigris hijau + bronze tembus — untuk Genderuwo/Naga."""
    img = Image.new('RGB', (SIZE, SIZE)); px = img.load()
    nf = _noise(91); nf2 = _noise(103)
    for y in range(SIZE):
        for x in range(SIZE):
            n = nf(x, y); v = nf2(x*1.3, y*1.3)
            if v > 0.5:   # verdigris hijau
                r = 62 + n*30; g = 108 + n*38; b = 92 + n*30
            else:         # bronze coklat-emas tembus
                r = 120 + n*40; g = 88 + n*28; b = 48 + n*18
            px[x, y] = (_clamp(r), _clamp(g), _clamp(b))
    _patches(px, SIZE, SIZE, nf, (48, 92, 80), 0.58, 0.5, 111)   # verdigris pekat
    _patches(px, SIZE, SIZE, nf2, (150, 120, 70), 0.80, 0.4, 113) # bronze terang
    _draw_cracks(px, SIZE, SIZE, 5, (38, 60, 52), 121, branch=False)
    img.save(OUT / 'relic_bronze.png')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    make_andesite(); make_terracotta(); make_bronze()
    print(f"3 tekstur relik tersimpan di {OUT}")


if __name__ == '__main__':
    main()
