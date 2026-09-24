"""Lereng berbatu dengan jalur desa, pelataran gua, dan cabang pemakaman."""
from game.config import G, D, P, TR, DR, DT, CV_W
from game.scenes.scene_base import Scene
from game.scenes.layout import blank, rect, border, hline, vline, scatter
from game.scenes.zone_paint import Zone, BATU_ALUN


def build_mountain():
    m = blank(30, 25, G)

    # Batas dan bahu tebing membentuk lembah, menyempit ke mulut gua.
    # Geometri tetap memakai ubin blocking agar cocok dengan pathfinder.
    border(m, CV_W)
    rect(m, 0, 0, 29, 2, CV_W)
    rect(m, 1, 3, 10, 6, CV_W)
    rect(m, 19, 3, 28, 6, CV_W)
    rect(m, 1, 7, 5, 10, CV_W)
    rect(m, 24, 7, 28, 10, CV_W)
    rect(m, 11, 3, 18, 10, D)
    rect(m, 6, 7, 23, 14, D)

    # Pepohonan berkelompok di kaki lereng, bukan mengacak jalur pemain.
    scatter(m, [(2, 12), (4, 13), (2, 16), (5, 16), (7, 18),
                (10, 16), (10, 21), (6, 22), (8, 23),
                (25, 12), (27, 14), (24, 16), (27, 18),
                (21, 19), (24, 21), (27, 23), (19, 23)], TR)
    scatter(m, [(7, 9), (22, 9), (9, 12), (21, 13)], DT)

    # Dua ubin penuh dari desa ke gua, termasuk titik kedatangan lama.
    vline(m, 14, 3, 24, P, thick=2)
    # Cabang pemakaman menyambung ke jalan utama, bukan berhenti di rumput.
    hline(m, 2, 15, 19, P, thick=2)
    vline(m, 2, 19, 23, P, thick=2)
    m[24][2] = P
    m[3][14] = m[3][15] = DR

    from game.scenes.rock_sanctuary import build_mountain_landscape
    scene = Scene('mountain', 'Lereng Gunung', m, portals=[
        (14, 24, 'town', 14, 1), (15, 24, 'town', 15, 1),
        (14, 3, 'naga_cave', 7, 9), (15, 3, 'naga_cave', 7, 9),
        (2, 24, 'cemetery', 8, 1),
    ], paint=[
        Zone(11, 3, 18, 6, **BATU_ALUN),
        Zone(6, 7, 23, 14, **BATU_ALUN),
    ])

    scene.builder = lambda world: build_mountain_landscape(world, scene)
    return scene
