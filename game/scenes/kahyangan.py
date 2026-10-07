"""Swarga sebagai kahyangan Jawa: pulau batu melayang di atas lautan awan.

Semua bentuk mengikuti grid swarga.py -- KUIL jadi candi, GOLD_W jadi tembok
bata dan candi bentar, SHRINE jadi kalpataru dan pelita -- jadi pathfinder dan
portal tidak berubah. Ubin di luar pulau adalah CV_W yang tidak terlihat:
pemain tidak bisa melangkah ke udara.
"""
import math
import random

from game.config import TILE_SIZE as TS, GROUND_H, CLOUD, GOLD_W, KUIL, SHRINE

BATU = (124, 116, 106)       # andesit
BATU_TUA = (98, 92, 86)
BATA = (168, 86, 62)         # bata merah Majapahit
EMAS = (214, 168, 84)
LANTAI = (190, 176, 150)

_PUSAT = (15, 15)


def _part(world, model, pos, scale, rgb, **kw):
    # Sengaja tidak didaftarkan ke wall cutaway: aturan itu memangkas apa pun
    # yang lebih dekat ke kamera daripada pemain, dan pemain hampir selalu di
    # taman -- candi akan terus tampil sebagai puntung. Kamera cukup curam
    # untuk melihat dari atasnya.
    from game.scenes.rock_sanctuary import _part as part
    return part(world, model, pos, scale, rgb, **kw)


def _mesh(verts):
    from ursina import Mesh, Vec3
    vs, ns = [], []
    for i in range(0, len(verts), 3):
        a, b, c = (Vec3(*v) for v in verts[i:i + 3])
        n = (b - a).cross(c - a).normalized()
        if n.y < -0.2 and abs(n.y) > 0.9:
            n = -n
        vs.extend((a, b, c))
        ns.extend((n, n, n))
    return Mesh(vertices=vs, normals=ns, mode='triangle')


def _garis_pulau(cx, cz, r, rng, n=96, acak=0.7):
    """Tepi pulau: berlian L1 (sesuai grid) yang sudutnya dibulatkan sedikit."""
    titik = []
    for i in range(n):
        a = i * math.tau / n
        c, s = math.cos(a), math.sin(a)
        l1 = r / (abs(c) + abs(s))
        rr = l1 * 0.82 + r * 0.18 * (0.78 + 0.22 * (abs(c) + abs(s)) / 1.414)
        rr = max(rr, l1) + rng.uniform(0.2, acak)
        titik.append((cx + c * rr, cz + s * rr))
    return titik


def _pulau(world, cx, cz, r, y_atas, dalam, rgb_atas, rng, n=96, acak=0.7):
    """Satu pulau melayang: permukaan rata + kerucut batu bergerigi di bawahnya."""
    tepi = _garis_pulau(cx, cz, r, rng, n, acak)
    atas = []
    for i in range(n):
        x0, z0 = tepi[i]
        x1, z1 = tepi[(i + 1) % n]
        atas.extend([(cx, y_atas, cz), (x1, y_atas, z1), (x0, y_atas, z0)])
    _part(world, _mesh(atas), (0, 0, 0), (1, 1, 1), rgb_atas, double_sided=True)

    # Tiga cincin menyempit lalu satu ujung: tiap faset datar supaya cahaya
    # senja menggambar patahan batu, bukan gumpalan halus.
    cincin = [[(x, y_atas, z) for x, z in tepi]]
    for skala, turun in ((0.86, dalam * 0.18), (0.55, dalam * 0.55), (0.24, dalam * 0.85)):
        cincin.append([(cx + (x - cx) * skala * rng.uniform(0.9, 1.08),
                        y_atas - turun * rng.uniform(0.85, 1.15),
                        cz + (z - cz) * skala * rng.uniform(0.9, 1.08)) for x, z in tepi])
    ujung = (cx + rng.uniform(-1, 1), y_atas - dalam, cz + rng.uniform(-1, 1))
    bawah = []
    for k in range(len(cincin) - 1):
        a_, b_ = cincin[k], cincin[k + 1]
        for i in range(n):
            j = (i + 1) % n
            bawah.extend([a_[i], b_[i], b_[j], a_[i], b_[j], a_[j]])
    for i in range(n):
        bawah.extend([cincin[-1][i], ujung, cincin[-1][(i + 1) % n]])
    _part(world, _mesh(bawah), (0, 0, 0), (1, 1, 1), (132, 112, 98), double_sided=True)


