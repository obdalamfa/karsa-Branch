from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_farm():
    """
    Kebun Paman Arsa — lahan bertani urban di pinggiran kota suram.
    Bukan ladang idilis: pagar kawat berkarat, tumpukan kompos, drum berkarat
    untuk berkebun, tanah setengah subur setengah kering.
    Farming mechanics tetap utuh: D tiles bisa dicangkul/ditanam.
    """
    W_, H_ = 25, 18
    m = [[G] * W_ for _ in range(H_)]

    # ── Rumah pemain (eksterior) ── portal ke house interior
    for y in range(2, 4):
        for x in range(2, 5): m[y][x] = H

    # ── Jalan setapak dari teras ke jalan kebun ──
    m[4][3] = P
    m[4][4] = P
    for y in range(5, 14): m[y][4] = P

    # ── Lahan pertanian utama (bisa dicangkul) ──
    # Petak kiri-tengah
    for y in range(6, 12):
        for x in range(6, 11): m[y][x] = D

    # Petak kanan-tengah
    for y in range(6, 12):
        for x in range(12, 18): m[y][x] = D

    # ── Kandang ternak (sisi kanan-atas) ──
    for y in range(2, 8):
        for x in range(15, 22):
            m[y][x] = STR_T
            if y in (2, 7) or x in (15, 21): m[y][x] = PEN
    m[7][18] = GT   # pintu kandang

    # ── Pagar keliling (kawat berkarat) ──
    for x in range(W_):
        m[0][x] = FN
        m[H_-1][x] = FN
    for y in range(H_):
        m[y][0] = FN
        m[y][W_-1] = P if 12 < y < 16 else FN

    # ── Jalan utama kebun (E-W) ──
    for x in range(4, W_):
        m[14][x] = P
        m[15][x] = P

    # ── Altar kecil di pojok — persembahan sebelum bertani ──
    m[13][2] = SHRINE

    # ── Tumpukan kompos/sampah organik di sudut ──
    m[12][6]  = DEBRIS
    m[5][20]  = DEBRIS
    m[16][20] = DEBRIS

    # ── Pohon tua di sudut (pembatas visual) ──
    m[1][6]  = TR
    m[1][11] = TR
    m[1][20] = DT   # pohon mati di sudut kanan atas
    m[16][6] = DT   # pohon mati di selatan lahan

    # ── Palm tua — sisa kebun lama sebelum jadi lahan ──
    m[1][23] = PALM

    # ── Jemuran di dekat rumah ──
    m[5][2] = LAUNDRY

    return Scene('farm', 'Kebun Paman Arsa', m, portals=[
        (3,  4, 'house', 7, 9),
        (24, 14, 'town',  1, 14),
        (24, 15, 'town',  1, 15),
    ])
