"""Ruang penjaga, pelataran tengah, dan lorong menuju kedalaman."""
from game.config import CV_F, CV_W, DR, LN, CRYS, STAIRS_DOWN, STAIRS_UP
from game.scenes.scene_base import Scene
from game.scenes.layout import blank, border, rect, scatter
from game.scenes.zone_paint import Zone


def build_naga_cave():
    m = blank(15, 12, CV_F)
    border(m, CV_W)
    # Bahu batu mengapit ruang suci tanpa menutup sumbu masuk.
    rect(m, 1, 1, 3, 2, CV_W)
    rect(m, 11, 1, 13, 2, CV_W)
    rect(m, 1, 5, 2, 7, CV_W)
    rect(m, 12, 5, 13, 6, CV_W)
    scatter(m, [(4, 2), (10, 2), (3, 6), (11, 6)], CRYS)
    scatter(m, [(5, 3), (9, 3), (1, 9), (5, 10), (9, 10), (13, 7)], LN)
    rect(m, 6, 1, 8, 1, CV_W)
    # Pertahankan koordinat portal dan titik kembali dari save/dungeon.
    m[11][7] = DR
    m[5][7] = STAIRS_UP
    m[10][13] = STAIRS_DOWN
    from game.scenes.rock_sanctuary import build_cavern
    scene = Scene('naga_cave', 'Gua Sang Hyang', m, portals=[
        (7, 11, 'mountain', 14, 4),
        (7, 5, 'swarga', 15, 20),
    ], indoor=True, has_horizon=False, paint=[
        # Alas obor memakai lantai batu yang sama, bukan ubin kayu default.
        Zone(x, y, x, y, base='cave_floor',
             light=(180, 174, 189), dark=(162, 156, 173))
        for y, row in enumerate(m) for x, tile in enumerate(row) if tile == LN
    ])

    scene.builder = lambda world: build_cavern(world, scene)
    return scene