def _lautan_awan(world, rng, cx, cz):
    from game.scenes.fx_suasana import pijar
    # Dasar di bawah awan sengaja lebih dalam: gumpalan baru terbaca sebagai
    # awan kalau ada bayangan senja di antaranya.
    pijar(world, 'plane', (cx, -19.0, cz), (900, 1, 900), (168, 104, 104))
    for _ in range(190):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(24, 240)
        x, z = cx + math.cos(a) * d, cz + math.sin(a) * d
        y = rng.uniform(-14.0, -9.5)
        s = rng.uniform(8, 22)
        v = rng.randint(0, 2)
        pijar(world, _gumpal((255, 236, 214), (206 - v * 8, 150, 150 + v * 6)), (x, y, z),
              (s, s * rng.uniform(0.3, 0.45), s * rng.uniform(0.6, 1.0)), (255, 255, 255))


def _gumpal(atas, perut):
    """Bola bergradasi terpanggang dari puncak (atas) ke perut (bawah).

    Bola Ursina yang dicahayai toon-shader membentuk tepi berundak seperti
    tumpukan panekuk; gradasi halus di warna verteks tidak punya pita itu.
    """
    from ursina import Mesh, color
    lintang, bujur = 7, 12
    verts, cols, tris = [], [], []
    for i in range(lintang + 1):
        t = i / lintang
        a = math.pi * (t - 0.5)
        for j in range(bujur):
            b = j * math.tau / bujur
            verts.append((math.cos(a) * math.cos(b) * 0.5, math.sin(a) * 0.5, math.cos(a) * math.sin(b) * 0.5))
            k = t ** 0.8
            cols.append(color.rgb(*(perut[c] + (atas[c] - perut[c]) * k for c in range(3))))
    for i in range(lintang):
        for j in range(bujur):
            a0 = i * bujur + j
            a1 = i * bujur + (j + 1) % bujur
            b0, b1 = a0 + bujur, a1 + bujur
            tris.extend((a0, b0, b1, a0, b1, a1))
    return Mesh(vertices=verts, triangles=tris, colors=cols)


def _pulau_jauh(world, rng, cx, cz):
    for i in range(7):
        a = i * math.tau / 7 + rng.uniform(-0.25, 0.25)
        d = rng.uniform(62, 120)
        x, z = cx + math.cos(a) * d, cz + math.sin(a) * d
        y = rng.uniform(-5, 9)
        r = rng.uniform(4, 9)
        _pulau(world, x, z, r, y, r * 1.6, (150, 158, 108), rng, n=24, acak=1.4)
        if i % 2 == 0:
            # Candi kecil di pulau seberang: penanda bahwa kahyangan itu luas.
            for k, (w, h) in enumerate(((3.0, 1.2), (2.2, 1.3), (1.4, 1.0))):
                _part(world, 'cube', (x, y + 0.6 + k * 1.2, z), (w, h, w), BATU)
            _part(world, 'sphere', (x, y + 4.0, z), (0.9, 1.1, 0.9), EMAS)
        else:
            from game.scenes.fx_suasana import pijar, halo
            _part(world, 'cylinder', (x, y + 1.0, z), (0.4, 2.0, 0.4), (110, 84, 60))
            pijar(world, 'sphere', (x, y + 2.6, z), (2.4, 1.8, 2.4), (255, 206, 110))
            halo(world, (x, y + 2.6, z), 4.0, (255, 200, 110), kuat=.30)


