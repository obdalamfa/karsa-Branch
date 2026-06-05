from game.config import *
from game.scenes.scene_base import Scene
import random
import math

def build_lake():
    """
    Danau Karsa — danau yang diam dan sedikit menakutkan.
    Airnya keruh, dermaga kayu lapuk, perahu tua tertambat.
    Di tepi: pohon-pohon tua menjulang, bangkai akar terendam.
    Vibe: Disco Elysium's fishing village — still, foggy, melancholic.
    """
    W_, H_ = 18, 14
    m = [[G] * W_ for _ in range(H_)]

    # ── Air danau (keruh) ──
    for y in range(2, 12):
        for x in range(3, 16): m[y][x] = W

    # ── Dermaga lapuk (DCK) ──
    for x in range(3, 8): m[7][x] = DCK
    m[8][7] = DCK
    m[6][4] = DCK   # dermaga kecil tambahan
    m[6][5] = DCK

    # ── Perahu tua tertambat ──
    m[7][9]  = BOT
    m[5][12] = BOT  # perahu kedua, lebih jauh — mungkin sudah tenggelam setengah

    # ── Teratai/eceng gondok (LLY) di tengah danau ──
    for x, y in [(5, 4), (12, 5), (14, 8), (11, 10), (6, 10), (13, 3), (8, 9), (10, 4)]:
        if 0 <= x < W_ and 0 <= y < H_ and m[y][x] == W:
            m[y][x] = LLY

    # ── Jalan masuk dari kota ──
    m[7][0]  = P;  m[8][0]  = P
    m[7][1]  = P;  m[8][1]  = P
    m[7][2]  = DCK; m[8][2] = DCK  # jembatan menuju dermaga

    # ── Pohon tua di tepi danau ──
    rng = random.Random(50)
    for y in range(H_):
        for x in [0, 1, W_-2, W_-1]:
            if rng.random() < 0.5: m[y][x] = TR if rng.random() > 0.3 else DT

    # Pohon mati di tepi air (akarnya terendam)
    m[12][2] = DT
    m[3][3]  = DT
    m[2][8]  = DT
    m[11][14]= DT
    m[3][15] = DT

    # ── Altar kecil di tepi danau (persembahan untuk air) ──
    m[13][4] = SHRINE

    # ── Tumpukan jaring/alat nelayan yang ditinggal ──
    m[13][7]  = DEBRIS
    m[13][11] = DEBRIS
    m[1][14]  = DEBRIS

    # ── Lantern di dermaga (untuk nelayan malam) ──
    m[7][4]  = LN
    m[8][6]  = LN

    return Scene('lake', 'Danau Karsa', m, portals=[
        (0, 7, 'town', 28, 14),
        (0, 8, 'town', 28, 15),
    ])
