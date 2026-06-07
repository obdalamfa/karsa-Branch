from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_cemetery():
    """
    Kuburan Tua — bukan tempat seram, tapi tempat yang tragis dan melankolis.
    Ala Disco Elysium: nisan-nisan buruh perkebunan yang terlupakan.
    Jalan setapak berlumpur, pohon-pohon reot, lantern yang nyaris padam.
    """
    W_, H_ = 18, 22
    m = [[D] * W_ for _ in range(H_)]

    # ── Pagar keliling (pohon mati sebagai batas alami) ──
    for x in range(W_):
        m[0][x]      = DT
        m[H_-1][x]   = DT
    for y in range(H_):
        m[y][0]      = DT
        m[y][W_-1]   = DT

    # ── Pintu masuk + jalan setapak tengah ──
    m[0][8] = GT
    m[0][9] = GT
    for y in range(1, H_-1):
        m[y][8] = P
        m[y][9] = P

    # ── Baris nisan — lebih rapat dari sebelumnya ──
    grave_rows = [3, 6, 9, 12, 15, 18]
    grave_cols_left  = [2, 4, 6]
    grave_cols_right = [11, 13, 15]
    for row in grave_rows:
        for col in grave_cols_left + grave_cols_right:
            if 0 < row < H_-1 and 0 < col < W_-1:
                m[row][col] = GR

    # Baris nisan tambahan (orang yang terlupakan)
    for col in [3, 5, 12, 14]:
        for row in [4, 7, 10, 13, 16]:
            if 0 < row < H_-1: m[row][col] = GR

    # ── Lantern di persimpangan (beberapa mati = DT) ──
    m[2][2]  = LN
    m[2][15] = LN
    m[11][2] = LN    # padam
    m[11][15]= DT    # sudah tidak berfungsi
    m[19][2] = DT
    m[19][15]= LN

    # ── Pohon-pohon tua tersebar di kuburan ──
    m[5][7]  = DT
    m[10][3] = DT
    m[14][14]= DT
    m[7][12] = DT
    m[16][5] = DT
    m[18][10]= DT
    m[4][11] = TR    # satu pohon masih hidup — harapan yang tersisa

    # ── Altar memorial di tengah kuburan ──
    m[10][8] = SHRINE
    m[10][9] = SHRINE

    # ── Tumpukan barang lama yang ditinggal ──
    m[6][2]  = DEBRIS
    m[14][15]= DEBRIS

    return Scene('cemetery', 'Kuburan Tua', m, portals=[
        (8, 0, 'mountain', 2, 23),
        (9, 0, 'mountain', 2, 23),
    ])