def _candi(world, tx, ty, lebar_ubin):
    """Candi bergaya Jawa Tengah di blok KUIL: batur, kaki, tubuh, atap tiga tingkat."""
    from game.scenes.fx_suasana import pijar, kolam_cahaya
    cx, cz = tx * TS, ty * TS
    W = lebar_ubin * TS
    lapis = [(W * 1.04, 0.9, BATU_TUA), (W * 0.88, 0.6, BATU), (W * 0.74, 1.2, BATU),
             (W * 0.6, 3.0, (138, 128, 114))]
    y = GROUND_H
    for lebar, tinggi, rgb in lapis:
        _part(world, 'cube', (cx, y + tinggi / 2, cz), (lebar, tinggi, lebar), rgb)
        _part(world, 'cube', (cx, y + tinggi, cz), (lebar * 1.03, 0.14, lebar * 1.03), EMAS)
        y += tinggi
    tubuh_atas = y
    lebar_tubuh = W * 0.6
    # Relung di keempat sisi; yang menghadap gerbang (+z) berpintu menyala.
    for sx, sz in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        px = cx + sx * (lebar_tubuh / 2 + 0.02)
        pz = cz + sz * (lebar_tubuh / 2 + 0.02)
        uk = (1.5 if sz else 0.12, 2.2, 0.12 if sz else 1.5)
        if sz == 1:
            pijar(world, 'cube', (px, tubuh_atas - 1.5, pz), uk, (255, 196, 110))
            kolam_cahaya(world, cx, cz + lebar_tubuh / 2 + 2.6, 3.2, (255, 180, 90), kuat=.35)
        else:
            _part(world, 'cube', (px, tubuh_atas - 1.5, pz), uk, (52, 46, 44))
        _part(world, 'cube', (px + sx * 0.04, tubuh_atas - 0.25, pz + sz * 0.04),
              (2.1 if sz else 0.2, 0.35, 0.2 if sz else 2.1), EMAS)
    # Atap tiga tingkat, tiap sudut bermahkota ratna kecil.
    for k in range(3):
        lebar = lebar_tubuh * (0.92 - k * 0.18)
        _part(world, 'cube', (cx, y + 0.35, cz), (lebar, 0.7, lebar), (130 - k * 6, 122 - k * 6, 110 - k * 6))
        y += 0.7
        for sx in (-1, 1):
            for sz in (-1, 1):
                _part(world, 'sphere', (cx + sx * lebar * 0.42, y + 0.18, cz + sz * lebar * 0.42),
                      (0.42, 0.5, 0.42), EMAS)
    _part(world, 'sphere', (cx, y + 0.55, cz), (1.5, 1.2, 1.5), EMAS)
    _part(world, 'cylinder', (cx, y + 1.6, cz), (0.32, 1.8, 0.32), EMAS)
    # Tangga di sisi gerbang.
    for i in range(4):
        _part(world, 'cube', (cx, GROUND_H + 0.2 + i * 0.32, cz + W * 0.52 + 1.5 - i * 0.42),
              (2.2, 0.32, 0.5), BATU)


def _bata(world, tx, ty, gold):
    """Satu ruas tembok bata keliling; sudut tembok dapat menara bermahkota emas."""
    x, z = tx * TS, ty * TS
    _part(world, 'cube', (x, GROUND_H + 0.65, z), (TS * 1.0, 1.3, TS * 1.0), BATA)
    _part(world, 'cube', (x, GROUND_H + 1.39, z), (TS * 1.06, 0.18, TS * 1.06), BATU)
    lurus_h = (tx + 1, ty) in gold and (tx - 1, ty) in gold
    lurus_v = (tx, ty + 1) in gold and (tx, ty - 1) in gold
    if not (lurus_h or lurus_v):
        _part(world, 'cube', (x, GROUND_H + 1.9, z), (1.0, 1.0, 1.0), BATA)
        _part(world, 'sphere', (x, GROUND_H + 2.6, z), (0.55, 0.7, 0.55), EMAS)


