from game.config import *
from game.scenes.scene_base import Scene

def build_swarga():
    W_, H_ = 31, 31
    m = [[CV_F] * W_ for _ in range(H_)]
    cx, cy = 15, 15

    # ── Pulau awan (diamond) ────────────────────────────────────────────────
    for y in range(H_):
        for x in range(W_):
            if abs(x - cx) + abs(y - cy) <= 13:
                m[y][x] = CLOUD

    # ── Tembok luar candi (compound) — 9×9, center di (15, 11) ─────────────
    # x = 11..19, y = 7..15
    for y in range(7, 16):
        for x in range(11, 20):
            if x == 11 or x == 19 or y == 7 or y == 15:
                m[y][x] = GOLD_W

    # ── Tubuh utama kuil (KUIL) — 5×5, center di (15, 10) ──────────────────
    # x = 13..17, y = 8..12
    for y in range(8, 13):
        for x in range(13, 18):
            m[y][x] = KUIL

    # ── Gerbang masuk di dinding selatan compound ────────────────────────────
    m[15][14] = CLOUD
    m[15][15] = CLOUD
    m[15][16] = CLOUD

    # ── Tiang gerbang (pillar) di selatan compound ───────────────────────────
    m[16][13] = GOLD_W
    m[16][17] = GOLD_W

    # ── Taman suci tengah ─────────────────────────────────────────────────────
    m[17][15] = SHRINE   # altar taman

    # ── 4 shrine di taman ─────────────────────────────────────────────────────
    m[17][11] = SHRINE
    m[17][19] = SHRINE
    m[19][11] = SHRINE
    m[19][19] = SHRINE

    # ── Pilar emas penjaga taman ──────────────────────────────────────────────
    m[18][11] = GOLD_W
    m[18][19] = GOLD_W

    return Scene('swarga', 'Swarga — Negeri Awan', m, portals=[
        (14, 22, 'naga_cave', 7, 6),
        (15, 22, 'naga_cave', 7, 6),
        (16, 22, 'naga_cave', 7, 6),
    ], indoor=False)
