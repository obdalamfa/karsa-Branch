"""
gen_terrain_tex.py — Dua tekstur tanah baru: rumput desa dan tanah garapan.

## Kenapa tekstur baru, bukan tint baru

Rumput di layar terbaca sebagai satu bidang hijau neon yang rata, dan itu TIDAK
bisa diperbaiki dari sisi tint. `grass_tso.png` rata-ratanya (79,158,51):
kanal biru cuma 32% dari kanal hijau. Warna entity di Ursina masuk sebagai
`p3d_ColorScale` dan dikalikan — perkalian hanya bisa MENURUNKAN kanal, jadi
tidak ada satu pun tint yang bisa mengangkat biru dan menjadikan hijaunya
hijau rumput alih-alih hijau layar. Simpangan bakunya juga cuma (18,25,13),
jadi dari jarak main tidak ada apa-apa di dalam teksturnya untuk dilihat.

Tekstur di sini dibuat dengan rasio kanal yang benar (biru ~52% dari hijau) dan
simpangan baku tiga kali lipat, sehingga tint tinggal mengurus NILAI dan
kekeringan — bukan menyelamatkan corak.

## Tidak ada aset yang ditimpa

Nama filenya baru (`rumput_desa.png`, `tanah_garap.png`). `grass_tso.png` dan
`sand_ground.png` dibiarkan utuh di disk dan masih dipakai untuk salju/pasir
serta oleh kode mana pun yang menyebut namanya.

Jalankan:
    python tools/gen_terrain_tex.py
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / 'assets' / 'textures'
N = 128


def _gambar_ubin(d, fn, x, y, w=N, h=N):
    """Gambar satu coretan berikut salinan bungkusnya di kedelapan tetangga.

    Tekstur ini diulang tiap ubin peta; coretan yang terpotong di tepi akan
    terlihat sebagai jahitan lurus di seluruh ladang. Menggambar sembilan kali
    jauh lebih murah daripada mendeteksi kasus tepi satu per satu.
    """
    for ox in (-w, 0, w):
        for oy in (-h, 0, h):
            fn(d, x + ox, y + oy)


def _coret(d, x0, y0, x1, y1, warna, tebal):
    d.line([(x0, y0), (x1, y1)], fill=warna, width=tebal)


# Palet helai rumput. Bobotnya diatur lewat pengulangan: hijau tengah paling
# banyak, kering dan pucat sedikit — bercak kering diurus oleh tint per-ubin di
# world.py, bukan oleh teksturnya, supaya letaknya bisa berubah antar ubin.
_HELAI = (
    [(44, 84, 38)] * 3 + [(62, 116, 50)] * 5 + [(84, 146, 64)] * 5 +
    [(110, 172, 80)] * 4 + [(140, 190, 98)] * 2 + [(168, 200, 118)] +
    [(118, 138, 66)] * 2 + [(74, 98, 48)] * 2
)


def gen_rumput_desa(seed=1409):
    rnd = random.Random(seed)
    img = Image.new('RGB', (N, N), (74, 66, 48))     # tanah di bawah rumput
    d = ImageDraw.Draw(img)

    # Bercak tanah gundul — beberapa titik di mana rumputnya tipis. Ini yang
    # membuat rumput terbaca sebagai rumput yang TUMBUH DI TANAH, bukan sebagai
    # karpet: di `_bench/refs/farm_wide.jpg` tanah selalu mengintip.
    for _ in range(9):
        cx, cy = rnd.randrange(N), rnd.randrange(N)
        rr = rnd.uniform(5, 13)
        warna = (rnd.randint(88, 112), rnd.randint(74, 96), rnd.randint(54, 72))

        def bercak(dd, x, y, rr=rr, warna=warna):
            dd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=warna)
        _gambar_ubin(d, bercak, cx, cy)

    # Helai. Arahnya condong ke atas dengan sebaran lebar — helai yang semuanya
    # sejajar terbaca sebagai arsiran, bukan sebagai rumput.
    for _ in range(2200):
        x, y = rnd.uniform(0, N), rnd.uniform(0, N)
        pj = rnd.uniform(2.0, 6.0)
        a = -math.pi / 2 + rnd.gauss(0.0, 0.65)
        warna = _HELAI[rnd.randrange(len(_HELAI))]
        tebal = 1 if rnd.random() < 0.78 else 2
        dx, dy = math.cos(a) * pj, math.sin(a) * pj

        def helai(dd, px, py, dx=dx, dy=dy, warna=warna, tebal=tebal):
            _coret(dd, px, py, px + dx, py + dy, warna, tebal)
        _gambar_ubin(d, helai, x, y)

    # Titik bunga/embun sangat kecil: satu-dua piksel, cukup untuk berkelip saat
    # kamera bergerak dan tidak cukup untuk terbaca sebagai benda.
    for _ in range(70):
        x, y = rnd.randrange(N), rnd.randrange(N)
        warna = rnd.choice(((176, 182, 148), (172, 156, 96), (150, 128, 140)))
        d.point((x, y), fill=warna)

    # SENGAJA tidak di-blur. Satu lewat SMOOTH menurunkan simpangan bakunya
    # dari 30 ke 20, dan simpangan baku itu SATU-SATUNYA hal yang membuat
    # rumput punya sesuatu untuk dilihat dari jarak main.
    img.save(OUT / 'rumput_desa.png')
    return img


def gen_tanah_garap(seed=776):
    rnd = random.Random(seed)
    img = Image.new('RGB', (N, N), (120, 96, 72))
    d = ImageDraw.Draw(img)

    # Bongkah tanah. Tiga pita nilai, dan yang paling menentukan adalah pita
    # GELAP: tanah yang baru dibalik selalu punya sisi lembap yang jauh lebih
    # tua daripada permukaannya. `sand_ground.png` yang lama simpangan bakunya
    # 12 — tidak punya sisi gelap sama sekali, dan itulah kenapa ladang terbaca
    # sebagai satu bidang oranye.
    for _ in range(560):
        x, y = rnd.uniform(0, N), rnd.uniform(0, N)
        rx, ry = rnd.uniform(2.0, 6.0), rnd.uniform(1.6, 4.6)
        p = rnd.random()
        if p < 0.34:
            warna = (rnd.randint(84, 104), rnd.randint(64, 82), rnd.randint(46, 62))
        elif p < 0.72:
            warna = (rnd.randint(116, 140), rnd.randint(92, 114), rnd.randint(68, 88))
        else:
            warna = (rnd.randint(142, 162), rnd.randint(120, 138), rnd.randint(94, 112))

        def bongkah(dd, px, py, rx=rx, ry=ry, warna=warna):
            dd.ellipse([px - rx, py - ry, px + rx, py + ry], fill=warna)
        _gambar_ubin(d, bongkah, x, y)

    # Alur cangkul: garis dangkal yang hampir sejajar. Satu-satunya pola
    # beraturan yang boleh ada di sini — ladang memang dibajak berbaris.
    for i in range(6):
        y = i * (N / 6.0) + rnd.uniform(-3, 3)
        warna = (rnd.randint(92, 108), rnd.randint(72, 86), rnd.randint(52, 66))

        def alur(dd, px, py, warna=warna):
            dd.line([(px - N, py), (px + N * 2, py + rnd.uniform(-2, 2))],
                    fill=warna, width=2)
        _gambar_ubin(d, alur, 0, y)

    # Kerikil kecil dan sisa akar.
    for _ in range(110):
        x, y = rnd.uniform(0, N), rnd.uniform(0, N)
        rr = rnd.uniform(0.6, 1.8)
        warna = rnd.choice(((116, 110, 100), (98, 92, 84), (146, 138, 126),
                            (92, 78, 56)))

        def batu(dd, px, py, rr=rr, warna=warna):
            dd.ellipse([px - rr, py - rr, px + rr, py + rr], fill=warna)
        _gambar_ubin(d, batu, x, y)

    img = img.filter(ImageFilter.SMOOTH)
    img.save(OUT / 'tanah_garap.png')
    return img


def gen_jerami_lantai(seed=311):
    """Lantai kandang: TANAH yang ditaburi jerami, bukan bidang jerami murni.

    `straw.png` rata-ratanya (186,149,53) dengan simpangan baku 12 — emas pekat
    dan rata. Lantai kandang 9x5 ubin yang dilapisinya jadi bidang datar
    terbesar di seluruh frame `farm`. Di `_bench/refs/barn_interior.jpg` lantai
    kandang selalu tanah yang KELIHATAN, dengan jerami berserak di atasnya —
    dan justru celah tanah di antara jerami itu yang memberi teksturnya nilai.
    """
    rnd = random.Random(seed)
    img = Image.new('RGB', (N, N), (108, 88, 64))
    d = ImageDraw.Draw(img)

    for _ in range(300):
        x, y = rnd.uniform(0, N), rnd.uniform(0, N)
        rx, ry = rnd.uniform(2.0, 6.5), rnd.uniform(1.8, 5.0)
        warna = (rnd.randint(86, 126), rnd.randint(70, 104), rnd.randint(50, 78))

        def bongkah(dd, px, py, rx=rx, ry=ry, warna=warna):
            dd.ellipse([px - rx, py - ry, px + rx, py + ry], fill=warna)
        _gambar_ubin(d, bongkah, x, y)

    # Batang jerami: panjang, hampir lurus, arah acak penuh. Berbeda dari helai
    # rumput yang condong ke atas — jerami sudah rebah, itu bedanya.
    for _ in range(900):
        x, y = rnd.uniform(0, N), rnd.uniform(0, N)
        pj = rnd.uniform(5.0, 16.0)
        a = rnd.uniform(0, math.tau)
        p = rnd.random()
        # Rentang nilainya dipersempit dibanding percobaan pertama: batang emas
        # terang di atas tanah gelap memberi simpangan baku 49, dan dari jarak
        # main itu terbaca sebagai DERAU, bukan sebagai jerami.
        if p < 0.30:
            warna = (rnd.randint(140, 162), rnd.randint(118, 138), rnd.randint(72, 92))
        elif p < 0.72:
            warna = (rnd.randint(168, 190), rnd.randint(146, 166), rnd.randint(96, 118))
        else:
            warna = (rnd.randint(196, 214), rnd.randint(178, 196), rnd.randint(132, 154))
        dx, dy = math.cos(a) * pj, math.sin(a) * pj

        def batang(dd, px, py, dx=dx, dy=dy, warna=warna):
            _coret(dd, px, py, px + dx, py + dy, warna, 1)
        _gambar_ubin(d, batang, x, y)

    img = img.filter(ImageFilter.SMOOTH)
    img.save(OUT / 'jerami_lantai.png')
    return img


if __name__ == '__main__':
    from PIL import ImageStat
    for fn in (gen_rumput_desa, gen_tanah_garap, gen_jerami_lantai):
        im = fn()
        st = ImageStat.Stat(im)
        print(f'{fn.__name__:18s} mean={tuple(round(v) for v in st.mean)} '
              f'std={tuple(round(v) for v in st.stddev)}')