def _candi_bentar(world, tx, ty, pusat_x):
    """Separuh gerbang terbelah: sisi dalam rata, sisi luar bertangga."""
    from game.scenes.fx_suasana import pijar
    x, z = tx * TS, ty * TS
    arah = 1 if tx < pusat_x else -1
    yy = GROUND_H
    for w, h in ((1.9, 2.2), (1.6, 1.4), (1.3, 1.1), (0.9, 0.9)):
        c = x + arah * (1.9 - w) / 2
        _part(world, 'cube', (c, yy + h / 2, z), (w, h, 1.9), BATA)
        _part(world, 'cube', (c, yy + h, z), (w * 1.05, 0.12, 1.95), BATU)
        yy += h
    pijar(world, 'sphere', (x, yy + 0.3, z), (0.35, 0.45, 0.35), (255, 220, 140))


def _tiang_pelita(world, tx, ty):
    from game.scenes.fx_suasana import pijar, halo, kolam_cahaya
    x, z = tx * TS, ty * TS
    _part(world, 'cube', (x, GROUND_H + 0.2, z), (1.1, 0.4, 1.1), BATU_TUA)
    _part(world, 'cylinder', (x, GROUND_H + 1.3, z), (0.5, 2.2, 0.5), BATU)
    _part(world, 'cube', (x, GROUND_H + 2.5, z), (0.9, 0.25, 0.9), EMAS)
    pijar(world, 'sphere', (x, GROUND_H + 2.85, z), (0.42, 0.5, 0.42), (255, 210, 120))
    halo(world, (x, GROUND_H + 2.9, z), 1.6, (255, 190, 100), kuat=.4)
    kolam_cahaya(world, x, z, 2.6, (255, 170, 80), kuat=.3)


def _candi_kecil(world, tx, ty):
    """Candi perwara: penanda arah mata angin di tepi kahyangan."""
    from game.scenes.fx_suasana import pijar, kolam_cahaya
    x, z = tx * TS, ty * TS
    y = GROUND_H
    for w, h, rgb in ((1.95, 0.6, BATU_TUA), (1.6, 1.5, (138, 128, 114)), (1.3, 0.5, BATU),
                      (1.0, 0.5, BATU), (0.7, 0.5, BATU)):
        _part(world, 'cube', (x, y + h / 2, z), (w, h, w), rgb)
        y += h
        _part(world, 'cube', (x, y, z), (w * 1.05, 0.08, w * 1.05), EMAS)
    _part(world, 'sphere', (x, y + 0.35, z), (0.55, 0.6, 0.55), EMAS)
    _part(world, 'cylinder', (x, y + 0.9, z), (0.12, 0.8, 0.12), EMAS)
    # Relung bercahaya di keempat sisi tubuh candi.
    for sx, sz in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        pijar(world, 'cube', (x + sx * 0.81, GROUND_H + 1.3, z + sz * 0.81),
              (0.5 if sz else 0.04, 0.8, 0.04 if sz else 0.5), (255, 200, 120))
    kolam_cahaya(world, x, z, 3.0, (255, 178, 90), kuat=.30)


