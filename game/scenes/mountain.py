from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_mountain():
    """
    Lereng Gunung — bekas lahan perkebunan karet yang ditinggalkan.
    Pohon-pohon tua masih berdiri, tapi sudah separuh mati.
    Jalan setapak berlumpur menyisir lereng. Di puncak: mulut gua.
    Vibe: Disco Elysium's outskirts — jauh dari kota, tapi belum benar-benar alam.
    """
    W_, H_ = 30, 25
    m = [[G] * W_ for _ in range(H_)]
    rng = random.Random(42)

    # ── Puncak gunung (dinding gua) ──
    for y in range(0, 4):
        for x in range(W_): m[y][x] = CV_W
    m[3][14] = DR
    m[3][15] = DR

    # ── Vegetasi lereng — campuran pohon hidup, mati, dan palm sisa perkebunan ──
    for y in range(4, H_):
        for x in range(W_):
            r = rng.random()
            if x < 11 or x > 19:         # sisi kiri-kanan: vegetasi lebat
                if r < 0.18:   m[y][x] = TR    # pohon hidup
                elif r < 0.28: m[y][x] = DT    # pohon mati
                elif r < 0.33 and y > 8: m[y][x] = PALM  # palm bekas kebun
            elif y > 10:                  # tengah-bawah: agak terbuka tapi ada sisa
                if r < 0.06:   m[y][x] = DT
                elif r < 0.09: m[y][x] = TR

    # ── Jalan setapak berlumpur (D) menyisir lereng ──
    for y in range(4, H_):
        m[y][14] = D
        m[y][15] = D

    # Percabangan jalan kiri (menuju kuburan)
    for y in range(20, 25): m[y][2] = P
    for x in range(2, 14):  m[20][x] = P

    # ── Area kuburan lama di lereng kiri (beberapa nisan) ──
    for y in range(20, 23):
        for x in range(3, 7):
            if (x + y) % 2 == 0: m[y][x] = GR

    # ── Altar/shrine di persimpangan jalan ──
    m[12][12] = SHRINE
    m[18][16] = SHRINE

    # ── Sisa peralatan perkebunan yang ditinggal (DEBRIS) ──
    m[5][3]  = DEBRIS
    m[8][25] = DEBRIS
    m[11][8] = DEBRIS
    m[15][22]= DEBRIS
    m[19][5] = DEBRIS

    # ── Lantern di tepi jalan (beberapa mati) ──
    m[8][13]  = LN
    m[12][16] = LN
    m[18][13] = LN

    return Scene('mountain', 'Lereng Gunung', m, builder=mountain_builder, portals=[
        (14, 24, 'town',      14,  1),
        (15, 24, 'town',      15,  1),
        (14,  3, 'naga_cave',  7,  9),
        (15,  3, 'naga_cave',  7,  9),
        (2,  24, 'cemetery',   8,  1),
    ])


def mountain_builder(world):
    """Lereng gunung: rumpun bambu, pohon mati, & batu/karung tersebar (M2)."""
    from .props import default_prop_builder, scatter_obj_props
    default_prop_builder(world, world.scene_obj)
    scatter_obj_props(world, world.scene_obj, [
        ('pohon_bambu', 1.4), ('pohon_mati', 1.0),
        ('prop_karung', 0.9), ('pagar_bambu', 1.0),
    ], count=12, seed=21)