def _petirtaan(world, kolam, pilar):
    """Kolam suci: air memancarkan cahaya, dibingkai batu dan pilar bermahkota."""
    from game.scenes.fx_suasana import pijar, halo, kolam_cahaya, Partikel
    for tx, ty in kolam:
        x, z = tx * TS, ty * TS
        for sx, sz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            _part(world, 'cube', (x + sx * TS * 0.47, GROUND_H + 0.25, z + sz * TS * 0.47),
                  (0.22 if sx else TS * 1.0, 0.5, TS * 1.0 if sx else 0.22), BATU)
        _part(world, 'cube', (x, GROUND_H - 0.15, z), (TS * 0.9, 0.2, TS * 0.9), (60, 72, 78))
        pijar(world, 'plane', (x, GROUND_H + 0.12, z), (TS * 0.86, 1, TS * 0.86), (120, 214, 210))
        halo(world, (x, GROUND_H + 0.9, z), 2.6, (150, 230, 220), kuat=.30)
        kolam_cahaya(world, x, z, 4.5, (140, 220, 210), kuat=.28)
        Partikel(world, x - 0.8, x + 0.8, z - 0.8, z + 0.8, GROUND_H + 0.2, GROUND_H + 3.5, 14,
                 (190, 245, 235), ukuran=.05, naik=.35, goyang=.12, seed=tx * 3 + ty)
    for tx, ty in pilar:
        x, z = tx * TS, ty * TS
        _part(world, 'cube', (x, GROUND_H + 0.2, z), (1.3, 0.4, 1.3), BATU_TUA)
        _part(world, 'cube', (x, GROUND_H + 1.4, z), (0.8, 2.0, 0.8), (138, 128, 114))
        _part(world, 'cube', (x, GROUND_H + 2.5, z), (1.15, 0.22, 1.15), EMAS)
        _part(world, 'sphere', (x, GROUND_H + 2.85, z), (0.7, 0.55, 0.7), EMAS)
        pijar(world, 'sphere', (x, GROUND_H + 3.25, z), (0.28, 0.36, 0.28), (255, 220, 140))


def _kalpataru(world, x, z, rng):
    from game.scenes.fx_suasana import pijar, halo, kolam_cahaya, Partikel
    _part(world, 'cube', (x, GROUND_H + 0.25, z), (2.2, 0.5, 2.2), BATU)
    _part(world, 'cube', (x, GROUND_H + 0.55, z), (1.7, 0.12, 1.7), EMAS)
    _part(world, 'cylinder', (x, GROUND_H + 1.9, z), (0.42, 2.8, 0.42), (118, 86, 58))
    for k in range(3):
        a = k * math.tau / 3
        _part(world, 'cylinder', (x + math.cos(a) * 0.5, GROUND_H + 3.1, z + math.sin(a) * 0.5),
              (0.16, 1.4, 0.16), (118, 86, 58), rotation=(math.cos(a) * 35, 0, math.sin(a) * 35))
    # Tajuk bertingkat seperti gunungan wayang: lebar di bawah, runcing di atas.
    # Gumpalan luarnya diberi cahaya scene supaya bervolume; inti di dalamnya
    # menyala sendiri sehingga pohon tetap terbaca bercahaya.
    for k, (r, yy) in enumerate(((2.4, 3.6), (1.9, 4.5), (1.3, 5.3), (0.7, 5.95))):
        for j in range(5 - k):
            a = j * math.tau / max(1, 5 - k) + k
            ox, oz = math.cos(a) * r * 0.42, math.sin(a) * r * 0.42
            pijar(world, _gumpal((255, 232 - k * 4, 140 + k * 14), (190, 118 + k * 8, 40)),
                  (x + ox, GROUND_H + yy, z + oz), (r, r * 0.62, r), (255, 255, 255))
        pijar(world, 'sphere', (x, GROUND_H + yy, z), (r * 0.9, r * 0.5, r * 0.9),
              (255, 226, 150))
    halo(world, (x, GROUND_H + 4.4, z), 4.5, (255, 200, 110), kuat=.16)
    kolam_cahaya(world, x, z, 5.0, (255, 186, 90), kuat=.26)
    Partikel(world, x - 3, x + 3, z - 3, z + 3, GROUND_H + 1.0, GROUND_H + 6.5, 22,
             (255, 214, 120), ukuran=.07, naik=-.25, goyang=.45, seed=int(x + z))


def _pelita(world, x, z):
    from game.scenes.fx_suasana import pijar, halo, kolam_cahaya
    _part(world, 'cube', (x, GROUND_H + 0.45, z), (0.9, 0.9, 0.9), BATU)
    _part(world, 'sphere', (x, GROUND_H + 1.0, z), (1.0, 0.35, 1.0), EMAS)
    pijar(world, 'sphere', (x, GROUND_H + 1.3, z), (0.26, 0.42, 0.26), (255, 214, 130))
    halo(world, (x, GROUND_H + 1.35, z), 1.4, (255, 190, 100), kuat=.45)
    kolam_cahaya(world, x, z, 2.4, (255, 170, 80), kuat=.30)


def _gapura_portal(world, portals):
    """Gapura paduraksa di atas tangga turun; tiangnya di ubin penghalang sebelahnya."""
    from game.scenes.fx_suasana import kolam_cahaya, halo
    xs = [p[0] for p in portals]
    y = portals[0][1]
    x0, x1 = (min(xs) - 1) * TS, (max(xs) + 1) * TS
    z = y * TS
    for x in (x0, x1):
        _part(world, 'cube', (x, GROUND_H + 0.2, z), (1.3, 0.4, 1.3), BATU_TUA)
        _part(world, 'cube', (x, GROUND_H + 1.8, z), (0.9, 3.2, 0.9), BATA)
        _part(world, 'cube', (x, GROUND_H + 3.5, z), (1.1, 0.2, 1.1), BATU)
    lebar = x1 - x0
    _part(world, 'cube', ((x0 + x1) / 2, GROUND_H + 3.85, z), (lebar + 1.2, 0.5, 1.0), BATA)
    for k, w in enumerate((lebar + 0.6, lebar - 0.6, lebar * 0.45)):
        _part(world, 'cube', ((x0 + x1) / 2, GROUND_H + 4.3 + k * 0.42, z), (w, 0.42, 0.9), BATU)
    _part(world, 'sphere', ((x0 + x1) / 2, GROUND_H + 5.8, z), (0.6, 0.7, 0.6), EMAS)
    # Tangga menurun ke gua: anak tangga makin gelap, cahaya teal dari bawah.
    for tx in xs:
        for i in range(4):
            _part(world, 'cube', (tx * TS, GROUND_H + 0.1 - i * 0.22, z - 0.7 + i * 0.45),
                  (TS * 0.9, 0.2, 0.45), (92 - i * 14, 96 - i * 14, 100 - i * 12))
        kolam_cahaya(world, tx * TS, z + 0.6, 1.8, (110, 210, 220), kuat=.35)
        halo(world, (tx * TS, GROUND_H + 0.4, z + 0.6), 1.2, (110, 210, 220), kuat=.3)


def _taman(world, rng, tiles, hindari):
    """Lumut keemasan dan rumpun bunga di pelataran, tidak di jalan batu."""
    from game.scenes.rock_sanctuary import _ground_patch
    from game.scenes.fx_suasana import pijar
    bebas = [(x, y) for y, row in enumerate(tiles) for x, t in enumerate(row)
             if t == CLOUD and (x, y) not in hindari]
    rng.shuffle(bebas)
    for x, y in bebas[:14]:
        _ground_patch(world, x * TS, y * TS, rng.uniform(1.0, 2.0), rng.uniform(0.9, 1.8),
                      (158, 162, 100), x * 7 + y, GROUND_H + 0.012)
    for x, y in bebas[14:34]:
        for _ in range(rng.randint(3, 6)):
            pijar(world, 'sphere', (x * TS + rng.uniform(-0.7, 0.7), GROUND_H + 0.1,
                                    y * TS + rng.uniform(-0.7, 0.7)), 0.16,
                  rng.choice(((255, 236, 236), (255, 200, 214), (255, 232, 160))))


def _jalan(world, dari, ke, tiles):
    """Jalan batu selebar tiga ubin dari portal ke pusat, hanya di ubin pijakan."""
    (x0, y0), (x1, y1) = dari, ke
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    tegak = abs(y1 - y0) >= abs(x1 - x0)
    sudah = set()
    for i in range(n + 1):
        cx = round(x0 + (x1 - x0) * i / n)
        cy = round(y0 + (y1 - y0) * i / n)
        for d in (-1, 0, 1):
            x, y = (cx + d, cy) if tegak else (cx, cy + d)
            if (x, y) in sudah or tiles[y][x] != CLOUD:
                continue
            sudah.add((x, y))
            _part(world, 'cube', (x * TS, GROUND_H + 0.02, y * TS), (TS * 0.94, 0.04, TS * 0.94),
                  (168, 156, 134) if (x + y) % 2 else (152, 142, 124))
    return sudah


def build_kahyangan(world, scene):
    from game.config import W as AIR, WALKABLE
    from game.scenes.fx_suasana import Partikel
    rng = random.Random(1945)
    for e in world._tile_ents:
        e.enabled = False
    for e in world._obj_ents:
        e.enabled = False
    world._wall_ents.clear()

    tiles = scene.tiles
    def sel(tid):
        return [(x, y) for y, row in enumerate(tiles) for x, t in enumerate(row) if t == tid]
    gold, kuil, shrine, kolam = set(sel(GOLD_W)), sel(KUIL), sel(SHRINE), sel(AIR)

    if kolam:
        px, py = kolam[0]
    elif kuil:
        px = sum(x for x, _ in kuil) / len(kuil)
        py = sum(y for _, y in kuil) / len(kuil)
    else:
        px, py = _PUSAT
    pijakan = [(x, y) for y, row in enumerate(tiles) for x, t in enumerate(row) if t in WALKABLE]
    r = max(abs(x - px) + abs(y - py) for x, y in pijakan) + 0.62

    cx, cz = px * TS, py * TS
    _pulau(world, cx, cz, r * TS, GROUND_H, 24, LANTAI, rng)
    _lautan_awan(world, rng, cx, cz)
    _pulau_jauh(world, rng, cx, cz)

    portal = [(p[0], p[1]) for p in scene.portals]
    ubin_jalan = set()
    if portal:
        ubin_jalan = _jalan(world, portal[0], (round(px), round(py)), tiles)
        _gapura_portal(world, portal)
    _taman(world, rng, tiles, ubin_jalan)

    if kuil:
        lebar = max(x for x, _ in kuil) - min(x for x, _ in kuil) + 1
        _candi(world, px, py, lebar)

    def tetangga(t):
        return sum((t[0] + dx, t[1] + dy) in gold for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    air = set(kolam)
    dekat_kolam = {t for t in gold if any((t[0] + dx, t[1] + dy) in air
                                          for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    _petirtaan(world, kolam, dekat_kolam)
    gerbang = {t for t in gold if kuil and t[1] == 16}
    tunggal = {t for t in gold - dekat_kolam if tetangga(t) == 0} | gerbang
    jauh = [t for t in tunggal - gerbang if abs(t[0] - px) + abs(t[1] - py) >= 8]
    utara = min(jauh, key=lambda t: t[1]) if jauh and not shrine else None
    for t in tunggal:
        if t in gerbang:
            _candi_bentar(world, t[0], t[1], px)
        elif t == utara:
            _kalpataru(world, t[0] * TS, t[1] * TS, rng)
        elif t in jauh:
            _candi_kecil(world, *t)
        else:
            _tiang_pelita(world, *t)
    for t in gold - dekat_kolam - tunggal:
        _bata(world, t[0], t[1], gold)

    for i, (x, y) in enumerate(sorted(shrine, key=lambda p: abs(p[0] - px))):
        if i == 0:
            _kalpataru(world, x * TS, y * TS, rng)
        else:
            _pelita(world, x * TS, y * TS)

    Partikel(world, cx - r * TS, cx + r * TS, cz - r * TS, cz + r * TS, GROUND_H + 0.3,
             GROUND_H + 7.0, 35, (255, 220, 150), ukuran=.06, naik=.22, goyang=.3, seed=7)
